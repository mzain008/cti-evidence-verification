"""Final independent benchmark (CTI-EvidenceQA-final).

Built ONCE, after the agent code (v4) was frozen, and never used for prompt tuning or controller changes.
Independence from development:
  * no focus entity (the technique / CVE / CAPEC / control a question is about) that appears in ANY
    development question (questions_FROZEN.jsonl: main, held-out and the unused pool) or in the
    development stress set is reused;
  * injected notes use new source names, new wording and a new random seed;
  * every candidate list is sorted before sampling, so the build is deterministic.

Five categories requested in the review, plus conflict negatives:
  C1 verification     technique-mitigation / technique-control claims and lists
  C2 relationships    CVE-CWE, CAPEC-ATT&CK claims; CVE->CWE, CAPEC->technique, CVE->CAPEC (2-hop) lists
  C3 conflict         real NVD vs CISA KEV disagreements + injected low-authority conflicts (lists and claims)
  C4 outdated         revoked techniques, withdrawn controls, Rev.4 vs Rev.5 mappings, ATT&CK version drift
  C5 insufficient     claims and questions about identifiers no source describes, and real entities for
                      which no source records the requested relation (correct behaviour: abstain)
  C6 benign_note      low-authority notes that AGREE with the authoritative sources (conflict negatives,
                      measure false conflict alarms)
Every question carries meta.category, meta.has_conflict and meta.answerable.
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

from .benchmark import (CLAIM_INSTR, BenchmarkBuilder, _name, _q, active, controls_of, mitigations_of,
                        old_mitigations_of, resolve_technique)
from .corpus import Corpus, Doc, extract_ids, id_kind

FINAL_SEED = 2027
NOTE_SOURCES = ["Threat Exchange Post", "Partner Advisory", "OSINT Digest", "Analyst Notebook"]  # authority 1
CATEGORY_LABEL = {"verification": "Technique and mitigation verification",
                  "relationships": "CVE/CWE/ATT&CK relationships",
                  "conflict": "Conflicting evidence",
                  "outdated": "Outdated or revised evidence",
                  "insufficient": "Insufficient evidence and abstention",
                  "benign_note": "Conflict negatives (agreeing low-authority note)"}

PLAN = {  # category -> [(subtype, n)]
    "verification": [("claim_mitigated_by", 20), ("claim_mapped_control", 16), ("attack_mitigation", 7),
                     ("nist_control", 7)],
    "relationships": [("claim_has_weakness", 16), ("claim_maps_to_attack", 16), ("cve_cwe", 6),
                      ("capec_technique", 6), ("cve_capec", 6)],
    "conflict": [("nvd_kev", 14), ("injected_mitigation", 14), ("injected_control", 8), ("injected_claim", 14)],
    "outdated": [("revoked", 14), ("withdrawn", 12), ("rev4_rev5", 12), ("version_drift", 12)],
    "insufficient": [("claim_nei", 14), ("unknown_technique", 9), ("unknown_cve", 9),
                     ("no_mitigation", 9), ("no_control_mapping", 9)],
    "benign_note": [("benign_mitigation", 15), ("benign_claim", 10)],
}

NOTE_TEMPLATES_WRONG = [
    "Field report on {t} ({tn}): our blue team found {a} ({an}) and {b} ({bn}) to be the controls that actually stopped it.",
    "{tn} / {t} - quick reference. Recommended countermeasures: {a} {an}; {b} {bn}.",
    "After three engagements involving {t}, we now advise {an} [{a}] first and {bn} [{b}] second.",
    "Detection and response digest: for {tn} ({t}) prioritise {a} and {b}; vendor guidance agrees.",
]
NOTE_TEMPLATES_CTRL = [
    "Compliance crosswalk (internal): {t} {tn} is covered by NIST SP 800-53 controls {a} and {b}.",
    "Audit worksheet: map {tn} ({t}) to {a} and {b} in the Rev. 5 catalogue.",
]
NOTE_TEMPLATES_CLAIM = [
    "Practitioner note: {a} ({an}) is an effective mitigation for {t} ({tn}) in our environment.",
    "Lessons from the field - {tn} [{t}] is mitigated by {an} ({a}).",
]
NOTE_TEMPLATES_BENIGN = [
    "Hardening checklist for {t} ({tn}): apply {a} ({an}) and {b} ({bn}).",
    "Team wiki: against {tn} [{t}] we rely on {an} ({a}) and {bn} ({b}).",
]


def focus_of(q: dict) -> str | None:
    """The entity a question is about (used to keep the final set disjoint from development)."""
    m = q.get("meta", {})
    if m.get("subject"):
        return m["subject"]
    ids = [i for i in extract_ids(q["question"]) if id_kind(i) not in ("mitigation", "cwe")]
    return ids[0] if ids else None


def dev_focus_entities(*question_files: Path) -> set[str]:
    out = set()
    for p in question_files:
        p = Path(p)
        if not p.exists():
            continue
        for line in p.read_text().splitlines():
            if line.strip():
                f = focus_of(json.loads(line))
                if f:
                    out.add(f)
    return out


class FinalBuilder(BenchmarkBuilder):
    def __init__(self, corpus: Corpus, cfg, exclude: set[str]):
        super().__init__(corpus, [], cfg)
        self.rng = random.Random(FINAL_SEED)
        self.techs = sorted(self.techs)
        self.excl = set(exclude)
        self.used = set()            # focus entities used inside the final set
        self.notes: list[Doc] = []
        self.short = {}              # subtype -> how many could not be built

    # -- helpers --------------------------------------------------------------------
    def free(self, e: str) -> bool:
        return e not in self.excl and e not in self.used

    def pick(self, pool, n):
        pool = sorted(set(x for x in pool if self.free(x if isinstance(x, str) else x[0])),
                      key=lambda x: x if isinstance(x, str) else x[0])
        self.rng.shuffle(pool)
        return pool[:n]

    def take(self, e):
        self.used.add(e)

    def wrong_mitigations(self, t):
        ms = set(mitigations_of(self.c, t)) | set(old_mitigations_of(self.c, t))
        return sorted({x for s in self.siblings(t) + self.same_tactic(t)[:40] for x in mitigations_of(self.c, s)} - ms)

    def add_note(self, t, links, text, newer):
        i = len(self.notes)
        src = NOTE_SOURCES[i % len(NOTE_SOURCES)]
        date = f"2026-09-{10 + i % 18:02d}" if newer else f"201{6 + i % 4}-0{1 + i % 9}-1{i % 10}"
        nid = f"fnote:{i:04d}"
        self.notes.append(Doc(nid, src, t, "note", f"{src}: {t}", text, date, "", "active", links,
                              {"note_for": t}))
        return nid

    def Q(self, cat, sub, question, gold, docs, has_conflict=False, answerable=True, **kw):
        qid = f"final-{cat[:4]}-{sub}-{sum(1 for x in self.out if x['subtype'] == sub):03d}"
        q = _q(qid, kw.pop("qtype", "final"), question, gold, docs, subtype=sub, category=cat,
               has_conflict=has_conflict, answerable=answerable, **kw)
        q["track"] = "evidence"
        self.out.append(q)
        return q

    @staticmethod
    def claim_q(text):
        return f"Verify the following claim against authoritative security sources: \"{text}\" {CLAIM_INSTR}"

    def mit_q(self, t):
        nm = _name(self.c, t)
        return f"Which MITRE ATT&CK mitigations (M-IDs) address technique {t}" + (f" ({nm})?" if nm else "?")

    def ctl_q(self, t):
        nm = _name(self.c, t)
        return (f"Which NIST SP 800-53 Rev. 5 controls are mapped as mitigations for ATT&CK technique {t}"
                + (f" ({nm})?" if nm else "?") + " List the control IDs.")

    def cwe_q(self, cve):
        return f"Which CWE weakness(es) are recorded for {cve}? Note whether the authoritative sources agree."

    def cwes(self, cve):
        """{source: cwes} from the latest snapshot of each authoritative source."""
        v = {}
        for _, w, did in self.c.current_neighbors(cve, "has_weakness"):
            v.setdefault(self.c.docs[did].source, set()).add(w)
        return v

    # -- build --------------------------------------------------------------------------
    def build(self) -> list[dict]:
        self.out: list[dict] = []
        c = self.c
        mit_pool = [t for t in self.techs if 1 <= len(mitigations_of(c, t)) <= 8]
        ctl_pool = [t for t in self.techs if 1 <= len(controls_of(c, t)) <= 15]
        kev = sorted((d for d in c.docs.values() if d.doc_id.startswith("kev:")), key=lambda d: d.entity_id)
        agree_cves, disagree_cves = [], []
        for d in kev:
            v = self.cwes(d.entity_id)
            if not v:
                continue
            (disagree_cves if len({frozenset(x) for x in v.values()}) > 1 else agree_cves).append(d.entity_id)
        capecs = sorted(d.entity_id for d in c.docs.values() if d.doc_id.startswith("capec:")
                        and d.status == "active" and any(r == "maps_to_attack" for r, _ in d.links))
        P = dict((s, n) for cat in PLAN.values() for s, n in cat)

        def short(sub, got):
            if got < P[sub]:
                self.short[sub] = P[sub] - got

        # ---------------- C4 outdated (built first: its pools are the rarest) ----------------
        cat = "outdated"
        rv = sorted({d.entity_id for d in c.docs.values() if d.entity_type == "technique"
                     and c.status_of(d.entity_id) == "revoked"})
        cands = []
        for t in rv:
            cur, _ = resolve_technique(c, t)
            ms = mitigations_of(c, cur)
            if cur != t and ms and len(ms) <= 8 and self.free(cur):
                cands.append(t)
        got = 0
        for t in self.pick(cands, P["revoked"]):
            cur, _ = resolve_technique(c, t)
            if not self.free(cur):
                continue
            self.take(t)
            self.take(cur)
            ms = mitigations_of(c, cur)
            nm = _name(c, t)
            q = (f"Which MITRE ATT&CK mitigations (M-IDs) should be applied against technique {t}"
                 + (f" ({nm})?" if nm else "?"))
            self.Q(cat, "revoked", q, ms, [f"attack:{t}", f"attack:{cur}"] + [f"attack:{m}" for m in ms],
                   requires_flag="REVOKED", replacement_ids=[cur],
                   stale_ids=[t] + sorted(set(old_mitigations_of(c, t)) - set(ms)))
            got += 1
        short("revoked", got)

        wd = sorted(d.entity_id for d in c.docs.values() if d.doc_id.startswith("nist:") and d.status == "withdrawn"
                    and any(r == "incorporated_into" for r, _ in d.links))
        got = 0
        for x in self.pick(wd, P["withdrawn"]):
            self.take(x)
            d = c.docs[f"nist:{x}"]
            tg = sorted({t for r, t in d.links if r == "incorporated_into"})
            q = (f"A legacy compliance baseline still lists NIST SP 800-53 control {x}. Is this control current in "
                 f"Rev. 5? If it is not, which control(s) should be assessed instead?")
            self.Q(cat, "withdrawn", q, tg, [d.doc_id] + [f"nist:{y}" for y in tg], requires_flag="WITHDRAWN",
                   replacement_ids=tg, stale_ids=[x])
            got += 1
        short("withdrawn", got)

        r45 = []
        for t in self.techs:
            c5, c4 = set(controls_of(c, t)), set(controls_of(c, t, "4"))
            if c5 and c4 and (c4 - c5) and len(c5) <= 15:
                r45.append(t)
        got = 0
        for t in self.pick(r45, P["rev4_rev5"]):
            self.take(t)
            c5, c4 = controls_of(c, t), controls_of(c, t, "4")
            self.Q(cat, "rev4_rev5", self.ctl_q(t), c5, [f"ctid5:{t}"], requires_flag="OUTDATED",
                   stale_ids=sorted(set(c4) - set(c5)))
            got += 1
        short("rev4_rev5", got)

        drift = []
        for t in self.techs:
            cur, old = set(mitigations_of(c, t)), set(old_mitigations_of(c, t))
            if cur and old and len(cur) <= 8 and cur != old:
                drift.append(t)
        n_drift = P["version_drift"] + sum(self.short.get(k, 0) for k in ("revoked", "withdrawn", "rev4_rev5"))
        got = 0
        for t in self.pick(drift, n_drift):
            self.take(t)
            ms, old = mitigations_of(c, t), old_mitigations_of(c, t)
            nm = _name(c, t)
            q = (f"Which MITRE ATT&CK mitigations (M-IDs) currently address technique {t}"
                 + (f" ({nm})?" if nm else "?"))
            self.Q(cat, "version_drift", q, ms, [f"attack:{t}"] + [f"attack:{m}" for m in ms],
                   stale_ids=sorted(set(old) - set(ms)), old_set=old,
                   requires_flag="OUTDATED" if set(old) - set(ms) else None)
            got += 1
        if n_drift > P["version_drift"]:
            self.short["revoked/withdrawn/rev4_rev5 (filled with version_drift)"] = n_drift - P["version_drift"]
        short("version_drift", got - (n_drift - P["version_drift"]))

        # ---------------- C1 verification ----------------
        cat = "verification"
        ts = self.pick(mit_pool, P["claim_mitigated_by"] * 2)
        k = 0
        for t in ts:
            if k >= P["claim_mitigated_by"]:
                break
            ms = mitigations_of(c, t)
            if k % 2 == 0:
                lab, m = "SUPPORTED", self.rng.choice(ms)
            else:
                wr = self.wrong_mitigations(t)
                if not wr:
                    continue
                lab, m = "UNSUPPORTED", self.rng.choice(wr)
            self.take(t)
            txt = f"MITRE ATT&CK mitigation {m} ({_name(c, m)}) mitigates technique {t} ({_name(c, t)})."
            self.Q(cat, "claim_mitigated_by", self.claim_q(txt), [m] if lab == "SUPPORTED" else [],
                   [f"attack:{t}"], qtype="claim", gold_label=lab, subject=t, obj=m, relation="mitigated_by")
            k += 1
        short("claim_mitigated_by", k)

        k = 0
        for t in self.pick(ctl_pool, P["claim_mapped_control"] * 2):
            if k >= P["claim_mapped_control"]:
                break
            cs = controls_of(c, t)
            if k % 2 == 0:
                lab, x = "SUPPORTED", self.rng.choice(cs)
            else:
                fams = {y.split("-")[0] for y in cs}
                c4 = set(controls_of(c, t, "4"))
                pool = sorted(d.entity_id for d in c.docs.values() if d.doc_id.startswith("nist:")
                              and d.status == "active" and d.entity_id.split("-")[0] in fams
                              and d.entity_id not in cs and d.entity_id not in c4 and "(" not in d.entity_id)
                if not pool:
                    continue
                lab, x = "UNSUPPORTED", self.rng.choice(pool)
            self.take(t)
            txt = (f"NIST SP 800-53 Rev. 5 control {x} ({_name(c, x)}) is mapped as a mitigation for ATT&CK "
                   f"technique {t} ({_name(c, t)}).")
            self.Q(cat, "claim_mapped_control", self.claim_q(txt), [x] if lab == "SUPPORTED" else [],
                   [f"ctid5:{t}"], qtype="claim", gold_label=lab, subject=t, obj=x, relation="mapped_control")
            k += 1
        short("claim_mapped_control", k)

        got = 0
        for t in self.pick(mit_pool, P["attack_mitigation"]):
            self.take(t)
            ms = mitigations_of(c, t)
            self.Q(cat, "attack_mitigation", self.mit_q(t), ms, [f"attack:{t}"] + [f"attack:{m}" for m in ms],
                   stale_ids=sorted(set(old_mitigations_of(c, t)) - set(ms)))
            got += 1
        short("attack_mitigation", got)
        got = 0
        for t in self.pick(ctl_pool, P["nist_control"]):
            self.take(t)
            cs = controls_of(c, t)
            self.Q(cat, "nist_control", self.ctl_q(t), cs, [f"ctid5:{t}"],
                   stale_ids=sorted(set(controls_of(c, t, "4")) - set(cs)))
            got += 1
        short("nist_control", got)

        # ---------------- C2 relationships ----------------
        cat = "relationships"
        k = 0
        for cve in self.pick(agree_cves, P["claim_has_weakness"] * 3):
            if k >= P["claim_has_weakness"]:
                break
            have = set().union(*self.cwes(cve).values())
            vendor = c.docs[f"kev:{cve}"].meta.get("vendor")
            if k % 2 == 0:
                lab, w = "SUPPORTED", sorted(have)[0]
            else:
                pool = sorted({x for d in kev if d.meta.get("vendor") == vendor for x in d.meta.get("cwes", [])}
                              - {w2 for _, w2, _ in c.neighbors(cve, "has_weakness")})
                if not pool:
                    continue
                lab, w = "UNSUPPORTED", self.rng.choice(pool)
            self.take(cve)
            txt = f"{cve} is caused by weakness {w}" + (f" ({_name(c, w)})." if _name(c, w) else ".")
            self.Q(cat, "claim_has_weakness", self.claim_q(txt), [w] if lab == "SUPPORTED" else [],
                   [f"kev:{cve}"], qtype="claim", gold_label=lab, subject=cve, obj=w, relation="has_weakness")
            k += 1
        short("claim_has_weakness", k)

        k = 0
        for cap in self.pick(capecs, P["claim_maps_to_attack"] * 3):
            if k >= P["claim_maps_to_attack"]:
                break
            tl = sorted(t for r, t in c.docs[f"capec:{cap}"].links if r == "maps_to_attack" and active(c, t))
            if not tl:
                continue
            if k % 2 == 0:
                lab, t = "SUPPORTED", self.rng.choice(tl)
            else:
                pool = sorted({x for t0 in tl for x in self.siblings(t0) + self.same_tactic(t0)[:30]} - set(tl)
                              - {x for _, x, _ in c.neighbors(cap, "maps_to_attack")})
                if not pool:
                    continue
                lab, t = "UNSUPPORTED", self.rng.choice(pool)
            self.take(cap)
            txt = f"CAPEC attack pattern {cap} ({_name(c, cap)}) maps to ATT&CK technique {t} ({_name(c, t)})."
            self.Q(cat, "claim_maps_to_attack", self.claim_q(txt), [t] if lab == "SUPPORTED" else [],
                   [f"capec:{cap}"], qtype="claim", gold_label=lab, subject=cap, obj=t, relation="maps_to_attack")
            k += 1
        short("claim_maps_to_attack", k)

        got = 0
        for cve in self.pick(agree_cves, P["cve_cwe"]):
            self.take(cve)
            gold = sorted(set().union(*self.cwes(cve).values()))
            self.Q(cat, "cve_cwe", self.cwe_q(cve), gold, [f"kev:{cve}", f"nvd:{cve}"])
            got += 1
        short("cve_cwe", got)

        got = 0
        for cap in self.pick(capecs, P["capec_technique"] * 2):
            if got >= P["capec_technique"]:
                break
            tl = sorted({t for _, t, _ in c.current_neighbors(cap, "maps_to_attack") if active(c, t)})
            if not 1 <= len(tl) <= 6:
                continue
            self.take(cap)
            q = f"Which MITRE ATT&CK techniques does CAPEC attack pattern {cap} ({_name(c, cap)}) map to?"
            self.Q(cat, "capec_technique", q, tl, [f"capec:{cap}"])
            got += 1
        short("capec_technique", got)

        got = 0
        for cve in self.pick(agree_cves, P["cve_capec"] * 4):
            if got >= P["cve_capec"]:
                break
            caps, docs = set(), {f"kev:{cve}"}
            for _, w, d1 in c.current_neighbors(cve, "has_weakness"):
                for _, cap, d2 in c.current_neighbors(w, "related_attack_pattern"):
                    if c.status_of(cap) == "active":
                        caps.add(cap)
                        docs |= {d1, d2}
            if not 1 <= len(caps) <= 6:
                continue
            self.take(cve)
            q = (f"Which CAPEC attack patterns are related to the weakness(es) recorded for {cve}? "
                 f"Return the CAPEC IDs.")
            self.Q(cat, "cve_capec", q, sorted(caps), sorted(docs), hops=2)
            got += 1
        short("cve_capec", got)

        # ---------------- C3 conflict ----------------
        cat = "conflict"
        got = 0
        for cve in self.pick(disagree_cves, P["nvd_kev"]):
            self.take(cve)
            v = self.cwes(cve)
            gold = sorted(set().union(*v.values()))
            self.Q(cat, "nvd_kev", self.cwe_q(cve), gold, [f"kev:{cve}", f"nvd:{cve}"], has_conflict=True,
                   requires_flag="CONFLICT", conflict_kind="equal_authority",
                   sources={s: sorted(x) for s, x in v.items()})
            got += 1
        n_inj_mit = P["injected_mitigation"] + max(0, P["nvd_kev"] - got)   # fill a shortage of real conflicts
        if got < P["nvd_kev"]:
            self.short["nvd_kev (filled with injected_mitigation)"] = P["nvd_kev"] - got

        got = 0
        for t in self.pick(mit_pool, n_inj_mit * 2):
            if got >= n_inj_mit:
                break
            wr = self.wrong_mitigations(t)
            if len(wr) < 2:
                continue
            a, b = self.rng.sample(wr, 2)
            self.take(t)
            txt = NOTE_TEMPLATES_WRONG[got % len(NOTE_TEMPLATES_WRONG)].format(
                t=t, tn=_name(c, t), a=a, an=_name(c, a), b=b, bn=_name(c, b))
            nid = self.add_note(t, [("mitigated_by", a), ("mitigated_by", b)], txt, newer=bool(got % 2))
            ms = mitigations_of(c, t)
            self.Q(cat, "injected_mitigation", self.mit_q(t), ms, [f"attack:{t}"] + [f"attack:{m}" for m in ms],
                   has_conflict=True, requires_flag="CONFLICT", conflict_kind="lower_authority",
                   injected_ids=[a, b], note_doc=nid, note_newer=bool(got % 2),
                   stale_ids=sorted(set(old_mitigations_of(c, t)) - set(ms)))
            got += 1
        short("injected_mitigation", got - max(0, n_inj_mit - P["injected_mitigation"]))

        got = 0
        for t in self.pick(ctl_pool, P["injected_control"] * 2):
            if got >= P["injected_control"]:
                break
            cs = controls_of(c, t)
            fams = {y.split("-")[0] for y in cs}
            c4 = set(controls_of(c, t, "4"))
            pool = sorted(d.entity_id for d in c.docs.values() if d.doc_id.startswith("nist:")
                          and d.status == "active" and d.entity_id.split("-")[0] in fams
                          and d.entity_id not in cs and d.entity_id not in c4 and "(" not in d.entity_id)
            if len(pool) < 2:
                continue
            a, b = self.rng.sample(pool, 2)
            self.take(t)
            txt = NOTE_TEMPLATES_CTRL[got % len(NOTE_TEMPLATES_CTRL)].format(t=t, tn=_name(c, t), a=a, b=b)
            nid = self.add_note(t, [("mapped_control", a), ("mapped_control", b)], txt, newer=bool(got % 2))
            self.Q(cat, "injected_control", self.ctl_q(t), cs, [f"ctid5:{t}"], has_conflict=True,
                   requires_flag="CONFLICT", conflict_kind="lower_authority", injected_ids=[a, b], note_doc=nid,
                   note_newer=bool(got % 2), stale_ids=sorted(c4 - set(cs)))
            got += 1
        short("injected_control", got)

        got = 0
        for t in self.pick(mit_pool, P["injected_claim"] * 2):
            if got >= P["injected_claim"]:
                break
            wr = self.wrong_mitigations(t)
            if not wr:
                continue
            m = self.rng.choice(wr)
            self.take(t)
            txt = NOTE_TEMPLATES_CLAIM[got % len(NOTE_TEMPLATES_CLAIM)].format(t=t, tn=_name(c, t), a=m,
                                                                               an=_name(c, m))
            nid = self.add_note(t, [("mitigated_by", m)], txt, newer=bool(got % 2))
            claim = f"MITRE ATT&CK mitigation {m} ({_name(c, m)}) mitigates technique {t} ({_name(c, t)})."
            self.Q(cat, "injected_claim", self.claim_q(claim), [], [f"attack:{t}"], qtype="claim",
                   gold_label="UNSUPPORTED", has_conflict=True, requires_flag="CONFLICT",
                   conflict_kind="lower_authority", injected_ids=[m], note_doc=nid, note_newer=bool(got % 2),
                   subject=t, obj=m, relation="mitigated_by")
            got += 1
        short("injected_claim", got)

        # ---------------- C5 insufficient evidence ----------------
        cat = "insufficient"

        def fake(kind):
            for _ in range(1000):
                x = {"technique": f"T{self.rng.randint(1700, 1999)}",
                     "subtech": f"T{self.rng.randint(1700, 1999)}.0{self.rng.randint(10, 99)}",
                     "cve": f"CVE-2031-{self.rng.randint(10000, 99999)}"}[kind]
                if not c.entity_docs(x) and x not in self.used:
                    self.used.add(x)
                    return x
            raise RuntimeError("could not create an unknown identifier")

        all_m = sorted(d.entity_id for d in c.docs.values() if d.doc_id.startswith("attack:M") and d.status == "active")
        all_w = sorted({w for d in kev for w in d.meta.get("cwes", [])})
        all_c = sorted(d.entity_id for d in c.docs.values() if d.doc_id.startswith("nist:") and d.status == "active"
                       and "(" not in d.entity_id)
        for i in range(P["claim_nei"]):
            kind = i % 3
            if kind == 0:
                s, o = fake("technique"), self.rng.choice(all_m)
                txt, rel = f"MITRE ATT&CK mitigation {o} ({_name(c, o)}) mitigates technique {s}.", "mitigated_by"
            elif kind == 1:
                s, o = fake("cve"), self.rng.choice(all_w)
                txt, rel = f"{s} is caused by weakness {o}.", "has_weakness"
            else:
                s, o = fake("subtech"), self.rng.choice(all_c)
                txt, rel = (f"NIST SP 800-53 Rev. 5 control {o} is mapped as a mitigation for ATT&CK technique {s}.",
                            "mapped_control")
            self.Q(cat, "claim_nei", self.claim_q(txt), [], [], qtype="claim", gold_label="NOT_ENOUGH_INFO",
                   answerable=False, subject=s, obj=o, relation=rel)
        for i in range(P["unknown_technique"]):
            t = fake("technique" if i % 2 == 0 else "subtech")
            self.Q(cat, "unknown_technique", self.mit_q(t), [], [], answerable=False)
        for i in range(P["unknown_cve"]):
            self.Q(cat, "unknown_cve", self.cwe_q(fake("cve")), [], [], answerable=False)

        no_mit = [t for t in self.techs if not mitigations_of(c, t) and not old_mitigations_of(c, t)
                  and c.docs.get(f"attack:{t}")]
        got = 0
        for t in self.pick(no_mit, P["no_mitigation"]):
            self.take(t)
            self.Q(cat, "no_mitigation", self.mit_q(t), [], [f"attack:{t}"], answerable=False)
            got += 1
        short("no_mitigation", got)
        no_ctl = [t for t in self.techs if not controls_of(c, t) and not controls_of(c, t, "4")
                  and not any(d.source == "CTID Mapping" for d in c.entity_docs(t))]
        got = 0
        for t in self.pick(no_ctl, P["no_control_mapping"]):
            self.take(t)
            self.Q(cat, "no_control_mapping", self.ctl_q(t), [], [f"attack:{t}"], answerable=False)
            got += 1
        short("no_control_mapping", got)

        # ---------------- C6 conflict negatives: agreeing low-authority notes ----------------
        cat = "benign_note"
        got = 0
        pool = [t for t in mit_pool if len(mitigations_of(c, t)) >= 2
                and set(old_mitigations_of(c, t)) <= set(mitigations_of(c, t))]   # no outdated IDs either
        for t in self.pick(pool, P["benign_mitigation"]):
            ms = mitigations_of(c, t)
            a, b = self.rng.sample(ms, 2)
            self.take(t)
            txt = NOTE_TEMPLATES_BENIGN[got % 2].format(t=t, tn=_name(c, t), a=a, an=_name(c, a), b=b,
                                                        bn=_name(c, b))
            nid = self.add_note(t, [("mitigated_by", a), ("mitigated_by", b)], txt, newer=bool(got % 2))
            self.Q(cat, "benign_mitigation", self.mit_q(t), ms, [f"attack:{t}"] + [f"attack:{m}" for m in ms],
                   note_doc=nid)
            got += 1
        short("benign_mitigation", got)
        got = 0
        for t in self.pick(mit_pool, P["benign_claim"]):
            m = self.rng.choice(mitigations_of(c, t))
            self.take(t)
            txt = NOTE_TEMPLATES_CLAIM[got % 2].format(t=t, tn=_name(c, t), a=m, an=_name(c, m))
            nid = self.add_note(t, [("mitigated_by", m)], txt, newer=bool(got % 2))
            claim = f"MITRE ATT&CK mitigation {m} ({_name(c, m)}) mitigates technique {t} ({_name(c, t)})."
            self.Q(cat, "benign_claim", self.claim_q(claim), [m], [f"attack:{t}"], qtype="claim",
                   gold_label="SUPPORTED", note_doc=nid, subject=t, obj=m, relation="mitigated_by")
            got += 1
        short("benign_claim", got)
        return self.out


def build_final(corpus: Corpus, cfg, dev_question_files: list[Path], out_q: Path, out_notes: Path,
                code_files: list[Path]) -> dict:
    """Build and freeze the final benchmark. Refuses to overwrite an existing frozen file."""
    out_q, out_notes = Path(out_q), Path(out_notes)
    if out_q.exists():
        raise RuntimeError(f"{out_q.name} already exists - the final benchmark is frozen and is never rebuilt")
    excl = dev_focus_entities(*dev_question_files)
    b = FinalBuilder(corpus, cfg, excl)
    qs = b.build()
    out_notes.write_text("".join(n.to_json() + "\n" for n in b.notes))
    out_q.write_text("".join(json.dumps(q) + "\n" for q in qs))
    info = {"n_questions": len(qs), "n_notes": len(b.notes), "excluded_dev_entities": len(excl),
            "shortfalls": b.short, "seed": FINAL_SEED,
            "questions_md5": hashlib.md5(out_q.read_bytes()).hexdigest(),
            "notes_md5": hashlib.md5(out_notes.read_bytes()).hexdigest(),
            "code_md5_at_build": {Path(p).name: hashlib.md5(Path(p).read_bytes()).hexdigest() for p in code_files}}
    out_q.with_name("final_FROZEN_info.json").write_text(json.dumps(info, indent=2))
    return info
