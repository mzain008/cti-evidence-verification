"""Paper tables (CSV / Markdown / LaTeX) and figures (PNG + PDF).

Results are always reported per TRACK: the text track (where language understanding is required) and
the evidence track (structured lookups under outdated / conflicting sources, where the no-LLM graph
oracle is a meaningful reference). Mixing them would hide where an LLM actually helps.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .evaluate import significance, summarize

ORDER = ["graph_oracle", "naive", "kg_rag", "multihop", "crag", "react_agent", "evidence_agent",
         "agent_no_temporal", "agent_no_graph", "agent_no_authority"]
LABEL = {"graph_oracle": "Graph oracle (no LLM)", "naive": "Naive RAG", "kg_rag": "KG-RAG",
         "multihop": "Multi-hop RAG", "crag": "Corrective RAG", "react_agent": "ReAct agent (no verif.)",
         "evidence_agent": "Evidence-Aware Agent", "agent_no_temporal": "− temporal",
         "agent_no_graph": "− graph tools", "agent_no_authority": "− authority",
         "agent_no_verify": "ReAct agent (no verif.)"}
TRACKS = {"text": "Text track", "evidence": "Evidence track", "structural": "Structural track"}
# validated categorical palette (light mode), fixed slot order; oracle in neutral gray
SLOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
INK, INK2, GRID, SURF, GRAY = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb", "#9a9893"


def color_of(s: str) -> str:
    if s == "graph_oracle":
        return GRAY
    llm = [x for x in ORDER if x != "graph_oracle"]
    return SLOTS[llm.index(s) % len(SLOTS)] if s in llm else INK2


def _ordered(systems):
    return [s for s in ORDER if s in systems] + sorted(set(systems) - set(ORDER))


def _style(ax):
    ax.set_facecolor(SURF)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.yaxis.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)


def fmt_ci(row, m, pct=True):
    if row is None or m not in row or pd.isna(row[m]):
        return "–"
    k = 100 if pct else 1
    return f"{row[m]*k:.1f} [{row[m+'_lo']*k:.1f}, {row[m+'_hi']*k:.1f}]"


def write_table(df: pd.DataFrame, path: Path, caption: str):
    df.to_csv(path.with_suffix(".csv"), index=False)
    path.with_suffix(".md").write_text(f"**{caption}**\n\n" + df.to_markdown(index=False))
    path.with_suffix(".tex").write_text(df.to_latex(index=False, escape=True, caption=caption,
                                                    label=f"tab:{path.stem}"))


def _get(summ, s):
    return summ.loc[s] if summ is not None and s in summ.index else None


def track_table(df, systems, track):
    d = df[df.track == track]
    if d.empty:
        return None
    ans, clm = d[d.qtype != "claim"], d[d.qtype == "claim"]
    s_ans = summarize(ans).set_index("system") if not ans.empty else None
    s_clm = summarize(clm).set_index("system") if not clm.empty else None
    s_tmp = summarize(d[d.qtype == "temporal"]).set_index("system") if (d.qtype == "temporal").any() else None
    rows = []
    for s in systems:
        a, c, t = _get(s_ans, s), _get(s_clm, s), _get(s_tmp, s)
        row = {"System": LABEL.get(s, s), "ID F1 ↑": fmt_ci(a, "f1"), "Abstain": fmt_ci(a, "abstain"),
               "UAR ↓": fmt_ci(a, "uar"), "Plausible UAR ↓": fmt_ci(a, "uar_plausible"),
               "Claim acc. ↑": fmt_ci(c, "claim_correct"),
               "Claim macro-F1 ↑": f"{c['claim_macro_f1']*100:.1f}" if c is not None and not pd.isna(c["claim_macro_f1"]) else "–",
               "False support ↓": fmt_ci(c, "false_support")}
        if track == "evidence":
            row["Stale adoption ↓"] = fmt_ci(t, "stale_adoption")
            row["Staleness aware ↑"] = fmt_ci(t, "staleness_aware")
        row["LLM calls"] = f"{a['calls']:.1f}" if a is not None else "–"
        rows.append(row)
    return pd.DataFrame(rows)


def make_report(df: pd.DataFrame, out_dir: Path, model_name: str = "") -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "per_question_scores.csv", index=False)
    systems = _ordered(df.system.unique())
    summarize(df, ("system", "track")).to_csv(out_dir / "summary_full.csv", index=False)

    for track in ("text", "evidence", "structural"):
        t = track_table(df, systems, track)
        if t is not None:
            write_table(t, out_dir / f"table_main_{track}",
                        f"{TRACKS[track]} ({model_name}): mean with 95% bootstrap CI, %")

    ans = df[df.qtype != "claim"]
    fam = summarize(ans, ("system", "subtype"))
    piv = fam.pivot(index="subtype", columns="system", values="f1")[[s for s in systems if s in set(fam.system)]] * 100
    piv.columns = [LABEL.get(c, c) for c in piv.columns]
    write_table(piv.round(1).reset_index(), out_dir / "table_f1_by_subtype", "Identifier F1 (%) by question family")

    tmp = summarize(df[df.qtype == "temporal"], ("system", "subtype"))
    if not tmp.empty:
        keep = ["system", "subtype", "n", "f1", "recall", "stale_adoption", "flag_correct", "staleness_aware",
                "replacement_found"]
        tmp = tmp[[k for k in keep if k in tmp]].copy()
        for k in keep[3:]:
            if k in tmp:
                tmp[k] = (tmp[k] * 100).round(1)
        tmp["system"] = tmp.system.map(lambda s: LABEL.get(s, s))
        write_table(tmp, out_dir / "table_temporal", "Outdated and conflicting evidence (%)")

    cl = summarize(df[df.qtype == "claim"], ("system", "subtype"))
    if not cl.empty:
        cl = cl[["system", "subtype", "n", "claim_correct", "false_support", "nei_recall"]].copy()
        for k in ("claim_correct", "false_support", "nei_recall"):
            cl[k] = (cl[k] * 100).round(1)
        cl["system"] = cl.system.map(lambda s: LABEL.get(s, s))
        write_table(cl, out_dir / "table_claims", "Claim verification by claim type (%)")

    sigs = []
    for track in ("text", "evidence"):
        sig = significance(df, track=track)
        if not sig.empty:
            sig.insert(0, "track", track)
            sigs.append(sig)
    if sigs:
        sig = pd.concat(sigs)
        sig["baseline"] = sig.baseline.map(lambda s: LABEL.get(s, s))
        write_table(sig.round(4), out_dir / "table_significance",
                    "Evidence-Aware Agent vs each system, per track: paired tests, Holm-corrected within track")

    figures(df, systems, out_dir)
    return {"systems": systems}


def multi_model_table(dfs: dict[str, pd.DataFrame], out_dir: Path,
                      metrics=(("text", "f1"), ("text", "claim_correct"), ("evidence", "f1"),
                               ("evidence", "stale_adoption"), ("evidence", "uar"))) -> pd.DataFrame:
    """dfs: {'<model>/r<repeat>': per-question frame}. Mean ± SD over repeats, per model and system."""
    rows = []
    for tag, df in dfs.items():
        model, rep = tag.rsplit("/r", 1) if "/r" in tag else (tag, "0")
        for (s, tr), g in df.groupby(["system", "track"]):
            for t, m in metrics:
                if tr == t and m in g:
                    v = g[m].mean()
                    if not np.isnan(v):
                        rows.append({"model": model, "repeat": rep, "system": s, "metric": f"{t}:{m}", "value": v})
    long = pd.DataFrame(rows)
    if long.empty:
        return long
    agg = long.groupby(["model", "system", "metric"]).value.agg(["mean", "std", "count"]).reset_index()
    agg["cell"] = agg.apply(lambda r: f"{r['mean']*100:.1f}" + (f" ± {r['std']*100:.1f}" if r["count"] > 1 else ""), axis=1)
    wide = agg.pivot_table(index=["model", "system"], columns="metric", values="cell", aggfunc="first").reset_index()
    wide["system"] = pd.Categorical(wide.system, [s for s in ORDER if s in set(wide.system)], ordered=True)
    wide = wide.sort_values(["model", "system"])
    wide["system"] = wide.system.map(lambda s: LABEL.get(s, s))
    write_table(wide, Path(out_dir) / "table_multi_model", "Main metrics per model (mean ± SD over repeats, %)")
    return wide


def figures(df, systems, out_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10,
                         "axes.titleweight": "bold", "figure.facecolor": SURF})

    def bars(ax, d, m, title):
        _style(ax)
        sm = summarize(d).set_index("system") if not d.empty and m in d else None
        for i, s in enumerate(systems):
            if sm is None or s not in sm.index or pd.isna(sm.loc[s, m]):
                continue
            v, lo, hi = sm.loc[s, m] * 100, sm.loc[s, m + "_lo"] * 100, sm.loc[s, m + "_hi"] * 100
            ax.bar(i, v, width=0.72, color=color_of(s), edgecolor=SURF, linewidth=2)
            ax.errorbar(i, v, yerr=[[v - lo], [hi - v]], color=INK2, lw=1, capsize=2)
        ax.set_title(title, color=INK, loc="left")
        ax.set_xticks(range(len(systems)))
        ax.set_xticklabels([LABEL.get(s, s) for s in systems], rotation=55, ha="right", fontsize=7.5)
        ax.set_ylim(0, 100)
        ax.set_ylabel("%", color=INK2)

    text, ev = df[df.track == "text"], df[df.track == "evidence"]
    panels = [(text[text.qtype != "claim"], "f1", "Text track: ID F1 ↑"),
              (text[text.qtype == "claim"], "claim_correct", "Text track: claim accuracy ↑"),
              (ev[ev.qtype != "claim"], "f1", "Evidence track: ID F1 ↑"),
              (ev[ev.qtype == "temporal"], "stale_adoption", "Evidence track: stale adoption ↓")]
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.8))
    for ax, (d, m, title) in zip(axes, panels):
        bars(ax, d, m, title)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(out_dir / f"fig_main_metrics.{ext}", dpi=220)
    plt.close(fig)

    ans = df[df.qtype != "claim"]
    fam = summarize(ans, ("system", "subtype")).pivot(index="subtype", columns="system", values="f1")
    fam = fam[[s for s in systems if s in fam.columns]] * 100
    fig, ax = plt.subplots(figsize=(1.1 * len(fam.columns) + 2.5, 0.42 * len(fam) + 1.6))
    im = ax.imshow(fam.values, cmap=LinearSegmentedColormap.from_list("seq", SEQ), vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(len(fam.columns)))
    ax.set_xticklabels([LABEL.get(s, s) for s in fam.columns], rotation=40, ha="right", fontsize=8)
    ax.set_yticks(range(len(fam.index)))
    ax.set_yticklabels(fam.index, fontsize=8)
    for i in range(fam.shape[0]):
        for j in range(fam.shape[1]):
            v = fam.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7.5, color="#ffffff" if v > 55 else INK)
    ax.set_title("Identifier F1 (%) by question family", loc="left", color=INK)
    fig.colorbar(im, ax=ax, fraction=0.03)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(out_dir / f"fig_f1_heatmap.{ext}", dpi=220)
    plt.close(fig)

    sm = summarize(ans).set_index("system")
    llm_sys = [s for s in systems if s != "graph_oracle"]
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    _style(ax)
    x = np.arange(len(llm_sys))
    pla = [sm.loc[s, "uar_plausible"] * 100 if s in sm.index else 0 for s in llm_sys]
    imp = [(sm.loc[s, "uar"] - sm.loc[s, "uar_plausible"]) * 100 if s in sm.index else 0 for s in llm_sys]
    ax.bar(x, pla, 0.62, color=SLOTS[0], edgecolor=SURF, linewidth=2, label="Plausible (near-miss of a correct ID)")
    ax.bar(x, imp, 0.62, bottom=pla, color=SLOTS[1], edgecolor=SURF, linewidth=2, label="Implausible")
    ax.set_xticks(x)
    ax.set_xticklabels([LABEL.get(s, s) for s in llm_sys], rotation=35, ha="right", fontsize=8)
    ax.set_ylabel("% of predicted identifiers", color=INK2)
    ax.set_title("Unsupported threat associations", loc="left", color=INK)
    ax.legend(frameon=False, fontsize=8, labelcolor=INK2)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(out_dir / f"fig_uar_breakdown.{ext}", dpi=220)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(5.6, 3.8))
    _style(ax)
    ax.xaxis.grid(True, color=GRID, lw=0.6)
    st = summarize(text[text.qtype != "claim"]).set_index("system") if not text.empty else sm
    for s in llm_sys:
        if s not in st.index:
            continue
        ax.scatter(st.loc[s, "calls"], st.loc[s, "f1"] * 100, s=60, color=color_of(s), edgecolor=SURF,
                   linewidth=2, zorder=3)
        ax.annotate(LABEL.get(s, s), (st.loc[s, "calls"], st.loc[s, "f1"] * 100), xytext=(5, 4),
                    textcoords="offset points", fontsize=7.5, color=INK2)
    ax.set_xlabel("LLM calls per question", color=INK2)
    ax.set_ylabel("Text-track ID F1 (%)", color=INK2)
    ax.set_title("Cost vs. answer quality", loc="left", color=INK)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(out_dir / f"fig_cost_quality.{ext}", dpi=220)
    plt.close(fig)
