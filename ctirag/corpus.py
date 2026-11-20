"""Parse the raw sources into one document corpus plus a provenance-tracked link graph.

Every document carries metadata the evidence-aware agent relies on:
source, authority tier, date, version and lifecycle status
(active / revoked / deprecated / withdrawn / rejected / superseded).
Every link (subject, relation, object) remembers which document asserted it,
so structural verification is always backed by a citable document.
"""
from __future__ import annotations

import io
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path

from .config import AUTHORITY, Config

# ---------------------------------------------------------------------------
# ID helpers
# ---------------------------------------------------------------------------
ID_PATTERNS = {
    "technique": re.compile(r"\bT\d{4}(?:\.\d{3})?\b"),
    "mitigation": re.compile(r"\bM\d{4}\b"),
    "group": re.compile(r"\bG\d{4}\b"),
    "capec": re.compile(r"\bCAPEC-\d+\b", re.I),
    "cwe": re.compile(r"\bCWE-\d+\b", re.I),
    "cve": re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.I),
    "control": re.compile(r"\b(?:AC|AT|AU|CA|CM|CP|IA|IR|MA|MP|PE|PL|PM|PS|PT|RA|SA|SC|SI|SR)-\d{1,2}(?:\s?\(\d{1,2}\))?(?![\d(])"),
}


def norm_id(x: str) -> str:
    x = x.strip().upper().replace(" ", "")
    return x


def extract_ids(text: str, kinds: tuple[str, ...] | None = None) -> list[str]:
    """Extract normalized security identifiers from free text, in order, de-duplicated."""
    out, seen = [], set()
    for kind, pat in ID_PATTERNS.items():
        if kinds and kind not in kinds:
            continue
        for m in pat.finditer(text or ""):
            i = norm_id(m.group(0))
            if i not in seen:
                seen.add(i)
                out.append(i)
    return out


def id_kind(i: str) -> str | None:
    for kind, pat in ID_PATTERNS.items():
        if pat.fullmatch(i):
            return kind
    return None


def oscal_to_control(cid: str) -> str:
    """'ac-2.10' -> 'AC-2(10)', 'ac-2' -> 'AC-2'."""
    cid = cid.lstrip("#").split("_")[0]
    m = re.match(r"([a-z]{2})-(\d+)(?:\.(\d+))?", cid)
    if not m:
        return cid.upper()
    fam, num, enh = m.groups()
    return f"{fam.upper()}-{int(num)}" + (f"({int(enh)})" if enh else "")


_CIT = re.compile(r"\(Citation:[^)]*\)")
_MDLINK = re.compile(r"\[([^\]]+)\]\((?:https?://)[^)]+\)")
_TAG = re.compile(r"<[^>]+>")


def clean(t: str | None) -> str:
    t = t or ""
    t = _CIT.sub("", t)
    t = _MDLINK.sub(r"\1", t)
    t = _TAG.sub(" ", t)
    return re.sub(r"\s+", " ", t).strip()


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
INVERSE = {
    "mitigated_by": "mitigates",
    "mitigates": "mitigated_by",
    "subtechnique_of": "has_subtechnique",
    "has_subtechnique": "subtechnique_of",
    "revoked_by": "revokes",
    "revokes": "revoked_by",
    "maps_to_attack": "attack_mapped_from_capec",
    "attack_mapped_from_capec": "maps_to_attack",
    "related_weakness": "related_attack_pattern",
    "related_attack_pattern": "related_weakness",
    "has_weakness": "weakness_of",
    "weakness_of": "has_weakness",
    "mapped_control": "control_mapped_to",
    "control_mapped_to": "mapped_control",
    "child_of": "parent_of",
    "parent_of": "child_of",
    "incorporated_into": "incorporates",
    "incorporates": "incorporated_into",
    "uses": "used_by",
    "used_by": "uses",
}


