# Dataset Methodology: Encrypted DNS Capture & Processing

This document provides a comprehensive specification of the experimental dataset collection, filtering pipeline, exclusion criteria, and schema for the Encrypted DNS traffic analysis project across Airtel Broadband (FTTH) and Reliance Jio Cellular (4G/5G).

---

## 1. Experimental Collection Matrix

The data collection campaign was conducted across two production access networks in India using the native `q` command-line DNS client (v0.19.12) paired with `dumpcap` (Wireshark 4.4+) for isolated per-query packet capture.

### Matrix Specifications

| Dimension | Airtel Broadband (FTTH) | Reliance Jio Cellular (4G/5G) |
| :--- | :--- | :--- |
| **Physical Interface** | Optical Fiber FTTH via Wi-Fi 6 (`en0`) | Cellular USB Tethering (`en5`) |
| **Candidate Domains** | 200 domains (100 Global + 100 India) | 100 domains (50 Global + 50 India) |
| **Upstream Resolvers** | 4 (Cloudflare, Google, AdGuard, Quad9) | 3 (Cloudflare, Google, AdGuard) |
| **Transports / Protocols** | 2: DoH (HTTP/2 / TCP 443), DoH/3 (QUIC / UDP 443) | 2: DoH (HTTP/2 / TCP 443), DoH/3 (QUIC / UDP 443) |
| **Target Repeats** | 20 repeats (repeats 0–19) | 10 repeats (repeats 0–9) |
| **Query Sequencing** | Shuffled randomized order, sequential execution | Shuffled randomized order, sequential execution |
| **Total Target Attempts**| $200 \times 4 \times 2 \times 20 = \mathbf{19,200\text{ queries}}$ | $100 \times 3 \times 2 \times 10 = \mathbf{6,000\text{ queries}}$ |

### Rationale for Quad9 Exclusion on Jio

Quad9 (`dns.quad9.net` / `9.9.9.9`) was evaluated on Airtel but deliberately excluded from the Jio cellular collection:
1. **Completion Stability:** During the Airtel baseline runs, Quad9 DoH/3 exhibited the lowest night-time completion rate (~85% success due to upstream transit packet drops and throttling).
2. **Cellular Session Budget:** Tethered cellular captures over USB (`caffeinate` session) required strict limits on continuous session duration (~7.5 hours) to minimize carrier connection resets and thermal throttling. Removing Quad9 reduced the matrix from 8,000 to 6,000 queries.
3. Quad9 measurements were therefore isolated to the residential broadband tier and clearly documented as such.

---

## 2. Domain Selection Methodology

Domains were selected using the **Tranco Top-1M List** (List ID: `L5PV4`, downloaded 2026-11-09) with resolution verification:

* **Global Workload (100 domains):** Selected by iterating through Tranco top ranks, issuing live DNS resolution checks, and accepting the first 100 domains that consistently resolved across all four resolvers.
* **India Regional Workload (100 domains):** Selected by filtering Tranco for `.in` country-code top-level domains (ccTLDs), augmented with 10 prominent Indian commercial seed domains (`flipkart.com`, `hotstar.com`, `indiatimes.com`, `jio.com`, `myntra.com`, `paytm.com`, `phonepe.com`, `swiggy.com`, `tatacliq.com`, `zomato.com`), verified against live resolution.
* **Workload Isolation:** The Global and India domain lists are strictly disjoint (0 overlapping domains between them) and are evaluated independently.

---

## 3. Capture Workflow & Query Isolation

To ensure that each capture reflects exactly one DNS query without inter-query packet bleeding:
1. **Dynamic BPF Filter:** `dumpcap` is spawned with an operating-system-level Berkeley Packet Filter restricted strictly to the resolver's bootstrap IPs and the active port:
   $$\text{Filter} = (\text{host } ip_1 \lor \text{host } ip_2 \dots) \land (\text{tcp port 443} \lor \text{udp port 443})$$
2. **Warmup & Dispatch:** The capture harness pauses 100–200 ms to ensure `dumpcap` is actively capturing on the socket, then launches `q` synchronously via `subprocess.run`.
3. **Tail Packet Flush:** Following query termination, the harness waits exactly 150 ms to capture trailing TCP ACKs or TLS connection close alerts, then issues a `SIGINT` to `dumpcap` to flush OS buffers.
4. **Metadata Logging:** Query latency, exit status, packet count, byte volume, answer record count, and TTL are parsed directly from `q` JSON metadata and written to the manifest.

