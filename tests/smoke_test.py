"""Smoke tests: run after `python -m ctirag.cli prepare`. No API key needed.

    CTIRAG_WORK=./work python tests/smoke_test.py

Checks that (1) every system runs end-to-end with the mock LLM, (2) the agent's verification rejects
outdated / non-latest evidence and the ablations bring the failure back, (3) no system keys on a source name.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ctirag.benchmark import load_questions  # noqa: E402
from ctirag.config import Config  # noqa: E402
from ctirag.index import HybridIndex  # noqa: E402
from ctirag.llm import MockLLM  # noqa: E402
from ctirag.runner import load_corpus, stratified_sample  # noqa: E402
from ctirag.systems import SYSTEMS  # noqa: E402


class Scripted:
    """Proposes a fixed answer, so the verification stage is tested in isolation."""

    def __init__(self, ids):
        self.ids = ids

    def json(self, messages, task, tr):
        tr["calls"] = tr.get("calls", 0) + 1
        if task == "agent_step":
            return {"actions": [{"action": "finish"}]}
        if task == "entail":
            return {"results": [{"supported": True}] * 10}
        return {"answer": "", "ids": self.ids, "flags": [], "claims": [], "focus_entity": None}


def main():
    cfg = Config(work_dir=os.environ.get("CTIRAG_WORK", "./work"), dense_model=None, llm_provider="mock").ensure()
    corpus = load_corpus(cfg)
    index = HybridIndex(corpus, None)
    qs = load_questions(cfg)
    assert qs, "run `python -m ctirag.cli prepare` first"

    # 1) every system runs on one question per family
    llm = MockLLM(cfg)
    sample = stratified_sample(qs, 1, 0)
    for name in cfg.systems:
        for q in sample:
            r = SYSTEMS[name](corpus, index, llm, cfg).run(q["question"])
            assert isinstance(r["ids"], list), (name, q["qid"])
    print(f"[ok] {len(cfg.systems)} systems x {len(sample)} families ran")

    # 2) real conflicts: outdated evidence is rejected by the agent, kept without temporal reasoning
    checked = 0
    for sub in ("version_drift", "rev4_rev5"):
        for q in [q for q in qs if q["subtype"] == sub and q["stale_ids"]][:3]:
            proposal = q["gold_ids"][:2] + q["stale_ids"][:2]
            full = SYSTEMS["evidence_agent"](corpus, index, Scripted(proposal), cfg).run(q["question"])
            abl = SYSTEMS["agent_no_temporal"](corpus, index, Scripted(proposal), cfg).run(q["question"])
            assert not set(full["ids"]) & set(q["stale_ids"]), (q["qid"], full["ids"])
            assert set(abl["ids"]) & set(q["stale_ids"]), (q["qid"], abl["ids"])
            assert "OUTDATED" in full["flags"], (q["qid"], full["flags"])
            checked += 1
    print(f"[ok] outdated evidence rejected on {checked} questions; ablation re-admits it")

    # 3) no hard-coded source names in the systems
    src = (Path(__file__).resolve().parents[1] / "ctirag" / "systems.py").read_text()
    for name in ("Community Note", "Vendor Blog", "Security Forum", "Analyst Wiki"):
        assert name not in src, f"systems.py must not key on source name {name!r}"
    print("[ok] no source-name special cases in systems.py")


if __name__ == "__main__":
    main()
