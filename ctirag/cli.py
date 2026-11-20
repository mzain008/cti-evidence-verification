"""Command line entry point.

python -m ctirag.cli prepare
python -m ctirag.cli run    --model llama-3.3-70b-versatile --repeat 0 --per-subtype 3
python -m ctirag.cli report --model llama-3.3-70b-versatile --repeat 0
python -m ctirag.cli compare                       # multi-model / multi-repeat table
python -m ctirag.cli annotate-export               # sheet for human validation
python -m ctirag.cli annotate-agree --a a.csv --b b.csv
python -m ctirag.cli run --mock --per-subtype 2    # pipeline test without an API key
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .benchmark import load_questions
from .config import Config
from .evaluate import load_results, score_run
from .index import HybridIndex
from .llm import make_llm
from .report import make_report, multi_model_table
from .runner import load_corpus, prepare, run_system, run_tag, stratified_sample


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prepare", "run", "report", "compare", "annotate-export", "annotate-agree"])
    ap.add_argument("--work", default=os.environ.get("CTIRAG_WORK", "./work"))
    ap.add_argument("--systems", nargs="*")
    ap.add_argument("--per-subtype", type=int, default=None, help="stratified sample size per question family")
    ap.add_argument("--model", default=None, help="Groq model id (default: first available preference)")
    ap.add_argument("--repeat", type=int, default=0)
    ap.add_argument("--base", default="main", help="run group name")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--mock", action="store_true", help="heuristic mock LLM (pipeline test only)")
    ap.add_argument("--no-nvd", action="store_true")
    ap.add_argument("--a")
    ap.add_argument("--b")
    a = ap.parse_args()
    cfg = Config(work_dir=a.work, nvd_enrich=not a.no_nvd, llm_provider="mock" if a.mock else "groq",
                 llm_model=a.model, repeat=a.repeat).ensure()
    systems = a.systems or cfg.systems

    if a.cmd == "prepare":
        prepare(cfg)
        return
    if a.cmd == "annotate-export":
        from .annotate import export_sample
        export_sample(load_questions(cfg), load_corpus(cfg), cfg.work_dir and Path(cfg.work_dir) / "annotation_sheet.csv")
        return
    if a.cmd == "annotate-agree":
        from .annotate import agreement
        print(json.dumps(agreement(Path(a.a), Path(a.b), Path(cfg.work_dir) / "annotation"), indent=2))
        return

    qs = stratified_sample(load_questions(cfg), a.per_subtype, cfg.seed)
    corpus = load_corpus(cfg)
    if a.cmd == "compare":
        dfs = {}
        for meta in sorted((cfg.run_dir / a.base).glob("*/r*/meta.json")):
            tag_dir = meta.parent
            m = json.loads(meta.read_text())
            res = load_results(tag_dir, systems)
            ids = set(m.get("qids", []))
            sub = [q for q in qs if not ids or q["qid"] in ids]
            dfs[f"{m['model']}/r{m.get('repeat', 0)}"] = score_run(sub, res, corpus)
        print(multi_model_table(dfs, cfg.run_dir / a.base).to_markdown(index=False))
        return

    model = "mock-heuristic" if a.mock else None
    llm = None
    if a.cmd == "run":
        llm = make_llm(cfg, os.environ.get("GROQ_API_KEY"))
        model = llm.model
    model = model or a.model
    if not model:
        raise SystemExit("--model is required for report (the model id used for the run)")
    tag = run_tag(model, a.repeat, a.base)
    tag_dir = cfg.run_dir / tag
    if a.cmd == "run":
        index = HybridIndex(corpus, cfg.dense_model, cfg.proc_dir)
        tag_dir.mkdir(parents=True, exist_ok=True)
        (tag_dir / "meta.json").write_text(json.dumps({"model": model, "repeat": a.repeat, "n_questions": len(qs),
                                                       "qids": [q["qid"] for q in qs], "systems": systems,
                                                       **cfg.to_dict()}, indent=2))
        for s in systems:
            run_system(s, corpus, index, llm, cfg, qs, tag, a.workers)
    df = score_run(qs, load_results(tag_dir, systems), corpus)
    make_report(df, tag_dir / "report", model)
    for t in ("text", "evidence"):
        p = tag_dir / "report" / f"table_main_{t}.md"
        if p.exists():
            print(p.read_text(), "\n")


if __name__ == "__main__":
    main()
