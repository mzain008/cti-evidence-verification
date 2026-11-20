"""v6.5 additions. The frozen v4 code (systems.py etc.) is NOT changed; everything new lives here.

1. Corrected conflict detector (agent code v4.1, systems suffixed "_v11")
   Defect in v4: a source's "view" of an entity e for a relation also counted inverse-index edges, i.e.
   assertions that come from documents about OTHER entities. For a claim "CVE-X is caused by CWE-Y" the
   identifiers are ordered by kind (CWE before CVE), so the detector compared CWE-Y -weakness_of-> CVEs.
   That inverse list is assembled from NVD records and from KEV records, which cover different vulnerability
   populations, so different coverage was read as an equal-authority disagreement (false CONFLICT).
   Fix (pre-specified, one rule, applies to every relation): a source's view of e counts only what that
   source's own documents ABOUT e assert (doc.entity_id == e). Nothing else changes: same retrieval, tool loop,
   prompts, temporal checks, authority rule, verification.
   Offline replay on the v5 ledgers (before any new run): every one of the 50 true conflicts is still detected
   by B, C and the detector ablations, and every detector false positive on the CVE-CWE claims disappears.

2. Conflict-aware RAG baseline ("conflict_aware_rag"), specified before it was run
   A strong non-verifier baseline that is explicitly designed for contradictory evidence. It is NOT a
   reproduction of ConflictRAG or any other published system; it follows the common detect -> classify ->
   resolve -> generate pattern with the LLM doing every step.
   - Evidence: exactly the same evidence set as the non-agentic verifier B (fixed hybrid retrieval + the
     question's entity documents + one-hop graph expansion), ranked the same way (question entities first,
     latest snapshot first, 16 documents), shown with the same metadata line (source, authority tier, date,
     version, status). So it gets the same information B gets; only the decision procedure differs.
   - Call 1 (analysis): the LLM lists what each source asserts about the asked relation, finds conflicts,
     classifies each as temporal (older release vs latest release of the same source), reliability (lower-
     vs higher-authority source) or equal_authority (equally authoritative current sources), and resolves it
     with fixed rules stated in the prompt: temporal -> latest release; reliability -> higher authority;
     equal authority -> keep all, attributed. It also states whether the question's identifiers are described
     by any evidence document.
   - Call 2 (answer): the standard answer prompt (same answer spec and requested-type line as B and C) plus the
     analysis. Flags: CONFLICT if call 1 found a reliability or equal-authority conflict, OUTDATED if it found a
     temporal one, plus the flags the answer call returns.
   - No deterministic checks and no verification: that is the difference to B and C under test.
"""
from __future__ import annotations

import json
import re
import time

from . import systems as S
from .corpus import Doc, extract_ids
from .llm import parse_json

CODE_VERSION = "v4.1"


# ---------------------------------------------------------------------------------------------
# 1. Corrected detector
# ---------------------------------------------------------------------------------------------
class DirectViews:
    """Mixin: a source's view of entity e counts only assertions made in its own documents about e."""

    def _views(self, e: str, rel: str, visible: set) -> dict:
        v = {}
        for r, t, did in self.c.edges.get(e, []):
            if r != rel or did not in visible or not self.c.is_latest(did):
                continue
            d = self.c.docs[did]
            if d.entity_id != e:          # inverse-index entry built from a document about another entity
                continue
            v.setdefault(d.source, set()).add(t)
        return v

    def evidence_checks(self, question, q_ids, want, ledger, flags, notes, conflicts):
        """For a claim, check the relation in both directions (subject->object and object->subject), so the
        direction in which the sources make their own assertions is always examined, whatever the order of the
        identifier kinds. Identical conflicts and notes are kept once."""
        if not (question.startswith(S.CLAIM_MARK) and len(q_ids) >= 2):
            return super().evidence_checks(question, q_ids, want, ledger, flags, notes, conflicts)
        rev = [q_ids[-1]] + q_ids[1:-1] + [q_ids[0]]
        found, new_notes = [], []
        for order in (q_ids, rev):
            super().evidence_checks(question, order, want, ledger, flags, new_notes, found)
        seen = set()
        for cf in found:
            k = json.dumps(cf, sort_keys=True)
            if k not in seen:
                seen.add(k)
                conflicts.append(cf)
        notes.extend(dict.fromkeys(new_notes))


