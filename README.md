# Evidence-aware verification for cyber threat intelligence: agentic vs non-agentic RAG

Code, frozen benchmarks, validation material and system outputs for the paper

> Z. Farooq, *Reliable Cyber Threat Intelligence through Evidence-Aware Verification: A Comparative Study of Agentic and Non-Agentic RAG*, submitted to *Cyber Security and Applications*.

The study compares an LLM-controlled evidence-aware agent (C) with a non-agentic verifier (B) that applies the same deterministic lifecycle, temporal, conflict and typed-path checks, plus a ReAct agent (A), four RAG baselines (Naive, KG-RAG, multi-hop, CRAG), a graph oracle and five ablations. The models are Qwen2.5-7B-Instruct and Llama-3.1-8B-Instruct, served with Ollama on one NVIDIA T4 GPU.

## Repository layout

| Path | Contents |
|---|---|
| `CTI_Evidence_RAG_Colab_v6_2.ipynb` | Colab notebook: installs the frozen agent code (v4), builds and freezes the final benchmark, runs all systems, the timing run, the report (Tables 1–6, Figures 1–3), gold-answer source verification and the human-validation summary |
| `ctirag/systems.py` | All systems: baselines, ReAct (A), non-agentic verifier (B), evidence-aware agent (C) and the ablations; `AGENT_VERSION = "v4"` |
| `ctirag/final_bench.py` | Deterministic generator of the final benchmark |
| `ctirag/final_eval.py` | Scoring, conflict trace, tables, significance tests (McNemar, permutation, Holm), bootstrap CIs and figures |
| `ctirag/verify_gold.py` | Re-derives every gold answer from the frozen raw files with independent parsers |
| `ctirag/` (other modules) | `config`, `corpus`, `index`, `llm`, `runner`, `benchmark`, `evaluate`, `annotate` |
| `data/` | Frozen benchmarks and injected notes with their `*_FROZEN_info.json` checksum files |
| `results/` | System outputs (`*.jsonl`) and report folders (CSV, Markdown, PNG) |
| `validation/Validation_completed.xlsx` | Completed human validation of a 50-question sample (one annotator) |

### Frozen files and checksums

| File | MD5 |
|---|---|
| Final benchmark (275 questions) `final_questions_FROZEN.jsonl` | `c414b59e48c8072275c57b34f0783898` |
| Second draw (seed 2028, 258 questions) | `63985e99…` (full value in its info file) |
| `ctirag/systems.py` (agent v4) | `e76d4ad373c8f099d2622e7f83caa23c` |
| `ctirag/final_bench.py` | `a73c96beec5f2ae7392887cd45c18801` |
| `ctirag/final_eval.py` | `d7f40e92f4d55180ff21dea2157337ce` |
| `ctirag/verify_gold.py` | `5c981874fd44203a1d9b832a9c5fa5df` |

The notebook refuses to run the final evaluation if the agent code differs from the checksums stored when the benchmark was built. For that reason the code files have not been edited after freezing. One docstring in `final_eval.py` still calls the conflict chart "Figure 2"; in the paper it is Figure 3, and the notebook now saves it as `fig3_conflict_prf.png`.

## Raw sources (frozen snapshots)

MITRE ATT&CK Enterprise STIX (2026-08-04) and v8.2, MITRE CAPEC, MITRE CWE v4.20, CISA KEV 2026.10.08, 1,000 NVD API 2.0 records for KEV vulnerabilities, NIST SP 800-53 Rev. 5 (OSCAL 5.2.0), and the CTID ATT&CK-to-SP 800-53 mappings (Rev. 5 and Rev. 4). Exact file names, versions and checksums are in `results/final/frozen_source_versions.csv`. The raw files are public and can be downloaded from MITRE, NIST, NVD, CISA and CTID.

## Validation of the gold answers

* **Programmatic.** All 275 gold answers were re-derived from the frozen raw files (`ctirag/verify_gold.py`; notebook section 14c) and all 275 matched. The same holds for the 258 answers of the second draw.
* **Human.** A stratified sample of 50 questions was checked by one annotator with a cyber-security background who did not build the benchmark. The annotator judged 49 of 50 gold answers correct (98.0%, Wilson 95% CI [89.5, 99.6]), found all 50 questions clear, and confirmed all 14 notes as labelled. There was one annotator, so no inter-annotator agreement is reported. The one disagreement (T1578.005, SP 800-53 mappings) is discussed in Section 3.4.1 of the paper. The benchmark was not edited after freezing.

## Reproducing the results

1. Copy the repository to Google Drive and open the notebook in Colab with a T4 GPU.
2. Follow the run plan at the top of the notebook. Run cells one by one with ▶ rather than *Run all*. Every run cell can be resumed.
3. Sections 13 and 14 (tables, figures, validation summary) need only a CPU.

## License

Code: MIT (see `LICENSE`). Benchmark questions derived from MITRE, NIST, NVD and CISA data follow the terms of those sources.
