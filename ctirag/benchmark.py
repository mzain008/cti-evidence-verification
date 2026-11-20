"""Generate the CTI-EvidenceQA benchmark (v2).

Two tracks, reported separately:

TEXT track (needs language understanding; a graph lookup cannot answer it)
  tech_id        held-out ATT&CK procedure (actor anonymised, name leakage filtered) -> technique
  ate            CTIBench CTI-ATE: report excerpt -> main ATT&CK techniques (external, curated gold)
  rcm            CTIBench CTI-RCM: CVE description -> CWE (the CVE's KEV/NVD record is held out)
  attribution    4 anonymised procedures of one intrusion set -> ATT&CK group
  claim_behaviour  "behaviour X is an instance of technique Y", plausible sibling negatives
  claim_name     association claims written with names only (no identifiers)

EVIDENCE track (structured lookups under outdated / conflicting sources)
  attack_mitigation, nist_control   technique -> ATT&CK mitigations / 800-53 Rev. 5 controls
  claim_<relation>                  ID-based association claims, SUPPORTED/UNSUPPORTED/NOT_ENOUGH_INFO
  revoked        technique revoked since ATT&CK v8.2 (the v8.2 doc in the corpus still says active)
  withdrawn      withdrawn 800-53 control -> incorporating control
  rev4_rev5      CTID Rev. 4 mapping (older snapshot) disagrees with Rev. 5
  version_drift  mitigation set changed between ATT&CK v8.2 and the current release
  nvd_kev        NVD and CISA KEV list different CWEs (needs NVD enrichment)
  poisoned       OPTIONAL stress test: injected low-authority notes (off by default)

STRUCTURAL track (optional, off by default): CVE->CWE->CAPEC->ATT&CK chains. CAPEC->ATT&CK
cross-references are sparse and sometimes loose, so these golds need expert filtering before use.
"""
from __future__ import annotations

import csv
import json
import random
import re
from collections import defaultdict

from .config import Config
from .corpus import Corpus, Doc, extract_ids

TEXT_QTYPES = {"tech_id", "ate", "rcm", "attribution"}
TEXT_CLAIMS = {"claim_behaviour", "claim_name"}


def track_of(q: dict) -> str:
    if q["qtype"] in TEXT_QTYPES or q["subtype"] in TEXT_CLAIMS:
        return "text"
    if q["qtype"] in ("cve_to_tech", "full_chain"):
        return "structural"
    return "evidence"


# ---------------------------------------------------------------------------
# Gold helpers: always computed from the LATEST snapshot of authoritative sources
# ---------------------------------------------------------------------------
def _name(c: Corpus, eid: str) -> str:
    ds = sorted(c.entity_docs(eid), key=lambda d: d.snapshot, reverse=True)
    return next((d.meta["name"] for d in ds if d.meta.get("name")), "")


def resolve_technique(c: Corpus, t: str, depth: int = 0) -> tuple[str, bool]:
    """Follow revoked_by links in the current release. Returns (current_id, was_stale)."""
    if depth > 5:
        return t, True
    if c.status_of(t) == "revoked":
        nxt = [x for _, x, _ in c.current_neighbors(t, "revoked_by", 3)]
        if nxt:
            cur, _ = resolve_technique(c, nxt[0], depth + 1)
            return cur, True
    return t, False


def active(c: Corpus, eid: str) -> bool:
    return c.status_of(eid) == "active"


def mitigations_of(c: Corpus, t: str) -> list[str]:
    return sorted({m for _, m, _ in c.current_neighbors(t, "mitigated_by", 3) if active(c, m)})


def old_mitigations_of(c: Corpus, t: str) -> list[str]:
    return sorted({m for _, m, d in c.neighbors(t, "mitigated_by", 3) if not c.is_latest(d)})


def controls_of(c: Corpus, t: str, rev: str = "5") -> list[str]:
    return sorted({x for _, x, d in c.neighbors(t, "mapped_control") if d.startswith(f"ctid{rev}:")})


