# Encrypted DNS Traffic Fingerprinting Pipeline

**An end-to-end system that captures live encrypted DNS traffic, extracts transport flow features, and measures how much an on-path observer can infer about user browsing activity. Evaluated across 32,262 raw capture attempts (31,200 unique query keys yielding 22,407 usable feature rows post-filtering) across three production network archetypes: Airtel Fiber (Residential FTTH), Reliance Jio (Mobile Cellular), and IIIT Allahabad (Enterprise Academic Campus Wi-Fi).**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-34%2F34%20passing-brightgreen.svg)](#6-testing-and-reproducibility)
[![Paper Draft](https://img.shields.io/badge/Paper-Draft%20Available-green.svg)](docs/paper.md)

---

## At a Glance

| Metric / Dimension | Specification |
| :--- | :--- |
| **System Scope** | Automated packet capture, feature extraction, ML classification, and statistical audit pipeline for encrypted DNS (DoH and DoH/3) |
| **Empirical Scale** | 32,262 raw capture attempts (20,262 Airtel, 6,000 Jio, 6,000 Campus Wi-Fi), 31,200 unique query keys, **22,407 usable captures post-filtering** (18,926 Airtel, 1,912 Jio, 1,569 Campus) |
| **Workload & Resolvers**| 100 pinned domains (50 Global, 50 India), 4 upstream resolvers (Airtel: 4, Jio: 3, Campus: 3), 3 physical network archetypes, 2 transport protocols |
| **Feature Space** | **44 directional flow features** per query (sizes, bursts, inter-arrival times, signed packet sequences; zero label leakage) |
| **Model Architectures** | Random Forest, XGBoost, 1D-CNN (sequence), GRU (recurrent), open-world detector |
| **Reproducibility** | Full analytical suite reruns deterministically from saved feature datasets in under 6 minutes; live capture required ~23+ hours |
| **Verification & Quality** | 34 automated unit tests, 6-check provenance suite, fixed deterministic seeds, 200 permutation tests per slice, auditable claims ledger |
| **Tech Stack** | Python, dumpcap/tshark (Wireshark suite), `q` DNS client, Scikit-Learn, PyTorch, Bash |

---

## 1. Problem & Core Research Question

DNS encryption hides human-readable hostnames by tunneling queries through TLS (DoH over HTTP/2, RFC 8484) or QUIC (DoH/3 over HTTP/3, RFC 9114). However, unencrypted transport metadata—packet sizes, directional counts, burst structures, and inter-arrival timing—still crosses the physical wire in the clear.

An on-path passive adversary (such as an ISP, cellular carrier, or campus network observer) can train supervised classifiers on these flow silhouettes to infer which domain was requested without decrypting the underlying ciphertext.

**Core Research Question:** Does migrating from HTTP/2 to HTTP/3 over QUIC provide intrinsic resistance against website fingerprinting, and does that resistance hold across different public resolvers and diverse real-world access networks?

---

## 2. Key Empirical Findings

### Headline Results (Global Workload, 100-Domain Closed World, Baseline Chance = 1.0%)

| Upstream Resolver | DoH (HTTP/2) Top-1 | DoH/3 (HTTP/3) Top-1 | Leakage Reduction |
| :--- | :--- | :--- | :--- |
| **Cloudflare** | 26.3% | 7.2% | **73% reduction** |
| **Quad9** | 45.2% | 6.6% | **85% reduction** |
| **AdGuard** | 26.2% | 11.2% | **57% reduction** |
| **Google** | 21.3% | 15.0% | **30% reduction** |

*All results evaluated with strict temporal holdout (repeats 8–17 train, 18–19 test), 200 domain-clustered permutation test iterations ($p < 0.005$), and 95% cluster-robust domain bootstrap confidence intervals. Full derivations are documented in the [Paper Draft](docs/paper.md).*

### Critical Systems Findings

1. **Lower Observed Leakage for DoH/3 on Three Resolvers:** DoH/3 showed lower observed fingerprinting accuracy than DoH for AdGuard, Cloudflare, and Quad9 across the evaluated workloads (57% to 85% observed relative reduction). This reduction is empirically associated with altered packet framing and flow size distributions; QUIC datagram coalescence and connection-establishment padding reduce query-specific size variance.
2. **The Google Anomaly (Implementation Outweighs Protocol):** Google DoH/3 exhibits smaller privacy gains (15.0% vs. 21.3%). Packet inspection revealed that Google returns unpadded response payloads where downstream packet size variations strongly correlate with the number of DNS resource records in the answer section, preserving distinct packet-size signatures.
3. **Universal Cross-Network Transfer Collapse ($3 \times 3$ Matrix):** Classifiers trained on fiber broadband (Airtel) completely fail when deployed against cellular (Jio) or enterprise campus Wi-Fi (IIIT Allahabad): transfer accuracy collapses to between **1.7% and 2.7%** (indistinguishable from the 2.0% chance baseline across 50 shared domains), with domain-clustered bootstrap confidence intervals spanning chance. Kolmogorov-Smirnov tests confirm massive distribution shifts ($p < 10^{-15}$) across network boundaries.
4. **Pervasive Carrier & Institutional QUIC/UDP-443 Blackout:** Outbound DoH/3 over UDP 443 experienced a **100% failure rate** across both Reliance Jio cellular (3,000/3,000 timed out) and IIIT Allahabad campus Wi-Fi (3,000/3,000 timed out, `udp_blocked_flag=true`, 0.0% reachability). This proves that QUIC reachability failure is not an isolated mobile telco quirk, but a pervasive reality across institutional perimeter firewalls and carrier middleboxes.
5. **Proxy-Induced Flow Obfuscation:** Behind an institutional HTTP/HTTPS forward proxy (`172.31.2.4:8080`), within-campus DoH fingerprinting accuracy drops to **1.8%–5.6%** (compared to **18.2%–45.2%** on direct FTTH broadband). Proxy encapsulation, connection multiplexing, and packet buffering naturally serve as an inadvertent privacy-preserving layer that dampens flow distinctiveness.
6. **Tri-Network Multi-Carrier Pooled Recovery:** Co-training on pooled data across all three network classes (Airtel + Jio + Campus) recovers composite test accuracy to **20.67%** (up to **45.0%** on AdGuard Global, and up to **73.3%** on held-out residential traces), demonstrating that multi-vantage adversaries can overcome carrier-specific channel noise.

---

## 3. System Architecture

```
 Workload Generator          Capture Engine             Feature Extractor            ML Evaluation Suite
 ------------------          --------------             -----------------            -------------------
 100 Pinned Domains          dumpcap / tshark           44 Flow Features             Random Forest, XGBoost
 (50 Global, 50 India)       Synchronous per-query      (Sizes, Bursts, IATs)        1D-CNN, GRU, Open-World
        |                    BPF port 443 filtering     Zero label leakage           Temporal holdout eval
        |                           |                          |                     200 permutation tests
        v                           v                          v                               |
  q DNS Client 0.19.12  ===>  Access Networks  ===>  data/processed/ Tables  ===>  results/ & figures/
  (HTTP/2 & HTTP/3)           (Airtel / Jio / Campus)  (dataset_tri_network.csv)   claims_ledger.csv
```

### Module Responsibilities

| Module | Purpose |
| :--- | :--- |
| `src/probe_and_capture.py` | Synchronous DNS query generator and dumpcap orchestrator with `--allow-proxy` support; guarantees 1:1 mapping between query and PCAP. |
| `src/extract_features.py` | High-throughput extractor converting raw PCAPs into 44-dimensional transport-agnostic feature vectors. |
| `src/encdns/` | Modular analysis package providing classifier training, baseline permutation testing, and claims ledger generation. |
| `scripts/run_airtel_all.py` | Master runner for broadband evaluation: n-grams (WP7), deep learning (WP8), open-world (WP9), scaling (WP10), time-stability (WP11), and defense simulations (WP13). |
| `scripts/run_jio_analysis.py` | Master runner for cellular & cross-network evaluation: within-Jio (N1), transfer tests (N2), pooled training (N3), distribution shift (N4), resolver ranking (N5), and network health (N8). |
| `scripts/run_jio_capture.sh` | Automated 6,000-query capture harness with sleep prevention (`caffeinate`) and interface auto-detection. |
| `scripts/run_campus_capture.sh` | Automated 6,000-query campus capture harness supporting institutional HTTP proxy environments. |
| `scripts/run_campus_analysis.py` | Master runner for campus & tri-network evaluation: within-campus ($C_1$), $3 \times 3$ transfer matrix ($C_2$), tri-network pooled training ($C_3$), feature drift ($C_4$), and protocol reachability ($C_5$). |
| `scripts/plot_slide_figures.py` | Publication figure generator for residential and cellular analysis (`fig1`–`fig4`). |
| `scripts/plot_tri_network_figures.py` | Publication figure generator for tri-network reachability (`fig5`) and $3 \times 3$ transfer matrix heatmap (`fig6`). |

---

## 4. Engineering & Systems Highlights

- **Synchronous Capture with Controlled Packet Flush:** To eliminate inter-query packet bleeding, each query is captured into an isolated PCAP. The harness sends a `SIGINT` flush signal to `dumpcap` exactly 150ms after query completion, capturing trailing ACKs/FINs without idling.
- **Zero Label Leakage Guarantee:** IP addresses, port numbers, SNI hostnames, and transport headers are stripped prior to model ingestion. Classifiers learn exclusively from physical traffic shape dynamics.
- **Institutional Forward Proxy Orchestration:** Added `--allow-proxy` mode to `src/probe_and_capture.py` to preserve proxy environment variables, route DoH through campus forward proxies (`172.31.2.4:8080`), and capture traffic targeting the gateway socket.
- **Temporal Split Validation:** Evaluation sets are partitioned strictly by query repeat (e.g., training on repeats 8–17, testing on repeats 18–19). Naive random train/test splits artificially leak temporal burst patterns and produce severely inflated accuracy.
- **Deep Sequence Model Analysis:** Evaluated Random Forest (26.2%), XGBoost (26.5%), 1D-CNN (1.0%), and GRU (1.4%) on AdGuard DoH. While tabular gradient boosting and tree ensembles capture aggregate volume and burst statistics, compact DNS flows (15–40 packets total) lack the sequential token depth needed to train recurrent or convolutional architectures effectively.
- **Dynamic Interface Binding:** Implemented automated interface resolution via system routing tables, seamlessly switching between physical Wi-Fi (`en0`) and macOS cellular USB tethering (`en5`).
- **Cryptographic Auditability:** All 39 statistical claims cited in the research paper and technical documentation are mapped directly to execution CSV artifacts in `docs/claims_ledger.csv`.

---

## 5. Technical Challenges & Solutions

| Technical Challenge | Root Cause | Engineering Solution |
| :--- | :--- | :--- |
| **Artificially inflated classifier accuracy** | Random train/test splits leak temporal session correlation across queries. | Implemented strict leave-repeat-out temporal holdout partitioning. |
| **Model shortcut learning** | Residual protocol/address metadata (IPs, ports, headers) allows trivial classification. | Enforced zero-label-leakage filter; validated statistical significance against 200 label-permutation baseline tests ($p < 0.005$). |
| **Google DoH/3 persistent leakage** | Unpadded server responses scale directly with DNS answer record count. | Extracted packet-level breakdown; identified implementation variance rather than protocol failure. |
| **Cross-network transfer collapse** | Access network differences in latency and packet framing alter IATs and packet sizes. | Quantified distribution shifts via Kolmogorov-Smirnov tests ($p < 10^{-15}$); trained pooled multi-network models to recover generalized representations (20.7%). |
| **100% DoH/3 failure on mobile & campus** | Outbound UDP 443 queries consistently timed out with 0 packets returned due to middlebox/firewall policies. | Hardened capture engine with a 2-second timeout and `udp_blocked_flag` tagging, rigorously documenting transport reachability. |
| **Campus firewall dropping direct resolver connections** | Enterprise perimeter firewall blocks direct outbound TCP/UDP 443 to public resolvers (`8.8.8.8`, `1.1.1.1`). | Augmented capture engine with `--allow-proxy` mode to route queries via campus forward proxy (`172.31.2.4:8080`) and capture traffic on the proxy gateway socket. |

---

## 6. Testing and Reproducibility

```bash
# Execute automated test suite (34 tests pass)
python3 -m unittest discover tests

# Verify all 39 empirical research claims against underlying CSVs
python3 scripts/verify_research_results.py
```

Preprocessed feature datasets are version-controlled under `data/processed/`, allowing full analytical reproduction without re-running long packet capture campaigns.

---

## 7. Quick Start Guide

### Prerequisites
- Python 3.10+
- Packet capture utilities: `dumpcap` and `tshark` (via `brew install wireshark` or `sudo apt install tshark`)
- DNS measurement client: [`q` DNS client v0.19.12+](https://github.com/natesales/q/releases)

### Setup
```bash
git checkout main
python3 -m venv .venv
source .venv/bin/activate          # On Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Reproduce Entire Analysis Suite (~6 Minutes)

Preprocessed feature datasets are version-controlled under `data/processed/` (`dataset_v2.csv`, `dataset_jio.csv`, `dataset_campus.csv`, `dataset_tri_network.csv`). The reproduction suite executes the entire machine learning and statistical evaluation suite from these saved feature datasets in ~6 minutes (compared to ~23+ hours of live physical packet collection across residential broadband, mobile cellular, and campus Wi-Fi).

```bash
# Step 1: Run headline Airtel fingerprinting with strict temporal holdout
PYTHONPATH=src python3 -m encdns analyze --run-id airtel_topup_20261113

# Step 2: Run cellular and cross-network transfer modules (N1 to N8)
python3 scripts/run_jio_analysis.py

# Step 3: Run model comparisons and broadband analyses (WP7-WP11, WP13)
python3 src/analysis_v2.py
python3 scripts/run_airtel_all.py

# Step 4: Run Tri-Network & Campus Wi-Fi evaluation (C1 to C5)
python3 scripts/run_campus_analysis.py

# Step 5: Regenerate all publication-ready figures (Figures 1-6)
python3 scripts/plot_slide_figures.py
python3 scripts/plot_tri_network_figures.py

# Step 6: Verify all empirical research claims against underlying CSVs
python3 scripts/verify_research_results.py
```

All results are written deterministically to `results/airtel_topup_20261113/`, `results/jio_analysis_20261113/`, `results/campus_analysis_20261120/`, `results/airtel_advanced_20261113/`, `results/airtel_all_20261113/`, and `results/figures/`.

---

## 8. Repository Structure

```
.
├── readme.md                  # Comprehensive project documentation
├── contributing.md            # Guidelines for contributing
├── license                    # MIT License file
├── requirements.txt           # Python dependency specifications
├── docs/
│   ├── paper.md               # Full academic research paper (9 sections, 9 tables)
│   ├── dataset.md             # Capture matrix, filtering criteria, and drop accounting
│   ├── features.md            # 44 flow features documentation and zero-label leakage guarantees
│   ├── methodology.md         # Evaluation protocols, temporal splits, and statistical tests
│   ├── limitations.md         # Threat model constraints, scope boundaries, and ethical compliance
│   ├── claims_ledger.csv      # Verification ledger mapping 39 claims to pipeline outputs
│   └── commands.md            # Measurement runbook and execution parameters
├── data/
│   └── processed/
│       ├── dataset_v2.csv          # Airtel FTTH broadband dataset (18,926 flows)
│       ├── dataset_jio.csv         # Reliance Jio cellular dataset (1,912 flows)
│       ├── dataset_campus.csv      # IIIT Allahabad campus dataset (1,569 flows)
│       └── dataset_tri_network.csv # Combined tri-network dataset (22,407 flows)
├── results/
│   ├── figures/               # Generated publication-quality figures
│   │   ├── fig1_headline_doh_vs_doh3.png
│   │   ├── fig2_cross_network_transfer.png
│   │   ├── fig3_carrier_quic_blocking.png
│   │   ├── fig4_feature_distribution_shift.png
│   │   ├── fig5_tri_network_reachability.png
│   │   └── fig6_tri_network_transfer_matrix.png
│   ├── airtel_topup_20261113/ # Headline Airtel fingerprinting (RQ1/RQ2)
│   ├── airtel_advanced_20261113/ # Model comparison outputs (RF vs XGBoost)
│   ├── airtel_all_20261113/   # Airtel analysis outputs (WP7-WP11, WP13)
│   ├── jio_analysis_20261113/ # Jio and cross-network outputs (N1-N8)
│   └── campus_analysis_20261120/ # Campus & tri-network outputs (C1-C5)
├── scripts/
│   ├── run_airtel_all.py      # Broadband analysis master runner
│   ├── run_jio_analysis.py    # Cellular & cross-network master runner
│   ├── run_jio_capture.sh     # 6,000-query automated cellular capture harness
│   ├── run_campus_analysis.py # Campus & tri-network master runner (C1-C5)
│   ├── run_campus_capture.sh  # 6,000-query automated campus capture harness
│   ├── plot_slide_figures.py  # Publication figure generator (Figs 1-4)
│   ├── plot_tri_network_figures.py # Tri-network figure generator (Figs 5-6)
│   └── verify_research_results.py # 6-check verification suite
├── src/
│   ├── probe_and_capture.py   # Synchronous probe and dumpcap capture orchestrator
│   ├── extract_features.py    # 44-feature network flow extraction module
│   └── encdns/                # Analysis library (classifiers, baselines, ledger)
└── tests/                     # Automated test suite (34 unit tests)
```

---

## 9. Limitations & Future Work

- **Evaluated Scope:** Closed-world evaluation across 100 domains from three distinct network archetypes (residential FTTH, mobile cellular, and enterprise campus Wi-Fi). While open-world evaluation was conducted (monitored vs. unmonitored), generalizability to additional worldwide ISPs remains uncharacterized.
- **Client & Resolver Matrix:** Measurements reflect specific versions of `q` (0.19.12) and public resolver configurations at the time of collection.
- **QUIC / UDP 443 Inaccessibility:** Because Reliance Jio cellular and IIIT Allahabad campus Wi-Fi yielded 100% client-side timeouts (0 packets returned) on outbound UDP 443, classifier accuracy could not be evaluated for DoH/3 on these vantage points.
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