def _v11(base):
    cls = type(base.__name__ + "V11", (DirectViews, base), {"name": base.name + "_v11"})
    cls.__doc__ = f"{base.name} with the corrected conflict detector (v4.1)."
    return cls


# Every system that runs the detector. react_agent (no checks) and agent_no_conflict (detector off) never
# call it, so their v5 results are unaffected; this is asserted in check_unaffected().
DETECTOR_SYSTEMS = ["graph_verifier", "evidence_agent", "agent_no_verify", "agent_no_graph",
                    "agent_no_temporal", "agent_no_authority"]
V11 = {f"{n}_v11": _v11(S.SYSTEMS[n]) for n in DETECTOR_SYSTEMS}


def check_unaffected():
    for n in ("react_agent", "agent_no_conflict", "naive", "kg_rag", "multihop", "crag", "graph_oracle"):
        cls = S.SYSTEMS[n]
        uses = issubclass(cls, S.EvidenceAgent) and cls.use_checks and cls.use_conflict
        assert not uses, f"{n} uses the detector"
    return True


# ---------------------------------------------------------------------------------------------
# 2. Conflict-aware RAG baseline
# ---------------------------------------------------------------------------------------------
ANALYSIS_SPEC = """Before answering, analyse the evidence for conflicts about the relation the question asks about.
1. Compare what the documents assert about that relation.
2. Find conflicts and classify each one:
   - "temporal": an older release of a source asserts something that the latest release of the same source does not;
   - "reliability": a lower-authority source asserts something that a higher-authority source does not (or contradicts it);
   - "equal_authority": equally authoritative current sources assert different identifiers.
3. Resolve every conflict with these rules: temporal -> trust the latest release; reliability -> trust the higher
   authority; equal_authority -> keep every identifier and attribute it to its source.
4. State whether the identifiers named in the question are described by at least one evidence document.
Keep the output short. Return JSON only, with the keys in this order:
{"conflicts": [{"type": "temporal|reliability|equal_authority", "docs": ["..."], "disputed_ids": ["..."], "resolution": "..."}],
 "trusted_ids": ["..."], "rejected_ids": ["..."], "question_entities_found": true, "note": "at most 30 words"}"""


class ConflictAwareRAG(S.System):
    name = "conflict_aware_rag"
    n_docs = 16

    # same evidence as the non-agentic verifier B (GraphVerifier.gather), same ranking as B's draft
    def gather(self, question: str):
        ledger: dict[str, Doc] = {}

        def add(docs):
            for d in docs:
                ledger.setdefault(d.doc_id, d)
        q_ids = extract_ids(question)
        for eid in q_ids:
            add(self.c.entity_docs(eid))
        docs = self.retrieve(question)
        add(docs)
        seeds = q_ids or [d.entity_id for d in docs[:3]]
        for s in seeds[:4]:
            for _, tgt, did in self.c.neighbors(s)[:40]:
                add([self.c.docs[did]] + self.c.entity_docs(tgt)[:2])
        ranked = sorted(ledger.values(), key=lambda d: (d.entity_id not in q_ids, not self.c.is_latest(d.doc_id)))
        return ledger, ranked[: self.n_docs]

    def run(self, question):
        t0, tr = time.time(), {}
        ledger, ev = self.gather(question)
        want = S.requested_kind(question)
        p1 = (f"<question>{question}</question>\n\n<evidence>\n{S.fmt_evidence(ev)}\n</evidence>\n\n{ANALYSIS_SPEC}")
        raw = self.llm.chat([{"role": "system", "content": S.SYSTEM}, {"role": "user", "content": p1}],
                            "conflict_analysis", True, tr)
        an = parse_json(raw)
        if not isinstance(an, dict):
            an = {}
        conflicts = [c for c in (an.get("conflicts") or []) if isinstance(c, dict)]
        types = {str(c.get("type", "")).lower() for c in conflicts}
        if not an and raw:      # output cut off before the JSON closed: keep the conflict types it did state
            types = set(re.findall(r'"type"\s*:\s*"(temporal|reliability|equal_authority)"', raw))
            conflicts = [{"type": t, "salvaged": True} for t in sorted(types)]
        flags = set()
        if types & {"reliability", "equal_authority"}:
            flags.add("CONFLICT")
        if "temporal" in types:
            flags.add("OUTDATED")
        extra = ("Conflict analysis of this evidence (follow its resolutions): "
                 + json.dumps({k: an.get(k) for k in ("conflicts", "trusted_ids", "rejected_ids",
                                                      "question_entities_found")}, ensure_ascii=False)[:3000]
                 + "\nIf the analysis found a reliability or equal-authority conflict, include CONFLICT in flags. "
                   "If the identifiers in the question are not described by any evidence document, return no ids "
                   "(or NOT_ENOUGH_INFO for a claim) and the flag INSUFFICIENT_EVIDENCE.\n")
        if want:
            extra = f"Requested answer type: {S.KIND_LABEL[want]}. Put only identifiers of this type in \"ids\".\n" + extra
        out = self.ask(S.user_prompt(question, ev, extra), "answer", tr)
        res = S.finalize(out, list(ledger), tr, t0)
        res["flags_llm"] = list(res["flags"])
        res["flags"] = sorted(set(res["flags"]) | flags)
        res["conflict_analysis"] = conflicts
        res["evidence_shown"] = [d.doc_id for d in ev]
        return res


