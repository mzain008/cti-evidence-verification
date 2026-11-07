"""Compared systems.

graph_oracle     NO LLM. Rule-based lookup over the link graph using the question templates. It is the
                 honest upper bound for structured lookups and shows where an LLM is actually needed.
naive            hybrid retrieval + one answer call
kg_rag           retrieval + 1-hop expansion over the link graph from question/retrieved entities, one call
multihop         iterative retrieve-reason loop (IRCoT / self-ask style)
crag             Corrective RAG: grade evidence, rewrite + re-retrieve when weak, answer from kept docs
react_agent      plain ReAct: the same tool loop as evidence_agent, then one answer call. No deterministic
                 evidence checks and no verification (v4; in v3 it also received the check notes)
graph_verifier   NON-agentic verifier: fixed retrieval + deterministic graph expansion of the question's
                 entities (no LLM-controlled tool loop), then exactly the same evidence checks, draft
                 prompt and verification as evidence_agent. Isolates what the agentic loop adds.
evidence_agent   proposed: tool-using planner + evidence ledger + deterministic evidence checks
                 (status, temporal, explicit conflict detection) + verification of every claimed
                 identifier (typed paths for structured links, strict entailment for text claims),
                 resolving conflicts only by source authority and same-source recency
ablations        agent_no_verify (checks, no verification), agent_no_graph, agent_no_temporal,
                 agent_no_authority, agent_no_conflict

v4 (conflict detection): every source that asserts a relation the question is about is compared with the
sources that own that relation (OWNER, authority tier). A source asserting an identifier the owners do not
assert is a CONFLICT, whether or not that identifier ends up in the answer, so the flag reports detection,
not acceptance. Owners that disagree with each other are an equal-authority CONFLICT. Each detected
conflict is recorded in the result ("conflicts") with source, authority, identifiers and resolution.
Without authority (agent_no_authority) every source counts as equal and the authority tier is hidden
from the LLM as well, so disagreements are reported but cannot be resolved.

Nothing in any system keys on a particular source *name*; conflicts are resolved from the numeric
authority tier and the snapshot date that every document carries.
"""
from __future__ import annotations

import re
import time
from collections import deque

from .config import AUTHORITY, Config

AGENT_VERSION = "v4"   # v2 typed answers; v3 claim IDs from the question; v4 explicit conflict detection
from .corpus import Corpus, Doc, extract_ids, id_kind, norm_id
from .index import HybridIndex
from .llm import BaseLLM

SYSTEM = ("You are a senior cyber threat intelligence analyst. Answer strictly from the evidence provided. "
          "Use exact identifiers (ATT&CK T####/T####.###, mitigations M####, groups G####, CWE-#, CAPEC-#, "
          "CVE-####-####, NIST SP 800-53 controls such as AC-2 or AC-2(1)). Never invent identifiers. Pay attention "
          "to each source's authority, date, version and status (revoked, deprecated, withdrawn). Respond with JSON only.")

ANSWER_SPEC = """Return a JSON object with keys:
"answer": a concise answer citing doc ids in square brackets,
"ids": list of the identifiers that answer the question (only the requested kind; empty list if none),
"verdict": for claim-verification questions exactly one of SUPPORTED, UNSUPPORTED, NOT_ENOUGH_INFO; otherwise null,
"flags": subset of [REVOKED, DEPRECATED, WITHDRAWN, OUTDATED, CONFLICT, INSUFFICIENT_EVIDENCE] that apply,
"citations": list of doc ids you relied on."""

def AUTHORITY_OF(source: str) -> int:  # noqa: N802
    return AUTHORITY.get(source, 1)


FLAGS = {"REVOKED", "DEPRECATED", "WITHDRAWN", "OUTDATED", "CONFLICT", "INSUFFICIENT_EVIDENCE"}
CLAIM_MARK = "Verify the following claim"


def header_no_authority(d: Doc) -> str:
    """Metadata line without the authority tier (used by agent_no_authority)."""
    return (f"[{d.doc_id}] source={d.source} date={d.date or 'n/a'} version={d.version or 'n/a'} "
            f"status={d.status}")


def fmt_doc(d: Doc, show_meta: bool = True, limit: int = 1100, show_auth: bool = True) -> str:
    t = d.text
    if len(t) > limit:  # keep head (definition) and tail (cross-reference lists)
        t = t[: int(limit * 0.55)] + " ... " + t[-int(limit * 0.45):]
    head = (d.header() if show_auth else header_no_authority(d)) if show_meta else f"[{d.doc_id}]"
    return f"{head}\n{t}"


def fmt_evidence(docs, show_meta=True, show_auth=True) -> str:
    return "\n\n".join(fmt_doc(d, show_meta, show_auth=show_auth) for d in docs)


def user_prompt(question: str, docs, extra: str = "", show_meta=True, show_auth=True) -> str:
    return (f"<question>{question}</question>\n\n<evidence>\n{fmt_evidence(docs, show_meta, show_auth)}\n"
            f"</evidence>\n\n{extra}{ANSWER_SPEC}")


