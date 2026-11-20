"""Per-question scoring, aggregation and significance testing.

Answer quality      precision / recall / F1 over identifiers of the requested kind
Grounding           evidence recall, citation precision
Unsupported assoc.  UAR = wrong ids / predicted ids, split into plausible (near-miss) vs implausible,
                    and into grounded (id visible in retrieved text) vs ungrounded (invented)
Claims              accuracy, macro-F1, false-support rate on plausible negatives, NEI recall
Temporal            stale/poison adoption, flag accuracy, replacement found, over-flagging on clean questions
Cost                LLM calls, tokens, latency
"""
from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from .corpus import Corpus, extract_ids, id_kind

FLAG_OK = {
    "REVOKED": {"REVOKED", "DEPRECATED"},
    "WITHDRAWN": {"WITHDRAWN", "DEPRECATED", "OUTDATED"},
    "OUTDATED": {"OUTDATED", "CONFLICT"},
    "CONFLICT": {"CONFLICT", "OUTDATED"},
}
AWARE_WORDS = ("revoked", "withdrawn", "deprecated", "replaced", "incorporated", "superseded", "no longer",
               "outdated", "older version", "older release", "previous version")
LABELS = ["SUPPORTED", "UNSUPPORTED", "NOT_ENOUGH_INFO"]


class Plausibility:
    """Decides whether a wrong identifier is a *plausible* confusion of a gold identifier."""

    def __init__(self, c: Corpus):
        self.c = c

    def _nb(self, x, rel):
        return {t for r, t, _ in self.c.neighbors(x, rel)}

    def near(self, w: str, gold: list[str]) -> bool:
        k = id_kind(w)
        for g in gold:
            if id_kind(g) != k:
                continue
            if k == "technique" and w.split(".")[0] == g.split(".")[0]:
                return True
            if k == "mitigation" and self._nb(w, "mitigates") & self._nb(g, "mitigates"):
                return True
            if k == "control":
                if w.split("(")[0] == g.split("(")[0] or w.split("-")[0] == g.split("-")[0]:
                    return True
            if k == "cwe" and (g in self._nb(w, "child_of") or w in self._nb(g, "child_of")
                               or self._nb(w, "related_attack_pattern") & self._nb(g, "related_attack_pattern")):
                return True
            if k == "capec" and self._nb(w, "related_weakness") & self._nb(g, "related_weakness"):
                return True
        return False


def target_kinds(q: dict) -> set[str]:
    if q["qtype"] in ("tech_id", "ate"):
        return {"technique"}
    if q["qtype"] == "rcm":
        return {"cwe"}
    if q["qtype"] == "attribution":
        return {"group"}
    ks = {id_kind(g) for g in q["gold_ids"]}
    return {k for k in ks if k}


