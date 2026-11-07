"""Source verification of the final benchmark's gold answers.

Every gold answer is re-derived DIRECTLY from the frozen raw source files in WORK/raw (MITRE ATT&CK STIX,
older ATT&CK v8.2 STIX, MITRE CAPEC STIX, MITRE CWE XML, CISA KEV JSON, NVD 2.0 records, NIST SP 800-53
Rev. 5 OSCAL, CTID ATT&CK->800-53 mappings). The parsers here are written independently of corpus.py,
so a bug in the corpus builder or the question generator shows up as a MISMATCH.

For each question the report gives: the expected answer according to the source, MATCH / MISMATCH,
the source file + version + md5 (the frozen snapshot), the raw record(s) the answer rests on, and the
official web page(s) for a human check. Note that the web pages show the LIVE version of each source,
which may differ from the frozen snapshot; the frozen record is authoritative for this benchmark.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import pandas as pd

from .corpus import extract_ids, id_kind, norm_id, oscal_to_control


def _md5(p: Path) -> str:
    return hashlib.md5(Path(p).read_bytes()).hexdigest() if Path(p).exists() else ""


def _ext(o: dict, names=("mitre-attack",)) -> str | None:
    for r in o.get("external_references", []):
        if r.get("source_name") in names and r.get("external_id"):
            return r["external_id"].upper()
    return None


def url_of(i: str) -> str:
    k = id_kind(i)
    if k == "technique":
        return "https://attack.mitre.org/techniques/" + i.replace(".", "/") + "/"
    if k == "mitigation":
        return f"https://attack.mitre.org/mitigations/{i}/"
    if k == "cve":
        return f"https://nvd.nist.gov/vuln/detail/{i}"
    if k == "cwe":
        return f"https://cwe.mitre.org/data/definitions/{i.split('-')[1]}.html"
    if k == "capec":
        return f"https://capec.mitre.org/data/definitions/{i.split('-')[1]}.html"
    if k == "control":
        return f"https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_1/home (control {i})"
    return ""


class RawSources:
    """Independent readers of the raw frozen files."""

    def __init__(self, raw_dir: Path):
        self.raw = Path(raw_dir)
        self.info, self.errors = {}, {}
        for name, fn in (("attack", self._attack), ("attack_old", self._attack_old), ("capec", self._capec),
                         ("cwe", self._cwe), ("kev", self._kev), ("nvd", self._nvd), ("nist", self._nist),
                         ("ctid", self._ctid)):
            try:
                fn()
            except Exception as e:  # noqa: BLE001
                self.errors[name] = f"{e.__class__.__name__}: {e}"

    # -- ATT&CK ---------------------------------------------------------------------------
    def _read_attack(self, path: Path):
        objs = json.loads(path.read_text())["objects"]
        coll = [o for o in objs if o["type"] == "x-mitre-collection"]
        version = coll[0].get("x_mitre_version", "") if coll else ""
        by_id = {o["id"]: o for o in objs}
        ext = {o["id"]: _ext(o) for o in objs if _ext(o)}
        tech, mit = {}, {}
        for o in objs:
            e = ext.get(o["id"])
            if not e:
                continue
            st = "revoked" if o.get("revoked") else ("deprecated" if o.get("x_mitre_deprecated") else "active")
            if o["type"] == "attack-pattern":
                tech[e] = {"name": o.get("name", ""), "status": st}
            elif o["type"] == "course-of-action" and re.fullmatch(r"M\d{4}", e):
                mit[e] = {"name": o.get("name", ""), "status": st}
        mitig = defaultdict(set)     # technique -> mitigations (relationship ids kept for evidence)
        rel_ids = {}
        revoked_by = {}
        for o in objs:
            if o["type"] != "relationship" or o.get("revoked") or o.get("x_mitre_deprecated"):
                continue
            s, t, rt = ext.get(o["source_ref"]), ext.get(o["target_ref"]), o["relationship_type"]
            if not s or not t:
                continue
            if rt == "mitigates" and by_id[o["source_ref"]]["type"] == "course-of-action" and s in mit:
                mitig[t].add(s)
                rel_ids[(s, t)] = o["id"]
            elif rt == "revoked-by":
                revoked_by[s] = t
        return {"version": version, "tech": tech, "mit": mit, "mitig": mitig, "rel_ids": rel_ids,
                "revoked_by": revoked_by, "file": path.name, "md5": _md5(path)}

    def _attack(self):
        self.attack = self._read_attack(self.raw / "attack.json")
        self.info["MITRE ATT&CK (current)"] = f"v{self.attack['version']} | attack.json | md5 {self.attack['md5']}"

    def _attack_old(self):
        p = self.raw / "attack_old.json"
        self.attack_old = self._read_attack(p) if p.exists() else None
        if self.attack_old:
            self.info["MITRE ATT&CK (older)"] = f"v{self.attack_old['version']} | attack_old.json | md5 {self.attack_old['md5']}"

    def mitigations(self, t, old=False):
        a = self.attack_old if old else self.attack
        if not a:
            return set()
        return {m for m in a["mitig"].get(t, set()) if a["mit"].get(m, {}).get("status") == "active"}

    def resolve(self, t):
        seen = 0
        while self.attack["tech"].get(t, {}).get("status") == "revoked" and t in self.attack["revoked_by"] and seen < 6:
            t = self.attack["revoked_by"][t]
            seen += 1
        return t

    # -- CAPEC / CWE -----------------------------------------------------------------------
    def _capec(self):
        p = self.raw / "capec.json"
        objs = json.loads(p.read_text())["objects"]
        self.capec = {}
        for o in objs:
            if o["type"] != "attack-pattern":
                continue
            cid = _ext(o, ("capec",))
            if not cid:
                continue
            cwes = {r["external_id"].upper() for r in o.get("external_references", [])
                    if r.get("source_name") == "cwe" and r.get("external_id")}
            atk = {"T" + r["external_id"].upper().lstrip("T") for r in o.get("external_references", [])
                   if r.get("source_name") == "ATTACK" and r.get("external_id")}
            st = "deprecated" if (o.get("x_capec_status") == "Deprecated" or o.get("revoked")) else "active"
            self.capec[cid] = {"name": o.get("name", ""), "cwes": cwes, "attack": atk, "status": st}
        self.info["MITRE CAPEC"] = f"capec.json | md5 {_md5(p)}"

    def _cwe(self):
        p = self.raw / "cwe.zip"
        self.cwe = {}
        if not p.exists():
            return
        raw = p.read_bytes()
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            raw = z.read([n for n in z.namelist() if n.endswith(".xml")][0])
        root = ET.fromstring(raw)
        for w in root.iter():
            if w.tag.split("}")[-1] not in ("Weakness", "Category"):
                continue
            caps = {f"CAPEC-{x.attrib['CAPEC_ID']}" for x in w.iter() if x.tag.split("}")[-1] == "Related_Attack_Pattern"}
            self.cwe[f"CWE-{w.attrib['ID']}"] = {"name": w.attrib.get("Name", ""), "capec": caps}
        self.info["MITRE CWE"] = f"v{root.attrib.get('Version', '')} | cwe.zip | md5 {_md5(p)}"

    def capecs_of_cwe(self, w):
        """Active CAPEC patterns related to a CWE, as asserted by either CWE or CAPEC."""
        out = set(self.cwe.get(w, {}).get("capec", set()))
        out |= {c for c, v in self.capec.items() if w in v["cwes"]}
        return {c for c in out if self.capec.get(c, {}).get("status") == "active"}

    # -- KEV / NVD -----------------------------------------------------------------------------
    def _kev(self):
        p = self.raw / "kev.json"
        k = json.loads(p.read_text())
        self.kev = {v["cveID"].upper(): {c.upper() for c in v.get("cwes", []) if c.upper().startswith("CWE-")}
                    for v in k["vulnerabilities"]}
        self.info["CISA KEV"] = f"catalog {k.get('catalogVersion', '')} ({k.get('dateReleased', '')[:10]}) | kev.json | md5 {_md5(p)}"

    def _nvd(self):
        p = self.raw / "nvd_cache.jsonl"
        self.nvd = {}
        if not p.exists():
            return
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("missing"):
                continue
            cw = {d.get("value", "").upper() for w in r.get("weaknesses", []) for d in w.get("description", [])}
            self.nvd[r["id"].upper()] = {c for c in cw if c.startswith("CWE-")}
        self.info["NVD (API 2.0 records)"] = f"{len(self.nvd)} records | nvd_cache.jsonl | md5 {_md5(p)}"

    def cwes(self, cve):
        out = {}
        if self.kev.get(cve):
            out["CISA KEV"] = self.kev[cve]
        if self.nvd.get(cve):
            out["NVD"] = self.nvd[cve]
        return out

    # -- NIST / CTID ---------------------------------------------------------------------------
    def _nist(self):
        p = self.raw / "sp80053_r5.json"
        cat = json.loads(p.read_text())["catalog"]
        self.nist = {}

        def walk(cs):
            for c in cs:
                cid = oscal_to_control(c["id"])
                wd = any(x.get("name") == "status" and x.get("value") == "withdrawn" for x in c.get("props", []))
                inc = {oscal_to_control(l["href"]) for l in c.get("links", [])
                       if l.get("rel") in ("incorporated-into", "moved-to")}
                self.nist[cid] = {"title": c.get("title", ""), "withdrawn": wd, "into": inc}
                walk(c.get("controls", []))
        for g in cat["groups"]:
            walk(g.get("controls", []))
        self.info["NIST SP 800-53 Rev. 5"] = f"OSCAL {cat['metadata'].get('version', '')} | sp80053_r5.json | md5 {_md5(p)}"

    def _ctid(self):
        self.ctid = {}
        stix2ext = {}
        for f in ("attack.json", "attack_old.json"):
            if (self.raw / f).exists():
                for o in json.loads((self.raw / f).read_text())["objects"]:
                    if _ext(o):
                        stix2ext.setdefault(o["id"], _ext(o))
        for rev in ("r5", "r4"):
            mp, cp = self.raw / f"ctid_{rev}_map.json", self.raw / f"ctid_{rev}_ctl.json"
            if not (mp.exists() and cp.exists()):
                continue
            coa = {}
            for o in json.loads(cp.read_text())["objects"]:
                if o["type"] == "course-of-action":
                    for r in o.get("external_references", []):
                        if r.get("external_id"):
                            coa[o["id"]] = norm_id(r["external_id"])
            per = defaultdict(set)
            for o in json.loads(mp.read_text())["objects"]:
                if o["type"] == "relationship" and o["relationship_type"] == "mitigates":
                    c, t = coa.get(o["source_ref"]), stix2ext.get(o["target_ref"])
                    if c and t:
                        per[t].add(c)
            self.ctid[rev] = per
            self.info[f"CTID mapping {rev}"] = f"ctid_{rev}_map.json md5 {_md5(mp)}"

    def known(self, i):
        k = id_kind(i)
        if k in ("technique",):
            return i in self.attack["tech"] or bool(self.attack_old and i in self.attack_old["tech"])
        if k == "mitigation":
            return i in self.attack["mit"]
        if k == "cve":
            return i in self.kev or i in self.nvd
        if k == "cwe":
            return i in self.cwe or any(i in v for v in self.kev.values())
        if k == "capec":
            return i in self.capec
        if k == "control":
            return i in self.nist
        return False


# ---------------------------------------------------------------------------------------------
def _fmt(xs):
    return ", ".join(sorted(xs)) if xs else "(none)"


def verify_question(q: dict, S: RawSources) -> dict:
    m, sub = q.get("meta", {}), q["subtype"]
    gold = set(q["gold_ids"])
    label = q.get("gold_label")
    s, o = m.get("subject"), m.get("obj")
    ids = extract_ids(q["question"])
    focus = s or next((i for i in ids if id_kind(i) not in ("mitigation", "cwe")), ids[0] if ids else None)
    out = {"qid": q["qid"], "category": m.get("category"), "subtype": sub,
           "gold": label or _fmt(gold) if (label or gold) else "(abstain)"}
    exp, ev, src, links = None, [], [], [url_of(i) for i in ([focus] if focus else []) + ([o] if o else []) if url_of(i)]

    def claim(ok):
        return "SUPPORTED" if ok else "UNSUPPORTED"

    if sub in ("claim_mitigated_by", "injected_claim", "benign_claim"):
        ms = S.mitigations(s)
        exp = claim(o in ms)
        src = ["MITRE ATT&CK (current)"]
        ev = [f"ATT&CK lists for {s} ({S.attack['tech'].get(s, {}).get('name', '?')}): {_fmt(ms)}"]
        if (o, s) in S.attack["rel_ids"]:
            ev.append(f"relationship {S.attack['rel_ids'][(o, s)]}: {o} mitigates {s}")
    elif sub == "claim_mapped_control":
        cs = S.ctid.get("r5", {}).get(s, set())
        exp, src = claim(o in cs), ["CTID mapping r5"]
        ev = [f"CTID Rev. 5 mapping for {s}: {_fmt(cs)}"]
    elif sub in ("attack_mitigation", "injected_mitigation", "benign_mitigation", "version_drift"):
        ms = S.mitigations(focus)
        exp, src = _fmt(ms), ["MITRE ATT&CK (current)"]
        ev = [f"ATT&CK current lists for {focus}: {_fmt(ms)}"]
        if sub == "version_drift" and S.attack_old:
            src.append("MITRE ATT&CK (older)")
            ev.append(f"ATT&CK v{S.attack_old['version']} listed: {_fmt(S.mitigations(focus, old=True))}")
        if m.get("injected_ids"):
            ev.append(f"injected IDs {_fmt(m['injected_ids'])} in ATT&CK? "
                      f"{'YES (!)' if set(m['injected_ids']) & ms else 'no'}")
    elif sub in ("nist_control", "injected_control", "rev4_rev5"):
        c5 = S.ctid.get("r5", {}).get(focus, set())
        exp, src = _fmt(c5), ["CTID mapping r5"]
        ev = [f"CTID Rev. 5 mapping for {focus}: {_fmt(c5)}"]
        if sub == "rev4_rev5":
            ev.append(f"CTID Rev. 4 mapping: {_fmt(S.ctid.get('r4', {}).get(focus, set()))}")
    elif sub == "claim_has_weakness":
        v = S.cwes(s)
        allw = set().union(*v.values()) if v else set()
        exp, src = claim(o in allw), list(v) or ["CISA KEV", "NVD (API 2.0 records)"]
        ev = [f"{k} records for {s}: {_fmt(x)}" for k, x in v.items()]
    elif sub in ("cve_cwe", "nvd_kev"):
        v = S.cwes(focus)
        exp = _fmt(set().union(*v.values())) if v else "(none)"
        src = list(v)
        ev = [f"{k} records for {focus}: {_fmt(x)}" for k, x in v.items()]
        disagree = len({frozenset(x) for x in v.values()}) > 1
        ev.append(f"sources disagree: {'YES' if disagree else 'no'} (expected {'YES' if sub == 'nvd_kev' else 'no'})")
        if (sub == "nvd_kev") != disagree:
            exp += " [conflict status differs]"
    elif sub == "claim_maps_to_attack":
        ts = {t for t in S.capec.get(s, {}).get("attack", set()) if S.attack["tech"].get(t, {}).get("status") == "active"}
        exp, src = claim(o in ts), ["MITRE CAPEC"]
        ev = [f"CAPEC {s} ATTACK references (active techniques): {_fmt(ts)}"]
    elif sub == "capec_technique":
        ts = {t for t in S.capec.get(focus, {}).get("attack", set()) if S.attack["tech"].get(t, {}).get("status") == "active"}
        exp, src = _fmt(ts), ["MITRE CAPEC"]
        ev = [f"CAPEC {focus} ATTACK references (active techniques): {_fmt(ts)}"]
    elif sub == "cve_capec":
        v = S.cwes(focus)
        ws = set().union(*v.values()) if v else set()
        caps = set().union(*(S.capecs_of_cwe(w) for w in ws)) if ws else set()
        exp, src = _fmt(caps), list(v) + ["MITRE CWE", "MITRE CAPEC"]
        ev = [f"CWEs of {focus}: {_fmt(ws)}"] + [f"{w} -> {_fmt(S.capecs_of_cwe(w))}" for w in sorted(ws)]
        links += [url_of(w) for w in sorted(ws)]
    elif sub == "revoked":
        cur = S.resolve(focus)
        ms = S.mitigations(cur)
        exp, src = _fmt(ms), ["MITRE ATT&CK (current)"]
        ev = [f"{focus} status in current ATT&CK: {S.attack['tech'].get(focus, {}).get('status')}; "
              f"revoked-by -> {cur}", f"ATT&CK lists for {cur}: {_fmt(ms)}"]
        links.append(url_of(cur))
    elif sub == "withdrawn":
        n = S.nist.get(focus, {})
        exp, src = _fmt(n.get("into", set())), ["NIST SP 800-53 Rev. 5"]
        ev = [f"{focus} withdrawn in Rev. 5: {n.get('withdrawn')}; incorporated into / moved to: {_fmt(n.get('into'))}"]
    elif sub in ("claim_nei", "unknown_technique", "unknown_cve"):
        unknown = [i for i in ids if not S.known(i)]
        exp = ("NOT_ENOUGH_INFO" if sub == "claim_nei" else "(abstain)") if unknown else "identifier exists (!)"
        src = ["all sources"]
        ev = [f"identifiers absent from every frozen source: {_fmt(unknown)}"]
    elif sub == "no_mitigation":
        a, b = S.mitigations(focus), S.mitigations(focus, old=True)
        exp = "(abstain)" if not a and not b else _fmt(a | b)
        src = ["MITRE ATT&CK (current)", "MITRE ATT&CK (older)"]
        ev = [f"ATT&CK mitigations for {focus}: current {_fmt(a)}, older {_fmt(b)}"]
    elif sub == "no_control_mapping":
        a, b = S.ctid.get("r5", {}).get(focus, set()), S.ctid.get("r4", {}).get(focus, set())
        exp = "(abstain)" if not a and not b else _fmt(a | b)
        src = ["CTID mapping r5", "CTID mapping r4"]
        ev = [f"CTID mappings for {focus}: Rev. 5 {_fmt(a)}, Rev. 4 {_fmt(b)}"]
    else:
        exp = "not verified (unknown family)"
    if m.get("note_doc"):
        ev.append(f"injected/agreeing note {m['note_doc']} is synthetic (low authority) and not a gold source")
    out["expected_from_source"] = exp
    out["status"] = "MATCH" if exp == out["gold"] else "MISMATCH"
    out["sources"] = "; ".join(dict.fromkeys(src))
    out["source_versions"] = " || ".join(f"{k}: {S.info[k]}" for k in dict.fromkeys(src) if k in S.info)
    out["raw_evidence"] = " | ".join(ev)
    out["official_pages"] = " ".join(dict.fromkeys(x for x in links if x))
    return out


def verify_all(questions: list[dict], raw_dir: Path, out_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, RawSources]:
    S = RawSources(raw_dir)
    rows = [verify_question(q, S) for q in questions]
    df = pd.DataFrame(rows)
    summ = df.groupby(["category", "subtype"]).status.value_counts().unstack(fill_value=0)
    for c in ("MATCH", "MISMATCH"):
        if c not in summ:
            summ[c] = 0
    summ["match_%"] = (summ["MATCH"] / summ[["MATCH", "MISMATCH"]].sum(1) * 100).round(1)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "gold_source_verification.csv", index=False)
    summ.to_csv(out_dir / "gold_source_verification_summary.csv")
    pd.DataFrame([{"source": k, "frozen snapshot": v} for k, v in S.info.items()]).to_csv(
        out_dir / "frozen_source_versions.csv", index=False)
    # blind helper for the human annotators: raw records and links, but no MATCH/expected column
    df[["qid", "sources", "source_versions", "raw_evidence", "official_pages"]].to_csv(
        out_dir / "annotation_source_records.csv", index=False)
    return df, summ, S
