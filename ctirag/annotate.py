"""Human validation of the automatically generated gold answers.

1. export_sample(): writes annotation_sheet.csv with a stratified sample (default 150 questions),
   the gold answer, and the gold evidence text. Give one copy to each annotator.
2. Each annotator fills `label` with one of: CORRECT / INCORRECT / AMBIGUOUS, plus an optional `comment`
   (and `corrected_gold` when INCORRECT). Annotators work independently.
3. agreement(): Cohen's kappa between the two sheets, per-family gold accuracy, and the list of
   disagreements to adjudicate. Report kappa and gold accuracy in the paper; drop or fix INCORRECT items.

Questions from CTIBench (ate, rcm) already have curated gold, so they are excluded by default.
"""
from __future__ import annotations

import random
from collections import defaultdict
from pathlib import Path

import pandas as pd

from .corpus import Corpus

LABELS = ["CORRECT", "INCORRECT", "AMBIGUOUS"]


def export_sample(questions: list[dict], corpus: Corpus, out: Path, n: int = 150, seed: int = 7,
                  skip_qtypes=("ate", "rcm")) -> Path:
    rng = random.Random(seed)
    by = defaultdict(list)
    for q in questions:
        if q["qtype"] not in skip_qtypes:
            by[q["subtype"]].append(q)
    per = max(1, n // max(1, len(by)))
    picked = []
    for k in sorted(by):
        xs = by[k][:]
        rng.shuffle(xs)
        picked += xs[:per]
    rows = []
    for q in picked:
        ev = []
        for d in q["gold_docs"][:4]:
            if d in corpus.docs:
                doc = corpus.docs[d]
                ev.append(f"[{d}] {doc.header()}\n{doc.text[:700]}")
        rows.append({"qid": q["qid"], "family": q["subtype"], "question": q["question"],
                     "gold_answer": q["gold_label"] or ", ".join(q["gold_ids"]),
                     "stale_or_negative_ids": ", ".join(q.get("stale_ids", [])),
                     "evidence": "\n\n".join(ev), "label": "", "corrected_gold": "", "comment": ""})
    out = Path(out)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"[annotate] wrote {len(rows)} items to {out}. Labels: {LABELS}")
    return out


def cohen_kappa(a: list[str], b: list[str]) -> float:
    cats = sorted(set(a) | set(b))
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def agreement(sheet_a: Path, sheet_b: Path, out_dir: Path | None = None) -> dict:
    A = pd.read_csv(sheet_a).set_index("qid")
    B = pd.read_csv(sheet_b).set_index("qid")
    common = [q for q in A.index if q in B.index and str(A.loc[q, "label"]).upper() in LABELS
              and str(B.loc[q, "label"]).upper() in LABELS]
    la = [str(A.loc[q, "label"]).upper() for q in common]
    lb = [str(B.loc[q, "label"]).upper() for q in common]
    kappa = cohen_kappa(la, lb)
    fam = A.loc[common, "family"]
    agreed = pd.DataFrame({"family": fam, "a": la, "b": lb})
    agreed["both_correct"] = (agreed.a == "CORRECT") & (agreed.b == "CORRECT")
    per_family = agreed.groupby("family").both_correct.mean().mul(100).round(1)
    disagreements = agreed[agreed.a != agreed.b]
    res = {"n": len(common), "kappa": round(kappa, 3), "gold_accuracy_both_correct": round(agreed.both_correct.mean() * 100, 1),
           "per_family": per_family.to_dict(), "n_disagreements": len(disagreements)}
    if out_dir:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        disagreements.to_csv(out_dir / "annotation_disagreements.csv")
        per_family.to_csv(out_dir / "annotation_gold_accuracy.csv")
    print(f"[annotate] n={res['n']} kappa={res['kappa']} gold accuracy={res['gold_accuracy_both_correct']}%")
    return res


def drop_rejected(questions: list[dict], sheet_a: Path, sheet_b: Path) -> list[dict]:
    """Remove questions that BOTH annotators marked INCORRECT (adjudicate the rest by hand)."""
    A = pd.read_csv(sheet_a).set_index("qid")
    B = pd.read_csv(sheet_b).set_index("qid")
    bad = {q for q in A.index if q in B.index and str(A.loc[q, "label"]).upper() == "INCORRECT"
           and str(B.loc[q, "label"]).upper() == "INCORRECT"}
    return [q for q in questions if q["qid"] not in bad]