def score_one(q: dict, r: dict, c: Corpus, pl: Plausibility) -> dict:
    row = {"qid": q["qid"], "qtype": q["qtype"], "subtype": q["subtype"], "track": q.get("track", "evidence")}
    u = r.get("usage", {}) or {}
    row.update(calls=u.get("calls", 0), prompt_tokens=u.get("prompt_tokens", 0),
               completion_tokens=u.get("completion_tokens", 0), latency=r.get("latency", 0.0),
               error=int(bool(r.get("error"))))
    retrieved = r.get("retrieved", [])
    gold_docs = [d for d in q["gold_docs"] if not d.startswith("note:")]
    row["evidence_recall"] = (len(set(gold_docs) & set(retrieved)) / len(gold_docs)) if gold_docs else np.nan
    retrieved_text = " ".join(c.docs[d].text for d in retrieved if d in c.docs)
    retrieved_ids = set(extract_ids(retrieved_text))
    flags = set(r.get("flags", []))

    if q["qtype"] == "claim":
        pred = r.get("verdict") or "NONE"
        row.update(claim_label=q["gold_label"], claim_pred=pred, claim_correct=float(pred == q["gold_label"]),
                   false_support=float(pred == "SUPPORTED") if q["gold_label"] == "UNSUPPORTED" else np.nan,
                   nei_recall=float(pred == "NOT_ENOUGH_INFO") if q["gold_label"] == "NOT_ENOUGH_INFO" else np.nan)
        row["over_flag"] = float(bool(flags & {"CONFLICT", "OUTDATED", "REVOKED", "WITHDRAWN"}))
        return row

    kinds = target_kinds(q)
    pred = [i for i in r.get("ids", []) if id_kind(i) in kinds]
    gold = set(q["gold_ids"])
    if q.get("meta", {}).get("parent_only"):  # CTIBench ATE is scored at the parent-technique level
        pred = list(dict.fromkeys(i.split(".")[0] for i in pred))
        gold = {g.split(".")[0] for g in gold}
    tp = len(set(pred) & gold)
    p = tp / len(set(pred)) if pred else 0.0
    rec = tp / len(gold) if gold else 0.0
    f1 = 2 * p * rec / (p + rec) if p + rec else 0.0
    wrong = [w for w in dict.fromkeys(pred) if w not in gold]
    row.update(precision=p, recall=rec, f1=f1, exact=float(set(pred) == gold), n_pred=len(set(pred)),
               abstain=float(not pred))
    if q["qtype"] == "tech_id":
        row["parent_match"] = float(any(x.split(".")[0] == g.split(".")[0] for x in pred for g in gold))
    n = len(set(pred))
    row["uar"] = len(wrong) / n if n else np.nan
    row["uar_plausible"] = sum(pl.near(w, list(gold)) for w in wrong) / n if n else np.nan
    row["uar_implausible"] = (row["uar"] - row["uar_plausible"]) if n else np.nan
    row["uar_ungrounded"] = sum(w not in retrieved_ids for w in wrong) / n if n else np.nan
    row["any_unsupported"] = float(bool(wrong)) if n else np.nan
    cited = [d for d in r.get("citations", []) if d in c.docs]
    if cited and pred:
        cid = set(extract_ids(" ".join(c.docs[d].text for d in cited))) | {t for d in cited for _, t in c.docs[d].links}
        row["citation_precision"] = sum(x in cid for x in set(pred)) / n
    else:
        row["citation_precision"] = np.nan
    stale = set(q.get("stale_ids", []))
    if stale:
        row["stale_adoption"] = float(bool(set(pred) & stale))
    need = q.get("requires_flag")
    if need:
        txt = (r.get("answer") or "").lower()
        row["flag_correct"] = float(bool(flags & FLAG_OK[need]))
        aware = bool(flags & FLAG_OK[need]) or any(w in txt for w in AWARE_WORDS)
        if q["subtype"] in ("revoked", "withdrawn"):
            rep = set(q.get("replacement_ids", []))
            aware = aware or bool(rep & (set(r.get("ids", [])) | set(extract_ids(r.get("answer") or ""))))
            row["replacement_found"] = float(bool(rep & (set(r.get("ids", [])) | set(extract_ids(r.get("answer") or "")))))
        row["staleness_aware"] = float(aware)
    else:
        row["over_flag"] = float(bool(flags & {"CONFLICT", "OUTDATED", "REVOKED", "WITHDRAWN"}))
    return row


def score_run(questions: list[dict], results: dict[str, dict[str, dict]], c: Corpus) -> pd.DataFrame:
    pl = Plausibility(c)
    qmap = {q["qid"]: q for q in questions}
    rows = []
    for sysname, res in results.items():
        for qid, r in res.items():
            if qid in qmap:
                row = score_one(qmap[qid], r, c, pl)
                row["system"] = sysname
                rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Aggregation & statistics
# ---------------------------------------------------------------------------
MAIN = ["abstain", "f1", "precision", "recall", "exact", "evidence_recall", "uar", "uar_plausible", "uar_ungrounded",
        "citation_precision", "claim_correct", "false_support", "nei_recall", "stale_adoption",
        "flag_correct", "staleness_aware", "replacement_found", "over_flag", "calls", "prompt_tokens", "latency"]


def bootstrap_ci(x, n=2000, alpha=0.05, seed=0):
    x = np.asarray([v for v in x if not (isinstance(v, float) and math.isnan(v))], dtype=float)
    if len(x) == 0:
        return (np.nan, np.nan, np.nan)
    rng = np.random.default_rng(seed)
    means = rng.choice(x, (n, len(x)), replace=True).mean(1)
    return (x.mean(), np.quantile(means, alpha / 2), np.quantile(means, 1 - alpha / 2))


