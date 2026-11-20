"""Central configuration: data-source URLs, paths and experiment settings."""
from __future__ import annotations

import os
from dataclasses import dataclass, field, asdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Data sources (all public). Primary URL first, mirrors after it.
# ---------------------------------------------------------------------------
SOURCES = {
    "attack": [
        "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json",
        "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json",
    ],
    # A real older ATT&CK release, loaded as an outdated snapshot of the same source (v8.2, Jan 2021).
    "attack_old": [
        "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack-8.2.json",
    ],
    # CTIBench (Alam et al., NeurIPS 2024 D&B): text-only tasks used as external, human-curated questions.
    "ctibench_ate": [
        "https://raw.githubusercontent.com/xashru/cti-bench/main/data/cti-ate.tsv",
    ],
    "ctibench_rcm": [
        "https://raw.githubusercontent.com/xashru/cti-bench/main/data/cti-rcm.tsv",
    ],
    "capec": [
        "https://raw.githubusercontent.com/mitre/cti/master/capec/2.1/stix-capec.json",
    ],
    "cwe": [
        "https://cwe.mitre.org/data/xml/cwec_latest.xml.zip",
    ],
    "kev": [
        "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
        "https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json",
    ],
    "sp80053_r5": [
        "https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json",
    ],
    # Center for Threat-Informed Defense ATT&CK -> NIST 800-53 mappings.
    # rev5 mapping (ATT&CK v12.1) is the "current" mapping; rev4 (ATT&CK v10.1)
    # is kept on purpose as an older, partly outdated source.
    "ctid_r5_map": [
        "https://raw.githubusercontent.com/center-for-threat-informed-defense/attack-control-framework-mappings/main/frameworks/attack_12_1/nist800_53_r5/stix/nist800-53-r5-mappings.json",
    ],
    "ctid_r5_ctl": [
        "https://raw.githubusercontent.com/center-for-threat-informed-defense/attack-control-framework-mappings/main/frameworks/attack_12_1/nist800_53_r5/stix/nist800-53-r5-controls.json",
    ],
    "ctid_r4_map": [
        "https://raw.githubusercontent.com/center-for-threat-informed-defense/attack-control-framework-mappings/main/frameworks/attack_10_1/nist800_53_r4/stix/nist800-53-r4-mappings.json",
    ],
    "ctid_r4_ctl": [
        "https://raw.githubusercontent.com/center-for-threat-informed-defense/attack-control-framework-mappings/main/frameworks/attack_10_1/nist800_53_r4/stix/nist800-53-r4-controls.json",
    ],
}
NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"

# Authority tiers used by the evidence-aware agent's conflict resolver.
# Higher = more authoritative for the relation the source owns.
AUTHORITY = {
    "MITRE ATT&CK": 3,
    "MITRE CWE": 3,
    "MITRE CAPEC": 3,
    "NIST SP 800-53": 3,
    "NVD": 3,
    "CISA KEV": 3,
    "CTID Mapping": 2,
    # Low-authority sources, used only by the optional injected-conflict stress test.
    "Community Note": 1,
    "Vendor Blog": 1,
    "Security Forum": 1,
    "Analyst Wiki": 1,
}

# Groq models in order of preference; the first one the account can see is used.
# Groq retired several Llama SKUs for free/dev tiers in 2026, so we check live.
GROQ_MODEL_PREFERENCE = [
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]


@dataclass
class Config:
    work_dir: str = os.environ.get("CTIRAG_WORK", "./work")
    # --- corpus ---
    nvd_enrich: bool = True            # call NVD API for KEV CVEs (needs network)
    nvd_api_key: str | None = os.environ.get("NVD_API_KEY")
    nvd_max_cves: int = 2000
    inject_conflicts: bool = False     # optional stress test: inject low-authority contradicting notes
    n_poisoned: int = 40               # used only when inject_conflicts=True
    # --- retrieval ---
    dense_model: str | None = "BAAI/bge-small-en-v1.5"  # None -> TF-IDF fallback
    top_k: int = 8
    # --- benchmark sizes (paper scale defaults) ---
    # Text track: needs language understanding; a graph lookup cannot answer these.
    n_tech_id: int = 120               # held-out ATT&CK procedure -> technique
    n_ctibench_ate: int = 60           # CTIBench CTI-ATE, Enterprise rows (47 available), report -> techniques
    n_ctibench_rcm: int = 200          # CTIBench CTI-RCM, CVE description -> CWE
    n_attribution: int = 60            # anonymised procedures -> threat group
    n_claims_text: int = 120           # behaviour claims + name-only claims
    # Evidence track: structured lookups, conflicts and outdated sources (graph oracle is reported here).
    n_mitigation: int = 100
    n_claims_id: int = 100
    n_temporal: int = 120              # revoked, withdrawn, rev4_rev5, version_drift, nvd_kev
    # Optional structural track (CAPEC chains are noisy - off by default, see README).
    n_cve_to_tech: int = 0
    n_full_chain: int = 0
    seed: int = 13
    # --- LLM ---
    llm_provider: str = "groq"         # "groq" | "mock"
    llm_model: str | None = None       # None -> pick from GROQ_MODEL_PREFERENCE
    temperature: float = 0.0
    repeat: int = 0                    # repeat index; part of the cache key so repeats are real re-runs
    max_tokens: int = 1024
    requests_per_minute: int = 25
    # --- agent ---
    max_agent_steps: int = 8
    max_hops: int = 4
    systems: list[str] = field(default_factory=lambda: [
        "graph_oracle", "naive", "kg_rag", "multihop", "crag", "react_agent", "evidence_agent",
        "agent_no_temporal", "agent_no_graph", "agent_no_authority",
    ])

    @property
    def raw_dir(self) -> Path:
        return Path(self.work_dir) / "raw"

    @property
    def proc_dir(self) -> Path:
        return Path(self.work_dir) / "processed"

    @property
    def run_dir(self) -> Path:
        return Path(self.work_dir) / "runs"

    def ensure(self) -> "Config":
        for p in (self.raw_dir, self.proc_dir, self.run_dir):
            p.mkdir(parents=True, exist_ok=True)
        return self

    def to_dict(self):
        d = asdict(self)
        d.pop("nvd_api_key", None)
        return d
