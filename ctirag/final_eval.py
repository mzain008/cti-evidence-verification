"""Scoring and reporting for the final independent benchmark (and the conflict trace of stress runs).

Metric definitions (all per question, then averaged with 95% bootstrap CIs):
  list_f1            ID-level F1 on answerable list questions (requested identifier kind only)
  claim_correct      verdict == gold (SUPPORTED / UNSUPPORTED / NOT_ENOUGH_INFO)
  uar                predicted identifiers not in gold / predicted identifiers
  stale_adoption     answer contains an identifier only an outdated release (or a revoked/withdrawn id) asserts
  injected_adoption  answer contains an identifier only an injected low-authority note asserts
  conflict detection the system output contains the CONFLICT flag (strict: OUTDATED does NOT count);
                     gold = meta.has_conflict. Precision / recall / F1 over all questions, false-positive rate
                     separately on clean questions and on questions with an AGREEING low-authority note
  resolution_correct on conflict questions: lower-authority conflicts -> no injected id adopted and (list) at
                     least one gold id kept / (claim) verdict correct; equal-authority conflicts -> every
                     identifier asserted by either authoritative source reported
  abstain_correct    on unanswerable questions: no identifier reported (claims: NOT_ENOUGH_INFO)
  flag_correct       the required lifecycle flag (REVOKED / WITHDRAWN / OUTDATED / CONFLICT), strict
  coverage / risk    answered = at least one id (claims: SUPPORTED/UNSUPPORTED); loss = 1 - F1 (claims: 0/1;
                     answering an unanswerable question = 1); risk = mean loss over answered questions
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

from .corpus import Corpus, extract_ids
from .evaluate import Plausibility, bootstrap_ci, holm, mcnemar_exact, paired_permutation, score_one

STRICT_FLAG = {"REVOKED": {"REVOKED", "DEPRECATED"}, "WITHDRAWN": {"WITHDRAWN"}, "OUTDATED": {"OUTDATED"},
               "CONFLICT": {"CONFLICT"}}
SYSTEM_LABEL = {"graph_oracle": "Graph oracle (no LLM, upper bound)", "naive": "Naive RAG", "kg_rag": "KG-RAG",
                "multihop": "Multi-hop RAG", "crag": "CRAG", "react_agent": "ReAct agent (A)",
                "graph_verifier": "Non-agentic graph verifier (B)", "evidence_agent": "Evidence-Aware Agent (C)",
                "agent_no_verify": "- verification", "agent_no_graph": "- graph verification",
                "agent_no_temporal": "- temporal verification", "agent_no_authority": "- authority verification",
                "agent_no_conflict": "- explicit conflict detection"}
ORDER = list(SYSTEM_LABEL)
AWARE = re.compile(r"conflict|disagree|contradict|inconsistent|low[- ]authority|lower[- ]authority|unverified|"
                   r"not authoritative|non-authoritative|community|blog|forum|wiki|note:|partner advisory|"
                   r"osint|notebook|threat exchange", re.I)


def ordered(systems):
    return [s for s in ORDER if s in systems] + sorted(set(systems) - set(ORDER))


# ---------------------------------------------------------------------------------------------
def score_final(questions: list[dict], results: dict[str, dict[str, dict]], c: Corpus) -> pd.DataFrame:
    pl = Plausibility(c)
    qmap = {q["qid"]: q for q in questions}
    rows = []
    for sysname, res in results.items():
        for qid, r in res.items():
            q = qmap.get(qid)
            if q is None:
                continue
            row = score_one(q, r, c, pl)
            m = q.get("meta", {})
            row["system"] = sysname
            row["category"] = m.get("category", q.get("subtype"))
            answerable = m.get("answerable", True)
            row["answerable"] = answerable
            is_claim = q["qtype"] == "claim"
            row["is_claim"] = is_claim
            flags = set(r.get("flags") or [])
            ids = set(r.get("ids") or [])
            gold = set(q["gold_ids"])
            # list questions without an answer: F1 is undefined, abstention is what is scored
            if not is_claim and not answerable:
                for k in ("f1", "precision", "recall", "exact"):
                    row[k] = np.nan
                row["abstain_correct"] = float(not ids)
            if is_claim and not answerable:
                row["abstain_correct"] = float(r.get("verdict") == "NOT_ENOUGH_INFO")
            row["list_f1"] = row.get("f1", np.nan) if (not is_claim and answerable) else np.nan
            # lifecycle flag, strict
            need = q.get("requires_flag")
            row["flag_correct"] = float(bool(flags & STRICT_FLAG[need])) if need else np.nan
            # conflicts
            has_c = bool(m.get("has_conflict", False))
            row["has_conflict"] = has_c
            row["pred_conflict"] = float("CONFLICT" in flags)
            row["conflict_detect_correct"] = float(row["pred_conflict"] == float(has_c))
            row["benign_note"] = row["category"] == "benign_note"
            inj = set(m.get("injected_ids", []))
            row["injected_adoption"] = float(bool(ids & inj)) if (inj and not is_claim) else np.nan
            if has_c:
                if m.get("conflict_kind") == "equal_authority":
                    row["resolution_correct"] = float(gold <= ids)
                elif is_claim:
                    row["resolution_correct"] = float(r.get("verdict") == q["gold_label"])
                else:
                    row["resolution_correct"] = float(not (ids & inj) and bool(ids & gold))
            else:
                row["resolution_correct"] = np.nan
            row["cached_calls"] = (r.get("usage") or {}).get("cached_calls", 0)
            row["conflicts_detected_by_code"] = len(r.get("conflicts") or [])
            # selective prediction
            if is_claim:
                answered = r.get("verdict") in ("SUPPORTED", "UNSUPPORTED")
                loss = 1.0 - float(r.get("verdict") == q["gold_label"])
            else:
                answered = row.get("n_pred", 0) > 0
                loss = (1.0 - row["f1"]) if answerable else 1.0
            row["answered"] = float(answered)
            row["loss"] = loss if answered else np.nan
            sr = r.get("support_ratio")
            row["support_ratio"] = np.nan if sr is None else float(sr)
            # "correct" for cost per correct answer
            if not answerable:
                corr = row.get("abstain_correct", 0.0)
            elif is_claim:
                corr = row["claim_correct"]
            else:
                corr = row["exact"]
            row["correct"] = corr
            rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------------
def _ci(x):
    m, lo, hi = bootstrap_ci(x)
    return m, lo, hi


def _fmt(m, lo, hi, scale=100, d=1):
    if m is None or (isinstance(m, float) and math.isnan(m)):
        return "–"
    return f"{m * scale:.{d}f} [{lo * scale:.{d}f}, {hi * scale:.{d}f}]"


def conflict_prf(g: pd.DataFrame, n_boot=2000, seed=0) -> dict:
    """Precision / recall / F1 of the CONFLICT flag over all questions, with bootstrap CIs."""
    y, p = g.has_conflict.astype(bool).values, g.pred_conflict.astype(bool).values

    def prf(yy, pp):
        tp, fp, fn = (yy & pp).sum(), (~yy & pp).sum(), (yy & ~pp).sum()
        pr = tp / (tp + fp) if tp + fp else 0.0
        rc = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
        return pr, rc, f1, tp, fp, fn
    pr, rc, f1, tp, fp, fn = prf(y, p)
    rng = np.random.default_rng(seed)
    bs = np.array([prf(y[i], p[i])[:3] for i in (rng.integers(0, len(y), len(y)) for _ in range(n_boot))])
    lo, hi = np.quantile(bs, 0.025, 0), np.quantile(bs, 0.975, 0)
    clean = g[~g.has_conflict & ~g.benign_note]
    benign = g[g.benign_note]
    conf = g[g.has_conflict]
    return {"TP": int(tp), "FP": int(fp), "FN": int(fn), "TN": int((~y & ~p).sum()),
            "precision": pr, "precision_lo": lo[0], "precision_hi": hi[0],
            "recall": rc, "recall_lo": lo[1], "recall_hi": hi[1], "f1": f1, "f1_lo": lo[2], "f1_hi": hi[2],
            "fpr_clean": clean.pred_conflict.mean() if len(clean) else np.nan, "n_clean": len(clean),
            "fpr_benign_note": benign.pred_conflict.mean() if len(benign) else np.nan, "n_benign": len(benign),
            "resolution_acc": conf.resolution_correct.mean() if len(conf) else np.nan, "n_conflict": len(conf),
            "injected_adoption": g.injected_adoption.mean()}


def table_conflict(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for s in ordered(df.system.unique()):
        g = df[df.system == s]
        r = conflict_prf(g)
        conf = g[g.has_conflict]
        res_m = _ci(conf.resolution_correct.values)
        rows.append({"System": SYSTEM_LABEL.get(s, s),
                     "TP/FP/FN": f"{r['TP']}/{r['FP']}/{r['FN']}",
                     "Precision": _fmt(r["precision"], r["precision_lo"], r["precision_hi"]),
                     "Recall": _fmt(r["recall"], r["recall_lo"], r["recall_hi"]),
                     "F1": _fmt(r["f1"], r["f1_lo"], r["f1_hi"]),
                     "FPR clean": f"{r['fpr_clean'] * 100:.1f}",
                     "FPR agreeing note": f"{r['fpr_benign_note'] * 100:.1f}",
                     "Resolution acc.": _fmt(*res_m),
                     "Injected adoption": f"{g.injected_adoption.mean() * 100:.1f}",
                     "Recall equal-auth.": f"{conf[conf.subtype == 'nvd_kev'].pred_conflict.mean() * 100:.1f}",
                     "Recall injected": f"{conf[conf.subtype != 'nvd_kev'].pred_conflict.mean() * 100:.1f}"})
    return pd.DataFrame(rows)


MAIN_COLS = [("list_f1", "List ID-F1"), ("claim_correct", "Claim acc."), ("uar", "UAR"),
             ("stale_adoption", "Stale adoption"), ("injected_adoption", "Injected adoption"),
             ("flag_correct", "Flag acc."), ("abstain_correct", "Abstention acc.")]


def table_main(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for s in ordered(df.system.unique()):
        g = df[df.system == s]
        row = {"System": SYSTEM_LABEL.get(s, s)}
        for col, lab in MAIN_COLS:
            row[lab] = _fmt(*_ci(g[col].values)) if col in g else "–"
        cp = conflict_prf(g)
        row["Conflict F1"] = f"{cp['f1'] * 100:.1f}"
        row["Coverage"] = f"{g.answered.mean() * 100:.1f}"
        row["Selective risk"] = f"{g.loss.mean() * 100:.1f}"
        rows.append(row)
    return pd.DataFrame(rows)


def table_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Headline metric per category: list F1 + claim accuracy pooled as 'task accuracy'."""
    d = df.copy()
    d["task_score"] = np.where(~d.answerable, d.abstain_correct, np.where(d.is_claim, d.claim_correct, d.f1))
    piv = d.pivot_table(index="category", columns="system", values="task_score", aggfunc="mean") * 100
    piv = piv[[s for s in ordered(piv.columns)]]
    piv.columns = [SYSTEM_LABEL.get(s, s) for s in piv.columns]
    return piv.round(1)


