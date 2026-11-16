# Encrypted DNS Traffic Fingerprinting Pipeline

**An end-to-end system that captures live encrypted DNS traffic, extracts transport flow features, and measures how much an on-path observer can infer about user browsing activity. Evaluated across 26,262 raw capture attempts (25,200 unique query keys yielding 20,838 usable feature rows post-filtering) on two production Indian access networks: Airtel Fiber (FTTH) and Reliance Jio Cellular.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-10%2F10%20passing-brightgreen.svg)](#6-testing-and-reproducibility)
[![Paper Draft](https://img.shields.io/badge/Paper-Draft%20Available-green.svg)](docs/paper.md)

---

## At a Glance

| Metric / Dimension | Specification |
| :--- | :--- |
| **System Scope** | Automated packet capture, feature extraction, ML classification, and statistical audit pipeline for encrypted DNS (DoH and DoH/3) |
| **Empirical Scale** | 26,262 raw capture attempts (20,262 Airtel, 6,000 Jio), 25,200 unique query keys, **20,838 usable captures post-filtering** (18,926 Airtel, 1,912 Jio) |
| **Workload & Resolvers**| 100 pinned domains (50 Global, 50 India), 4 upstream resolvers (Airtel: 4, Jio: 3), 2 physical networks, 2 transport protocols |
| **Feature Space** | **44 directional flow features** per query (sizes, bursts, inter-arrival times, signed packet sequences; zero label leakage) |
| **Model Architectures** | Random Forest, XGBoost, 1D-CNN (sequence), GRU (recurrent), open-world detector |
| **Reproducibility** | Full analytical suite reruns deterministically from saved feature datasets in under 6 minutes; live capture required ~20+ hours |
| **Verification & Quality** | 10 automated unit tests, fixed deterministic seeds, 200 permutation tests per slice, auditable claims ledger |
| **Tech Stack** | Python, dumpcap/tshark (Wireshark suite), `q` DNS client, Scikit-Learn, PyTorch, Bash |

---

## 1. Problem & Core Research Question

DNS encryption hides human-readable hostnames by tunneling queries through TLS (DoH over HTTP/2, RFC 8484) or QUIC (DoH/3 over HTTP/3, RFC 9114). However, unencrypted transport metadata—packet sizes, directional counts, burst structures, and inter-arrival timing—still crosses the physical wire in the clear.

An on-path passive adversary (such as an ISP or local network observer) can train supervised classifiers on these flow silhouettes to infer which domain was requested without decrypting the underlying ciphertext.

**Core Research Question:** Does migrating from HTTP/2 to HTTP/3 over QUIC provide intrinsic resistance against website fingerprinting, and does that resistance hold across different public resolvers and real-world access networks?

---

## 2. Key Empirical Findings

### Headline Results (100-Domain Closed World, Baseline Chance = 1.0%)

| Upstream Resolver | DoH (HTTP/2) Top-1 | DoH/3 (HTTP/3) Top-1 | Leakage Reduction |
| :--- | :--- | :--- | :--- |
| **Cloudflare** | 23.6% | 6.0% | **75% reduction** |
| **Quad9** | 34.2% | 4.6% | **86% reduction** |
| **AdGuard** | 26.2% | 8.9% | **66% reduction** |
| **Google** | 17.5% | 16.9% | **~3% reduction (no practical gain)** |

*All results evaluated with leave-repeat-out temporal splits, 200 label-permutation baseline iterations ($p < 0.005$), and 95% Wilson confidence intervals. Full derivations are documented in the [Paper Draft](docs/paper.md).*

### Critical Systems Findings

1. **Protocol Framing Reduces Leakage on Most Resolvers:** On Cloudflare, Quad9, and AdGuard, HTTP/3 significantly suppresses fingerprintability (leakage reduced by 66% to 86%). QUIC's mandatory Initial packet padding ($\ge 1200$ bytes) and unified frame multiplexing act as natural padding against query-length leakage.
2. **The Google Anomaly (Implementation Outweighs Protocol):** Google DoH/3 shows almost zero privacy improvement (16.9% vs. 17.5%). Packet inspection revealed that Google returns unpadded response payloads where downstream packet size variations strongly correlate with the number of DNS resource records in the answer section, preserving distinct packet-size signatures.
3. **Cross-Network Transfer Collapse:** Classifiers trained on fiber broadband (Airtel) completely fail when deployed against cellular traffic (Jio), dropping to **1.6%–2.4%** accuracy (indistinguishable from the 2.0% random chance baseline for the 50 shared domains). Two-sample Kolmogorov-Smirnov tests confirm major distribution shifts ($p < 10^{-6}$) driven by cellular radio scheduling, MTU clamping, and variable link latency.
4. **Cellular UDP/443 Filtering:** On Reliance Jio cellular, **100% of the 3,000 DoH/3 queries timed out** with 0 packets returned. Observations are consistent with carrier middlebox filtering or blackholing of outbound UDP port 443, which would force standard user agents to fall back to older, higher-leakage protocols.

---

## 3. System Architecture

```
 Workload Generator          Capture Engine             Feature Extractor            ML Evaluation Suite
 ------------------          --------------             -----------------            -------------------
 100 Pinned Domains          dumpcap / tshark           44 Flow Features             Random Forest, XGBoost
 (50 Global, 50 India)       Synchronous per-query      (Sizes, Bursts, IATs)        1D-CNN, GRU, Open-World
        |                    BPF port 443 filtering     Zero label leakage           Leave-repeat-out CV
        |                           |                          |                     200 permutation tests
        v                           v                          v                               |
  q DNS Client 0.19.12  ===>  Access Network  ===>  data/processed/ Tables  ===>  results/ & figures/
  (HTTP/2 & HTTP/3)           (Airtel / Jio)        (dataset_combined.csv)        claims_ledger.csv
```

### Module Responsibilities

| Module | Purpose |
| :--- | :--- |
| `src/probe_and_capture.py` | Synchronous DNS query generator and dumpcap orchestrator; guarantees 1:1 mapping between query and PCAP. |
| `src/extract_features.py` | High-throughput extractor converting raw PCAPs into 44-dimensional transport-agnostic feature vectors. |
| `src/encdns/` | Modular analysis package providing classifier training, baseline permutation testing, and claims ledger generation. |
| `scripts/run_airtel_all.py` | Master runner for broadband evaluation: n-grams (WP7), deep learning (WP8), open-world (WP9), scaling (WP10), time-stability (WP11), and defense simulations (WP13). |
| `scripts/run_jio_analysis.py` | Master runner for cellular & cross-network evaluation: within-Jio (N1), transfer tests (N2), pooled training (N3), distribution shift (N4), resolver ranking (N5), and network health (N8). |
| `scripts/run_jio_capture.sh` | Automated 6,000-query capture harness with sleep prevention (`caffeinate`) and interface auto-detection. |
| `scripts/plot_slide_figures.py` | Publication figure generator producing high-resolution vector PNGs for paper and slide decks. |

---

## 4. Engineering & Systems Highlights

- **Synchronous Capture with Controlled Packet Flush:** To eliminate inter-query packet bleeding, each query is captured into an isolated PCAP. The harness sends a `SIGINT` flush signal to `dumpcap` exactly 150ms after query completion, capturing trailing ACKs/FINs without idling.
- **Zero Label Leakage Guarantee:** IP addresses, port numbers, SNI hostnames, and transport headers are stripped prior to model ingestion. Classifiers learn exclusively from physical traffic shape dynamics.
- **Temporal Split Validation:** Evaluation sets are partitioned strictly by query repeat (e.g., training on repeats 8–17, testing on repeats 18–19). Naive random train/test splits artificially leak temporal burst patterns and produce severely inflated accuracy.
- **Deep Sequence Model Analysis:** Evaluated 1D-CNN and GRU sequence architectures against raw packet size vectors (`pkt_00`–`pkt_19`). Both deep learning models collapsed to near-chance (~1.0%–1.4%), whereas Random Forest achieved 26.2%. Because encrypted DNS flows are ultra-compact (15–40 packets total), flows lack the sequential token depth required by deep recurrent/convolutional layers; cumulative flow volumes and burst aggregates provide the true predictive signal.
- **Dynamic Interface Binding:** Implemented automated interface resolution via system routing tables, seamlessly switching between physical Wi-Fi (`en0`) and macOS cellular USB tethering (`en5`).
- **Cryptographic Auditability:** All 39 statistical claims cited in the research paper and technical documentation are mapped directly to execution CSV artifacts in `docs/claims_ledger.csv`.

---

## 5. Technical Challenges & Solutions

| Technical Challenge | Root Cause | Engineering Solution |
| :--- | :--- | :--- |
| **Artificially inflated classifier accuracy** | Random train/test splits leak temporal session correlation across queries. | Implemented strict leave-repeat-out temporal cross-validation. |
| **Model shortcut learning** | Residual protocol/address metadata (IPs, ports, headers) allows trivial classification. | Enforced zero-label-leakage filter; validated statistical significance against 200 label-permutation baseline tests ($p < 0.005$). |
| **Google DoH/3 persistent leakage** | Unpadded server responses scale directly with DNS answer record count. | Extracted packet-level breakdown; identified implementation variance rather than protocol failure. |
| **Cross-network transfer collapse** | Cellular radio resource scheduling and MTU clamping alter IATs and packet sizes. | Quantified distribution shifts via Kolmogorov-Smirnov tests ($p < 10^{-6}$); trained pooled multi-network models to recover generalized representations (16.0%–20.7%). |
| **100% DoH/3 failure on mobile network** | Carrier core middleboxes drop outbound UDP 443 packets. | Hardened capture engine with a 2-second timeout and `udp_blocked_flag` tagging, documenting the silent fallback vulnerability. |

---

## 6. Testing and Reproducibility

```bash
# Execute automated test suite (10/10 tests pass)
python3 -m unittest discover tests
```

Preprocessed feature datasets are version-controlled under `data/processed/`, allowing full analytical reproduction without re-running long packet capture campaigns.

---

## 7. Quick Start Guide

### Prerequisites
- Python 3.9+
- Packet capture utilities: `dumpcap` and `tshark` (via `brew install wireshark` or `sudo apt install tshark`)
- DNS measurement client: [`q` DNS client v0.19.12+](https://github.com/natesales/q/releases)

### Setup
```bash
git checkout aman
python3 -m venv .venv
source .venv/bin/activate          # On Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Reproduce Entire Analysis Suite (~6 Minutes)

Preprocessed feature datasets are version-controlled under `data/processed/` (`dataset_v2.csv`, `dataset_jio.csv`, `dataset_combined.csv`). The ~6-minute reproduction command suite below executes the entire machine learning and statistical evaluation suite from these saved feature datasets. (In contrast, the live packet capture campaign comprising 26,262 attempts required ~20+ hours of physical collection across residential broadband and mobile cellular networks.)

```bash
# Step 1: Run broadband analysis modules (WP7 to WP11, WP13)
python3 scripts/run_airtel_all.py

# Step 2: Run cellular and cross-network transfer modules (N1 to N8)
python3 scripts/run_jio_analysis.py

# Step 3: Regenerate all publication-ready figures
python3 scripts/plot_slide_figures.py
```

All results are written deterministically to `results/airtel_all_20261113/`, `results/jio_analysis_20261113/`, and `results/figures/`.

---

## 8. Repository Structure

```
.
├── readme.md                  # Comprehensive project documentation
├── contributing.md            # Guidelines for contributing
├── license                    # MIT License file
├── requirements.txt           # Python dependency specifications
├── to-do.md                   # Verification and deliverable audit checklist
├── docs/
│   ├── paper.md               # Full academic research paper (9 sections, 9 tables)
│   ├── dataset.md             # Capture matrix, filtering criteria, and drop accounting
│   ├── features.md            # 44 flow features documentation and zero-label leakage guarantees
│   ├── methodology.md         # Evaluation protocols, temporal splits, and statistical tests
│   ├── limitations.md         # Threat model constraints, scope boundaries, and ethical compliance
│   ├── claims_ledger.csv      # Verification ledger mapping 39 claims to pipeline outputs
│   └── commands.md            # Measurement runbook and execution parameters
├── results/
│   ├── figures/               # Generated publication-quality figures
│   │   ├── fig1_headline_doh_vs_doh3.png
│   │   ├── fig2_cross_network_transfer.png
│   │   ├── fig3_carrier_quic_blocking.png
│   │   └── fig4_feature_distribution_shift.png
│   ├── airtel_all_20261113/   # Airtel analysis outputs (WP7-WP11, WP13)
│   └── jio_analysis_20261113/ # Jio and cross-network outputs (N1-N8)
├── scripts/
│   ├── run_airtel_all.py      # Broadband analysis master runner
│   ├── run_jio_analysis.py    # Cellular & cross-network master runner
│   ├── run_jio_capture.sh     # 6,000-query automated cellular capture harness
│   └── plot_slide_figures.py  # Publication figure generator
├── src/
│   ├── probe_and_capture.py   # Synchronous probe and dumpcap capture orchestrator
│   ├── extract_features.py    # 44-feature network flow extraction module
│   └── encdns/                # Analysis library (classifiers, baselines, ledger)
└── tests/                     # Automated test suite
```

---

## 9. Limitations & Future Work

- **Evaluated Scope:** Closed-world evaluation across 100 domains from two access networks. While open-world evaluation was conducted (monitored vs. unmonitored), generalizability to additional worldwide ISPs remains uncharacterized.
- **Client & Resolver Matrix:** Measurements reflect specific versions of `q` (0.19.12) and public resolver configurations at the time of collection.
- **Cellular DoH/3 Inaccessibility:** Because Reliance Jio dropped 100% of outbound UDP 443 packets, classifier accuracy could not be evaluated for DoH/3 on the cellular path.
- **Future Directions:** Expanding collection to multiple vantage points across the Global South, testing browser-driven full page loads, evaluating padding defenses on live traffic, and packaging the measurement harness as a standalone CLI tool.

---

## 10. Ethics & Open Science

- **Passive Observational Framework:** All traffic captures were conducted passively against client-initiated queries. No payload modification, injection, or decryption was performed.
- **Privacy Compliance:** Raw PCAP files, proprietary network identifiers, credentials, and local IP addresses are excluded from version control per `.gitignore`.
- **Reproducibility:** Seed configurations (`17`, `42`, `101`) and analytical workflows are fully automated and deterministic.

---

## 11. Author

**Aman Kashyap** ([iit2024140@iiita.ac.in](mailto:iit2024140@iiita.ac.in))  
Department of Information Technology, Indian Institute of Information Technology, Allahabad (IIIT Allahabad)  
Research Methodology Coursework, November 2026

Released under the [MIT License](https://opensource.org/licenses/MIT).
