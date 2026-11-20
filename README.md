# Evidence-aware verification for cyber threat intelligence: agentic vs non-agentic RAG

Code, frozen benchmarks, system outputs and validation material for the paper

> Z. Farooq, B. Jamil, H. Ijaz, *Reliable Cyber Threat Intelligence through Evidence-Aware Verification: A Comparative Study of Agentic and Non-Agentic RAG*, submitted to *Cyber Security and Applications*.

The study compares an evidence-aware agent (C), in which the LLM controls evidence gathering, with a non-agentic verifier (B) that applies the same deterministic lifecycle, temporal, conflict and typed-path checks to evidence from fixed retrieval and one-hop graph expansion. A ReAct agent (A), four RAG baselines (Naive, KG-RAG, multi-hop, CRAG), a graph oracle without an LLM and five ablations of C are the reference points. Models: Qwen2.5-7B-Instruct and Llama-3.1-8B-Instruct (Ollama, 4-bit Q4_K_M) on one NVIDIA T4 GPU, temperature 0.

## Repository layout

| Path | Contents |
|---|---|
| `CTI_Evidence_RAG_Colab_v6_2.ipynb` | Main Colab notebook for the final evaluation: installs the frozen agent code (v4), builds and freezes the final benchmark, runs all systems, the timing run, the report (Tables 1–6, Figures 1–3), the gold-answer source verification and the human-validation summary |
| `notebooks/CTI_Evidence_RAG_Colab.ipynb` | Earlier development notebook (corpus download and build, development benchmark, development runs). Use it only for those steps; it installs an older agent version |
| `ctirag/` | Python package. `systems.py` holds every system (baselines, A, B, C and the ablations; `AGENT_VERSION = "v4"`); `final_bench.py` the benchmark generator; `final_eval.py` scoring, statistics and figures; `verify_gold.py` the independent re-derivation of gold answers from the raw files; `corpus.py`, `download.py`, `index.py`, `llm.py`, `runner.py`, `benchmark.py`, `evaluate.py`, `annotate.py`, `report.py`, `config.py`, `cli.py` the corpus, retrieval, LLM and evaluation infrastructure |
| `data/` | Frozen question sets and injected notes (see below) |
| `results/runs/` | Raw system outputs, one `.jsonl` file per system with a `meta.json` per run |
| `results/reports/final/` | Tables, figures and per-question reports of the final evaluation |
| `validation/Validation_completed.xlsx` | Completed human validation of a 50-question sample (one annotator) |
| `tests/smoke_test.py` | Quick check that the package imports and runs |
| `requirements.txt` | Python dependencies |

### Frozen data (`data/`)

| File | What it is |
|---|---|
| `docs.jsonl` | The processed corpus: all 8,571 documents with source, authority tier, release date, version, lifecycle status and typed links |
| `procedures.jsonl` | ATT&CK procedure examples used by the development text track |
| `final_questions_FROZEN.jsonl` | Final benchmark, 275 questions (MD5 `c414b59e48c8072275c57b34f0783898`) |
| `final_notes_FROZEN.jsonl` | The 61 synthetic low-authority notes used by the final benchmark |
| `final_FROZEN_info.json` | Build information: seed, excluded entities, MD5 of the questions, notes and agent code at build time |
| `replicate2/final2_questions_FROZEN.jsonl` | Second benchmark draw, seed 2028, 258 questions with no focus entity shared with the final benchmark (MD5 starts `63985e99`); its notes and build information are in the same folder |
| `external_ctibench_qids.json` | Identifiers of the 126 CTIBench rows used for the external validation (100 CTI-RCM, 26 CTI-ATE). The CTIBench data itself is not redistributed; download it from the CTIBench authors |
| `questions_FROZEN.jsonl` | Development pool (866 questions); not used for the paper's main claims |
| `stress_questions_FROZEN.jsonl`, `stress_notes_FROZEN.jsonl` | Development stress test with 40 injected notes |

### System outputs (`results/runs/`)

| Folder | Paper section |
|---|---|
| `final/` | Final benchmark, all 13 systems, both models (Tables 2–5) |
| `final_timing/` | Uncached, sequential timing run on 40 questions, Qwen (Table 6) |
| `external_ctibench/` | External validation on 126 CTIBench questions: Naive RAG, A, B, C (Table 7) |
| `replicate2/` | Second benchmark draw, seed 2028, 258 questions: graph oracle, A, B, C (Table 8) |
| `stress/`, `stress_v4/` | Development stress test before and after explicit conflict detection (Section 6.1) |
| `main/`, `heldout/`, `pilot/`, `pilot_frozen/`, `timing/`, `MIGRATED_TO_v3/` | Development runs with earlier agent versions (Section 6.6); reported as supporting evidence only |

### Checksums of the frozen code

| File | MD5 |
|---|---|
| `ctirag/systems.py` (agent v4) | `e76d4ad373c8f099d2622e7f83caa23c` |
| `ctirag/final_bench.py` | `a73c96beec5f2ae7392887cd45c18801` |
| `ctirag/final_eval.py` | `d7f40e92f4d55180ff21dea2157337ce` |
| `ctirag/verify_gold.py` | `5c981874fd44203a1d9b832a9c5fa5df` |

The notebook refuses to run the final evaluation if the agent code differs from the checksums stored when the benchmark was built, so these files were not edited after freezing. One docstring in `final_eval.py` still calls the conflict chart "Figure 2"; in the paper it is Figure 3, and the notebook saves it as `fig3_conflict_prf.png`.

## Corpus and raw sources

The corpus has 8,571 documents, each one record from a frozen source release: 1,528 ATT&CK techniques, 191 groups and 86 mitigations (MITRE ATT&CK Enterprise STIX of 2026-08-04 and v8.2), 615 CAPEC attack patterns, 1,391 CWE weaknesses (v4.20), 1,738 CISA KEV entries (catalogue 2026.10.08), 999 NVD records (from 1,000 downloaded via the NVD API 2.0), 1,196 NIST SP 800-53 Rev. 5 controls (OSCAL 5.2.0) and 827 CTID ATT&CK-to-SP 800-53 mapping documents (Rev. 5 and Rev. 4).

The raw downloads are not included because they are large and freely available from MITRE, NIST, NVD, CISA and CTID. File names, versions and checksums of the exact snapshots are in `results/reports/final/frozen_source_versions.csv`.

## Validation of the gold answers

* **Programmatic.** `ctirag/verify_gold.py` re-derives every gold answer directly from the frozen raw files with its own parsers. All 275 answers of the final benchmark matched (`results/reports/final/gold_source_verification*.csv`), as did all 258 answers of the second draw.
* **Human.** A stratified sample of 50 questions was checked by one annotator with a cybersecurity background who did not build the benchmark. 49 of 50 gold answers were judged correct (98.0%, Wilson 95% CI [89.5, 99.6]), all 50 questions were clear, and all 14 notes were labelled as intended. With one annotator, no inter-annotator agreement is reported. The one disagreement (T1578.005, SP 800-53 mappings) is discussed in Section 3.4.1 of the paper. The benchmark was not edited after freezing.

## Reproducing the results

1. Copy the repository into Google Drive and open `CTI_Evidence_RAG_Colab_v6_2.ipynb` in Colab with a T4 GPU.
2. Follow the run plan at the top of the notebook. Run the cells one by one with ▶, not *Run all*. Every run cell resumes where it stopped.
3. Tables, figures and the validation summary (sections 13 and 14) need only a CPU and read the outputs in `results/`.

## License

Code: MIT (see `LICENSE`). Benchmark questions are derived from MITRE, NIST, NVD, CISA and CTID data and follow the terms of those sources.