NEW_SYSTEMS = {**V11, ConflictAwareRAG.name: ConflictAwareRAG}


def register():
    """Add the v6.5 systems to the runner's registry (the frozen SYSTEMS dict object is extended, not replaced)."""
    check_unaffected()
    S.SYSTEMS.update(NEW_SYSTEMS)
    label("")
    return sorted(NEW_SYSTEMS)


# ---------------------------------------------------------------------------------------------
# 3. Regression tests (CPU, no LLM)
# ---------------------------------------------------------------------------------------------
def _toy_corpus():
    from .corpus import Corpus
    R = "2026-08-04"
    docs = [
        # CVE-2099-0001: NVD and KEV agree on CWE-1. CVE-2099-0002: only NVD lists CWE-1; CVE-2099-0003: only KEV.
        Doc("nvd:CVE-2099-0001", "NVD", "CVE-2099-0001", "cve", "c1", "t", R, "", "active", [("has_weakness", "CWE-1")]),
        Doc("kev:CVE-2099-0001", "CISA KEV", "CVE-2099-0001", "cve", "c1", "t", R, "", "active", [("has_weakness", "CWE-1")]),
        Doc("nvd:CVE-2099-0002", "NVD", "CVE-2099-0002", "cve", "c2", "t", R, "", "active", [("has_weakness", "CWE-1")]),
        Doc("kev:CVE-2099-0003", "CISA KEV", "CVE-2099-0003", "cve", "c3", "t", R, "", "active", [("has_weakness", "CWE-1")]),
        # a real equal-authority disagreement: NVD says CWE-1, KEV says CWE-2
        Doc("nvd:CVE-2099-0004", "NVD", "CVE-2099-0004", "cve", "c4", "t", R, "", "active", [("has_weakness", "CWE-1")]),
        Doc("kev:CVE-2099-0004", "CISA KEV", "CVE-2099-0004", "cve", "c4", "t", R, "", "active", [("has_weakness", "CWE-2")]),
        Doc("cwe:CWE-1", "MITRE CWE", "CWE-1", "cwe", "w1", "t", R),
        Doc("cwe:CWE-2", "MITRE CWE", "CWE-2", "cwe", "w2", "t", R),
        # technique with an injected lower-authority note asserting a wrong mitigation
        Doc("attack:T9999", "MITRE ATT&CK", "T9999", "technique", "t", "t", R, "", "active", [("mitigated_by", "M9001")]),
        Doc("attack:M9001", "MITRE ATT&CK", "M9001", "mitigation", "m1", "t", R, "", "active", [("mitigates", "T9999")]),
        Doc("attack:M9002", "MITRE ATT&CK", "M9002", "mitigation", "m2", "t", R),
        Doc("note:T9999", "Security Blog", "T9999", "technique", "n", "t", R, "", "active", [("mitigated_by", "M9002")]),
        # agreeing note
        Doc("attack:T9998", "MITRE ATT&CK", "T9998", "technique", "t", "t", R, "", "active", [("mitigated_by", "M9001")]),
        Doc("note:T9998", "Security Blog", "T9998", "technique", "n", "t", R, "", "active", [("mitigated_by", "M9001")]),
    ]
    return Corpus(docs)