---

## 4. Filtering, Quality Control & Exclusion Criteria

Raw capture PCAPs undergo rigorous quality-control filtering before feature extraction. Captures are excluded if they meet any of the following criteria:

1. **Client Execution Failure (`query_failed`):** The `q` binary returned a non-zero exit code (e.g., DNS timeout, TLS alert, connection refused).
2. **Slow Query Cut-Off (`slow_query`):** Query latency $> 1.5\text{ seconds}$. Because dumpcap is bounded by a fixed capture window, queries taking $> 1.5\text{ s}$ risk truncated trailing packets.
3. **Too Few Packets (`too_few_packets`):** PCAPs containing fewer than 3 packets (indicative of early TCP resets, zero-byte captures, or immediate interface drops).
4. **Missing Server Packets (`server_packets_missing`):** PCAPs where no captured packets originated from the designated resolver IP.
5. **Missing File (`missing_file`):** PCAP file could not be read or resolved.

### Drop Accounting

* **Airtel FTTH:** 20,262 raw manifest attempts $\rightarrow$ 1,062 retry attempts $\rightarrow$ 19,200 unique query keys $\rightarrow$ **18,926 usable captures** in `dataset_v2.csv` (98.6% yield of unique keys). Dropped rows are detailed in `data/processed/drop_reasons_v2.csv`.
* **Reliance Jio:** 6,000 raw manifest attempts:
  * 3,000 DoH/3 queries: 100% timed out after 2 seconds on UDP 443 (`query_failed`), yielding 0 usable traces.
  * 3,000 DoH queries: 1,920 succeeded (Google: 1,000, AdGuard: 905, Cloudflare: 15).
  * 8 captures dropped during feature extraction (7 `slow_query`, 1 `too_few_packets`), leaving **1,912 usable captures** in `dataset_jio.csv`. Detailed in `data/processed/drop_reasons_jio.csv`.

---

## 5. Dataset Summary & Final Accounting

| Metric / Dimension | Airtel Broadband (FTTH) | Reliance Jio Cellular (4G/5G) | Combined Total |
| :--- | :--- | :--- | :--- |
| **Raw Manifest Rows / Attempts** | 20,262 | 6,000 | **26,262** |
| **Unique Query Keys Targeted** | 19,200 | 6,000 | **25,200** |
| **Total Usable Feature Rows** | **18,926** | **1,912** | **20,838** |
| **DoH Usable Captures (TCP 443)** | 9,478 | 1,912 | **11,390** |
| **DoH/3 Usable Captures (UDP 443)**| 9,448 | 0 (100% timed out) | **9,448** |
| **Evaluated Candidate Domains** | 200 (100 Global, 100 India) | 100 (50 Global, 50 India) | 200 unique |
| **Shared Cross-Network Domains** | — | — | **50 per workload** |
| **Upstream Resolvers Evaluated** | 4 (Google, Cloudflare, AdGuard, Quad9) | 3 (Google, Cloudflare, AdGuard) | 4 |

---

## 6. Processed Dataset Schema (`dataset_combined.csv`)

The consolidated table contains 52 columns: 8 identification/context labels and 44 numerical traffic features.

| Column Category | Column Names | Data Type | Description |
| :--- | :--- | :--- | :--- |
| **Labels & Context** (8) | `network` | string | `airtel` or `jio` |
| | `resolver` | string | `adguard`, `cloudflare`, `google`, `quad9` |
| | `protocol` | string | `doh` or `doh3` |
| | `workload` | string | `global` or `india` |
| | `domain` | string | Fully qualified domain name (target label) |
| | `repeat` | integer | Repeat index ($0 \dots 19$) |
| | `pcap_path` | string | Relative path to local PCAP |
| | `latency_s` | float | Total DNS client resolution duration (seconds) |
| **Traffic Features** (44) | `n_pkts` $\dots$ `pkt_19` | integer / float | 44 directional flow features (see `features.md`) |