def claim_macro_f1(df: pd.DataFrame) -> float:
    d = df.dropna(subset=["claim_label"]) if "claim_label" in df else df.iloc[0:0]
    if d.empty:
        return np.nan
    f1s = []
    for lab in LABELS:
        tp = ((d.claim_pred == lab) & (d.claim_label == lab)).sum()
        fp = ((d.claim_pred == lab) & (d.claim_label != lab)).sum()
        fn = ((d.claim_pred != lab) & (d.claim_label == lab)).sum()
        f1s.append(2 * tp / (2 * tp + fp + fn) if tp else 0.0)
    return float(np.mean(f1s))


def summarize(df: pd.DataFrame, by=("system",)) -> pd.DataFrame:
    """Mean and 95% bootstrap CI of every metric per group."""
    out = []
    for key, g in df.groupby(list(by)):
        key = key if isinstance(key, tuple) else (key,)
        row = dict(zip(by, key))
        row["n"] = len(g)
        for m in MAIN:
            if m in g:
                mean, lo, hi = bootstrap_ci(g[m].values)
                row[m], row[m + "_lo"], row[m + "_hi"] = mean, lo, hi
        row["claim_macro_f1"] = claim_macro_f1(g)
        out.append(row)
    return pd.DataFrame(out)


def paired_permutation(a, b, n=10000, seed=0):
    """Two-sided paired sign-flip permutation test on per-question differences."""
    d = np.asarray(a, float) - np.asarray(b, float)
    d = d[~np.isnan(d)]
    if len(d) == 0 or np.allclose(d, 0):
        return 1.0
    rng = np.random.default_rng(seed)
    obs = abs(d.mean())
    signs = rng.choice([-1, 1], (n, len(d)))
    return float((np.abs((signs * d).mean(1)) >= obs).mean())


def mcnemar_exact(a, b):
    """Exact McNemar test for paired binary outcomes."""
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    n01, n10 = int((~a & b).sum()), int((a & ~b).sum())
    n = n01 + n10
    if n == 0:
        return 1.0
    k = min(n01, n10)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def holm(pvals: dict) -> dict:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, out, run = len(items), {}, 0.0
    for i, (k, p) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p))
        out[k] = run
    return out


def significance(df: pd.DataFrame, ref: str = "evidence_agent", track: str | None = None) -> pd.DataFrame:
    rows = []
    if track:
        df = df[df.track == track]
    if ref not in set(df.system):
        return pd.DataFrame()
    r = df[df.system == ref].set_index("qid")
    tests = {}
    for s in sorted(set(df.system) - {ref, "graph_oracle"}):
        o = df[df.system == s].set_index("qid")
        common = r.index.intersection(o.index)
        for metric, kind in (("f1", "perm"), ("uar", "perm"), ("evidence_recall", "perm"),
                             ("claim_correct", "mcnemar"), ("stale_adoption", "perm")):
            if metric not in r or metric not in o:
                continue
            a, b = r.loc[common, metric], o.loc[common, metric]
            mask = a.notna() & b.notna()
            if mask.sum() < 5:
                continue
            p = mcnemar_exact(a[mask] > 0.5, b[mask] > 0.5) if kind == "mcnemar" else paired_permutation(a[mask], b[mask])
            tests[(s, metric)] = p
            rows.append({"baseline": s, "metric": metric, "n": int(mask.sum()), "ref_mean": a[mask].mean(),
                         "baseline_mean": b[mask].mean(), "diff": a[mask].mean() - b[mask].mean(),
                         "test": kind, "p": p})
    adj = holm(tests)
    for row in rows:
        row["p_holm"] = adj[(row["baseline"], row["metric"])]
    return pd.DataFrame(rows)


def load_results(run_dir: Path, systems: list[str]) -> dict[str, dict[str, dict]]:
    out = {}
    for s in systems:
        p = Path(run_dir) / f"{s}.jsonl"
        if p.exists():
            res = {}
            for line in p.read_text().splitlines():
                if line.strip():
                    r = json.loads(line)
                    res[r["qid"]] = r
            out[s] = res
    return out