def cve_chain(c: Corpus, cve: str):
    """Return (techniques, stale_techniques, docs_on_path, cwes, capecs) via the current snapshot."""
    techs, stale, docs, cwes, caps = set(), set(), set(), set(), set()
    for _, cwe, d1 in c.current_neighbors(cve, "has_weakness", 3):
        for _, cap, d2 in c.current_neighbors(cwe, "related_attack_pattern", 3):
            if c.status_of(cap) != "active":
                continue
            for _, t, d3 in c.current_neighbors(cap, "maps_to_attack", 3):
                cur, was_stale = resolve_technique(c, t)
                if c.status_of(cur) != "active":
                    continue
                techs.add(cur)
                if was_stale:
                    stale.add(t)
                docs |= {d1, d2, d3, f"attack:{cur}"}
                cwes.add(cwe)
                caps.add(cap)
    return sorted(techs), sorted(stale), sorted(docs), sorted(cwes), sorted(caps)


def _q(qid, qtype, question, gold_ids, gold_docs, **kw):
    q = {"qid": qid, "qtype": qtype, "subtype": kw.pop("subtype", qtype), "question": question,
         "gold_ids": list(gold_ids), "gold_docs": list(gold_docs), "gold_label": kw.pop("gold_label", None),
         "stale_ids": list(kw.pop("stale_ids", [])), "requires_flag": kw.pop("requires_flag", None),
         "replacement_ids": list(kw.pop("replacement_ids", [])), "meta": kw}
    q["track"] = track_of(q)
    return q


CLAIM_INSTR = ("Answer SUPPORTED, UNSUPPORTED (the sources do not establish this association or contradict it), "
               "or NOT_ENOUGH_INFO (an entity in the claim cannot be found).")


def _anonymise(text: str, names: list[str]) -> str:
    for nm in sorted({n for n in names if n and len(n) > 2}, key=len, reverse=True):
        text = re.sub(rf"(?i)\b{re.escape(nm)}\b", "the adversary", text)
    return text