def finalize(out: dict, retrieved: list[str], tracker: dict, t0: float, **extra) -> dict:
    raw_ids = out.get("ids") or []
    if isinstance(raw_ids, str):
        raw_ids = [raw_ids]
    ids = extract_ids(" ".join(str(x) for x in raw_ids))
    verdict = out.get("verdict")
    if isinstance(verdict, str):
        v = verdict.upper().replace(" ", "_")
        verdict = next((x for x in ("NOT_ENOUGH_INFO", "UNSUPPORTED", "SUPPORTED") if x in v), None)
    else:
        verdict = None
    flags = sorted({str(f).upper() for f in (out.get("flags") or []) if str(f).upper() in FLAGS})
    cites = [c for c in (out.get("citations") or []) if isinstance(c, str)]
    return {"answer": str(out.get("answer", ""))[:2000], "ids": ids, "verdict": verdict, "flags": flags,
            "citations": cites, "retrieved": list(dict.fromkeys(retrieved)), "usage": tracker,
            "latency": time.time() - t0, **extra}


class System:
    name = "base"
    uses_llm = True

    def __init__(self, corpus: Corpus, index: HybridIndex, llm: BaseLLM | None, cfg: Config):
        self.c, self.ix, self.llm, self.cfg = corpus, index, llm, cfg

    def retrieve(self, query: str, k: int | None = None):
        return [d for d, _ in self.ix.search(query, k or self.cfg.top_k)]

    def ask(self, prompt: str, task: str, tr: dict) -> dict:
        return self.llm.json([{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}], task, tr)

    def run(self, question: str) -> dict:  # pragma: no cover
        raise NotImplementedError


# ---------------------------------------------------------------------------
class GraphOracle(System):
    """No LLM. Parses the question with the benchmark's own templates and looks the answer up."""
    name = "graph_oracle"
    uses_llm = False

    def _mitigations(self, t):
        return sorted({m for _, m, _ in self.c.current_neighbors(t, "mitigated_by", 3)
                       if self.c.status_of(m) == "active"})

    def _resolve(self, t):
        for _ in range(5):
            if self.c.status_of(t) != "revoked":
                break
            nxt = [x for _, x, _ in self.c.current_neighbors(t, "revoked_by", 3)]
            if not nxt:
                break
            t = nxt[0]
        return t

    def run(self, question):
        t0 = time.time()
        ids = extract_ids(question)
        out = {"answer": "", "ids": [], "verdict": None, "flags": []}
        q = question
        if q.startswith(CLAIM_MARK):
            if len(ids) < 2:
                out["answer"] = "abstain: no identifiers to look up"
            else:
                a, b = ids[0], ids[1]
                if not self.c.entity_docs(a) or not self.c.entity_docs(b):
                    out["verdict"] = "NOT_ENOUGH_INFO"
                else:  # any direct link, either direction, from the latest authoritative snapshot
                    ok = any(self.c.is_latest(d) and self.c.docs[d].authority >= 2
                             for r, x, d in self.c.edges.get(a, []) if x == b)
                    out["verdict"] = "SUPPORTED" if ok else "UNSUPPORTED"
        elif "800-53" in q and "still current" in q and ids:
            out["ids"] = [x for _, x, _ in self.c.current_neighbors(ids[0], "incorporated_into")]
            if self.c.status_of(ids[0]) == "withdrawn":
                out["flags"] = ["WITHDRAWN"]
        elif "800-53" in q and ids and id_kind(ids[0]) == "technique":
            out["ids"] = sorted({x for _, x, d in self.c.current_neighbors(ids[0], "mapped_control")})
        elif "M-ID" in q and ids and id_kind(ids[0]) == "technique":
            t = self._resolve(ids[0])
            if t != ids[0]:
                out["flags"] = ["REVOKED"]
            out["ids"] = self._mitigations(t)
        elif "CWE weakness(es) are recorded" in q and ids:
            out["ids"] = sorted({w for _, w, _ in self.c.current_neighbors(ids[0], "has_weakness")})
        else:
            out["answer"] = "abstain: question needs language understanding"
        return finalize(out, [], {"calls": 0}, t0)


# ---------------------------------------------------------------------------
class NaiveRAG(System):
    name = "naive"

    def run(self, question):
        t0, tr = time.time(), {}
        docs = self.retrieve(question)
        out = self.ask(user_prompt(question, docs), "answer", tr)
        return finalize(out, [d.doc_id for d in docs], tr, t0)


class KGRAG(System):
    """Retrieval + one-hop expansion over the link graph (non-agentic graph baseline)."""
    name = "kg_rag"

    def run(self, question):
        t0, tr = time.time(), {}
        docs = self.retrieve(question)
        seeds = extract_ids(question) or [d.entity_id for d in docs[:3]]
        extra, seen = [], {d.doc_id for d in docs}
        for s in seeds[:4]:
            for d in self.c.entity_docs(s):
                if d.doc_id not in seen:
                    seen.add(d.doc_id)
                    extra.append(d)
            for _, tgt, did in self.c.neighbors(s)[:12]:
                for d in [self.c.docs[did]] + self.c.entity_docs(tgt)[:1]:
                    if d.doc_id not in seen:
                        seen.add(d.doc_id)
                        extra.append(d)
        ev = (docs + extra)[:18]
        out = self.ask(user_prompt(question, ev), "answer", tr)
        return finalize(out, [d.doc_id for d in ev], tr, t0)


