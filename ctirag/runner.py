"""End-to-end orchestration: prepare data, build index, run systems (resumable), score."""
from __future__ import annotations

import json
import random
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .benchmark import build_benchmark, load_questions
from .config import Config
from .corpus import Corpus, build_corpus
from .download import fetch_all, fetch_nvd
from .index import HybridIndex
from .llm import BaseLLM, DailyLimitReached
from .systems import SYSTEMS


def prepare(cfg: Config, force_download: bool = False):
    """Download sources, build the corpus and the benchmark. Safe to re-run."""
    cfg.ensure()
    got = fetch_all(cfg, force_download)
    optional = {"cwe", "attack_old", "ctibench_ate", "ctibench_rcm"}
    missing = [k for k, v in got.items() if v is None and k not in optional]
    if missing:
        raise RuntimeError(f"Required sources failed to download: {missing}")
    for k in sorted(optional):
        if got.get(k) is None:
            print(f"[prepare] WARNING optional source '{k}' missing - the questions that need it are skipped")
    nvd = None
    if cfg.nvd_enrich:
        kev = json.loads((cfg.raw_dir / "kev.json").read_text())["vulnerabilities"]
        ids = [v["cveID"] for v in sorted(kev, key=lambda v: v["dateAdded"], reverse=True)]
        try:
            nvd = fetch_nvd(ids, cfg)
        except Exception as e:  # noqa: BLE001
            print(f"[prepare] NVD enrichment skipped: {e}")
    corpus, procedures = build_corpus(cfg, nvd)
    qs, notes = build_benchmark(corpus, procedures, cfg)
    (cfg.proc_dir / "config.json").write_text(json.dumps(cfg.to_dict(), indent=2))
    return corpus, qs


def load_corpus(cfg: Config, with_notes: bool | None = None) -> Corpus:
    with_notes = cfg.inject_conflicts if with_notes is None else with_notes
    paths = [cfg.proc_dir / "docs.jsonl"] + ([cfg.proc_dir / "notes.jsonl"] if with_notes else [])
    return Corpus.load(*paths)


def run_tag(model: str, repeat: int = 0, base: str = "main") -> str:
    """Directory name for one (model, repeat) run, e.g. 'main/llama-3.3-70b-versatile/r0'."""
    return f"{base}/{model.replace('/', '_')}/r{repeat}"


def stratified_sample(qs: list[dict], per_subtype: int | None, seed: int = 0) -> list[dict]:
    if not per_subtype:
        return qs
    rng = random.Random(seed)
    by = {}
    for q in qs:
        by.setdefault(q["subtype"], []).append(q)
    out = []
    for k in sorted(by):
        xs = by[k][:]
        rng.shuffle(xs)
        out += xs[:per_subtype]
    return out


def run_system(name: str, corpus: Corpus, index: HybridIndex, llm: BaseLLM, cfg: Config,
               questions: list[dict], run_tag: str = "main", workers: int = 1) -> Path:
    out_dir = cfg.run_dir / run_tag
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{name}.jsonl"
    done = set()
    if out.exists():
        done = {json.loads(l)["qid"] for l in out.read_text().splitlines() if l.strip()}
    todo = [q for q in questions if q["qid"] not in done]
    if not todo:
        print(f"[run] {name}: all {len(questions)} done")
        return out
    sysobj = SYSTEMS[name](corpus, index, llm, cfg)
    lock = threading.Lock()
    stop = threading.Event()
    print(f"[run] {name}: {len(todo)} to go ({len(done)} cached)")

    def one(q):
        if stop.is_set():
            return None
        try:
            r = sysobj.run(q["question"])
        except DailyLimitReached:
            stop.set()
            raise
        except Exception as e:  # noqa: BLE001
            r = {"answer": "", "ids": [], "verdict": None, "flags": [], "citations": [], "retrieved": [],
                 "usage": {}, "latency": 0.0, "error": f"{e.__class__.__name__}: {e}",
                 "trace": traceback.format_exc()[-1500:]}
        r["qid"] = q["qid"]
        with lock, out.open("a") as fh:
            fh.write(json.dumps(r) + "\n")
        return r

    try:
        from tqdm.auto import tqdm
    except Exception:  # noqa: BLE001
        tqdm = lambda x, **k: x  # noqa: E731
    try:
        if workers <= 1:
            for q in tqdm(todo, desc=name):
                one(q)
        else:
            with ThreadPoolExecutor(workers) as ex:
                futs = [ex.submit(one, q) for q in todo]
                for f in tqdm(as_completed(futs), total=len(futs), desc=name):
                    f.result()
    except DailyLimitReached as e:
        print(f"[run] {name}: provider daily limit reached - progress saved, re-run later to resume.\n  {e}")
    return out
