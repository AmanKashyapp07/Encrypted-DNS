# Final Submission & Presentation Package
## Encrypted DNS Traffic Fingerprinting Across Multi-Carrier & Enterprise Networks

**Author:** Aman Kashyap (`iit2024140@iiita.ac.in`)  
**Department:** Information Technology, Indian Institute of Information Technology, Allahabad (IIIT Allahabad)  
**Research Context:** Research Methodology Coursework, November 2026  
**GitHub Repository:** [github.com/AmanKashyapp07/Encrypted-DNS](https://github.com/AmanKashyapp07/Encrypted-DNS)  
**Status:** All empirical captures, 44-feature extraction, statistical analyses, and verification checks are locked and reproducible.

---

## Directory Contents & Guide for Professor

This `final/` folder contains the curated, submission-ready deliverables for presentation and academic grading:

```
final/
├── README.md               # This index, project guide, and submission overview
├── findings_report.md      # Executive Brief (Research Scope, 5 Findings, Conclusions)
├── paper.md                # Full Academic Research Paper Manuscript (9 sections, 12 tables)
├── presentation_slides.md  # 10-Slide Deck with Speaker Notes & Viva/Defense FAQ
├── claims_ledger.csv       # Verification ledger mapping all empirical claims to source CSVs
└── figures/                # Publication-grade figures (300 DPI vector PNGs)
    ├── fig1_headline_doh_vs_doh3.png        # DoH vs DoH/3 comparison on broadband
    ├── fig2_cross_network_transfer.png      # Airtel <-> Jio pairwise transfer
    ├── fig3_carrier_quic_blocking.png       # Jio cellular QUIC reachability breakdown
    ├── fig4_feature_distribution_shift.png  # Kolmogorov-Smirnov CDF feature shifts
    ├── fig5_tri_network_reachability.png    # Tri-network reachability & UDP 443 blocking
    └── fig6_tri_network_transfer_matrix.png # 3x3 Cross-network transfer matrix heatmap
```

---

## Document Summary & Review Guide

### 1. `findings_report.md` — The Executive Brief (Recommended First Read)
* **Target Audience:** Professor / Examiner looking for a rapid 5-minute summary of findings.
* **Contents:**
  * **Section 1: Research Scope:** Background on DoH (RFC 8484) vs. DoH/3 (RFC 9114), 3 research questions, experimental design, 3 network archetypes, and explicit scope boundaries.
  * **Section 2: Five Key Findings:**
    1. *Finding 1:* DoH/3 reduces leakage by 57%–85% on padded resolvers (Quad9, Cloudflare), but Google's unpadded responses limit gains to 30%.
    2. *Finding 2:* Universal QUIC reachability failure on mobile and campus networks (6,000/6,000 attempts failed on UDP 443; 0.0% reachability).
    3. *Finding 3:* Cross-network transfer collapses to chance (1.7%–2.7% vs. 2.0% chance) across all 6 directional pairs in the $3 \times 3$ matrix.
    4. *Finding 4:* Institutional forward proxies act as an unintended privacy shield (1.8%–5.6% within-campus accuracy).
    5. *Finding 5:* Multi-vantage co-training restores adversarial power to 20.67% composite accuracy (10.3× above chance).
  * **Section 3: Overall Conclusions & Practical Implications:** Actionable takeaways for users, resolver operators, network admins, and researchers.

### 2. `paper.md` — The Formal Academic Paper Manuscript
* **Target Audience:** Reviewers evaluating formal academic writing, related literature, threat model, and comprehensive methodology.
* **Structure:** 9 Sections, 12 data tables, formal math notation:
  * Abstract & Section 1: Introduction and contributions
  * Section 2: Related Work (classical WFP vs. encrypted DNS)
  * Section 3: Threat Model (passive on-path adversary, zero-label leakage)
  * Section 4: Experimental Methodology (44 features, leave-repeat-out temporal splits, permutation tests)
  * Section 5: Empirical Results (Airtel, Jio, Campus Wi-Fi, Tri-network matrix, n-grams, deep sequence models, open-world, scaling, time stability, defenses)
  * Section 6: Discussion (QUIC implications, resolver variance, proxy shielding, Indian ISP context)
  * Section 7–9: Limitations, Ethics & Reproducibility, Conclusion

### 3. `presentation_slides.md` — Slide Deck & Viva Defense Guide
* **Target Audience:** Presentation delivery and viva/oral defense.
* **Structure:**
  * 10 structured presentation slides with complete visual layouts.
  * **Speaker Notes:** Dedicated scripts with estimated timings for an 8–10 minute presentation.
  * **Appendix: Professor Defense & Viva Cheat Sheet:** Data-backed answers to the top 5 challenging questions examiners typically ask.

### 4. `claims_ledger.csv` — Reproducibility & Audit Trail
* **Purpose:** Maps every quantitative statement in the paper directly to execution CSV artifacts, sample sizes, confidence intervals, analysis scripts, and git commit hashes.
* **Verification:** Validated by `python3 scripts/verify_research_results.py` (6/6 checks pass).

---

## Empirical Scale at a Glance

* **Total Raw Capture Attempts:** 34,400 queries (22,400 Airtel broadband + 6,000 Jio cellular + 6,000 Campus Wi-Fi).
* **Usable Zero-Leakage Flow Traces:** 22,407 completed flows (18,926 Airtel + 1,912 Jio + 1,569 Campus).
* **Workloads & Resolvers:** 100 pinned domains (50 Global, 50 India) across 4 upstream recursive resolvers (Google, Cloudflare, Quad9, AdGuard).
* **Feature Space:** 44 directional flow features (sizes, counts, bursts, inter-arrival times, handshake packet sequences; no IP/port/SNI leakage).
* **Testing:** 34 automated unit tests (`tests/`) and 6 automated consistency checks (`scripts/verify_research_results.py`).
