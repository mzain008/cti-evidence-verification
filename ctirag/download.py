"""Download raw sources with mirrors, caching and a polite NVD client."""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

from .config import SOURCES, NVD_API, Config

UA = {"User-Agent": "cti-evidence-rag/1.0 (research)"}


def _get(url: str, timeout: int = 120, headers: dict | None = None) -> bytes:
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_source(name: str, cfg: Config, force: bool = False) -> Path | None:
    """Download one named source to raw_dir. Returns the path or None if all mirrors fail."""
    cfg.ensure()
    ext = ".zip" if name == "cwe" else (".tsv" if name.startswith("ctibench") else ".json")
    out = cfg.raw_dir / f"{name}{ext}"
    if out.exists() and out.stat().st_size > 0 and not force:
        return out
    for url in SOURCES[name]:
        try:
            data = _get(url)
            out.write_bytes(data)
            print(f"[download] {name}: {len(data)/1e6:.1f} MB from {url}")
            return out
        except Exception as e:  # noqa: BLE001
            print(f"[download] {name}: failed {url} ({e.__class__.__name__}: {e})")
    return None


def fetch_all(cfg: Config, force: bool = False) -> dict[str, Path | None]:
    return {name: fetch_source(name, cfg, force) for name in SOURCES}


def fetch_nvd(cve_ids: list[str], cfg: Config) -> dict[str, dict]:
    """Fetch NVD 2.0 records for the given CVEs, cached line-by-line (resumable).

    Without an API key NVD allows ~5 requests / 30 s, with a key ~50 / 30 s.
    """
    cache = cfg.raw_dir / "nvd_cache.jsonl"
    have: dict[str, dict] = {}
    if cache.exists():
        for line in cache.read_text().splitlines():
            if line.strip():
                rec = json.loads(line)
                have[rec["id"]] = rec
    todo = [c for c in cve_ids if c not in have][: max(0, cfg.nvd_max_cves - len(have))]
    if not todo:
        return have
    delay = 0.7 if cfg.nvd_api_key else 6.2
    headers = {"apiKey": cfg.nvd_api_key} if cfg.nvd_api_key else {}
    print(f"[nvd] fetching {len(todo)} CVEs (~{len(todo)*delay/60:.0f} min). Resumable.")
    with cache.open("a") as fh:
        for i, cid in enumerate(todo):
            for attempt in range(4):
                try:
                    raw = json.loads(_get(f"{NVD_API}?cveId={cid}", timeout=60, headers=headers))
                    vulns = raw.get("vulnerabilities", [])
                    rec = vulns[0]["cve"] if vulns else {"id": cid, "missing": True}
                    rec["id"] = cid
                    have[cid] = rec
                    fh.write(json.dumps(rec) + "\n")
                    fh.flush()
                    break
                except Exception as e:  # noqa: BLE001
                    wait = delay * (2 ** attempt) + 2
                    print(f"[nvd] {cid} attempt {attempt+1} failed ({e}); sleeping {wait:.0f}s")
                    time.sleep(wait)
            time.sleep(delay)
            if (i + 1) % 100 == 0:
                print(f"[nvd] {i+1}/{len(todo)}")
    return have
