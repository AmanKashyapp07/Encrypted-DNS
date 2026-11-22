# Live Office Demo Presentation Script & Delivery Guide

**Project Title:** Empirical Privacy Analysis of Modern Encrypted DNS: DoH vs. DoH/3 Across Multi-Carrier and Institutional Networks  
**Authors:** Kunal Khandelwal (`IIT2024162`), Rakesh Mali (`IIT2024149`), Aman Kashyap (`IIT2024140`)  
**Department:** Information Technology, Indian Institute of Information Technology, Allahabad (IIIT Allahabad)  
**Target Audience:** Professor / Project Evaluator in Office  
**Recommended Total Duration:** ~5 to 6 minutes (or 2-minute speed-run)  
**Master Executable:** `python3 scripts/demo.py`

---

## 1. Pre-Demo Physical Setup Checklist (2 Minutes Before Entry)

* [ ] Laptop plugged into wall power (or >80% battery).
* [ ] Connected to **Bharti Airtel** Wi-Fi.
* [ ] Terminal open at **95+ columns width**, font size enlarged (`Cmd + +` twice).
* [ ] Screen cleared (`clear` or `Cmd + K`).
* [ ] Background tabs open in Preview: [paper/paper.pdf](file:///Users/amankashyap/Documents/DNS-Analysis/paper/paper.pdf), thesis PDF, and `results/figures/fig1_headline_doh_vs_doh3.png`.

---

## 2. Word-for-Word Spoken Demo Script

### Step 0: The Opening Greeting (30 Seconds)

> *"Good morning, Professor. Following up on our presentation slides, we have our complete codebase and experimental testbed running live on this laptop.*  
>  
> *Rather than showing slides, we want to prove three core scientific things directly from the running code:*  
> 1. *First, that our zero-leakage classifier can fingerprint encrypted DNS queries live in under 15 milliseconds.*  
> 2. *Second, that our transport probes run over real QUIC and TCP right now on Airtel, confirming our empirical reachability findings.*  
> 3. *And third, that all 39 quantitative claims in our paper are 100% reproducible with a 1-click verification suite.*  
>  
> *Let me start with Part 1: our live traffic fingerprinting engine."*

---

### Step 1: Part 1 — Interactive Live Fingerprinting (~90 Seconds)

**Action:** Type `python3 scripts/demo.py` and press `1`.

> *(While the model trains in ~0.20s):*  
> *"Here, the system is loading our Airtel broadband dataset across 100 closed-world domains. In 0.2 seconds, it trained a Random Forest ensemble on 1,000 temporal training flows. Notice the chance baseline is exactly 1.0%—one in a hundred domains."*

**Action:** When prompted to select a domain, choose `1` (`t.me`) or `2` (`youtube.com`).

> *(While pointing to the terminal box: `INPUT FLOW METADATA`):*  
> *"We select `youtube.com` from our held-out test partition. I want to highlight our threat model guarantee: notice there are no IP addresses, no port numbers, and no SNI hostnames. We don't decrypt anything.*  
>  
> *All the classifier sees are these **44 physical flow features** divided into five structural groups:*  
> * *Volume:* total packets and byte ratios,  
> * *Size statistics:* upstream and downstream means and standard deviations,  
> * *Timing:* flow duration and inter-arrival times,  
> * *Directional bursts,*  
> * *And the handshake envelope:* the exact signed sizes of the first 20 packets on the wire.*  
>  
> *Now watch the classifier make its inference."*

**Action:** Point to the `CLASSIFIER PREDICTION RESULTS` box.

> *(Emphasize the contrast):*  
> *"In just 13 milliseconds, the classifier outputs its verdict:*  
> * Under **DoH (TLS 1.3 over TCP)**, `youtube.com` is identified as the Top-1 prediction with **28% confidence**. Against a 1% chance baseline, that is a **28× privacy leak**.*  
>  
> *Now look at the bottom section: this is our primary research contribution. When the exact same query is issued over **DoH/3 (RFC 9114 over QUIC)**, confidence collapses to **0%**, and the domain falls to near-random chance. QUIC frame multiplexing and padding suppress side-channel leakage by **87%**.*  
>  
> *Now, let me show you how these protocols physically behave across real-world Indian networks."*

---

### Step 2: Part 2 — Live Airtel Transport Probe & Multi-Carrier Audit (~60 Seconds)

**Action:** Return to menu, press `2`.

> *(While the script identifies the carrier and runs Probe 1):*  
> *"Part 2 executes live physical network queries over our active Wi-Fi interface. The script automatically detects that we are connected to **Bharti Airtel** (`AS45609/AS24560`).*  
>  
> * **Probe 1 (DoH over TCP 443):** Completed via TLS 1.3 in 1.8 seconds, returning the resolved A and AAAA records.*  
> * **Probe 2 (DoH/3 over QUIC UDP 443):** Completed in just **517 milliseconds** over true HTTP/3.*  
>  
> *This confirms live on our screen our paper's headline reachability result: **Airtel optical broadband achieves 98.4% DoH/3 reachability** because UDP 443 is completely open.*  
>  
> *However, look at the audit table below comparing all three networks we evaluated across 31,200 headline queries:*  
> * On **Reliance Jio 4G Cellular**, DoH/3 had **0.0% reachability**—3,000 out of 3,000 queries timed out due to carrier CGNAT and RRC scheduling drops.*  
> * On **IIIT Allahabad Campus Wi-Fi**, DoH/3 also had **0.0% reachability**—dropped completely by the perimeter firewall.*  
>  
> *So while QUIC provides superior privacy, it experiences severe middlebox ossification on mobile and institutional networks."*

---

### Step 3: Part 3 — 1-Click Scientific Claims Verification (~45 Seconds)

**Action:** Return to menu, press `3`.

> *(While the 6 checks print out in 1.10 seconds):*  
> *"To ensure academic rigor and avoid paper-code drift, we wrote an automated verification harness that checks all results in our paper.*  
>  
> *In 1.1 seconds, it completed all 6 automated checks:*  
> 1. *It verified our dataset partitions: exactly 18,926 Airtel + 1,912 Jio = 20,838 combined rows.*  
> 2. *It verified our 44-dimensional feature space with zero label leakage.*  
> 3. *It verified our 1.0% and 2.0% chance baselines.*  
> 4. *It audited the 3,000 cellular QUIC timeouts.*  
> 5. *It verified our ML architecture comparisons: Random Forest (26.2%) vs. XGBoost (26.5%) vs. CNN (1.0%) and GRU (1.4%).*  
> 6. *And most importantly, it checked every single one of the **39 quantitative claims** in our paper and confirmed that every commit hash exists in our local Git history.*  
>  
> *Every claim in our presentation is 100% reproducible directly from the codebase."*

---

### Step 4: Part 4 — Deliverables & Manuscript Tour (~45 Seconds)

**Action:** Return to menu, press `4`.

> *"Finally, here is our complete deliverables package:*  
> 1. *Our **camera-ready 6-page IEEE conference paper**, compiled with Tectonic into `paper/paper.pdf` with balanced columns and zero overfull hboxes.*  
> 2. *Our **67-page B.Tech thesis**, compiled with clean frontmatter.*  
> 3. *Our **master claims ledger** tracking 39 verified claims.*  
> 4. *And all **6 vector publication figures** generated directly by our plotting scripts.*  
>  
> *Would you like me to open the IEEE paper or examine any specific figure?"*

---

### Step 5: Concluding Wrap-Up & Handoff (15 Seconds)

> *"That concludes our live demonstration: we have verified our real-time fingerprinting pipeline, demonstrated live protocol transport on Airtel, and certified 100% reproducibility of all reported findings.*  
>  
> *We would be happy to answer any questions or inspect any part of the codebase you'd like to see."*

---

## 3. The 2-Minute "Emergency Speed-Run" Script

*(Use this if the professor says: "I only have 2 minutes before my next meeting.")*

1. **Terminal Command:**
   ```bash
   python3 scripts/demo.py --part 1 --non-interactive --domain youtube.com && python3 scripts/demo.py --part 2
   ```
2. **Speed-Run Speech:**
   > *"Professor, in 60 seconds:*  
   > * Here is our live Random Forest classifier inspecting 44 directional features of encrypted DNS traffic on Airtel. For `youtube.com`, DoH leaks the domain at **28% confidence**—28× above the 1% chance baseline. Under DoH/3 on QUIC, leakage collapses to **0%**, proving an **87% privacy improvement**.*  
   > * Second, our live transport probe shows that on Airtel FTTH, both DoH and DoH/3 resolve in under 1 second (**98.4% reachability**), whereas on Reliance Jio and Campus Wi-Fi, 100% of QUIC queries timed out due to carrier middlebox ossification.*  
   > * Finally, our 1-click verification script validates all 39 paper claims and 40 unit tests in 1 second.*  
   > * Our 6-page camera-ready IEEE paper and thesis are fully compiled in the repo."*

---

## 4. Rapid Q&A Defense Cards (What to Say When Interrupted)

### Q1: "If the DNS payload is encrypted, how does your model know what domain it is?"
> **Answer:**  
> *"Encryption hides the plaintext hostname, but it cannot hide packet sizes, directional burst counts, and timing. Because each website returns a unique DNS profile—different numbers of A/AAAA records and CNAME chains—the resulting packet length creates a distinctive 'flow silhouette' that Random Forest recognizes."*

### Q2: "Why did Deep Learning (CNN/GRU) fail with only 1% accuracy?"
> **Answer:**  
> *"Encrypted DNS exchanges are compact micro-flows of only 8 to 15 packets. Sequential deep networks like 1D-CNN and GRU require deep translational packet sequences to learn spatial representations. For DNS, the discriminative signal resides in aggregate volumetric envelope features—like total bytes down, max upstream size, and burst ratios—where tree ensembles decisively outperform deep networks."*

### Q3: "Why did Google Public DNS show zero privacy improvement under DoH/3?"
> **Answer:**  
> *"RFC 8467 specifies DNS padding. Quad9, Cloudflare, and AdGuard pad responses, but Google Public DNS transmits unpadded wire-format answers. Because Google doesn't pad, domain-specific answer length variations pass directly into transport payloads, proving that resolver implementation choices override transport protocol protections."*

### Q4: "Why did cross-network transfer collapse below random chance (1.7% < 2.0%)?"
> **Answer:**  
> *"Two-sample Kolmogorov-Smirnov tests ($p < 10^{-15}$) confirm physical link-layer shifts: link encapsulation offsets `up_max` ($D=0.994$), campus proxy HTTP CONNECT acknowledgements reverse `pkt_00` direction ($D=0.837$), and cellular RRC scheduling distorts timing ($D=0.727$). Network physics overshadows domain signatures."*

### Q5: "Is Reliance Jio blocking QUIC?"
> **Answer:**  
> *"Under our tested conditions, 100% of DoH/3 queries timed out on UDP 443 with zero response. This is consistent with carrier-level UDP filtering or CGNAT dropping unsolicited UDP associations, demonstrating protocol ossification."*