@dataclass
class Doc:
    doc_id: str
    source: str
    entity_id: str
    entity_type: str
    title: str
    text: str
    date: str = ""
    version: str = ""
    status: str = "active"
    links: list = field(default_factory=list)  # [(relation, target_entity_id)]
    meta: dict = field(default_factory=dict)

    @property
    def authority(self) -> int:
        return AUTHORITY.get(self.source, 1)

    @property
    def snapshot(self) -> str:
        """Release date of the dataset snapshot this doc comes from (falls back to the doc date)."""
        return self.meta.get("release_date") or self.date

    def header(self) -> str:
        """Metadata line shown to LLMs next to every evidence passage."""
        return (f"[{self.doc_id}] source={self.source} (authority {self.authority}) "
                f"date={self.date or 'n/a'} version={self.version or 'n/a'} status={self.status}")

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @staticmethod
    def from_json(s: str) -> "Doc":
        d = json.loads(s)
        d["links"] = [tuple(x) for x in d.get("links", [])]
        return Doc(**d)


class Corpus:
    def __init__(self, docs: list[Doc]):
        self.docs: dict[str, Doc] = {}
        self.by_entity: dict[str, list[str]] = defaultdict(list)
        # edges[subject] -> list of (relation, object, doc_id)
        self.edges: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
        self._latest: dict[tuple[str, str], str] | None = None
        for d in docs:
            self.add(d)

    def add(self, d: Doc):
        if d.doc_id in self.docs:
            return
        self.docs[d.doc_id] = d
        self._latest = None
        self.by_entity[d.entity_id].append(d.doc_id)
        for rel, tgt in d.links:
            self.edges[d.entity_id].append((rel, tgt, d.doc_id))
            inv = INVERSE.get(rel)
            if inv:
                self.edges[tgt].append((inv, d.entity_id, d.doc_id))

    def __len__(self):
        return len(self.docs)

    def entity_docs(self, eid: str) -> list[Doc]:
        return [self.docs[i] for i in self.by_entity.get(norm_id(eid), [])]

    def neighbors(self, eid: str, relation: str | None = None, min_authority: int = 0):
        eid = norm_id(eid)
        out = []
        for rel, tgt, did in self.edges.get(eid, []):
            if relation and rel != relation:
                continue
            if self.docs[did].authority < min_authority:
                continue
            out.append((rel, tgt, did))
        return out

    def link_support(self, subj: str, rel: str, obj: str) -> list[str]:
        """Doc ids that assert subj-rel->obj (directly or via inverse)."""
        subj, obj = norm_id(subj), norm_id(obj)
        return sorted({did for r, t, did in self.edges.get(subj, []) if r == rel and t == obj})

    def is_latest(self, doc_id: str) -> bool:
        """True if no newer snapshot of the same source describes the same entity.

        This is the only recency rule: an older ATT&CK release, the Rev. 4 CTID mapping, etc. lose
        to a newer document *from the same source*. Different sources are never ranked by date.
        """
        if self._latest is None:
            best: dict[tuple[str, str], str] = {}
            for d in self.docs.values():
                k = (d.entity_id, d.source)
                if d.snapshot > best.get(k, ""):
                    best[k] = d.snapshot
            self._latest = best
        d = self.docs[doc_id]
        return d.snapshot >= self._latest.get((d.entity_id, d.source), "")

    def current_neighbors(self, eid: str, relation: str | None = None, min_authority: int = 2):
        """Neighbors asserted by the latest snapshot of a source with at least `min_authority`."""
        return [(r, t, d) for r, t, d in self.neighbors(eid, relation, min_authority) if self.is_latest(d)]

    def status_of(self, eid: str) -> str:
        """Lifecycle status from the latest snapshot of authoritative (>=2) sources."""
        ds = [d for d in self.entity_docs(eid) if d.authority >= 2 and self.is_latest(d.doc_id)]
        if not ds:
            return "unknown"
        ds.sort(key=lambda d: (d.authority, d.snapshot), reverse=True)
        for d in ds:
            if d.status in ("revoked", "deprecated", "withdrawn", "rejected"):
                return d.status
        return ds[0].status

    def save(self, path: Path):
        with Path(path).open("w") as fh:
            for d in self.docs.values():
                fh.write(d.to_json() + "\n")

    @staticmethod
    def load(*paths: Path) -> "Corpus":
        docs = []
        for p in paths:
            if Path(p).exists():
                docs += [Doc.from_json(l) for l in Path(p).read_text().splitlines() if l.strip()]
        return Corpus(docs)


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------
def _ext_id(obj: dict, source_names=("mitre-attack",)) -> str | None:
    for r in obj.get("external_references", []):
        if r.get("source_name") in source_names and r.get("external_id"):
            return r["external_id"]
    return None