ABL_METRICS = [("list_f1", "List F1"), ("claim_correct", "Claim acc."), ("stale_adoption", "Stale adopt."),
               ("injected_adoption", "Injected adopt."), ("resolution_correct", "Conflict resolution"),
               ("abstain_correct", "Abstention")]


def table_ablation(dfs: dict[str, pd.DataFrame], systems: list[str]) -> pd.DataFrame:
    rows = []
    for s in systems:
        row = {"Configuration": SYSTEM_LABEL.get(s, s)}
        for model, df in dfs.items():
            g = df[df.system == s]
            short = model.split(":")[0].split("/")[-1]
            if g.empty:
                continue
            for col, lab in ABL_METRICS:
                row[f"{short} {lab}"] = round(g[col].mean() * 100, 1)
            row[f"{short} Conflict F1"] = round(conflict_prf(g)["f1"] * 100, 1)
        rows.append(row)
    return pd.DataFrame(rows)


def significance_final(df: pd.DataFrame, ref="evidence_agent", others=None) -> pd.DataFrame:
    tests, rows = {}, []
    if ref not in set(df.system):
        return pd.DataFrame()
    r = df[df.system == ref].set_index("qid")
    for s in (others or sorted(set(df.system) - {ref, "graph_oracle"})):
        if s not in set(df.system):
            continue
        o = df[df.system == s].set_index("qid")
        common = r.index.intersection(o.index)
        for metric, kind in (("list_f1", "perm"), ("claim_correct", "mcnemar"), ("conflict_detect_correct", "mcnemar"),
                             ("resolution_correct", "mcnemar"), ("injected_adoption", "perm"),
                             ("stale_adoption", "perm"), ("abstain_correct", "mcnemar"), ("uar", "perm")):
            a, b = r.loc[common, metric], o.loc[common, metric]
            mask = a.notna() & b.notna()
            if mask.sum() < 5:
                continue
            p = (mcnemar_exact(a[mask] > 0.5, b[mask] > 0.5) if kind == "mcnemar"
                 else paired_permutation(a[mask], b[mask]))
            tests[(s, metric)] = p
            rows.append({"comparison": f"{SYSTEM_LABEL.get(ref)} vs {SYSTEM_LABEL.get(s, s)}", "metric": metric,
                         "n": int(mask.sum()), "ref": round(a[mask].mean() * 100, 1),
                         "other": round(b[mask].mean() * 100, 1),
                         "diff": round((a[mask].mean() - b[mask].mean()) * 100, 1), "test": kind, "p": p})
    adj = holm(tests)
    keys = list(tests)
    for row, k in zip(rows, keys):
        row["p_holm"] = adj[k]
        row["significant (0.05)"] = "yes" if adj[k] < 0.05 else ""
    return pd.DataFrame(rows)