class MultiHopRAG(System):
    name = "multihop"

    def run(self, question):
        t0, tr = time.time(), {}
        docs = self.retrieve(question)
        seen = {d.doc_id for d in docs}
        notes = []
        for hop in range(1, self.cfg.max_hops):
            p = (f"<question>{question}</question>\n\n<evidence>\n{fmt_evidence(docs)}\n</evidence>\n\n"
                 f"Hop {hop}. Reasoning so far: {' | '.join(notes) or 'none'}\n"
                 "Decide whether the evidence is sufficient to answer. If not, write the single next search "
                 "query that retrieves the missing information.\n"
                 'Return JSON: {"done": true|false, "note": "what you learned", "next_query": "..."}')
            st = self.ask(p, "hop", tr)
            notes.append(str(st.get("note", ""))[:200])
            if st.get("done") or not st.get("next_query"):
                break
            new = [d for d in self.retrieve(str(st["next_query"]), max(4, self.cfg.top_k // 2)) if d.doc_id not in seen]
            seen |= {d.doc_id for d in new}
            docs += new
        docs = docs[-16:]
        out = self.ask(user_prompt(question, docs, f"Reasoning chain: {' | '.join(notes)}\n\n"), "answer", tr)
        return finalize(out, list(seen), tr, t0)


class CorrectiveRAG(System):
    name = "crag"

    def grade(self, question, docs, tr):
        p = (f"<question>{question}</question>\n\n<evidence>\n{fmt_evidence(docs)}\n</evidence>\n\n"
             "Grade each evidence document for whether it contains information needed to answer the question. "
             'Return JSON: {"relevant": [doc ids], "overall": "CORRECT" | "AMBIGUOUS" | "INCORRECT"} where '
             "CORRECT means the relevant documents suffice, AMBIGUOUS means partially, INCORRECT means not at all.")
        g = self.ask(p, "grade", tr)
        rel = {str(x) for x in (g.get("relevant") or [])}
        return [d for d in docs if d.doc_id in rel], str(g.get("overall", "AMBIGUOUS")).upper()

    def run(self, question):
        t0, tr = time.time(), {}
        docs = self.retrieve(question)
        retrieved = [d.doc_id for d in docs]
        kept, overall = self.grade(question, docs, tr)
        if overall != "CORRECT":
            p = (f"<question>{question}</question>\n\nThe first retrieval was {overall}. Already useful: "
                 f"{', '.join(d.doc_id for d in kept) or 'nothing'}.\nDecompose the information need into up to 3 "
                 'focused search queries for missing facts. Return JSON: {"queries": ["...", "..."]}')
            rq = self.ask(p, "rewrite", tr)
            extra, seen = [], set(retrieved)
            for qq in (rq.get("queries") or [])[:3]:
                for d in self.retrieve(str(qq), max(4, self.cfg.top_k // 2)):
                    if d.doc_id not in seen:
                        seen.add(d.doc_id)
                        extra.append(d)
            retrieved += [d.doc_id for d in extra]
            if extra:
                k2, _ = self.grade(question, extra, tr)
                kept += k2
            if not kept:
                kept = docs[:4]
        out = self.ask(user_prompt(question, kept), "answer", tr)
        return finalize(out, retrieved, tr, t0, kept=[d.doc_id for d in kept])


# ---------------------------------------------------------------------------
# Evidence-aware agent
# ---------------------------------------------------------------------------
PATHS = {
    ("cve", "cwe"): ["has_weakness"],
    ("cve", "capec"): ["has_weakness", "related_attack_pattern"],
    ("cve", "technique"): ["has_weakness", "related_attack_pattern", "maps_to_attack"],
    ("cve", "mitigation"): ["has_weakness", "related_attack_pattern", "maps_to_attack", "mitigated_by"],
    ("cwe", "capec"): ["related_attack_pattern"],
    ("cwe", "technique"): ["related_attack_pattern", "maps_to_attack"],
    ("capec", "technique"): ["maps_to_attack"],
    ("capec", "cwe"): ["related_weakness"],
    ("technique", "mitigation"): ["mitigated_by"],
    ("technique", "control"): ["mapped_control"],
    ("mitigation", "technique"): ["mitigates"],
    ("control", "technique"): ["control_mapped_to"],
    ("control", "control"): ["incorporated_into"],
    ("cwe", "cve"): ["weakness_of"],
    ("technique", "capec"): ["attack_mapped_from_capec"],
    # NOTE: group -> technique ("uses") is deliberately absent: attribution is verified by entailment,
    # because the question shows behaviours, not technique IDs.
}
# Which source *type* owns each relation. Expressed as sources so the rule is auditable.
OWNER = {
    "has_weakness": {"NVD", "CISA KEV"}, "weakness_of": {"NVD", "CISA KEV"},
    "related_attack_pattern": {"MITRE CWE", "MITRE CAPEC"}, "related_weakness": {"MITRE CWE", "MITRE CAPEC"},
    "maps_to_attack": {"MITRE CAPEC"}, "attack_mapped_from_capec": {"MITRE CAPEC"},
    "mitigated_by": {"MITRE ATT&CK"}, "mitigates": {"MITRE ATT&CK"},
    "mapped_control": {"CTID Mapping"}, "control_mapped_to": {"CTID Mapping"},
    "incorporated_into": {"NIST SP 800-53"}, "revoked_by": {"MITRE ATT&CK"},
}

# Answer typing: the identifier kind a question asks for, read from its own wording (no source names).
ASKED_KIND = [
    ("control", r"\bwhich\s+(?:nist\s+sp\s+800-53\s+(?:rev\.?\s*\d+\s+)?)?(?:security\s+)?control"),
    ("cwe", r"\bwhich\s+cwe\b"),
    ("mitigation", r"\(m-ids?\)|\bwhich\s+(?:mitre\s+att&ck\s+)?mitigations\b"),
    ("capec", r"\bwhich\s+capec\b"),
    ("group", r"\(g-id\)|\bwhich\s+(?:mitre\s+att&ck\s+)?threat\s+group"),
    ("technique", r"\bwhich\s+(?:mitre\s+att&ck\s+)?(?:sub-)?techniques?\b|\bextract\s+every\s+mitre\s+att&ck"),
]
KIND_LABEL = {
    "control": "NIST SP 800-53 control identifiers (e.g. AC-2, SI-4(1))",
    "cwe": "CWE identifiers (e.g. CWE-79)",
    "mitigation": "MITRE ATT&CK mitigation identifiers (M####)",
    "capec": "CAPEC identifiers (e.g. CAPEC-66)",
    "group": "MITRE ATT&CK group identifiers (G####)",
    "technique": "MITRE ATT&CK technique identifiers (T#### or T####.###)",
}


def requested_kind(question: str) -> str | None:
    if question.startswith(CLAIM_MARK):
        return None
    q = question.lower()
    for kind, pat in ASKED_KIND:
        if re.search(pat, q):
            return kind
    return None


class EvidenceAgent(System):
    name = "evidence_agent"
    use_verify = True       # C: verify every identifier / claim before it is reported
    use_checks = True       # B: deterministic evidence checks (status, temporal, conflict) shown to the drafter
    use_temporal = True
    use_graph = True
    use_authority = True
    use_conflict = True     # v4: explicit conflict detection

    def _add(self, ledger: dict, docs):
        for d in docs:
            ledger.setdefault(d.doc_id, d)

    def _summary(self, ledger: dict) -> str:
        lines = []
        for d in list(ledger.values())[-30:]:
            links = "; ".join(f"{r}->{t}" for r, t in d.links[:12])
            meta = f" | {d.source} | {d.version or d.date} | {d.status}" if self.use_temporal else ""
            lines.append(f"[{d.doc_id}] {d.title[:80]}{meta} | links: {links or '-'}")
        return "\n".join(lines)

    # -- B: evidence checks --------------------------------------------------------------
    def _views(self, e: str, rel: str, visible: set) -> dict:
        """{source: targets} that each source's LATEST snapshot asserts for e -rel->, using only documents
        the system has gathered (`visible`). Older snapshots are handled by the temporal check."""
        v = {}
        for r, t, did in self.c.edges.get(e, []):
            if r == rel and did in visible and self.c.is_latest(did):
                v.setdefault(self.c.docs[did].source, set()).add(t)
        return v

    def _owners(self, views: dict, rel: str) -> list[str]:
        """Sources whose assertions are the reference for `rel`: the relation's owners (authority >= 2),
        else the most authoritative sources present. Without authority every source is an owner."""
        if not self.use_authority:
            return sorted(views)
        own = [s for s in views if s in OWNER.get(rel, set()) and AUTHORITY_OF(s) >= 2]
        if own:
            return sorted(own)
        auth = [s for s in views if AUTHORITY_OF(s) >= 2]
        if not auth:
            return []
        top = max(AUTHORITY_OF(s) for s in auth)
        return sorted(s for s in auth if AUTHORITY_OF(s) == top)

    def detect_conflicts(self, e: str, rel: str, visible: set, only: str | None = None) -> list[dict]:
        """Explicit conflict detection for one (entity, relation).
        lower_authority: a non-owner source asserts an identifier the owners do not assert.
        equal_authority: owners (e.g. NVD and CISA KEV) assert different sets.
        A conflict is detected independently of whether the disputed identifier is later accepted.
        `only` restricts detection to conflicts that involve that identifier (claim questions)."""
        views = self._views(e, rel, visible)
        if len(views) < 2:
            return []
        owners = self._owners(views, rel)
        if not owners:
            return []
        out = []
        ref = set().union(*(views[s] for s in owners))
        if len(owners) >= 2 and len({frozenset(views[s]) for s in owners}) > 1:
            diff = ref - set.intersection(*(views[s] for s in owners))
            if only is None or only in diff:
                out.append({"entity": e, "relation": rel, "kind": "equal_authority",
                            "sources": {s: sorted(views[s]) for s in owners}, "disputed": sorted(diff),
                            "resolution": "report all, attributed"})
        for s in sorted(set(views) - set(owners)):
            extra = views[s] - ref
            if extra and (only is None or only in extra):
                out.append({"entity": e, "relation": rel, "kind": "lower_authority", "source": s,
                            "authority": AUTHORITY_OF(s), "owners": owners, "disputed": sorted(extra),
                            "resolution": "rejected (owner/authority wins)"})
        return out

    def evidence_checks(self, question: str, q_ids: list[str], want: str | None, ledger: dict,
                        flags: set, notes: list, conflicts: list):
        """B: deterministic checks on the relation the question is about.
        - conflict: explicit detection over every gathered source (v4)
        - temporal: identifiers only an older snapshot of the same source asserts -> OUTDATED"""
        visible = set(ledger) | {d.doc_id for e in q_ids for d in self.c.entity_docs(e)}
        pairs = []   # (entity, relation, identifier the conflict must involve or None)
        if question.startswith(CLAIM_MARK) and len(q_ids) >= 2:
            s, o = q_ids[0], q_ids[-1]
            for a, b in ((s, o), (o, s)):
                chain = PATHS.get((id_kind(a), id_kind(b)))
                if chain and len(chain) == 1:
                    pairs.append((a, chain[0], b))
                    break
        elif want:
            for e in q_ids:
                chain = PATHS.get((id_kind(e), want))
                if chain and len(chain) == 1:
                    pairs.append((e, chain[0], None))
        for e, rel, only in pairs:
            if self.use_conflict:
                for cf in self.detect_conflicts(e, rel, visible, only):
                    conflicts.append(cf)
                    flags.add("CONFLICT")
                    if cf["kind"] == "equal_authority":
                        listing = "; ".join(f"{s} lists {', '.join(v)}" for s, v in cf["sources"].items())
                        notes.append(f"Equally authoritative current sources disagree about {e}: {listing}. Report "
                                     f"every identifier these sources assert, say which source asserts it, and "
                                     f"flag CONFLICT")
                    else:
                        notes.append(f"CONFLICT: {cf['source']} (a lower-authority source) asserts "
                                     f"{', '.join(cf['disputed'])} for {e}, which the authoritative source(s) "
                                     f"{', '.join(cf['owners'])} do not. Resolve by authority: do not report or "
                                     f"support these, and flag CONFLICT")
            if self.use_temporal and only is None:
                cur, old = {}, {}
                for r, t, did in self.c.edges.get(e, []):
                    d = self.c.docs[did]
                    if r == rel and (d.authority >= 2 or not self.use_authority):
                        (cur if self.c.is_latest(did) else old).setdefault(d.source, set()).add(t)
                for s, v in old.items():
                    only_old = sorted(v - cur.get(s, set()))
                    if only_old and s in cur:
                        notes.append(f"An older release of {s} also lists {', '.join(only_old[:10])} for {e}, which "
                                     f"its latest release no longer lists; do not report these as current")
                        flags.add("OUTDATED")

    # -- A: plan & gather -----------------------------------------------------------
    def gather(self, question: str, tr: dict) -> dict:
        ledger: dict[str, Doc] = {}
        for eid in extract_ids(question):
            self._add(ledger, self.c.entity_docs(eid))
        self._add(ledger, self.retrieve(question))
        tools = ('{"action": "search", "query": "..."} full-text search over the corpus\n'
                 '{"action": "lookup", "id": "CWE-79"} fetch every source document about an identifier\n')
        if self.use_graph:
            tools += ('{"action": "expand", "id": "CVE-2021-44228", "relation": "has_weakness"} follow typed '
                      'links (has_weakness, related_attack_pattern, maps_to_attack, mitigated_by, mapped_control, '
                      'revoked_by, incorporated_into, subtechnique_of, uses) and fetch the linked documents\n')
        tools += '{"action": "finish"} when the ledger contains enough evidence\n'
        for step in range(self.cfg.max_agent_steps):
            p = (f"<question>{question}</question>\n<step>{step}</step>\n\n<evidence>\n{self._summary(ledger)}\n"
                 f"</evidence>\n\nYou are collecting evidence to answer the question with verifiable support. "
                 f"Plan what is still missing, and whether any source is outdated or conflicting and needs a "
                 f"cross-check.\nTools:\n{tools}\n"
                 'Return JSON: {"thought": "...", "actions": [up to 4 tool calls]}')
            st = self.ask(p, "agent_step", tr)
            acts = st.get("actions") or []
            if isinstance(acts, dict):
                acts = [acts]
            if not acts or any(str(a.get("action")) == "finish" for a in acts if isinstance(a, dict)):
                break
            before = len(ledger)
            for a in acts[:4]:
                if not isinstance(a, dict):
                    continue
                kind = a.get("action")
                if kind == "search" and a.get("query"):
                    self._add(ledger, self.retrieve(str(a["query"]), max(4, self.cfg.top_k // 2)))
                elif kind == "lookup" and a.get("id"):
                    self._add(ledger, self.c.entity_docs(str(a["id"])))
                elif kind == "expand" and self.use_graph and a.get("id"):
                    for _, tgt, did in self.c.neighbors(str(a["id"]), a.get("relation") or None)[:25]:
                        self._add(ledger, [self.c.docs[did]] + self.c.entity_docs(tgt)[:2])
            if len(ledger) == before:
                break
        return ledger

    # -- C: verification ---------------------------------------------------------------
    def acceptable(self, d: Doc) -> bool:
        """A document may support a claim if it is (a) the latest snapshot of its source and
        (b) authoritative. Each condition is switched off by its ablation."""
        if self.use_temporal and not self.c.is_latest(d.doc_id):
            return False
        if self.use_authority and d.authority < 2:
            return False
        return True

    def edge_ok(self, s: str, rel: str, t: str, used: set) -> tuple[bool, list[str]]:
        docs = [self.c.docs[d] for r, x, d in self.c.edges.get(s, []) if r == rel and x == t]
        good = [d for d in docs if self.acceptable(d)]
        if not good:
            return False, []
        if self.use_authority:
            owners = [d for d in good if d.source in OWNER.get(rel, set())]
            if not owners and len({d.source for d in good}) < 2:
                return False, []
        used.update(d.doc_id for d in good)
        return True, [d.doc_id for d in good]

    def path_ok(self, s: str, t: str, used: set) -> bool:
        chain = PATHS.get((id_kind(s), id_kind(t)))
        if not chain:
            return False
        frontier, visited = deque([(s, 0)]), set()
        while frontier:
            node, i = frontier.popleft()
            if (node, i) in visited:
                continue
            visited.add((node, i))
            if i == len(chain):
                if node == t:
                    return True
                continue
            if self.use_temporal and id_kind(node) == "technique" and self.c.status_of(node) == "revoked":
                for _, nxt, _ in self.c.current_neighbors(node, "revoked_by"):
                    frontier.append((nxt, i))
            for r, nxt, _ in self.c.edges.get(node, []):
                if r == chain[i] and self.edge_ok(node, r, nxt, used)[0]:
                    frontier.append((nxt, i + 1))
        return False

    def entail(self, question, claims, ledger, tr) -> list[bool]:
        """Strict LLM entailment for claims without a typed path (behaviour->technique, report->CWE, ...)."""
        if not claims:
            return []
        docs = []
        for cl in claims:
            if cl.get("subject"):
                docs += self.c.entity_docs(cl["subject"])[:2]
            docs += self.c.entity_docs(cl["object"])[:2]
        docs += [d for d in ledger.values() if any(cl["object"] in d.text for cl in claims)][:4]
        docs = [d for d in {d.doc_id: d for d in docs}.values() if self.acceptable(d)] or docs
        docs = docs[:10]
        lines = "\n".join(f"{i+1}. {cl['text']}" for i, cl in enumerate(claims))
        p = (f"<question>{question}</question>\n\n<evidence>\n"
             f"{fmt_evidence(docs, self.use_temporal, self.use_authority)}\n"
             f"</evidence>\n\n<claims>\n{lines}\n</claims>\n\nFor each numbered claim decide whether the evidence "
             "documents directly support it. Be strict: a merely related item, a sibling sub-technique or a "
             'broader parent is not support. Return JSON: {"results": [{"n": 1, "supported": true|false, '
             '"reason": "..."}]}')
        res = self.ask(p, "entail", tr).get("results") or []
        flags = [bool(r.get("supported")) if isinstance(r, dict) else False for r in res]
        return (flags + [False] * len(claims))[: len(claims)]

    def why_rejected(self, focus_list, i) -> set[str]:
        """Explain a rejected identifier: only an older snapshot, or only a low-authority source, asserted it."""
        docs = [self.c.docs[d] for f in focus_list for _, x, d in self.c.edges.get(f, []) if x == i]
        flags = set()
        if self.use_temporal and docs and any(d.authority >= 2 for d in docs) \
                and all(not self.c.is_latest(d.doc_id) for d in docs if d.authority >= 2):
            flags.add("OUTDATED")
        if self.use_conflict and self.use_authority and any(d.authority < 2 for d in docs):
            flags.add("CONFLICT")
        return flags

    # -- main ----------------------------------------------------------------------------
    def run(self, question):
        t0, tr = time.time(), {}
        ledger = self.gather(question, tr)
        q_ids = extract_ids(question)
        is_claim = question.startswith(CLAIM_MARK)
        flags, notes, resolved, conflicts = set(), [], {}, []
        want = requested_kind(question)
        if self.use_checks:
            if self.use_temporal:
                for e in q_ids:
                    st = self.c.status_of(e)
                    if st in ("revoked", "withdrawn", "deprecated"):
                        rel = "revoked_by" if st == "revoked" else "incorporated_into"
                        rep = [t for _, t, _ in self.c.current_neighbors(e, rel)]
                        flags.add({"revoked": "REVOKED", "withdrawn": "WITHDRAWN", "deprecated": "DEPRECATED"}[st])
                        if rep:
                            resolved[e] = rep
                            for r in rep:
                                self._add(ledger, self.c.entity_docs(r))
                            notes.append(f"{e} is {st} in the latest release; current replacement: {', '.join(rep)}")
                    srcs = {}
                    for d in self.c.entity_docs(e):
                        srcs.setdefault(d.source, set()).add(d.snapshot)
                    if any(len(v) > 1 for v in srcs.values()):
                        notes.append(f"several releases of the same source describe {e}; prefer the latest one")
            self.evidence_checks(question, q_ids, want, ledger, flags, notes, conflicts)
        reps = {x for v in resolved.values() for x in v}
        ev_docs = sorted(ledger.values(), key=lambda d: (d.entity_id not in q_ids and d.entity_id not in reps,
                                                         not self.c.is_latest(d.doc_id)))[:16]
        extra = ("Also return \"claims\": a list of {\"subject\": id or null, \"relation\": short text, \"object\": id} "
                 "for every association your answer asserts (for a claim-verification question, the single claim "
                 "being verified, with names resolved to identifiers), and \"focus_entity\" (the identifier the "
                 "question is about, or null).\n")
        if want:
            extra = (f"Requested answer type: {KIND_LABEL[want]}. Put only identifiers of this type in \"ids\".\n"
                     + extra)
        if notes:
            extra = "Status notes: " + "; ".join(notes) + "\n" + extra
        draft = self.ask(user_prompt(question, ev_docs, extra, self.use_temporal, self.use_authority), "draft", tr)
        res = finalize(draft, list(ledger), tr, t0)
        flags |= set(res["flags"])
        res["conflicts"] = conflicts
        res["flags_llm"] = list(res["flags"])          # flags the LLM itself raised (for the conflict trace)
        if not self.use_verify:
            res["flags"] = sorted(flags)
            return res

        used: set[str] = set()
        focus = norm_id(str(draft.get("focus_entity") or (q_ids[0] if q_ids else "")))
        focus = focus if focus and self.c.entity_docs(focus) else ""
        if not focus:   # the drafter's focus is unknown: fall back to the first known question entity
            focus = next((e for e in q_ids if self.c.entity_docs(e)), "")
        focus_list = resolved.get(focus, [focus]) if focus else []

        if is_claim:
            res["draft_verdict"] = res["verdict"]
            res.update(self._verify_claim(question, draft, q_ids, ledger, res, tr, used), flags=sorted(flags))
        elif q_ids and not any(self.c.entity_docs(e) for e in q_ids):
            # v4: the question is about identifiers no source describes -> abstain
            flags.add("INSUFFICIENT_EVIDENCE")
            res.update(ids=[], draft_ids=res["ids"],
                       rejected=[(i, "question entity unknown to every source") for i in res["ids"]],
                       flags=sorted(flags), support_ratio=0.0 if res["ids"] else None)
        else:
            kept, rejected, textual = [], [], []
            n_draft = len(res["ids"])
            if want:  # answer typing: identifiers of the wrong kind can never answer the question
                wrong = [i for i in res["ids"] if id_kind(i) != want]
                if wrong and len(wrong) == len(res["ids"]):
                    fix = (f"Your previous draft answered with {', '.join(wrong[:6])}, which are not "
                           f"{KIND_LABEL[want]}. The question asks for {KIND_LABEL[want]}. Answer again using only "
                           f"identifiers of that type that appear in the evidence.\n")
                    redo = finalize(self.ask(user_prompt(question, ev_docs, fix + extra, self.use_temporal,
                                                         self.use_authority), "retype", tr), list(ledger), tr, t0)
                    flags |= set(redo["flags"])
                    res["answer"] = redo["answer"]
                    res["draft_ids_wrong_type"] = wrong
                    res["ids"] = redo["ids"]
                    n_draft = len(res["ids"])
                rejected += [(i, "wrong identifier type") for i in res["ids"] if id_kind(i) != want]
                res["ids"] = [i for i in res["ids"] if id_kind(i) == want]
            for i in res["ids"]:
                if i in q_ids:
                    rejected.append((i, "echo of question entity"))
                    continue
                st = self.c.status_of(i) if self.use_temporal else "active"
                if st in ("revoked", "withdrawn"):
                    rep = [t for _, t, _ in self.c.current_neighbors(i, "revoked_by" if st == "revoked" else "incorporated_into")]
                    flags.add("REVOKED" if st == "revoked" else "WITHDRAWN")
                    rejected.append((i, f"{st} -> {rep}"))
                    if not rep:
                        continue
                    i = rep[0]
                if not self.c.entity_docs(i):
                    rejected.append((i, "unknown identifier"))
                    continue
                typed = self.use_graph and any(PATHS.get((id_kind(f), id_kind(i))) for f in focus_list)
                if any(f == i for f in focus_list) or (typed and any(self.path_ok(f, i, used) for f in focus_list)):
                    kept.append(i)
                elif typed:
                    rejected.append((i, "no acceptable evidence path"))
                    flags |= self.why_rejected(focus_list, i)
                else:
                    textual.append(i)
            if textual:
                claims = [{"object": i, "text": f"{i} ({self._name(i)}) is a correct answer to the question."}
                          for i in textual]
                for i, ok in zip(textual, self.entail(question, claims, ledger, tr)):
                    (kept.append(i) if ok else rejected.append((i, "not entailed")))
                if not kept and not q_ids:
                    # identification questions without identifiers (text track): keep the top guess, flagged
                    kept.append(textual[0])
                    flags.add("INSUFFICIENT_EVIDENCE")
            kept = list(dict.fromkeys(kept))
            if not kept:
                flags.add("INSUFFICIENT_EVIDENCE")
            res.update(ids=kept, draft_ids=res["ids"], rejected=rejected, flags=sorted(flags),
                       support_ratio=(len(kept) / n_draft) if n_draft else None)
        res["citations"] = sorted(used) or res["citations"]
        res["retrieved"] = list(dict.fromkeys(res["retrieved"] + sorted(used)))
        res["usage"], res["latency"] = tr, time.time() - t0
        return res

    def _name(self, i):
        for d in self.c.entity_docs(i):
            if d.meta.get("name"):
                return d.meta["name"]
        return ""

    def _verify_claim(self, question, draft, q_ids, ledger, res, tr, used) -> dict:
        cl = (draft.get("claims") or [{}])[0] if isinstance(draft.get("claims"), list) and draft.get("claims") else {}
        if not isinstance(cl, dict):
            cl = {}
        s = norm_id(str(cl.get("subject") or "")) if cl.get("subject") else ""
        o = norm_id(str(cl.get("object") or "")) if cl.get("object") else ""
        if not o and q_ids:
            o = q_ids[-1]
        if not s and len(q_ids) >= 2:
            s = q_ids[0]
        # v3: identifiers written in the question are authoritative; the LLM parse only fills gaps
        # (e.g. a technique given by name). A parse that disagrees with them, or a degenerate
        # subject == object, is replaced by the question's own identifiers.
        if len(q_ids) >= 2 and {s, o} != {q_ids[0], q_ids[-1]}:
            s, o = q_ids[0], q_ids[-1]
        if s and s == o:
            s = ""
        # an identifier written in the claim that no source knows -> NOT_ENOUGH_INFO
        if any(not self.c.entity_docs(x) for x in q_ids):
            return {"verdict": "NOT_ENOUGH_INFO", "verified_ids": [], "support_ratio": 0.0}
        if (s and not self.c.entity_docs(s)) or (o and not self.c.entity_docs(o)):
            return {"verdict": "NOT_ENOUGH_INFO" if q_ids else "UNSUPPORTED", "verified_ids": [], "support_ratio": 0.0}
        if s and o and self.use_graph and (PATHS.get((id_kind(s), id_kind(o))) or PATHS.get((id_kind(o), id_kind(s)))):
            ok = self.path_ok(s, o, used) or self.path_ok(o, s, used)
        elif o:
            text = question.split('"', 1)[1].rsplit('"', 1)[0] if question.count('"') >= 2 else question
            ok = self.entail(question, [{"subject": s or None, "object": o, "text": text}], ledger, tr)[0]
        else:
            return {"verdict": res["verdict"], "verified_ids": []}
        return {"verdict": "SUPPORTED" if ok else "UNSUPPORTED", "verified_ids": [o] if ok else [],
                "resolved_claim": [s, o], "support_ratio": 1.0}


class GraphVerifier(EvidenceAgent):
    """Non-agentic baseline: fixed retrieval + deterministic one-hop graph expansion of the question's
    entities instead of the LLM-controlled tool loop. Same checks, draft prompt and verification."""
    name = "graph_verifier"

    def gather(self, question: str, tr: dict) -> dict:
        ledger: dict[str, Doc] = {}
        q_ids = extract_ids(question)
        for eid in q_ids:
            self._add(ledger, self.c.entity_docs(eid))
        docs = self.retrieve(question)
        self._add(ledger, docs)
        seeds = q_ids or [d.entity_id for d in docs[:3]]
        for s in seeds[:4]:
            for _, tgt, did in self.c.neighbors(s)[:40]:
                self._add(ledger, [self.c.docs[did]] + self.c.entity_docs(tgt)[:2])
        return ledger


class ReActAgent(EvidenceAgent):
    """Plain ReAct: the same tool loop, then one answer call. No evidence checks, no verification."""
    name = "react_agent"
    use_verify = False
    use_checks = False


class AgentNoVerify(EvidenceAgent):
    name = "agent_no_verify"
    use_verify = False


class AgentNoTemporal(EvidenceAgent):
    name = "agent_no_temporal"
    use_temporal = False


class AgentNoGraph(EvidenceAgent):
    name = "agent_no_graph"
    use_graph = False


class AgentNoAuthority(EvidenceAgent):
    name = "agent_no_authority"
    use_authority = False


class AgentNoConflict(EvidenceAgent):
    name = "agent_no_conflict"
    use_conflict = False


SYSTEMS = {cls.name: cls for cls in (GraphOracle, NaiveRAG, KGRAG, MultiHopRAG, CorrectiveRAG, ReActAgent,
                                     GraphVerifier, EvidenceAgent, AgentNoVerify, AgentNoTemporal, AgentNoGraph,
                                     AgentNoAuthority, AgentNoConflict)}