def parse_attack(path: Path, prefix: str = "attack", release: str | None = None, include_groups: bool = True):
    """Returns (docs, procedures, stix_to_ext, names). Procedures are held out of the corpus.

    `prefix`/`release` let an older ATT&CK release (e.g. v8.2) be loaded next to the current one as a
    genuinely older snapshot of the same source.
    """
    objs = json.loads(Path(path).read_text())["objects"]
    release_date = max((o.get("modified") or "")[:10] for o in objs)
    coll = [o for o in objs if o["type"] == "x-mitre-collection"]
    release = release or (f"ATT&CK v{coll[0].get('x_mitre_version')}" if coll else f"ATT&CK release {release_date}")
    by_id = {o["id"]: o for o in objs}
    stix2ext = {}
    for o in objs:
        e = _ext_id(o)
        if e:
            stix2ext[o["id"]] = e
    mit_of = defaultdict(list)      # technique -> [M]
    sub_of = {}
    revoked_by = {}
    uses = defaultdict(list)        # group -> [T]
    procedures = []
    for o in objs:
        if o["type"] != "relationship" or o.get("revoked") or o.get("x_mitre_deprecated"):
            continue
        s, t, rt = o["source_ref"], o["target_ref"], o["relationship_type"]
        if s not in stix2ext or t not in stix2ext:
            continue
        if rt == "mitigates" and by_id[s]["type"] == "course-of-action":
            if not by_id[s].get("x_mitre_deprecated"):
                mit_of[stix2ext[t]].append(stix2ext[s])
        elif rt == "subtechnique-of":
            sub_of[stix2ext[s]] = stix2ext[t]
        elif rt == "revoked-by":
            revoked_by[stix2ext[s]] = stix2ext[t]
        elif rt == "uses" and by_id[t]["type"] == "attack-pattern":
            if by_id[s]["type"] == "intrusion-set":
                uses[stix2ext[s]].append(stix2ext[t])
            desc = clean(o.get("description"))
            if desc and len(desc) > 60:
                procedures.append({
                    "actor_id": stix2ext[s], "actor_name": by_id[s].get("name", ""),
                    "actor_type": by_id[s]["type"], "technique": stix2ext[t],
                    "text": desc,
                })
    names = {stix2ext[o["id"]]: o.get("name", "") for o in objs if o["id"] in stix2ext}
    docs = []
    for o in objs:
        if o["id"] not in stix2ext:
            continue
        eid = stix2ext[o["id"]]
        date = (o.get("modified") or "")[:10]
        ver = f"{release} (object v{o.get('x_mitre_version', '?')})"
        rmeta = {"release_date": release_date, "release": release}
        status = "revoked" if o.get("revoked") else ("deprecated" if o.get("x_mitre_deprecated") else "active")
        if o["type"] == "attack-pattern":
            tactics = [p["phase_name"] for p in o.get("kill_chain_phases", [])]
            links = [("mitigated_by", m) for m in sorted(set(mit_of.get(eid, [])))]
            if eid in sub_of:
                links.append(("subtechnique_of", sub_of[eid]))
            text = f"{eid} {o.get('name','')}. "
            if status == "revoked":
                rb = revoked_by.get(eid)
                if rb:
                    links.append(("revoked_by", rb))
                text += (f"This ATT&CK technique has been REVOKED and replaced by {rb} "
                         f"{names.get(rb,'')}. " if rb else "This technique has been REVOKED. ")
            elif status == "deprecated":
                text += "This ATT&CK technique is DEPRECATED and should no longer be used. "
            if eid in sub_of:
                text += f"Sub-technique of {sub_of[eid]} {names.get(sub_of[eid],'')}. "
            if tactics:
                text += f"Tactics: {', '.join(tactics)}. "
            if o.get("x_mitre_platforms"):
                text += f"Platforms: {', '.join(o['x_mitre_platforms'])}. "
            text += clean(o.get("description"))
            ms = sorted(set(mit_of.get(eid, [])))
            if ms:
                text += " Mitigations: " + "; ".join(f"{m} {names.get(m,'')}" for m in ms) + "."
            docs.append(Doc(f"{prefix}:{eid}", "MITRE ATT&CK", eid, "technique",
                            f"{eid} {o.get('name','')}", text, date, ver, status, links,
                            {"tactics": tactics, "name": o.get("name", ""), **rmeta}))
        elif o["type"] == "course-of-action":
            if not re.fullmatch(r"M\d{4}", eid):  # pre-2020 1:1 mitigations reuse T-ids
                continue
            tgts = sorted({t for t, ms in mit_of.items() if eid in ms})
            text = f"{eid} {o.get('name','')} (ATT&CK mitigation). {clean(o.get('description'))}"
            if status != "active":
                text = f"{eid} {o.get('name','')} — this ATT&CK mitigation is {status.upper()}. " + text
            if tgts:
                text += " Mitigates: " + ", ".join(tgts[:80]) + ("..." if len(tgts) > 80 else "")
            docs.append(Doc(f"{prefix}:{eid}", "MITRE ATT&CK", eid, "mitigation",
                            f"{eid} {o.get('name','')}", text, date, ver, status,
                            [("mitigates", t) for t in tgts], {"name": o.get("name", ""), **rmeta}))
        elif o["type"] == "intrusion-set" and include_groups:
            ts = sorted(set(uses.get(eid, [])))
            text = f"{eid} {o.get('name','')} (threat group). Aliases: {', '.join(o.get('aliases', []))}. " \
                   f"{clean(o.get('description'))}"
            if ts:
                text += " Techniques used: " + ", ".join(ts) + "."
            docs.append(Doc(f"{prefix}:{eid}", "MITRE ATT&CK", eid, "group",
                            f"{eid} {o.get('name','')}", text, date, ver, status,
                            [("uses", t) for t in ts],
                            {"name": o.get("name", ""), "aliases": o.get("aliases", []), **rmeta}))
    return docs, procedures, stix2ext, names