def table_cost(df_main: pd.DataFrame, df_timing: pd.DataFrame | None) -> pd.DataFrame:
    """Calls and tokens from the main run (identical with or without cache); latency ONLY from the
    uncached, sequential timing run so that every system is timed under the same conditions."""
    rows = []
    base = None
    for s in ordered(df_main.system.unique()):
        g = df_main[df_main.system == s]
        tok = (g.prompt_tokens + g.completion_tokens)
        n_corr = g.correct.sum()
        row = {"System": SYSTEM_LABEL.get(s, s), "LLM calls / q": round(g.calls.mean(), 2),
               "Input tok / q": int(g.prompt_tokens.mean()), "Output tok / q": int(g.completion_tokens.mean()),
               "Tokens per correct answer": int(tok.sum() / n_corr) if n_corr else None}
        if df_timing is not None and s in set(df_timing.system):
            t = df_timing[df_timing.system == s]
            row["Latency mean (s)"] = round(t.latency.mean(), 1)
            row["Latency p95 (s)"] = round(float(np.quantile(t.latency, 0.95)), 1)
            row["Cached calls in timing run"] = int(t.cached_calls.sum()) if "cached_calls" in t else 0
            if s == "naive":
                base = t.latency.mean()
        rows.append(row)
    out = pd.DataFrame(rows)
    if base and "Latency mean (s)" in out:
        out["Latency vs naive"] = (out["Latency mean (s)"] / base).round(1).astype(str) + "x"
    return out


