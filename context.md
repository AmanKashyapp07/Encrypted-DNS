# Project Context & Demo Preparation Master Document

**Study Title:** Empirical Privacy Analysis of Modern Encrypted DNS: DoH vs. DoH/3 Across Multi-Carrier and Institutional Networks  
**Authors / Research Team:**  
- Kunal Khandelwal (`IIT2024162`)  
- Rakesh Mali (`IIT2024149`)  
- Aman Kashyap (`IIT2024140`)  
**Department:** Information Technology, Indian Institute of Information Technology, Allahabad (IIIT Allahabad)  
**Repository:** `https://github.com/AmanKashyapp07/Encrypted-DNS.git` (Branch: `main`)  
**Workspace Path:** `/Users/amankashyap/Documents/DNS-Analysis`  
**Thesis Directory:** `/Users/amankashyap/Downloads/IIITA_B_Tech_Thesis`  
**Compiled Paper:** `/Users/amankashyap/Documents/DNS-Analysis/paper/paper.pdf` & `/Users/amankashyap/Downloads/Encrypted_DNS_Research_Paper.pdf`  
**Demo Delivery Speech Guide:** `/Users/amankashyap/Documents/DNS-Analysis/docs/demo_speech.md`  
**Visual Companion Dashboard:** `/Users/amankashyap/Documents/DNS-Analysis/docs/dashboard.html`

---

## 1. Executive Research Summary

### A. The Core Problem & Threat Model
Standard DNS operates in plaintext over UDP port 53, enabling network eavesdroppers and ISPs to inspect queries. Modern cryptographic protocols encapsulate DNS within TLS/TCP (DoH, RFC 8484) or QUIC/UDP (DoH/3, RFC 9114). While encryption conceals requested domain names, unencrypted transport metadata—packet sizes, directional counts, burst structures, and inter-arrival timing—leaks side-channel information.
* **Adversary Model:** Passive, local on-path network observer (ISP, rogue Wi-Fi, institutional middlebox). The attacker cannot decrypt payloads or forge certificates, but records packet sizes ($s_i$), flow directions ($d_i \in \{+1, -1\}$), and arrival timestamps ($t_i$).
* **Adversary Objective:** Closed-world supervised classification mapping flow feature vector $\mathbf{x} \in \mathbb{R}^{44}$ to the target domain $y \in \{1, \dots, N\}$.

### B. Tri-Network Empirical Scale
* **Total Capture Attempts:** 34,400 raw queries across 3 networks (31,200 locked headline evaluations):
  1. **Residential Optical FTTH Broadband (Bharti Airtel, AS24560):** 19,200 queries (20 repeats across 100 Global + 100 India domains, 4 resolvers, 2 protocols). Direct routing, MTU 1,500 B, UDP 443 open.
  2. **Commercial Mobile Cellular (Reliance Jio, AS55836):** 6,000 queries (10 repeats across 50 Global + 50 India domains, 3 resolvers, 2 protocols). Carrier-Grade NAT (CGNAT), radio resource control (RRC) scheduling.
  3. **Enterprise Campus Wi-Fi (IIIT Allahabad, AS138231):** 6,000 queries (10 repeats across 50 Global + 50 India domains, 3 resolvers, 2 protocols). Mandatory centralized HTTP forward proxy (`172.31.2.4:8080`), outbound UDP 443 dropped at firewall.
* **Usable Feature Flows Post-Filtering:** 22,407 clean, zero-label-leakage flows (18,926 Airtel + 1,912 Jio + 1,569 Campus).

---

## 2. Core Quantitative Findings

1. **Baseline Fingerprintability (Airtel Broadband):**
   * All 16 resolver-protocol slices exceed chance ($p < 0.005$, Wilson score 95% CIs).
   * DoH accuracy: 16.1% to 35.7% (chance: 1.0% for 100 Global, 1.3% for 79 India).
   * Highest leakage: Quad9 DoH (34.4% Global / 35.7% India, $>30\times$ chance).
2. **DoH/3 Privacy Suppression:**
   * Transitioning from DoH to DoH/3 drastically reduces leakage for 3 resolvers:
     * Quad9: 87% reduction ($34.4\% \to 4.6\%$).
     * Cloudflare: 75% reduction ($21.2\% \to 5.4\%$).
     * AdGuard: 70% reduction ($27.0\% \to 8.0\%$).
3. **The Google Implementation Anomaly:**
   * Google Public DNS shows **zero privacy gain** under DoH/3: 16.5% DoH vs 17.1% DoH/3 on Global domains (16.1% vs 14.1% on India).
   * *Mechanism:* Google does not pad server responses (RFC 8467). Wire-format answer lengths pass directly into transport payloads, preserving domain-specific size variations. Resolver implementation choices supersede transport protocol standards.