def parse_capec(path: Path) -> list[Doc]:
    objs = json.loads(Path(path).read_text())["objects"]
    docs = []
    for o in objs:
        if o["type"] != "attack-pattern":
            continue
        cid = _ext_id(o, ("capec",))
        if not cid:
            continue
        cwes = sorted({r["external_id"].upper() for r in o.get("external_references", [])
                       if r.get("source_name") == "cwe" and r.get("external_id")})
        atk = sorted({"T" + r["external_id"].lstrip("T") for r in o.get("external_references", [])
                      if r.get("source_name") == "ATTACK" and r.get("external_id")})
        status = "deprecated" if (o.get("x_capec_status") == "Deprecated" or o.get("revoked")) else "active"
        text = f"{cid} {o.get('name','')} (CAPEC attack pattern). {clean(o.get('description'))}"
        if cwes:
            text += " Related weaknesses: " + ", ".join(cwes) + "."
        if atk:
            text += " Related ATT&CK techniques: " + ", ".join(atk) + "."
        links = [("related_weakness", c) for c in cwes] + [("maps_to_attack", t) for t in atk]
        docs.append(Doc(f"capec:{cid}", "MITRE CAPEC", cid, "capec", f"{cid} {o.get('name','')}",
                        text, (o.get("modified") or "")[:10], o.get("x_capec_version", ""), status, links,
                        {"name": o.get("name", "")}))
    return docs