def repeat_stability(dfs_by_rep: dict[int, pd.DataFrame], systems) -> pd.DataFrame:
    rows = []
    for s in systems:
        vals = {}
        for rep, df in dfs_by_rep.items():
            g = df[df.system == s]
            if g.empty:
                continue
            vals.setdefault("list_f1", []).append(g.list_f1.mean())
            vals.setdefault("claim_correct", []).append(g.claim_correct.mean())
            vals.setdefault("conflict_f1", []).append(conflict_prf(g, n_boot=10)["f1"])
            vals.setdefault("injected_adoption", []).append(g.injected_adoption.mean())
            vals.setdefault("stale_adoption", []).append(g.stale_adoption.mean())
        if vals:
            row = {"System": SYSTEM_LABEL.get(s, s), "repeats": len(vals["list_f1"])}
            for k, v in vals.items():
                v = np.array(v) * 100
                row[k] = f"{v.mean():.1f} ± {v.std(ddof=1) if len(v) > 1 else 0:.1f}"
            rows.append(row)
    return pd.DataFrame(rows)


def table_composition(questions: list[dict], notes_n: int, info: dict | None = None,
                      validation: dict | None = None) -> pd.DataFrame:
    from .final_bench import CATEGORY_LABEL
    prov = {"verification": "MITRE ATT&CK (current), CTID ATT&CK->800-53 Rev. 5 mapping",
            "relationships": "NVD, CISA KEV, MITRE CWE, MITRE CAPEC",
            "conflict": "NVD vs CISA KEV (real); injected low-authority notes",
            "outdated": "ATT&CK v8.2 vs current; NIST 800-53 Rev. 5 withdrawn; CTID Rev. 4 vs Rev. 5",
            "insufficient": "identifiers absent from every source; relations no source records",
            "benign_note": "ATT&CK + agreeing low-authority notes (conflict negatives)"}
    df = pd.DataFrame([{"category": q["meta"]["category"], "subtype": q["subtype"], "claim": q["qtype"] == "claim",
                        "conflict": q["meta"].get("has_conflict", False),
                        "answerable": q["meta"].get("answerable", True)} for q in questions])
    rows = []
    for cat in [k for k in CATEGORY_LABEL if k in set(df.category)]:
        g = df[df.category == cat]
        row = {"Category": CATEGORY_LABEL.get(cat, cat), "Questions": len(g),
               "Claims / lists": f"{int(g.claim.sum())} / {int((~g.claim).sum())}",
               "Families": ", ".join(f"{k} ({v})" for k, v in g.subtype.value_counts(sort=False).items()),
               "With conflict": int(g.conflict.sum()), "Unanswerable": int((~g.answerable).sum()),
               "Provenance": prov.get(cat, "")}
        if validation and cat in validation.get("per_category", {}):
            row["Gold validated (both annotators)"] = validation["per_category"][cat]
        rows.append(row)
    rows.append({"Category": "Total", "Questions": len(df),
                 "Claims / lists": f"{int(df.claim.sum())} / {int((~df.claim).sum())}",
                 "With conflict": int(df.conflict.sum()), "Unanswerable": int((~df.answerable).sum()),
                 "Families": f"{df.subtype.nunique()} families, {notes_n} injected notes",
                 "Provenance": f"frozen md5 {info['questions_md5'][:10]}" if info else ""})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------------------------
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def _style(ax):
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.yaxis.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)