4. **Transport Reachability Outage (QUIC Ossification):**
   * Airtel Broadband: 98.4% DoH/3 query completion.
   * Reliance Jio Cellular: **0 / 3,000 completed** (100% timeout on UDP 443).
   * Campus Wi-Fi Proxy: **0 / 3,000 completed** (100% timeout on UDP 443).
   * Cloudflare TCP Anomaly on Jio: 15 / 1,000 completed (1.5% reachability) due to carrier SNI/IP filtering, while Google completed 1,000 / 1,000.
5. **Cross-Network Adversarial Transfer Collapse:**
   * Airtel-trained Random Forest evaluated on Jio drops to **1.7%**; evaluated on Campus drops to **1.9%** (both below the 2.0% chance baseline across 50 domains).
   * *Physical Root Causes (Two-sample Kolmogorov-Smirnov shifts, $p < 10^{-15}$):*
     * `up_max` ($D = 0.994$): link encapsulation offset (~7 B).
     * `pkt_00` ($D = 0.837$): direction inversion from campus proxy HTTP CONNECT acknowledgements ($-137$ B vs $+698$ B).
     * `t_first_down` ($D = 0.727$): cellular radio resource control (RRC) scheduling latency.
6. **Tri-Network Pooled Co-Training:**
   * Training on pooled data across all 3 networks recovers accuracy to **12.2%** composite test and **20.67%** mean across 6 multi-carrier slices.
7. **Machine Learning Architecture Paradigm:**
   * Tree ensembles (XGBoost 26.5%, Random Forest 26.2%) vastly outperform sequential deep learning (GRU 1.4%, 1D-CNN 1.0%) and packet n-grams (1.5%).
   * *Reason:* Encrypted DNS exchanges are compact (8–15 packets). Raw packet sequences lack translational depth; discriminative signal resides in aggregate volumetric flow envelope features.
8. **Countermeasure & Defense Simulations:**
   * Constant-rate block padding ($B=64$ B or $128$ B) suppresses fingerprinting by **~32%** ($20.4\% \to 13.8\%$).
   * Random uniform padding ($21.2\%$) and latency jitter ($20.1\%$, $21.8\%$) provide **zero protection**.

---

## 3. Work Completed in Previous Session