def parse_cwe(path: Path) -> list[Doc]:
    raw = Path(path).read_bytes()
    if raw[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            name = [n for n in z.namelist() if n.endswith(".xml")][0]
            raw = z.read(name)
    root = ET.fromstring(raw)
    version = root.attrib.get("Version", "")
    date = root.attrib.get("Date", "")
    docs = []

    def it(el, name):
        return (x for x in el.iter() if x.tag.split("}")[-1] == name)

    def txt(el):
        return clean(" ".join(el.itertext())) if el is not None else ""

    for w in root.iter():
        tag = w.tag.split("}")[-1]
        if tag not in ("Weakness", "Category"):
            continue
        cid = f"CWE-{w.attrib['ID']}"
        status = w.attrib.get("Status", "")
        st = "deprecated" if status in ("Deprecated", "Obsolete") else "active"
        desc = txt(w.find("{*}Description")) or txt(w.find("{*}Summary"))
        ext = txt(w.find("{*}Extended_Description"))
        links = []
        for rw in it(w, "Related_Weakness"):
            if rw.attrib.get("Nature") == "ChildOf":
                links.append(("child_of", f"CWE-{rw.attrib['CWE_ID']}"))
        for rap in it(w, "Related_Attack_Pattern"):
            links.append(("related_attack_pattern", f"CAPEC-{rap.attrib['CAPEC_ID']}"))
        mits = [txt(m.find("{*}Description")) for m in it(w, "Mitigation")][:3]
        kind = "weakness" if tag == "Weakness" else "category"
        text = f"{cid} {w.attrib.get('Name','')} (CWE {kind}). "
        if st != "active":
            text += f"This CWE entry is {status.upper()}. "
        text += f"{desc} {ext[:800]}"
        parents = [t for r, t in links if r == "child_of"]
        if parents:
            text += " Child of: " + ", ".join(parents) + "."
        caps = [t for r, t in links if r == "related_attack_pattern"]
        if caps:
            text += " Related attack patterns: " + ", ".join(caps) + "."
        if mits:
            text += " Potential mitigations: " + " | ".join(m[:300] for m in mits if m)
        docs.append(Doc(f"cwe:{cid}", "MITRE CWE", cid, "cwe", f"{cid} {w.attrib.get('Name','')}",
                        text.strip(), date, version, st, links, {"name": w.attrib.get("Name", "")}))
    return docs


def cwe_stubs_from_capec(capec_docs: list[Doc]) -> list[Doc]:
    """Fallback when cwe.mitre.org is unreachable: minimal CWE docs from CAPEC cross-refs."""
    rev = defaultdict(list)
    for d in capec_docs:
        for r, t in d.links:
            if r == "related_weakness":
                rev[t].append(d.entity_id)
    return [Doc(f"cwe:{c}", "MITRE CWE", c, "cwe", c,
                f"{c} (CWE weakness; full text unavailable). Related attack patterns: {', '.join(sorted(caps))}.",
                "", "stub", "active", [("related_attack_pattern", x) for x in sorted(caps)])
            for c, caps in rev.items()]


def parse_kev(path: Path) -> list[Doc]:
    k = json.loads(Path(path).read_text())
    docs = []
    for v in k["vulnerabilities"]:
        cid = v["cveID"].upper()
        cwes = sorted({c.upper() for c in v.get("cwes", []) if c.upper().startswith("CWE-")})
        text = (f"{cid} {v.get('vulnerabilityName','').strip()} — {v.get('vendorProject','')} "
                f"{v.get('product','')}. {v.get('shortDescription','')} "
                f"Added to CISA Known Exploited Vulnerabilities catalog on {v.get('dateAdded','')}. "
                f"Known ransomware campaign use: {v.get('knownRansomwareCampaignUse','Unknown')}. "
                f"Required action: {v.get('requiredAction','')[:300]}")
        if cwes:
            text += f" Weaknesses (CISA): {', '.join(cwes)}."
        docs.append(Doc(f"kev:{cid}", "CISA KEV", cid, "cve", f"{cid} {v.get('vulnerabilityName','').strip()}",
                        text, v.get("dateAdded", ""), k.get("catalogVersion", ""), "active",
                        [("has_weakness", c) for c in cwes],
                        {"vendor": v.get("vendorProject", ""), "product": v.get("product", ""),
                         "cwes": cwes, "ransomware": v.get("knownRansomwareCampaignUse", "")}))
    return docs


def parse_nvd(records: dict[str, dict]) -> list[Doc]:
    docs = []
    for cid, r in records.items():
        if r.get("missing"):
            continue
        desc = next((d["value"] for d in r.get("descriptions", []) if d.get("lang") == "en"), "")
        cwes, cwe_src = [], {}
        for w in r.get("weaknesses", []):
            for d in w.get("description", []):
                v = d.get("value", "").upper()
                if v.startswith("CWE-"):
                    cwes.append(v)
                    cwe_src.setdefault(v, []).append(f"{w.get('source','')}({w.get('type','')})")
        cwes = sorted(set(cwes))
        score = ""
        for key in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30"):
            m = r.get("metrics", {}).get(key)
            if m:
                score = f"CVSS {m[0]['cvssData'].get('version','')} base {m[0]['cvssData'].get('baseScore','')}"
                break
        vs = r.get("vulnStatus", "")
        status = "rejected" if vs.lower() == "rejected" else "active"
        text = f"{cid} (NVD record, status {vs}). {clean(desc)} {score}."
        if cwes:
            text += " Weaknesses (NVD): " + "; ".join(f"{c} [{', '.join(cwe_src[c])}]" for c in cwes) + "."
        text += f" Published {r.get('published','')[:10]}, last modified {r.get('lastModified','')[:10]}."
        docs.append(Doc(f"nvd:{cid}", "NVD", cid, "cve", cid, text, r.get("lastModified", "")[:10],
                        "", status, [("has_weakness", c) for c in cwes], {"cwes": cwes, "cwe_sources": cwe_src}))
    return docs


def parse_sp80053(path: Path) -> list[Doc]:
    cat = json.loads(Path(path).read_text())["catalog"]
    date = cat["metadata"].get("last-modified", "")[:10]
    version = cat["metadata"].get("version", "")
    docs = []

    def prose(parts, depth=0):
        out = []
        for p in parts or []:
            if p.get("prose"):
                out.append(p["prose"])
            out += prose(p.get("parts"), depth + 1)
        return out

    def walk(controls):
        for c in controls:
            cid = oscal_to_control(c["id"])
            status = "withdrawn" if any(p["name"] == "status" and p["value"] == "withdrawn"
                                        for p in c.get("props", [])) else "active"
            links = []
            for l in c.get("links", []):
                if l.get("rel") in ("incorporated-into", "moved-to"):
                    links.append(("incorporated_into", oscal_to_control(l["href"])))
            stmt = [p for p in c.get("parts", []) if p.get("name") == "statement"]
            guid = [p for p in c.get("parts", []) if p.get("name") == "guidance"]
            text = f"NIST SP 800-53 Rev. 5 control {cid} {c.get('title','')}. "
            if status == "withdrawn":
                tg = ", ".join(t for _, t in links) or "another control"
                text += f"This control has been WITHDRAWN and incorporated into {tg}. "
            text += clean(" ".join(prose(stmt)))
            g = clean(" ".join(prose(guid)))
            if g:
                text += " Discussion: " + g[:900]
            docs.append(Doc(f"nist:{cid}", "NIST SP 800-53", cid, "control", f"{cid} {c.get('title','')}",
                            text, date, f"Rev5 {version}", status, links, {"family": cid.split("-")[0]}))
            walk(c.get("controls", []))

    for g in cat["groups"]:
        walk(g.get("controls", []))
    return docs


def parse_ctid(map_path: Path, ctl_path: Path, stix2ext: dict, names: dict, rev: str) -> list[Doc]:
    rels = json.loads(Path(map_path).read_text())["objects"]
    ctls = json.loads(Path(ctl_path).read_text())["objects"]
    coa = {}
    for o in ctls:
        if o["type"] == "course-of-action":
            for r in o.get("external_references", []):
                if r.get("external_id"):
                    coa[o["id"]] = norm_id(r["external_id"])
    per_tech = defaultdict(set)
    for o in rels:
        if o["type"] == "relationship" and o["relationship_type"] == "mitigates":
            c, t = coa.get(o["source_ref"]), stix2ext.get(o["target_ref"])
            if c and t:
                per_tech[t].add(c)
    is_current = rev == "r5"
    attack_v = "ATT&CK v12.1" if is_current else "ATT&CK v10.1"
    date = "2023-06-14" if is_current else "2021-11-04"
    docs = []
    for t, cs in per_tech.items():
        cs = sorted(cs, key=lambda x: (x.split("-")[0], int(re.findall(r"\d+", x)[0]), x))
        rv = "Rev. 5" if is_current else "Rev. 4"
        text = (f"CTID mapping of {t} {names.get(t,'')} ({attack_v}) to NIST SP 800-53 {rv} "
                f"security controls: {', '.join(cs)}.")
        docs.append(Doc(f"ctid{rev[-1]}:{t}", "CTID Mapping", t, "mapping", f"{t} -> 800-53 {rv}", text,
                        date, f"{rv} / {attack_v}", "active",
                        [("mapped_control", c) for c in cs], {"rev": rev, "release_date": date}))
    return docs


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def holdout_cves(cfg: Config) -> set[str]:
    """CVEs used as text-only CTIBench RCM questions: their KEV/NVD records are removed from the corpus."""
    p = cfg.raw_dir / "ctibench_rcm.tsv"
    if not p.exists():
        return set()
    return {m.upper() for m in re.findall(r"CVE-\d{4}-\d{4,7}", p.read_text(), re.I)}


def build_corpus(cfg: Config, nvd_records: dict | None = None) -> tuple[Corpus, list[dict]]:
    raw = cfg.raw_dir
    docs: list[Doc] = []
    attack_docs, procedures, stix2ext, names = parse_attack(raw / "attack.json")
    docs += attack_docs
    if (raw / "attack_old.json").exists():
        # A real older ATT&CK release as an outdated snapshot of the same source (no groups: the
        # attribution questions must not see two copies of each group's technique list).
        old_docs, _, old_s2e, _ = parse_attack(raw / "attack_old.json", prefix="attack_old", include_groups=False)
        docs += old_docs
        stix2ext = {**old_s2e, **stix2ext}
    capec = parse_capec(raw / "capec.json")
    docs += capec
    if (raw / "cwe.zip").exists():
        docs += parse_cwe(raw / "cwe.zip")
    else:
        print("[corpus] CWE XML missing -> using CAPEC-derived CWE stubs")
        docs += cwe_stubs_from_capec(capec)
    held = holdout_cves(cfg)
    docs += [d for d in parse_kev(raw / "kev.json") if d.entity_id not in held]
    if nvd_records:
        docs += [d for d in parse_nvd(nvd_records) if d.entity_id not in held]
    docs += parse_sp80053(raw / "sp80053_r5.json")
    for rev in ("r5", "r4"):
        if (raw / f"ctid_{rev}_map.json").exists() and (raw / f"ctid_{rev}_ctl.json").exists():
            docs += parse_ctid(raw / f"ctid_{rev}_map.json", raw / f"ctid_{rev}_ctl.json", stix2ext, names, rev)
    corpus = Corpus(docs)
    corpus.save(cfg.proc_dir / "docs.jsonl")
    with (cfg.proc_dir / "procedures.jsonl").open("w") as fh:
        for p in procedures:
            fh.write(json.dumps(p) + "\n")
    stats = defaultdict(int)
    for d in corpus.docs.values():
        stats[f"{d.source}/{d.status}"] += 1
    print(f"[corpus] {len(corpus)} docs; held-out procedures: {len(procedures)}; held-out CVEs: {len(held)}")
    for k in sorted(stats):
        print(f"   {k:40s} {stats[k]}")
    return corpus, procedures