def _detect(cls, c, question):
    agent = cls.__new__(cls)
    agent.c = c
    q_ids = extract_ids(question)
    ledger = {d.doc_id: d for d in c.docs.values()}
    flags, notes, conflicts = set(), [], []
    agent.evidence_checks(question, q_ids, S.requested_kind(question), ledger, flags, notes, conflicts)
    return conflicts


def regression_test(verbose=True):
    """old = frozen v4 detector, new = v4.1. Each case: (question, expected conflict old, expected conflict new)."""
    c = _toy_corpus()
    claim = S.CLAIM_MARK + ' against authoritative security sources: "{}"'
    cases = [
        ("CVE->CWE claim, CVE only in NVD, KEV has no record (the v4 bug)", claim.format("CVE-2099-0002 is caused by weakness CWE-1."), True, False),
        ("CVE->CWE claim, NVD and KEV agree", claim.format("CVE-2099-0001 is caused by weakness CWE-1."), False, False),
        ("CVE->CWE claim, real NVD/KEV disagreement", claim.format("CVE-2099-0004 is caused by weakness CWE-1."), True, True),
        ("CVE->CWE list question, real disagreement", "Which CWE weaknesses (CWE-IDs) does CVE-2099-0004 have?", True, True),
        ("CVE->CWE list question, sources agree", "Which CWE weaknesses (CWE-IDs) does CVE-2099-0001 have?", False, False),
        ("mitigation list, injected lower-authority note", "Which MITRE ATT&CK mitigations (M-IDs) address technique T9999?", True, True),
        ("mitigation claim, injected note", claim.format("MITRE ATT&CK mitigation M9002 mitigates technique T9999."), True, True),
        ("mitigation list, agreeing note", "Which MITRE ATT&CK mitigations (M-IDs) address technique T9998?", False, False),
    ]
    rows, ok = [], True
    for name, q, exp_old, exp_new in cases:
        old = bool(_detect(S.SYSTEMS["evidence_agent"], c, q))
        new = bool(_detect(V11["evidence_agent_v11"], c, q))
        good = (old == exp_old) and (new == exp_new)
        ok &= good
        rows.append({"case": name, "v4 conflict": old, "v4.1 conflict": new, "expected v4.1": exp_new, "pass": good})
    if verbose:
        for r in rows:
            print(("PASS " if r["pass"] else "FAIL ") + f"{r['case']}: v4={r['v4 conflict']} v4.1={r['v4.1 conflict']}")
    assert ok, "regression test failed"
    return rows


def replay(corpus, questions, results, cls_old, cls_new):
    """Re-run the deterministic checks on the evidence each system actually gathered (no LLM).
    Returns per question: conflicts recorded in the run, replayed with v4, replayed with v4.1."""
    out = []
    qmap = {q["qid"]: q for q in questions}
    for qid, r in results.items():
        if qid not in qmap:
            continue
        qu = qmap[qid]["question"]
        q_ids = extract_ids(qu)
        ledger = {d: corpus.docs[d] for d in r.get("retrieved") or [] if d in corpus.docs}
        rows = []
        for cls in (cls_old, cls_new):
            a = cls.__new__(cls)
            a.c = corpus
            cf = []
            a.evidence_checks(qu, q_ids, S.requested_kind(qu), dict(ledger), set(), [], cf)
            rows.append(sorted((x["entity"], x["relation"], x["kind"]) for x in cf))
        rec = sorted((x["entity"], x["relation"], x["kind"]) for x in r.get("conflicts") or [])
        out.append({"qid": qid, "recorded": rec, "replay_v4": rows[0], "replay_v41": rows[1],
                    "has_conflict": bool(qmap[qid]["meta"].get("has_conflict"))})
    return out


# ---------------------------------------------------------------------------------------------
# 4. Analyses on question-level results (no LLM). Used for the v5 results and for the v6.5 runs.
# ---------------------------------------------------------------------------------------------
LABELS = {"graph_verifier_v11": "Non-agentic graph verifier (B), v4.1",
          "evidence_agent_v11": "Evidence-Aware Agent (C), v4.1",
          "agent_no_verify_v11": "- verification, v4.1", "agent_no_graph_v11": "- graph verification, v4.1",
          "agent_no_temporal_v11": "- temporal verification, v4.1",
          "agent_no_authority_v11": "- authority verification, v4.1",
          "conflict_aware_rag": "Conflict-aware RAG baseline"}