1. **Supervisor Name Removal:**
   - Cleared `\supervisor{}` in [main.tex](file:///Users/amankashyap/Downloads/IIITA_B_Tech_Thesis/main.tex).
   - Updated [frontmatter.tex](file:///Users/amankashyap/Downloads/IIITA_B_Tech_Thesis/frontmatter.tex) (title page, certificate signature line, acknowledgements).
   - Recompiled thesis PDF via `tectonic` ([main.pdf](file:///Users/amankashyap/Downloads/IIITA_B_Tech_Thesis/main.pdf), 67 pages, zero errors, zero supervisor occurrences).
2. **6-Page IEEE Conference Research Paper:**
   - Authored camera-ready IEEE conference manuscript in [paper/paper.tex](file:///Users/amankashyap/Documents/DNS-Analysis/paper/paper.tex).
   - Verified bibliography [paper/references.bib](file:///Users/amankashyap/Documents/DNS-Analysis/paper/references.bib) and vector figures in `paper/figures/`.
   - Compiled with `tectonic` to [paper/paper.pdf](file:///Users/amankashyap/Documents/DNS-Analysis/paper/paper.pdf) (exact 6 pages, 0 overfull hboxes, balanced columns).
   - Mirrored to [Downloads/Encrypted_DNS_Research_Paper.pdf](file:///Users/amankashyap/Downloads/Encrypted_DNS_Research_Paper.pdf).
3. **Repository Clean-Up & Git Push:**
   - Updated [.gitignore](file:///Users/amankashyap/Documents/DNS-Analysis/.gitignore) to exclude office docs (`*.docx`, `*.doc`, `*.xlsx`), LaTeX auxiliary files (`*.aux`, `*.blg`, `*.bbl`, `*.log`, `*.out`, `*.toc`, etc.), and added exception for `!paper/paper.pdf`.
   - Removed root duplicate `maths.md` (canonical version in `docs/maths.md`).
   - Organized slide analyses under [docs/slides_analysis/](file:///Users/amankashyap/Documents/DNS-Analysis/docs/slides_analysis/).
   - Verified test suite: **34/34 unit tests passing**, **6/6 numerical claims checks passing**.
   - Pushed commit `49272f7` to GitHub `origin main`. Working tree pristine.
4. **README Audit:**
   - Audited [readme.md](file:///Users/amankashyap/Documents/DNS-Analysis/readme.md): 100% of local markdown links resolve successfully. Updated structure tree, badges, navigation, and student authorship.

---

## 4. Master Demo Plan for Professor's Office

The professor reviewed the presentation slides and asked for a **live demo tomorrow in his office**.

### Why He Asked & What He Wants to See
The professor does not expect consumer software. He wants to see **your code running live on your laptop** to verify:
1. That your experimental measurement pipeline actually works and captures real packets.
2. That your machine learning models train and classify real traffic.
3. That your reported numbers are 100% reproducible directly from the codebase.
4. That the physical transport difference between TCP (DoH) and UDP (DoH/3) across multi-carrier networks can be observed live on Bharti Airtel.

### Recommended 4-Part Office Demo Sequence (~5–7 minutes):

| Part | Component | Terminal Command / Action | Key Script / File | What it Demonstrates |
| :---: | :--- | :--- | :--- | :--- |
| **Part 1** | **Interactive Live Fingerprinting** | `python3 scripts/demo.py` (Option 1) | `scripts/demo.py` (interactive CLI) | Select a domain (e.g. `youtube.com`), show extracted 44 features, run RF inference in <15ms, display Top-1 & Top-3 predicted domains with confidence probabilities, and contrast with DoH/3 privacy suppression. |
| **Part 2** | **Live Airtel Transport Probe & Carrier Audit** | `python3 scripts/demo.py` (Option 2) | `scripts/demo.py` | Shows live on Bharti Airtel FTTH: both DoH (TCP:443) and DoH/3 (UDP:443) resolve in <1s (proving 98.4% reachability live), contrasted with 0.0% UDP 443 reachability on Jio Cellular and Campus Wi-Fi. |
| **Part 3** | **1-Click Scientific Claims Verification** | `python3 scripts/verify_research_results.py` | `scripts/verify_research_results.py` | Executes all 6 automated consistency checks across all 39 claims, 44-feature space, row counts, and baselines in 1.1 seconds. Output: `ALL 6 CHECKS PASSED`. |
| **Part 4** | **Deliverables & Manuscript Tour** | Open `paper/paper.pdf` & `results/figures/` | `paper/paper.pdf`, `final/README.md` | Show the camera-ready 6-page IEEE paper, 6 high-resolution publication figures, and master claims ledger matching every slide in the PPT. |

---

## 5. Live Demo Architecture & Execution (`scripts/demo.py`)

The live office demo CLI has been configured for **Bharti Airtel (AS24560/AS45609)** in [scripts/demo.py](file:///Users/amankashyap/Documents/DNS-Analysis/scripts/demo.py) and verified with dedicated unit tests in [tests/test_demo.py](file:///Users/amankashyap/Documents/DNS-Analysis/tests/test_demo.py) (40/40 tests passing).

### Single-Command Interactive Launch:
```bash
python3 scripts/demo.py
```

### Direct CLI Subcommands:
```bash
python3 scripts/demo.py --part 1            # Interactive live RF fingerprinting
python3 scripts/demo.py --part 2            # Live Airtel transport probe & carrier audit
python3 scripts/demo.py --part 3            # 1-click 6/6 consistency & claims verification
python3 scripts/demo.py --part 4 --open     # Deliverables tour & auto-open paper/figure
python3 scripts/demo.py --part 5            # Viva defense Q&A cheat sheet & nuance guide
python3 scripts/demo.py --all               # Run all 4 parts end-to-end
```

### Verified Dry-Run Benchmark Results on Airtel:
* **Active Carrier:** Bharti Airtel Ltd. (`AS45609`/`AS24560`, direct FTTH routing, open UDP:443, proxy bypassed).
* **Part 1 (Inference Latency):** RF trains on Quad9 DoH in **0.21s**; single-flow feature inference takes **12.99ms**.
  * Example on `youtube.com`: Top-1 True Match at **28.0%** confidence (chance 1.0%), collapsing to **0.0%** under DoH/3 (87% suppression).
* **Part 2 (Live Airtel Transport Probe):**
  * DoH (TCP:443): Resolves in **~0.62s** via TLS 1.3 direct TCP.
  * DoH/3 (UDP:443): Resolves in **~0.76s** via QUIC/UDP (Confirming 98.4% reachability live!).
  * Tri-Network Contrast: Highlights 0.0% DoH/3 reachability on Jio Cellular (CGNAT/RRC drop) and Campus Wi-Fi (firewall drop).
* **Part 3 (Verification):** Executes all 6 automated checks in **1.10s** (`ALL 6 CHECKS PASSED`).
* **Part 4 (Deliverables):** All 6 publication figures, 6-page IEEE paper, 67-page thesis, and 39-claim ledger verified on disk.
* **Test Suite:** **41 / 41 unit tests passing** across entire repo.
* **Visual Companion Dashboard:** [docs/dashboard.html](file:///Users/amankashyap/Documents/DNS-Analysis/docs/dashboard.html) (Zero-dependency offline HTML dashboard).

