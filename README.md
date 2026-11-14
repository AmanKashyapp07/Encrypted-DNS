# Encrypted DNS Privacy: DoH vs. DoH/3

**Does moving encrypted DNS from HTTP/2 to HTTP/3 actually protect what you browse? An empirical study on Indian networks (Airtel Fiber and Reliance Jio cellular).**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Paper Draft](https://img.shields.io/badge/Paper-Draft%20Available-green.svg)](docs/PAPER_DRAFT.md)
[![Slides](https://img.shields.io/badge/Slides-presentation.md-blueviolet.svg)](presentation.md)

---

## TL;DR

Encrypting DNS hides the domain name, but not the shape of the traffic. We captured **26,838 live encrypted DNS queries** on two production Indian networks and trained classifiers to guess the queried domain from packet metadata alone.

| # | Finding | Headline number |
| :-: | :--- | :--- |
| 1 | HTTP/3 (DoH/3) greatly reduces leakage on Cloudflare, Quad9 and AdGuard | Top-1 accuracy cut by 66% to 86% |
| 2 | Google's resolver is the exception: DoH/3 gives no privacy gain | 16.9% (DoH/3) vs. 17.5% (DoH) |
| 3 | Classifiers trained on Airtel fiber do not transfer to Jio cellular | 1.6% to 2.4% accuracy, near chance |
| 4 | Jio cellular blocks DoH/3 entirely in our tests | 3,000 of 3,000 queries failed |

**Takeaway:** the protocol matters, the resolver implementation matters, and the access network decides whether the better protocol is even usable.

---

## Table of Contents

1. [Background](#1-background)
2. [Threat Model](#2-threat-model)
3. [Key Results](#3-key-results)
4. [Methodology](#4-methodology)
5. [Limitations](#5-limitations)
6. [Repository Structure](#6-repository-structure)
7. [Quick Start](#7-quick-start)
8. [Deliverables](#8-deliverables)
9. [Ethics and Reproducibility](#9-ethics-and-reproducibility)
10. [Author](#10-author)

---

## 1. Background

Before a browser loads a site such as `wikipedia.org`, it asks a recursive resolver to turn the name into an IP address. This is the job of the **Domain Name System (DNS)**.

Classic DNS (RFC 1035) is sent in cleartext over UDP port 53, so anyone on the path (ISPs, network administrators, surveillance systems) can read every name you look up.

```
Traditional DNS
Client ---------- "query: bank.com" ----------> Resolver
        (on-path observers can read the query)
```

Two standards encrypt DNS to fix this:

| Protocol | Standard | Transport | Port |
| :--- | :--- | :--- | :--- |
| **DoH** (DNS-over-HTTPS) | RFC 8484 | HTTP/2 over TLS/TCP | 443/TCP |
| **DoH/3** (DNS-over-HTTP/3) | RFC 8484 carried over HTTP/3, RFC 9114 | HTTP/3 over QUIC/UDP | 443/UDP |

```
Encrypted DNS
Client ===== [ encrypted tunnel ] =====> Resolver
        (query contents are protected, traffic metadata is not)
```

## 2. Threat Model

Encryption hides the payload, but an on-path observer still sees:

- Byte volumes and packet counts per direction
- Packet size distributions and handshake patterns
- Inter-arrival times and flow duration

A supervised classifier can learn to map these signatures back to domain names without breaking any cryptography. This attack is called **domain traffic fingerprinting**, and it is what this project measures.

**Adversary:** passive, on-path (for example an ISP). Cannot decrypt, modify or inject traffic.

## 3. Key Results

### 3.1 DoH vs. DoH/3 by resolver

Closed-world identification across 100 domains (50 global from Tranco, 50 Indian regional). Random-guess baseline is 1.0%.

| Resolver | DoH (HTTP/2) | DoH/3 (HTTP/3) | Relative reduction | Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **Cloudflare** | 23.6% [21.5, 25.8] | 6.0% [4.7, 7.6] | 75% | Strong improvement |
| **Quad9** | 34.2% [31.8, 36.6] | 4.6% [3.5, 6.0] | 86% | Strong improvement |
| **AdGuard** | 26.2% [24.1, 28.5] | 8.9% [7.4, 10.7] | 66% | Good improvement |
| **Google** | 17.5% [15.6, 19.5] | 16.9% [15.1, 18.9] | about 3% | No meaningful improvement |

Values are top-1 accuracy with 95% Wilson confidence intervals. All results use leave-repeat-out temporal cross-validation and 200 label-permutation tests (p < 0.005).

### 3.2 Why HTTP/3 helps, and why Google differs

- **Why HTTP/3 helps:** QUIC requires client Initial packets to be padded to at least 1200 bytes and multiplexes frames uniformly, which hides the small size differences between short and long domain names.
- **Why Google differs:** packet inspection shows Google's responses are not padded and scale with the number of answer records, so size signatures survive even over HTTP/3.

### 3.3 Cross-network transfer failure

Models trained on Airtel fiber and tested on Jio cellular fall to **1.6% to 2.4%** accuracy. Two-sample Kolmogorov-Smirnov tests confirm a large distribution shift (p < 10^-6), consistent with cellular radio scheduling, jitter and MTU differences.

*Implication: a fingerprinting attacker must train per network type, which raises the cost of a real attack.*

### 3.4 Carrier-level blocking of QUIC

On Jio cellular, **100% of outbound DoH/3 queries (3,000 of 3,000)** failed. This is consistent with UDP/443 filtering in the carrier network. Clients that silently fall back to HTTP/2 DoH would lose the privacy benefit shown in 3.1.

*Implication: the privacy gain of DoH/3 depends on deployment conditions, not just on the protocol.*

## 4. Methodology

```
 Workload                 Capture                  Network                   Resolvers
 -----------------        ------------------       --------------------      ------------------
 100 pinned domains  -->  dumpcap / tshark    -->  Airtel FTTH (Wi-Fi 6) --> Cloudflare 1.1.1.1
 50 global (Tranco)       one PCAP per query       Jio 4G/5G (USB tether)    Google 8.8.8.8
 50 Indian regional       synchronous flush                                  Quad9 9.9.9.9
                                                                             AdGuard
 Client: q DNS client 0.19.12 (HTTP/2 and HTTP/3)
```

### Controls

- **No label leakage:** IP addresses, ports, SNI and protocol headers are excluded. Models see only traffic dynamics (39 flow features).
- **Temporal integrity:** train and test splits are separated by query repeat to avoid burst autocorrelation.
- **Statistical baselines:** 200 permutation shuffles confirm accuracy exceeds chance.
- **Model suite:** Random Forest, XGBoost, 1D-CNN and GRU on packet sequences, plus open-world evaluation, domain-scaling curves and simulated defenses.

## 5. Limitations

- Closed-world evaluation on 100 domains; real-world accuracy against the open internet will differ (open-world results are in the paper).
- Two networks and one vantage point each; results may not generalize to other ISPs or regions.
- Findings depend on the resolver and client software versions tested.
- Jio DoH/3 measurements are limited to the failure result; no classifier could be evaluated on that path.

## 6. Repository Structure

```
.
|-- README.md
|-- presentation.md            12-slide Marp deck with speaker notes
|-- requirements.txt
|-- to-do.md                   verification checklist
|-- docs/
|   |-- PAPER_DRAFT.md         full paper draft (9 sections, 9 tables)
|   |-- PRESENTATION_SLIDES.md slide content and speaker documentation
|   |-- claims_ledger.csv      ledger mapping all 24 claims to pipeline outputs
|   `-- CAPTURE_COMMANDS.md    measurement runbook
|-- results/
|   |-- figures/               publication figures
|   |-- airtel_all_20261113/   Airtel analysis tables (WP7-WP11, WP13)
|   `-- jio_analysis_20261113/ Jio and cross-network tables (N1-N8)
|-- scripts/
|   |-- run_airtel_all.py
|   |-- run_jio_analysis.py
|   |-- run_jio_capture.sh     6,000-query Jio capture harness
|   `-- plot_slide_figures.py
`-- src/
    |-- probe_and_capture.py   probe and dumpcap orchestrator
    |-- extract_features.py    39-feature flow extraction
    `-- encdns/                fingerprinting, baselines, ledger
```

## 7. Quick Start

### Prerequisites

- Python 3.9+
- `tshark` and `dumpcap` (only needed to capture new data): `brew install wireshark` (macOS) or `sudo apt install tshark` (Linux)
- [`q` DNS client](https://github.com/natesales/q/releases) 0.19.12+ (only needed to capture new data)

### Install

```bash
git checkout aman
python3 -m venv .venv
source .venv/bin/activate        # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Reproduce the results (about 6 minutes)

Preprocessed, leakage-free feature tables are in `data/processed/`, so no capture is required.

```bash
python3 scripts/run_airtel_all.py      # Airtel analyses (WP7-WP11, WP13)
python3 scripts/run_jio_analysis.py    # Jio and cross-network analyses (N1-N8)
python3 scripts/plot_slide_figures.py  # publication figures
```

Outputs are written to `results/airtel_all_20261113/`, `results/jio_analysis_20261113/` and `results/figures/`.

### Run the tests

```bash
python3 -m unittest discover tests     # 10/10 passing
```

## 8. Deliverables

| Deliverable | Description |
| :--- | :--- |
| [Paper draft](docs/PAPER_DRAFT.md) | Related work, threat model, methodology, evaluation, limitations, ethics |
| [Presentation](presentation.md) | 12 Marp slides with word-for-word speaker notes |
| [Claims ledger](docs/claims_ledger.csv) | Every statistical claim traced to a pipeline output |
| [Figure 1](results/figures/fig1_headline_doh_vs_doh3.png) | DoH vs. DoH/3 leakage comparison |
| [Figure 2](results/figures/fig2_cross_network_transfer.png) | Cross-network transfer collapse |
| [Figure 3](results/figures/fig3_carrier_quic_blocking.png) | QUIC blocking on Jio cellular |
| [Figure 4](results/figures/fig4_feature_distribution_shift.png) | Feature distribution shift across networks |

## 9. Ethics and Reproducibility

- **Passive measurement:** only client-initiated queries were captured. No payload was decrypted, modified or injected.
- **Privacy:** raw PCAPs, network identifiers, credentials and local IPs are excluded from version control via `.gitignore`.
- **Determinism:** fixed seeds (17, 42, 101) and an automated pipeline make results reproducible.

## 10. Author

**Aman Kashyap** ([iit2024140@iiita.ac.in](mailto:iit2024140@iiita.ac.in))
Department of Information Technology, Indian Institute of Information Technology, Allahabad
Research Methodology coursework, November 2026

Released under the [MIT License](https://opensource.org/licenses/MIT).