# Pre-specified equivalence margins (percentage points), fixed before the v6.5 runs.
EQ_MARGIN = {"claim_correct": 3.0, "abstain_correct": 3.0, "list_f1": 5.0, "resolution_correct": 10.0,
             "conflict_detect_correct": 3.0}


def label(s):
    from . import final_eval as fe
    fe.SYSTEM_LABEL.update(LABELS)
    return fe.SYSTEM_LABEL.get(s, s)


def exact_ci(k, n, alpha=0.05):
    """Clopper-Pearson interval for k successes out of n."""
    from scipy.stats import beta
    if n == 0:
        return (float("nan"), float("nan"))
    lo = 0.0 if k == 0 else beta.ppf(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(1 - alpha / 2, k + 1, n - k)
    return float(lo), float(hi)


def _prf(g):
    import numpy as np
    y, p = g.has_conflict.astype(bool).values, g.pred_conflict.astype(bool).values
    tp, fp, fn = int((y & p).sum()), int((~y & p).sum()), int((y & ~p).sum())
    pr = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    return tp, fp, fn, pr, rc, (2 * pr * rc / (pr + rc) if pr + rc else 0.0)


def summary(df):
    """One numeric row per system: the headline metrics of the paper (percent)."""
    import numpy as np
    import pandas as pd
    rows = []
    for s in df.system.unique():
        g = df[df.system == s]
        tp, fp, fn, pr, rc, f1 = _prf(g)
        cl = g[g.is_claim]                      # all claim questions, incl. NOT_ENOUGH_INFO ones (as in the paper)
        ab = g[~g.answerable]
        rows.append({"system": s, "n": len(g),
                     "claim_acc": 100 * cl.claim_correct.mean(), "claim_k_n": f"{int(cl.claim_correct.sum())}/{len(cl)}",
                     "abstention": 100 * ab.abstain_correct.mean(), "abst_k_n": f"{int(ab.abstain_correct.sum())}/{len(ab)}",
                     "list_f1": 100 * g.list_f1.mean(), "conflict_P": 100 * pr, "conflict_R": 100 * rc,
                     "conflict_F1": 100 * f1, "TP/FP/FN": f"{tp}/{fp}/{fn}",
                     "resolution": 100 * g[g.has_conflict].resolution_correct.mean(),
                     "injected_adoption": 100 * g.injected_adoption.mean(),
                     "flag_recall": 100 * g.flag_correct.mean(),
                     "coverage": 100 * g.answered.mean(), "selective_risk": 100 * g.loss.mean(),
                     "support_ratio": 100 * g.support_ratio.mean() if g.support_ratio.notna().any() else np.nan})
    return pd.DataFrame(rows)


def claim_ci_table(df):
    """Exact 95% intervals for claim accuracy and abstention (k/n), so 100% is not read as a population value."""
    import pandas as pd
    rows = []
    for s in df.system.unique():
        g = df[df.system == s]
        cl = g[g.is_claim]
        ab = g[~g.answerable]
        for name, x in (("claim accuracy", cl.claim_correct), ("abstention", ab.abstain_correct)):
            k, n = int(x.sum()), int(x.notna().sum())
            lo, hi = exact_ci(k, n)
            rows.append({"system": s, "metric": name, "k/n": f"{k}/{n}", "estimate": round(100 * k / n, 1),
                         "95% exact CI": f"{100 * lo:.1f}-{100 * hi:.1f}"})
    return pd.DataFrame(rows)


def cluster_bootstrap(df, metric, systems, cluster="subtype", n_boot=5000, seed=0):
    """Mean of `metric` per system with a 95% CI that resamples whole question families (23 sub-types) instead
    of single questions, and the paired difference of the first two systems on the same resamples."""
    import numpy as np
    import pandas as pd
    d = df[df.system.isin(systems)].pivot_table(index=["qid", cluster], columns="system", values=metric)
    d = d.dropna()
    fam = d.index.get_level_values(cluster)
    groups = {f: np.where(fam == f)[0] for f in pd.unique(fam)}
    keys = list(groups)
    vals = d[systems].values
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        idx = np.concatenate([groups[keys[i]] for i in rng.integers(0, len(keys), len(keys))])
        boots.append(vals[idx].mean(0))
    boots = np.array(boots) * 100
    out = {"metric": metric, "n_questions": len(d), "n_clusters": len(keys)}
    for j, s in enumerate(systems, 1):
        out[f"system {j}"] = s
        out[f"mean {j}"] = round(100 * vals[:, j - 1].mean(), 1)
        out[f"95% CI {j}"] = f"{np.quantile(boots[:, j - 1], .025):.1f}-{np.quantile(boots[:, j - 1], .975):.1f}"
    if len(systems) >= 2:
        diff = boots[:, 0] - boots[:, 1]
        out["diff (1-2)"] = round(100 * (vals[:, 0].mean() - vals[:, 1].mean()), 1)
        out["diff 95% CI"] = f"{np.quantile(diff, .025):.1f} to {np.quantile(diff, .975):.1f}"
        lo90, hi90 = np.quantile(diff, .05), np.quantile(diff, .95)
        out["diff 90% CI"] = f"{lo90:.1f} to {hi90:.1f}"
        m = EQ_MARGIN.get(metric)
        if m is not None:
            out["margin"] = f"±{m:g}"
            out["equivalent (TOST, 90% CI inside margin)"] = "yes" if (lo90 > -m and hi90 < m) else "no"
    return out


def real_vs_synthetic(df):
    """Conflict detection and resolution separately for real NVD/KEV disagreements and injected notes."""
    import pandas as pd
    rows = []
    for s in df.system.unique():
        g = df[(df.system == s) & df.has_conflict]
        for kind, sub in (("real (NVD vs KEV)", g[g.subtype == "nvd_kev"]),
                          ("synthetic (injected note)", g[g.subtype != "nvd_kev"])):
            rows.append({"system": s, "conflicts": kind, "n": len(sub),
                         "detected %": round(100 * sub.pred_conflict.mean(), 1),
                         "resolved correctly %": round(100 * sub.resolution_correct.mean(), 1)})
    return pd.DataFrame(rows)


def provenance(questions, results):
    """Which mechanism decided each final answer of a verifier system (B, C):
    unknown-identifier rule, typed graph path, LLM entailment, or a mix. Read from the saved result fields."""
    import collections
    import pandas as pd
    qmap = {q["qid"]: q for q in questions}
    rows = []
    for s, res in results.items():
        cnt = collections.Counter()
        for qid, r in res.items():
            q = qmap[qid]
            tasks = (r.get("usage") or {}).get("tasks") or []
            ent = "entail" in tasks
            if q["question"].startswith(S.CLAIM_MARK):
                if r.get("verdict") == "NOT_ENOUGH_INFO" and not r.get("resolved_claim"):
                    k = "claim: unknown-identifier rule"
                elif ent:
                    k = "claim: LLM entailment"
                else:
                    k = "claim: typed graph path (rule)"
            else:
                rej = " ".join(str(x) for x in r.get("rejected") or [])
                if "question entity unknown" in rej:
                    k = "list: abstained, question entity unknown (rule)"
                elif r.get("ids"):
                    k = "list: answer ids kept via LLM entailment (at least one)" if ent else \
                        "list: answer ids kept via typed graph path (rule)"
                else:
                    k = "list: every drafted id rejected (" + ("rules + entailment" if ent else "rules") + ")"
            cnt[k] += 1
        n = sum(cnt.values())
        for k, v in sorted(cnt.items()):
            rows.append({"system": s, "decided by": k, "questions": v, "%": round(100 * v / n, 1)})
    return pd.DataFrame(rows)


def changes(questions, res_old, res_new):
    """Per question: did the final ids, verdict, flags or the CONFLICT flag change between two runs?"""
    import pandas as pd
    rows = []
    for qid, a in res_old.items():
        b = res_new.get(qid)
        if b is None:
            continue
        rows.append({"qid": qid, "ids_changed": sorted(a.get("ids") or []) != sorted(b.get("ids") or []),
                     "verdict_changed": a.get("verdict") != b.get("verdict"),
                     "flags_changed": sorted(a.get("flags") or []) != sorted(b.get("flags") or []),
                     "conflict_flag_changed": ("CONFLICT" in (a.get("flags") or [])) != ("CONFLICT" in (b.get("flags") or [])),
                     "detector_changed": len(a.get("conflicts") or []) != len(b.get("conflicts") or [])})
    d = pd.DataFrame(rows)
    d["any_answer_change"] = d.ids_changed | d.verdict_changed
    return d