class BenchmarkBuilder:
    def __init__(self, corpus: Corpus, procedures: list[dict], cfg: Config):
        self.c, self.procs, self.cfg = corpus, procedures, cfg
        self.rng = random.Random(cfg.seed)
        self.notes: list[Doc] = []
        self.used_procs: set[str] = set()
        self.techs = [d.entity_id for d in corpus.docs.values()
                      if d.doc_id.startswith("attack:") and d.entity_type == "technique" and d.status == "active"]
        self.by_tactic = defaultdict(list)
        for t in self.techs:
            for tac in corpus.docs[f"attack:{t}"].meta.get("tactics", []):
                self.by_tactic[tac].append(t)
        # every name a technique has ever had (current + older release), for leakage filtering
        self.all_names = defaultdict(set)
        for d in corpus.docs.values():
            if d.entity_type == "technique" and d.meta.get("name"):
                self.all_names[d.entity_id].add(d.meta["name"].lower())
        self.proc_techs = defaultdict(set)  # procedure text -> every technique it is linked to
        for p in procedures:
            self.proc_techs[p["text"]].add(p["technique"])

    # -- helpers ------------------------------------------------------------------
    def siblings(self, t: str) -> list[str]:
        parent = t.split(".")[0]
        return [x for x in self.techs if x.split(".")[0] == parent and x != t]

    def same_tactic(self, t: str) -> list[str]:
        d = self.c.docs.get(f"attack:{t}")
        tacs = d.meta.get("tactics", []) if d else []
        return sorted({x for tac in tacs for x in self.by_tactic[tac]} - {t})

    def sample(self, xs, n):
        xs = list(xs)
        self.rng.shuffle(xs)
        return xs[:max(0, n)]

    def leaks(self, text: str, t: str) -> bool:
        low = text.lower()
        parent = t.split(".")[0]
        if t.lower() in low or re.search(rf"\b{parent}\b", text):
            return True
        names = self.all_names[t] | self.all_names[parent]
        return any(len(n) > 3 and n in low for n in names)

    def _proc_pool(self, actor_type=None):
        out = defaultdict(list)
        for p in self.procs:
            t = p["technique"]
            if t not in self.techs or not (80 <= len(p["text"]) <= 600) or self.leaks(p["text"], t):
                continue
            if actor_type and p["actor_type"] != actor_type:
                continue
            out[t].append(p)
        return out

    def _anon_proc(self, p) -> str:
        names = [p["actor_name"]] + p["actor_name"].split()
        d = self.c.docs.get(f"attack:{p['actor_id']}")
        if d:
            names += d.meta.get("aliases", [])
        return _anonymise(p["text"], names)

    # -- TEXT track -----------------------------------------------------------------
    def tech_id(self, n):
        pool = self._proc_pool()
        out = []
        for t in self.sample(pool, n):
            p = self.rng.choice(pool[t])
            self.used_procs.add(p["text"])
            q = (f"A threat report describes the following observed behaviour: \"{self._anon_proc(p)}\" "
                 f"Which MITRE ATT&CK technique (the most specific sub-technique where one applies) "
                 f"does this behaviour correspond to? Give the ATT&CK ID.")
            out.append(_q(f"tech_id-{len(out):04d}", "tech_id", q, [t], [f"attack:{t}"], actor_type=p["actor_type"]))
        return out

    def ctibench_ate(self, n):
        p = self.cfg.raw_dir / "ctibench_ate.tsv"
        if not p.exists() or n <= 0:
            return []
        # Enterprise rows only: the corpus is ATT&CK Enterprise (13 of the 60 rows are Mobile)
        rows = [r for r in csv.DictReader(p.open(), delimiter="\t") if r.get("Platform", "Enterprise") == "Enterprise"]
        out = []
        for r in self.sample(rows, n):
            raw_gold = sorted({g.split(".")[0] for g in extract_ids(r["GT"], ("technique",))})
            # CTIBench label noise: a few Enterprise rows contain Mobile IDs; keep Enterprise techniques only
            gold = [g for g in raw_gold if f"attack:{g}" in self.c.docs]
            if not gold:
                continue
            q = ("Extract every MITRE ATT&CK Enterprise technique described in the following threat report "
                 "excerpt. Return the main technique IDs only (T####, no sub-technique suffix). "
                 f"Excerpt: \"{r['Description'].strip()}\"")
            out.append(_q(f"ate-{len(out):04d}", "ate", q, gold, [f"attack:{g}" for g in gold],
                          parent_only=True, source_url=r.get("URL", ""), dropped_gold=sorted(set(raw_gold) - set(gold))))
        return out

    def ctibench_rcm(self, n):
        p = self.cfg.raw_dir / "ctibench_rcm.tsv"
        if not p.exists() or n <= 0:
            return []
        rows = list(csv.DictReader(p.open(), delimiter="\t"))
        out = []
        for r in self.sample(rows, n):
            gold = extract_ids(r["GT"], ("cwe",))
            if not gold:
                continue
            desc = re.sub(r"(?i)CVE-\d{4}-\d{4,7}", "this vulnerability", r["Description"].strip())
            q = (f"A vulnerability report states: \"{desc}\" Which CWE weakness is the root cause of this "
                 f"vulnerability? Give the single most specific CWE ID.")
            cve = extract_ids(r.get("URL", ""), ("cve",))
            out.append(_q(f"rcm-{len(out):04d}", "rcm", q, gold[:1], [f"cwe:{gold[0]}"],
                          cve=cve[0] if cve else None))
        return out

    def attribution(self, n):
        groups = defaultdict(list)
        for p in self.procs:
            if p["actor_type"] == "intrusion-set" and p["technique"] in self.techs \
                    and 80 <= len(p["text"]) <= 500 and p["text"] not in self.used_procs:
                groups[p["actor_id"]].append(p)
        users = defaultdict(set)
        for g, ps in groups.items():
            for p in ps:
                users[p["technique"]].add(g)
        out = []
        for g in self.sample([g for g, ps in groups.items() if len({p["technique"] for p in ps}) >= 6], n):
            ps = sorted(groups[g], key=lambda p: (len(users[p["technique"]]), self.rng.random()))
            chosen, seen_t = [], set()
            for p in ps:
                if p["technique"] not in seen_t:
                    chosen.append(p)
                    seen_t.add(p["technique"])
                if len(chosen) == 4:
                    break
            for p in chosen:
                self.used_procs.add(p["text"])
            items = " ".join(f"({i+1}) {self._anon_proc(p)}" for i, p in enumerate(chosen))
            q = (f"The following behaviours were observed in a single intrusion campaign: {items} "
                 f"Which MITRE ATT&CK threat group (G-ID) is most consistent with this activity?")
            out.append(_q(f"attribution-{len(out):04d}", "attribution", q, [g],
                          [f"attack:{g}"] + [f"attack:{p['technique']}" for p in chosen],
                          techniques=[p["technique"] for p in chosen]))
        return out

    def claims_text(self, n):
        out = []
        # (a) behaviour claims
        pool = self._proc_pool()
        nb = n // 2
        for i, t in enumerate(self.sample(pool, nb)):
            cands = [p for p in pool[t] if p["text"] not in self.used_procs] or pool[t]
            p = self.rng.choice(cands)
            self.used_procs.add(p["text"])
            linked = self.proc_techs[p["text"]]
            if i % 2 == 0:
                label, tt = "SUPPORTED", t
            else:
                # plausible negative: a sibling sub-technique, else a same-tactic technique from another family
                negs = [x for x in self.siblings(t) if x not in linked]
                if not negs:
                    parents = {y.split(".")[0] for y in linked}
                    negs = [x for x in self.same_tactic(t)[:40] if x not in linked and x.split(".")[0] not in parents]
                if not negs:
                    continue
                label, tt = "UNSUPPORTED", self.rng.choice(negs)
            claim = (f"The behaviour \"{self._anon_proc(p)}\" is an instance of ATT&CK technique {tt} "
                     f"({_name(self.c, tt)}).")
            q = f"Verify the following claim against authoritative security sources: \"{claim}\" {CLAIM_INSTR}"
            out.append(_q(f"claim_t-{len(out):04d}", "claim", q, [tt] if label == "SUPPORTED" else [],
                          [f"attack:{t}"], gold_label=label, subtype="claim_behaviour",
                          subject=None, obj=tt, relation="instance_of", true_technique=t))
        # (b) name-only association claims (no identifiers -> entity resolution needed)
        name_count = defaultdict(int)
        for t in self.techs:
            name_count[_name(self.c, t).lower()] += 1
        uniq = [t for t in self.techs if name_count[_name(self.c, t).lower()] == 1 and mitigations_of(self.c, t)]
        k = 0
        while k < n - nb and uniq:
            t = self.rng.choice(uniq)
            ms = mitigations_of(self.c, t)
            if k % 2 == 0:
                label, m = "SUPPORTED", self.rng.choice(ms)
            else:
                pool_m = sorted({x for s in self.siblings(t) + self.same_tactic(t)[:40]
                                 for x in mitigations_of(self.c, s)} - set(ms))
                if not pool_m:
                    continue
                label, m = "UNSUPPORTED", self.rng.choice(pool_m)
            claim = f"The ATT&CK mitigation \"{_name(self.c, m)}\" mitigates the technique \"{_name(self.c, t)}\"."
            q = f"Verify the following claim against authoritative security sources: \"{claim}\" {CLAIM_INSTR}"
            out.append(_q(f"claim_n-{len(out):04d}", "claim", q, [m] if label == "SUPPORTED" else [],
                          [f"attack:{t}", f"attack:{m}"], gold_label=label, subtype="claim_name",
                          subject=t, obj=m, relation="mitigated_by"))
            k += 1
        return out

    # -- EVIDENCE track -------------------------------------------------------------
    def mitigation(self, n):
        out = []
        pool_m = [t for t in self.techs if 1 <= len(mitigations_of(self.c, t)) <= 8]
        pool_c = [t for t in self.techs if 1 <= len(controls_of(self.c, t)) <= 15]
        for t in self.sample(pool_m, n // 2):
            ms = mitigations_of(self.c, t)
            q = f"Which MITRE ATT&CK mitigations (M-IDs) address technique {t} ({_name(self.c, t)})?"
            out.append(_q(f"mitigation-{len(out):04d}", "mitigation", q, ms,
                          [f"attack:{t}"] + [f"attack:{m}" for m in ms], subtype="attack_mitigation",
                          stale_ids=sorted(set(old_mitigations_of(self.c, t)) - set(ms))))
        for t in self.sample(pool_c, n - n // 2):
            cs = controls_of(self.c, t)
            q = (f"According to the Center for Threat-Informed Defense mapping, which NIST SP 800-53 Rev. 5 "
                 f"controls mitigate technique {t} ({_name(self.c, t)})? List the control IDs.")
            out.append(_q(f"mitigation-{len(out):04d}", "mitigation", q, cs, [f"ctid5:{t}"],
                          subtype="nist_control", stale_ids=sorted(set(controls_of(self.c, t, "4")) - set(cs))))
        return out

    def claims_id(self, n):
        out = []
        n_nei = max(1, int(n * 0.10))
        n_sup = int((n - n_nei) / 2)
        n_uns = n - n_nei - n_sup
        rels = ["mitigated_by", "has_weakness", "maps_to_attack", "mapped_control"]
        kev = [x for x in self.c.docs.values() if x.doc_id.startswith("kev:") and x.meta.get("cwes")]
        capec = [x for x in self.c.docs.values() if x.doc_id.startswith("capec:") and x.status == "active"
                 and any(r == "maps_to_attack" for r, _ in x.links)]

        def make(rel, label):
            for _ in range(300):
                if rel == "mitigated_by":
                    t = self.rng.choice(self.techs)
                    ms = mitigations_of(self.c, t)
                    if not ms:
                        continue
                    if label == "SUPPORTED":
                        return t, self.rng.choice(ms), [f"attack:{t}"]
                    pool = sorted({x for s in self.siblings(t) + self.same_tactic(t)[:40]
                                   for x in mitigations_of(self.c, s)} - set(ms) - set(old_mitigations_of(self.c, t)))
                    if pool:
                        return t, self.rng.choice(pool), [f"attack:{t}"]
                elif rel == "has_weakness":
                    d = self.rng.choice(kev)
                    allw = {w for _, w, _ in self.c.neighbors(d.entity_id, "has_weakness")}
                    if label == "SUPPORTED":
                        return d.entity_id, self.rng.choice(d.meta["cwes"]), [d.doc_id]
                    pool = sorted({w for x in kev if x.meta.get("vendor") == d.meta.get("vendor")
                                   for w in x.meta["cwes"]} - allw)
                    if pool:
                        return d.entity_id, self.rng.choice(pool), [d.doc_id]
                elif rel == "maps_to_attack":
                    d = self.rng.choice(capec)
                    ts = [t for r, t in d.links if r == "maps_to_attack" and active(self.c, t)]
                    if not ts:
                        continue
                    if label == "SUPPORTED":
                        return d.entity_id, self.rng.choice(ts), [d.doc_id]
                    pool = sorted({x for t in ts for x in self.siblings(t) + self.same_tactic(t)[:30]} - set(ts))
                    if pool:
                        return d.entity_id, self.rng.choice(pool), [d.doc_id]
                elif rel == "mapped_control":
                    t = self.rng.choice(self.techs)
                    cs = controls_of(self.c, t)
                    if not cs:
                        continue
                    if label == "SUPPORTED":
                        return t, self.rng.choice(cs), [f"ctid5:{t}"]
                    fams = {x.split("-")[0] for x in cs}
                    pool = sorted(d.entity_id for d in self.c.docs.values() if d.doc_id.startswith("nist:")
                                  and d.status == "active" and d.entity_id.split("-")[0] in fams
                                  and d.entity_id not in cs and "(" not in d.entity_id)
                    if pool:
                        return t, self.rng.choice(pool), [f"ctid5:{t}"]
            raise RuntimeError(f"could not build {rel}/{label}")

        def text(rel, s, o):
            sn, on = _name(self.c, s), _name(self.c, o)
            sn, on = (f" ({sn})" if sn else ""), (f" ({on})" if on else "")
            return {
                "mitigated_by": f"MITRE ATT&CK mitigation {o}{on} mitigates technique {s}{sn}.",
                "has_weakness": f"{s} is caused by weakness {o}{on}.",
                "maps_to_attack": f"CAPEC attack pattern {s}{sn} maps to ATT&CK technique {o}{on}.",
                "mapped_control": f"NIST SP 800-53 Rev. 5 control {o}{on} is mapped as a mitigation for ATT&CK technique {s}{sn}.",
            }[rel]

        seen = set()
        for label, cnt in (("SUPPORTED", n_sup), ("UNSUPPORTED", n_uns)):
            for i in range(cnt):
                rel = rels[i % len(rels)]
                for _ in range(20):
                    s, o, docs = make(rel, label)
                    if (s, o) not in seen:
                        seen.add((s, o))
                        break
                q = f"Verify the following claim against authoritative security sources: \"{text(rel, s, o)}\" {CLAIM_INSTR}"
                out.append(_q(f"claim-{len(out):04d}", "claim", q, [o] if label == "SUPPORTED" else [],
                              docs, gold_label=label, subtype=f"claim_{rel}", subject=s, obj=o, relation=rel))
        fakes = [("mitigated_by", lambda: (f"T{self.rng.randint(1800, 1999)}", self.rng.choice(["M1038", "M1026", "M1042"]))),
                 ("has_weakness", lambda: (f"CVE-2031-{self.rng.randint(10000, 99999)}", "CWE-787")),
                 ("mapped_control", lambda: (f"T{self.rng.randint(1800, 1999)}.0{self.rng.randint(10, 99)}", "AC-2"))]
        for i in range(n_nei):
            rel, f = fakes[i % len(fakes)]
            s, o = f()
            while self.c.entity_docs(s):
                s, o = f()
            claim = {"mitigated_by": f"MITRE ATT&CK mitigation {o} mitigates technique {s}.",
                     "has_weakness": f"{s} is caused by weakness {o}.",
                     "mapped_control": f"NIST SP 800-53 Rev. 5 control {o} is mapped as a mitigation for ATT&CK technique {s}."}[rel]
            q = f"Verify the following claim against authoritative security sources: \"{claim}\" {CLAIM_INSTR}"
            out.append(_q(f"claim-{len(out):04d}", "claim", q, [], [], gold_label="NOT_ENOUGH_INFO",
                          subtype="claim_nei", subject=s, obj=o, relation=rel))
        return out

    def temporal(self, n, nvd_loaded=False):
        out = []
        quota = {"revoked": 0.25, "withdrawn": 0.15, "rev4_rev5": 0.15, "version_drift": 0.30, "nvd_kev": 0.15}
        if not nvd_loaded:
            quota["version_drift"] += quota.pop("nvd_kev")
        quota = {k: int(round(v * n)) for k, v in quota.items()}

        # revoked: prefer techniques that the older ATT&CK release (also in the corpus) still lists as active
        rv = {d.entity_id for d in self.c.docs.values() if d.entity_type == "technique"
              and self.c.status_of(d.entity_id) == "revoked"}
        old_active = {d.entity_id for d in self.c.docs.values() if d.doc_id.startswith("attack_old:")
                      and d.status == "active"}
        cands = []
        for t in rv:
            cur, _ = resolve_technique(self.c, t)
            ms = mitigations_of(self.c, cur)
            if cur != t and ms and len(ms) <= 8:
                cands.append((t in old_active, t, cur, ms))
        cands.sort(key=lambda x: (not x[0], self.rng.random()))
        for conflict, t, cur, ms in cands[:quota["revoked"]]:
            q = (f"Which MITRE ATT&CK mitigations (M-IDs) should be applied against technique {t} "
                 f"({_name(self.c, t)})?")
            out.append(_q(f"temporal-{len(out):04d}", "temporal", q, ms,
                          [f"attack:{t}", f"attack:{cur}"] + [f"attack:{m}" for m in ms],
                          subtype="revoked", requires_flag="REVOKED", replacement_ids=[cur],
                          stale_ids=[t] + sorted(set(old_mitigations_of(self.c, t)) - set(ms)),
                          older_release_says_active=conflict))

        wd = [d for d in self.c.docs.values() if d.doc_id.startswith("nist:") and d.status == "withdrawn"
              and any(r == "incorporated_into" for r, _ in d.links)]
        for d in self.sample(wd, quota["withdrawn"]):
            tg = sorted({t for r, t in d.links if r == "incorporated_into"})
            q = (f"An older audit checklist requires NIST SP 800-53 control {d.entity_id}. Is this control still "
                 f"current in Rev. 5? If not, which control(s) should be assessed instead?")
            out.append(_q(f"temporal-{len(out):04d}", "temporal", q, tg, [d.doc_id] + [f"nist:{x}" for x in tg],
                          subtype="withdrawn", requires_flag="WITHDRAWN", replacement_ids=tg, stale_ids=[d.entity_id]))

        r45 = []
        for t in self.techs:
            c5, c4 = set(controls_of(self.c, t)), set(controls_of(self.c, t, "4"))
            if c5 and c4 and (c4 - c5) and len(c5) <= 15:
                r45.append((t, sorted(c5), sorted(c4 - c5)))
        for t, c5, only4 in self.sample(r45, quota["rev4_rev5"]):
            q = (f"Which NIST SP 800-53 controls are currently mapped as mitigations for ATT&CK technique {t} "
                 f"({_name(self.c, t)})?")
            out.append(_q(f"temporal-{len(out):04d}", "temporal", q, c5, [f"ctid5:{t}"], subtype="rev4_rev5",
                          requires_flag="OUTDATED", stale_ids=only4))

        # version drift between the older ATT&CK release and the current one (real, not injected)
        removed, added = [], []
        for t in self.techs:
            cur, old = set(mitigations_of(self.c, t)), set(old_mitigations_of(self.c, t))
            if not cur or not old or len(cur) > 8:
                continue
            if old - cur:
                removed.append(t)
            elif cur - old:
                added.append(t)
        picks = self.sample(removed, quota["version_drift"])
        picks += self.sample(added, quota["version_drift"] - len(picks))
        for t in picks:
            ms = mitigations_of(self.c, t)
            old = old_mitigations_of(self.c, t)
            q = f"Which MITRE ATT&CK mitigations (M-IDs) currently address technique {t} ({_name(self.c, t)})?"
            out.append(_q(f"temporal-{len(out):04d}", "temporal", q, ms,
                          [f"attack:{t}"] + [f"attack:{m}" for m in ms], subtype="version_drift",
                          stale_ids=sorted(set(old) - set(ms)), old_set=old,
                          drift="removed" if set(old) - set(ms) else "added"))

        if nvd_loaded:
            dis = []
            for d in self.c.docs.values():
                if d.doc_id.startswith("nvd:"):
                    k = self.c.docs.get(f"kev:{d.entity_id}")
                    if k and k.meta.get("cwes") and d.meta.get("cwes") and set(k.meta["cwes"]) != set(d.meta["cwes"]):
                        dis.append((d, k))
            for d, k in self.sample(dis, quota.get("nvd_kev", 0)):
                gold = sorted(set(d.meta["cwes"]) | set(k.meta["cwes"]))
                q = (f"Which CWE weakness(es) are recorded for {d.entity_id}? Note whether the authoritative "
                     f"sources agree.")
                out.append(_q(f"temporal-{len(out):04d}", "temporal", q, gold, [d.doc_id, k.doc_id],
                              subtype="nvd_kev", requires_flag="CONFLICT", nvd=d.meta["cwes"], kev=k.meta["cwes"]))
        return out

    def poisoned(self, n):
        """Optional stress test. Varied low-authority sources and wording; nothing in the agent keys on them."""
        srcs = ["Community Note", "Vendor Blog", "Security Forum", "Analyst Wiki"]
        templates = [
            "In our incident-response experience the effective controls for {t} {tn} are {a} {an} and {b} {bn}.",
            "Updated guidance for {t} ({tn}): prioritise {a} ({an}) together with {b} ({bn}); other listed mitigations add little.",
            "Q: what stops {tn} ({t})? A: we deployed {a} {an} and {b} {bn} and saw it blocked.",
            "{tn} [{t}] defensive notes - recommended mitigations: {a}, {b}.",
            "Lessons learned: against {t} the measures that mattered were {an} ({a}) and {bn} ({b}).",
        ]
        out = []
        pool = [t for t in self.techs if 2 <= len(mitigations_of(self.c, t)) <= 8]
        for t in self.sample(pool, n * 2):
            if len(out) >= n:
                break
            ms = mitigations_of(self.c, t)
            wrong = sorted({x for s in self.siblings(t) + self.same_tactic(t)[:40]
                            for x in mitigations_of(self.c, s)} - set(ms))
            if len(wrong) < 2:
                continue
            a, b = self.rng.sample(wrong, 2)
            i = len(self.notes)
            date = "2026-08-15" if i % 2 else f"201{self.rng.randint(6, 9)}-0{self.rng.randint(1, 9)}-12"
            txt = templates[i % len(templates)].format(t=t, tn=_name(self.c, t), a=a, an=_name(self.c, a),
                                                       b=b, bn=_name(self.c, b))
            nid = f"note:{i:04d}"
            self.notes.append(Doc(nid, srcs[i % len(srcs)], t, "note", f"{srcs[i % len(srcs)]}: {t}", txt, date,
                                  "", "active", [("mitigated_by", a), ("mitigated_by", b)], {"poison_for": t}))
            q = f"Which MITRE ATT&CK mitigations (M-IDs) address technique {t} ({_name(self.c, t)})?"
            out.append(_q(f"poisoned-{len(out):04d}", "temporal", q, ms, [f"attack:{t}"] + [f"attack:{m}" for m in ms],
                          subtype="poisoned", requires_flag="CONFLICT", stale_ids=[a, b], poison_doc=nid,
                          poison_newer=bool(i % 2)))
        return out

    # -- STRUCTURAL track (optional) -------------------------------------------------
    def cve_chain_questions(self, n, full_chain=False):
        if n <= 0:
            return []
        cands = []
        for d in self.c.docs.values():
            if d.doc_id.startswith("kev:"):
                techs, stale, docs, cwes, caps = cve_chain(self.c, d.entity_id)
                if 1 <= len(techs) <= 6:
                    cands.append((d, techs, stale, docs, cwes, caps))
        self.rng.shuffle(cands)
        out = []
        for d, techs, stale, docs, cwes, caps in cands:
            if len(out) >= n:
                break
            if not full_chain:
                q = (f"CISA lists {d.entity_id} ({d.meta.get('vendor','')} {d.meta.get('product','')}) as a known "
                     f"exploited vulnerability. Using its documented weakness (CWE) and the CAPEC attack patterns "
                     f"related to that weakness, which MITRE ATT&CK techniques could an adversary employ when "
                     f"exploiting it? Return the ATT&CK technique IDs.")
                out.append(_q(f"cve_to_tech-{len(out):04d}", "cve_to_tech", q, techs, docs, stale_ids=stale,
                              cwes=cwes, capecs=caps))
            else:
                mits = sorted({m for t in techs for m in mitigations_of(self.c, t)})
                if not 1 <= len(mits) <= 8:
                    continue
                q = (f"For {d.entity_id} ({d.meta.get('vendor','')} {d.meta.get('product','')}), trace its weakness "
                     f"(CWE) to related CAPEC attack patterns and the ATT&CK techniques they map to. Which MITRE "
                     f"ATT&CK mitigations (M-IDs) address those techniques?")
                out.append(_q(f"full_chain-{len(out):04d}", "full_chain", q, mits,
                              docs + [f"attack:{m}" for m in mits], stale_ids=stale, techniques=techs))
        return out

    def build(self) -> list[dict]:
        cfg = self.cfg
        nvd_loaded = any(d.startswith("nvd:") for d in self.c.docs)
        qs = []
        qs += self.tech_id(cfg.n_tech_id)
        qs += self.attribution(cfg.n_attribution)
        qs += self.claims_text(cfg.n_claims_text)
        qs += self.ctibench_ate(cfg.n_ctibench_ate)
        qs += self.ctibench_rcm(cfg.n_ctibench_rcm)
        qs += self.mitigation(cfg.n_mitigation)
        qs += self.claims_id(cfg.n_claims_id)
        qs += self.temporal(cfg.n_temporal, nvd_loaded)
        if cfg.inject_conflicts:
            qs += self.poisoned(cfg.n_poisoned)
        qs += self.cve_chain_questions(cfg.n_cve_to_tech)
        qs += self.cve_chain_questions(cfg.n_full_chain, full_chain=True)
        return qs


def build_benchmark(corpus: Corpus, procedures: list[dict], cfg: Config):
    b = BenchmarkBuilder(corpus, procedures, cfg)
    qs = b.build()
    with (cfg.proc_dir / "questions.jsonl").open("w") as fh:
        for q in qs:
            fh.write(json.dumps(q) + "\n")
    with (cfg.proc_dir / "notes.jsonl").open("w") as fh:
        for d in b.notes:
            fh.write(d.to_json() + "\n")
    cnt = defaultdict(int)
    for q in qs:
        cnt[(q["track"], q["subtype"])] += 1
    print(f"[benchmark] {len(qs)} questions, {len(b.notes)} injected notes")
    for k in sorted(cnt):
        print(f"   {k[0]:10s} {k[1]:24s} {cnt[k]}")
    return qs, b.notes


def load_questions(cfg: Config) -> list[dict]:
    p = cfg.proc_dir / "questions.jsonl"
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