def fig_conflict(dfs: dict[str, pd.DataFrame], systems, path: Path):
    """Figure 2: precision / recall / F1 of the CONFLICT flag, one panel per LLM, systems on the y axis."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    sy = [s for s in ordered(systems) if any(s in set(df.system) for df in dfs.values())]
    fig, axes = plt.subplots(1, len(dfs), figsize=(4.4 * len(dfs) + 1.6, 0.42 * len(sy) + 1.2), sharey=True,
                             squeeze=False)
    y = np.arange(len(sy))[::-1]
    h = 0.26
    for ax, (model, df) in zip(axes[0], dfs.items()):
        vals = {k: [] for k in ("precision", "recall", "f1")}
        for s in sy:
            g = df[df.system == s]
            r = conflict_prf(g, n_boot=10) if len(g) else {"precision": np.nan, "recall": np.nan, "f1": np.nan}
            for k in vals:
                vals[k].append(r[k] * 100)
        for j, (k, lab) in enumerate((("precision", "Precision"), ("recall", "Recall"), ("f1", "F1"))):
            ax.barh(y + (1 - j) * h, vals[k], h - 0.04, color=PALETTE[j], label=lab, edgecolor="white", lw=0.8)
        ax.set_yticks(y)
        ax.set_yticklabels([SYSTEM_LABEL.get(s, s) for s in sy], fontsize=7.5, color=INK2)
        ax.set_xlim(0, 105)
        ax.set_xlabel("CONFLICT flag (%)", fontsize=8, color=INK2)
        ax.set_title(model, fontsize=9, color=INK)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        for sp in ("left", "bottom"):
            ax.spines[sp].set_color(GRID)
        ax.tick_params(colors=INK2, labelsize=7.5)
        ax.xaxis.grid(True, color=GRID, lw=0.6)
        ax.set_axisbelow(True)
    axes[0][-1].legend(fontsize=7, frameon=False, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


CURVE_SYSTEMS = ["graph_oracle", "naive", "kg_rag", "multihop", "crag", "react_agent", "graph_verifier",
                 "evidence_agent"]   # 8 systems = 8 fixed palette slots (ablations are reported in Table 4)


def coverage_risk_points(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for s in ordered(df.system.unique()):
        g = df[df.system == s]
        rows.append({"system": s, "coverage": g.answered.mean(), "risk": g.loss.mean()})
    return pd.DataFrame(rows)


def coverage_risk_curve(g: pd.DataFrame):
    """Curve for systems that report a verification support ratio: answer only when support >= tau."""
    g = g[g.answered > 0].copy()
    if g.support_ratio.isna().all():
        return None
    g["conf"] = g.support_ratio.fillna(1.0)
    n_all = None
    pts = []
    for tau in sorted(set(np.round(g.conf, 3)) | {0.0}):
        a = g[g.conf >= tau]
        pts.append((tau, len(a), a.loss.mean() if len(a) else np.nan))
    return pts


def fig_coverage_risk(dfs: dict[str, pd.DataFrame], path: Path, curve_systems=("evidence_agent", "graph_verifier")):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, len(dfs), figsize=(4.6 * len(dfs), 3.6), sharey=True, squeeze=False)
    for ax, (model, df) in zip(axes[0], dfs.items()):
        pts = coverage_risk_points(df[df.system.isin(CURVE_SYSTEMS)])
        for r in pts.itertuples():
            col = PALETTE[CURVE_SYSTEMS.index(r.system)]
            ax.scatter(r.coverage * 100, r.risk * 100, s=46, color=col, edgecolor="white", lw=1.5, zorder=3,
                       label=SYSTEM_LABEL.get(r.system, r.system))
            if r.system in curve_systems:
                cur = coverage_risk_curve(df[df.system == r.system])
                if cur:
                    n = len(df[df.system == r.system])
                    xs = [k / n * 100 for _, k, _ in cur]
                    ys = [v * 100 for _, _, v in cur]
                    ax.plot(xs, ys, color=col, lw=2, alpha=0.8, zorder=2)
        ax.set_xlabel("Coverage: questions answered (%)", fontsize=8, color=INK2)
        ax.set_title(model, fontsize=9, color=INK)
        ax.set_xlim(0, 102)
        _style(ax)
    axes[0][0].set_ylabel("Selective risk: mean loss when answering (%)", fontsize=8, color=INK2)
    axes[0][-1].legend(fontsize=6.5, frameon=False, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------------------------
# Conflict trace (answers "how many injected conflicts were retrieved / recognised / flagged")
# ---------------------------------------------------------------------------------------------
def conflict_trace(questions: list[dict], results: dict[str, dict[str, dict]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for q in questions:
        m = q.get("meta", {})
        note = m.get("poison_doc") or m.get("note_doc")
        inj = set(m.get("injected_ids") or (q.get("stale_ids") if q["subtype"] == "poisoned" else []) or [])
        if not note or not inj:
            continue
        for s, res in results.items():
            r = res.get(q["qid"])
            if not r:
                continue
            flags = set(r.get("flags") or [])
            draft = set(r.get("draft_ids", r.get("ids") or []))
            rej = {i for i, _ in (r.get("rejected") or [])}
            dv = r.get("draft_verdict", r.get("verdict"))
            if q["qtype"] == "claim" and dv == "SUPPORTED" and r.get("verdict") != "SUPPORTED":
                rej |= inj
            verdict_ok = r.get("verdict") == "UNSUPPORTED" if q["qtype"] == "claim" else None
            text = (r.get("answer") or "")
            rows.append({
                "qid": q["qid"], "system": s,
                "retrieved": note in (r.get("retrieved") or []) or note in (r.get("kept") or []),
                "drafted_injected": bool(draft & inj) if q["qtype"] != "claim" else dv == "SUPPORTED",
                "verifier_rejected": bool(rej & inj),
                "adopted": bool(set(r.get("ids") or []) & inj) if q["qtype"] != "claim" else verdict_ok is False,
                "code_detected": any(cf.get("kind") for cf in (r.get("conflicts") or [])),
                "text_mentions_conflict": bool(AWARE.search(text)) or note in text,
                "flag_conflict": "CONFLICT" in flags,
                "flag_outdated_only": "OUTDATED" in flags and "CONFLICT" not in flags,
                "llm_flag_conflict": "CONFLICT" in set(r.get("flags_llm") or []),
            })
    tr = pd.DataFrame(rows)
    if tr.empty:
        return tr, tr
    tr["recognised"] = tr.verifier_rejected | tr.code_detected | tr.text_mentions_conflict | tr.flag_conflict
    tr["recognised_not_flagged"] = tr.recognised & ~tr.flag_conflict
    summ = tr.groupby("system")[["retrieved", "drafted_injected", "verifier_rejected", "adopted", "code_detected",
                                 "text_mentions_conflict", "recognised", "flag_conflict",
                                 "recognised_not_flagged", "flag_outdated_only"]].sum().astype(int)
    summ.insert(0, "n", tr.groupby("system").size())
    summ["old metric (CONFLICT or OUTDATED)"] = summ.flag_conflict + summ.flag_outdated_only
    return tr, summ.loc[ordered(summ.index)]


# ---------------------------------------------------------------------------------------------
# Representative cases
# ---------------------------------------------------------------------------------------------
def pick_cases(df: pd.DataFrame, questions, results, systems=("evidence_agent", "react_agent", "graph_verifier"),
               per_kind=3) -> str:
    qmap = {q["qid"]: q for q in questions}
    ea = df[df.system == "evidence_agent"].set_index("qid")
    kinds = {
        "Correct (agent right, ReAct wrong)": [],
        "Incorrect (agent wrong)": [],
        "Contradictory evidence": [],
        "Unanswerable": [],
    }
    ra = df[df.system == "react_agent"].set_index("qid")
    for qid, r in ea.iterrows():
        sc = r.claim_correct if r.is_claim else (r.abstain_correct if not r.answerable else r.f1)
        rs = None
        if qid in ra.index:
            rr = ra.loc[qid]
            rs = rr.claim_correct if rr.is_claim else (rr.abstain_correct if not rr.answerable else rr.f1)
        if r.has_conflict:
            kinds["Contradictory evidence"].append(qid)
        elif not r.answerable:
            kinds["Unanswerable"].append(qid)
        elif sc is not None and sc >= 0.99 and rs is not None and rs < 0.5:
            kinds["Correct (agent right, ReAct wrong)"].append(qid)
        elif sc is not None and sc < 0.5:
            kinds["Incorrect (agent wrong)"].append(qid)
    out = []
    for k, qids in kinds.items():
        out.append(f"## {k}\n")
        for qid in sorted(qids)[:per_kind]:
            q = qmap[qid]
            out.append(f"**{qid}** ({q['subtype']}) — {q['question']}\n\n- Gold: "
                       f"{q.get('gold_label') or ', '.join(q['gold_ids']) or '(abstain)'}"
                       + (f"; injected: {', '.join(q['meta'].get('injected_ids', []))}" if q['meta'].get('injected_ids') else "")
                       + (f"; outdated: {', '.join(q.get('stale_ids', []))}" if q.get('stale_ids') else ""))
            for s in systems:
                r = results.get(s, {}).get(qid)
                if not r:
                    continue
                cf = "; ".join(f"{c.get('kind')}: {c.get('source', '')} {c.get('disputed')}" for c in r.get("conflicts") or [])
                out.append(f"- {SYSTEM_LABEL.get(s, s)}: ids={r.get('ids')} verdict={r.get('verdict')} "
                           f"flags={r.get('flags')}" + (f" | rejected={r.get('rejected')[:4]}" if r.get('rejected') else "")
                           + (f" | conflicts: {cf}" if cf else ""))
            out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------------------------
# Gold-label validation
# ---------------------------------------------------------------------------------------------
def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (np.nan, np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, max(0.0, c - h), min(1.0, c + h)


def export_annotation(questions, corpus: Corpus, out_dir: Path, per_category: int = 17, seed: int = 11):
    """Two identical blind sheets (annotator_A.csv, annotator_B.csv). Columns to fill:
    gold_label (CORRECT / INCORRECT / AMBIGUOUS), conflict_label (YES / NO: do the sources really disagree),
    corrected_gold, comment."""
    import random
    rng = random.Random(seed)
    by = {}
    for q in questions:
        by.setdefault(q["meta"]["category"], []).append(q)
    picked = []
    for cat in sorted(by):
        xs = sorted(by[cat], key=lambda q: q["qid"])
        rng.shuffle(xs)
        picked += xs[:per_category]
    rows = []
    for q in picked:
        docs = list(dict.fromkeys(q["gold_docs"] + ([q["meta"]["note_doc"]] if q["meta"].get("note_doc") else [])))
        if q["meta"].get("subject"):
            docs += [d.doc_id for d in corpus.entity_docs(q["meta"]["subject"])]
        docs = list(dict.fromkeys(docs))[:5]
        ev = "\n\n".join(f"{corpus.docs[d].header()}\n{corpus.docs[d].text[:700]}" for d in docs if d in corpus.docs)
        rows.append({"qid": q["qid"], "category": q["meta"]["category"], "question": q["question"],
                     "gold_answer": q.get("gold_label") or ", ".join(q["gold_ids"]) or "(no answer: abstain)",
                     "outdated_or_injected_ids": ", ".join(sorted(set(q.get("stale_ids", []))
                                                                  | set(q["meta"].get("injected_ids", [])))),
                     "evidence": ev or "(no source describes the identifiers in the question)",
                     "gold_label": "", "conflict_label": "", "corrected_gold": "", "comment": ""})
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    for who in ("A", "B"):
        df.to_csv(out_dir / f"annotator_{who}.csv", index=False)
    key = pd.DataFrame([{"qid": q["qid"], "has_conflict": q["meta"].get("has_conflict", False)} for q in picked])
    key.to_csv(out_dir / "annotation_key_DO_NOT_SHARE.csv", index=False)
    return out_dir, len(rows)


def annotation_agreement(sheet_a: Path, sheet_b: Path, key: Path) -> dict:
    from .annotate import cohen_kappa
    A, B = pd.read_csv(sheet_a).set_index("qid"), pd.read_csv(sheet_b).set_index("qid")
    K = pd.read_csv(key).set_index("qid")
    labs = {"CORRECT", "INCORRECT", "AMBIGUOUS"}
    common = [q for q in A.index if q in B.index and str(A.loc[q, "gold_label"]).strip().upper() in labs
              and str(B.loc[q, "gold_label"]).strip().upper() in labs]
    la = [str(A.loc[q, "gold_label"]).strip().upper() for q in common]
    lb = [str(B.loc[q, "gold_label"]).strip().upper() for q in common]
    both = [x == "CORRECT" and y == "CORRECT" for x, y in zip(la, lb)]
    p, lo, hi = wilson(sum(both), len(both))
    cats = A.loc[common, "category"]
    per_cat = {}
    for cat in sorted(set(cats)):
        idx = [i for i, q in enumerate(common) if cats[q] == cat]
        k = sum(both[i] for i in idx)
        pc, l2, h2 = wilson(k, len(idx))
        per_cat[cat] = f"{pc * 100:.0f}% [{l2 * 100:.0f}, {h2 * 100:.0f}] (n={len(idx)})"
    # conflict labels vs the benchmark's has_conflict
    cl = [q for q in common if str(A.loc[q, "conflict_label"]).strip().upper() in ("YES", "NO")
          and str(B.loc[q, "conflict_label"]).strip().upper() in ("YES", "NO")]
    ca = [str(A.loc[q, "conflict_label"]).strip().upper() for q in cl]
    cb = [str(B.loc[q, "conflict_label"]).strip().upper() for q in cl]
    gold_c = ["YES" if bool(K.loc[q, "has_conflict"]) else "NO" for q in cl]
    res = {"n": len(common), "kappa_gold_label": round(cohen_kappa(la, lb), 3),
           "raw_agreement": round(sum(x == y for x, y in zip(la, lb)) / max(1, len(common)), 3),
           "gold_accuracy_both_correct": f"{p * 100:.1f}% [{lo * 100:.1f}, {hi * 100:.1f}]",
           "per_category": per_cat,
           "n_conflict_labelled": len(cl),
           "kappa_conflict_label": round(cohen_kappa(ca, cb), 3) if cl else None,
           "conflict_label_agreement_with_benchmark_A": round(np.mean([x == g for x, g in zip(ca, gold_c)]), 3) if cl else None,
           "conflict_label_agreement_with_benchmark_B": round(np.mean([x == g for x, g in zip(cb, gold_c)]), 3) if cl else None,
           "disagreements": [q for q, x, y in zip(common, la, lb) if x != y]}
    return res


# ---------------------------------------------------------------------------------------------
# Figure 1: architecture
# ---------------------------------------------------------------------------------------------
def fig_architecture(path: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
    fig, ax = plt.subplots(figsize=(12, 4.6))
    ax.set_xlim(0, 120)
    ax.set_ylim(6, 46)
    ax.axis("off")
    fill = {"A": "#cde2fb", "B": "#fde0d0", "C": "#d2f0e3", "io": "#f0efec"}
    LS = 2.3   # line spacing in data units

    def box(x, y, w, h, title, lines, fc, note=None):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=1.0", fc=fc, ec="#8a8984",
                                    lw=0.8))
        ax.text(x + w / 2, y + h - 1.4, title, ha="center", va="top", fontsize=8.5, color=INK, weight="bold")
        for i, ln in enumerate(lines):
            ax.text(x + 1.0, y + h - 5.0 - i * LS, ln, ha="left", va="top", fontsize=7, color=INK2)
        if note:
            ax.text(x + w / 2, y - 1.2, note, ha="center", va="top", fontsize=6.6, color="#6250d6", style="italic")

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=10, color="#52514e", lw=1))

    Y, H = 14, 24
    box(0.5, 20, 11, 12, "Question", ["claim or list", "question with", "IDs or names"], fill["io"])
    box(14, Y, 21, H, "A  Plan & gather", ["LLM tool loop (ReAct style)", "- search: BM25 + dense",
                                            "- lookup(ID): every source", "- expand(ID, relation):",
                                            "  typed graph links", "-> evidence ledger: source,",
                                            "  authority, release, status"], fill["A"],
        "baseline B: fixed retrieval +\n1-hop expansion, no LLM loop")
    box(38, Y, 23, H, "B  Evidence checks (no LLM)", ["- lifecycle: revoked / withdrawn", "  -> current replacement",
                                                        "- temporal: only an older", "  release lists it -> OUTDATED",
                                                        "- conflict detection: every", "  source vs relation owners",
                                                        "  (authority tier) -> CONFLICT"], fill["B"],
        "ablations: - temporal, - authority,\n- conflict detection")
    box(64, 22, 16, 16, "Draft (LLM)", ["typed answer, claims,", "flags, citations;", "sees B's notes"], fill["io"])
    box(83, Y, 20, H, "C  Verification", ["- answer-type check", "- typed graph path over", "  acceptable documents",
                                           "  (latest release,", "  authority >= 2)", "- strict entailment for",
                                           "  untyped claims"], fill["C"], "ablations: - graph, - verification")
    box(106, 18, 13.5, 16, "Output", ["verified IDs or", "verdict + flags", "conflict record", "rejected IDs"],
        fill["io"])
    arrow(11.5, 26, 14, 26)
    arrow(35, 26, 38, 26)
    arrow(61, 30, 64, 30)
    arrow(80, 30, 83, 30)
    arrow(103, 26, 106, 26)
    ax.text(60, 44.5, "CONFLICT flag = detection in stage B, independent of whether the disputed identifier is "
            "accepted in stage C", ha="center", fontsize=8, color=INK)
    ax.text(60, 41.8, "Baseline A (ReAct): stage A + draft only.    Baseline B (non-agentic verifier): fixed "
            "retrieval + B + draft + C.    Proposed: A + B + draft + C.", ha="center", fontsize=7.5, color=INK2)
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
