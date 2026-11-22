# Final Research Presentation: Speech and Speaker Notes
**Study Title:** DoH vs DoH/3: A Traffic-Analysis Study of Encrypted DNS Fingerprinting on Indian Networks  
**Presenters:** Kunal Khandelwal (`IIT2024162`), Rakesh Mali (`IIT2024149`), Aman Kashyap (`IIT2024140`)  
**Department:** Information Technology, IIIT Allahabad — Research Methodology Coursework, November 2026  
**Source Presentation Deck:** `RM-Presentation-v3.pdf` / `RM-Presentation-v5.pptx`  
**Status:** Audited and Verified against Empirical Data Repository (`data/processed/`, `results/`, `claims_ledger.csv`)

---

## 1. Division of Slides & Presentation Mechanics

The presentation follows a natural 3-stage research narrative: foundations and architecture, then methodology and empirical findings, then generalization, limitations, and defense.

* **Member 1: Kunal Khandelwal (Slides 1–5 | ~4 minutes)**  
  *Scope:* Introduction, problem statement, threat model, research questions, experimental design, dataset scale, and capture-to-classification architecture.
* **Member 2: Rakesh Mali (Slides 6–10 | ~4–5 minutes)**  
  *Scope:* Evaluation methodology, DoH vs DoH/3 results on Airtel FTTH, machine learning model comparison, multi-network leakage (Jio & Campus Wi-Fi), and cross-network transfer collapse.
* **Member 3: Aman Kashyap (Slides 11–15 | ~4–5 minutes)**  
  *Scope:* Pooled training recovery (pairwise & tri-network), DoH/3 reachability & QUIC transport analysis, limitations & defense boundaries, conclusions, and leading the Q&A defense.

**Target Presentation Duration:** 12 to 14 minutes total (~4 minutes per speaker), leaving 5–6 minutes for viva questions.

---

## 2. Complete Word-for-Word Presentation Script

### Member 1: Kunal Khandelwal
**Slides 1–5 | Foundations, Threat Model & System Architecture**

#### Slide 1: Title & Overview
> *"Good morning, respected faculty members and evaluators.*  
>  
> *We are here to present our research titled: **'DoH vs DoH/3: A Traffic-Analysis Study of Encrypted DNS Fingerprinting on Indian Networks.'** This work was conducted by Kunal Khandelwal, Rakesh Mali, and Aman Kashyap.*  
>  
> *Our research addresses a fundamental question in modern Internet privacy: When a user encrypts their DNS traffic using modern standards like DNS-over-HTTPS or DNS-over-QUIC, can a passive network observer still infer which website they are visiting simply by inspecting the shape, size, and timing of the traffic?*  
>  
> *To answer this, we conducted an extensive empirical measurement campaign across three distinct network environments: Airtel FTTH residential broadband, Reliance Jio 4G cellular, and the IIIT Allahabad campus Wi-Fi network.*  
>  
> *Across 34,400 raw collection attempts, we curated a zero-leakage dataset of 22,407 usable traffic traces, engineered 44 transport-agnostic metadata features, and evaluated both tree-based and deep neural sequence models.*  
>  
> *I will begin by outlining our research motivation, threat model, and experimental architecture."*

---

#### Slide 2: Research at a Glance
> *"Let us start with our central research question: **Can encrypted DNS traffic metadata reveal the target domain without decrypting any encrypted payloads?***  
>  
> *To evaluate this, we captured both DoH—operating over HTTP/2 and TLS—and DoH/3—operating over HTTP/3 and QUIC—across four major public recursive resolvers: AdGuard, Cloudflare, Google, and Quad9.*  
>  
> *Our dataset spans 34,400 raw collection attempts. After rigorous quality and usability checks, we retained 22,407 verified flow traces: 18,926 from Airtel FTTH, 1,912 from Jio cellular, and 1,569 from campus Wi-Fi.*  
>  
> *Our main empirical finding is that DoH/3 noticeably reduces observed fingerprinting accuracy across all four tested resolvers on Airtel FTTH. However, the magnitude of this privacy gain varies substantially across resolvers.*  
>  
> *We emphasize an essential methodological boundary: our research analyzes external traffic patterns and flow silhouettes. We do not decrypt DNS payloads, inspect private keys, or identify individual users."*

---

#### Slide 3: Motivation, Threat Model & Research Questions
> *"Why is payload encryption not the entire privacy story?*  
>  
> *While cryptographic protocols like TLS and QUIC secure message contents from plaintext snooping, transport-level side-channels remain exposed on the physical wire. A passive eavesdropper can still observe packet counts, total byte volumes, direction changes, and burst timings.*  
>  
> *Our threat model assumes a **passive adversary** observing local network links, ISP gateways, or institutional proxies. This observer has:*
> 1. *No capability to decrypt encrypted payloads.*
> 2. *Zero access to endpoint state or TLS session keys.*
> 3. *And in our classifiers, we strictly exclude IP addresses, port numbers, SNI hostnames, and DNS header fields.*
>  
> *To investigate this threat model systematically, we formulated three research questions:*  
> * **RQ1:** How accurately can encrypted DNS requests be fingerprinted within each local network environment?  
> * **RQ2:** How do fingerprinting vulnerabilities compare between DoH and DoH/3 on residential broadband?  
> * **RQ3:** Do fingerprinting models generalize across different carrier boundaries like Airtel, Jio, and campus Wi-Fi, and can multi-vantage joint training recover predictive signal?*  
>  
> *These questions enable us to evaluate not just whether leakage exists, but how protocol design, resolver implementations, and physical access networks interact."*

---

#### Slide 4: Experimental Design & Dataset
> *"To ensure real-world ecological validity, our testbed spans three physical network archetypes:*  
> 1. *First, **Airtel FTTH**, representing high-speed residential fiber broadband.*  
> 2. *Second, **Reliance Jio**, representing mobile cellular connectivity over 4G/LTE.*  
> 3. *Third, **IIIT Allahabad Campus Wi-Fi**, representing an enterprise institutional network where all outbound web traffic is routed through an authenticated HTTP forward proxy.*  
>  
> *We evaluated four major public recursive resolvers: AdGuard, Cloudflare, Google, and Quad9. Airtel experiments included all four resolvers. On Jio cellular and campus Wi-Fi, three resolvers were evaluated—AdGuard, Cloudflare, and Google—while Quad9 was omitted due to pre-capture reachability constraints.*  
>  
> *Our workload comprises 100 closed-world domains on Airtel and 50 domains on Jio and Campus, drawn from the top ranks of the Tranco snapshot across Global and India-specific workloads. We performed 20 collection repeats per domain on Airtel and 10 repeats on Jio and Campus.*  
>  
> *Crucially, our evaluation avoids random cross-validation, which causes temporal data leakage. Instead, we enforce a strict **temporal holdout split**: earlier collection repeats are used for model training, and the final two repeats are held out exclusively for testing. Against these test sets, the uniform random guessing chance baseline is 1.0% for the 100-domain Airtel experiments and 2.0% for the 50-domain Jio and Campus experiments."*

---

#### Slide 5: System Architecture: Capture to Classification
> *"This slide summarizes our end-to-end experimental pipeline across six distinct stages:*  
> * *Stage 1 is **Domain Workload Selection**, sourcing standardized Global and India domain lists.*  
> * *Stage 2 is the **DNS Client**. We use the `q` client to dispatch queries over DoH using HTTP/2, and over DoH/3 using HTTP/3 over QUIC. On campus, DoH traffic is routed via the institutional forward proxy.*  
> * *Stage 3 is **Traffic Capture**. Using `dumpcap` and `tshark`, we record isolated, per-query PCAP micro-flows bounded by kernel-level BPF filters on port 443.*  
> * *Stage 4 is **Feature Extraction**. For every usable flow, we extract 44 numerical features across five orthogonal groups: 7 volume features, 6 packet-size statistics, 6 timing dynamics, 5 burst features, and a 20-packet signed length sequence representing the initial handshake.*  
> * *Stage 5 is **Model Training and Statistical Validation**. We train Random Forest as our primary classifier, benchmark it against XGBoost, 1D-CNN, and GRU models across seeds 17, 42, and 101, and validate results using 200 domain-clustered permutation tests and 1,000-iteration bootstrap confidence intervals.*  
> * *Finally, Stage 6 produces our **Empirical Outputs**: within-network leakage, DoH versus DoH/3 comparisons, cross-network transfer matrices, and protocol availability metrics.*  
>  
> *This completes the experimental setup and pipeline. I will now hand over to Rakesh, who will explain our evaluation methodology and core results."*

---

### Member 2: Rakesh Mali
**Slides 6–10 | Methodology, Headline Results & Generalization Collapse**

#### Slide 6: Evaluation Methodology
> *"Thank you, Kunal.*  
>  
> *I will now explain our evaluation methodology and experimental findings. In total, we executed 34,400 query attempts across the three networks, capturing over 23 hours of active physical network traffic.*  
>  
> *From each validated PCAP trace, we extracted 44 directional features. We deliberately selected Random Forest as our primary classifier due to its proven performance on tabular network metadata, and benchmarked it against XGBoost, a 1D Convolutional Neural Network, and a Bidirectional GRU.*  
>  
> *To ensure our findings are methodologically sound and reproducible, we enforced three rigorous validation controls:*  
> 1. *First, a **strict temporal holdout**: models are trained on earlier collection repeats and evaluated on the final two repeats, testing whether models remain predictive over time.*  
> 2. *Second, to eliminate stochastic bias, all experiments are evaluated across three random seeds: 17, 42, and 101. Reported accuracies represent the arithmetic mean across these seeds.*  
> 3. *Third, we conducted **200 domain-clustered permutation tests** to establish that models learn genuine domain traffic signatures rather than background network artifacts, and computed **95% confidence intervals using 1,000 domain-clustered bootstrap iterations**.*  
>  
> *With these controls established, let us examine the results."*

---

#### Slide 7: Main Result: DoH vs DoH/3 on Airtel FTTH
> *"Slide 7 presents one of the most critical empirical findings of our study: the comparison between DoH and DoH/3 on Airtel FTTH across a 100-domain closed world.*  
>  
> *Looking at the data:*  
> * *On **Quad9**, accuracy drops dramatically from **45.2% on DoH down to 6.6% on DoH/3**—an 85% relative reduction in fingerprintability.*  
> * *On **Cloudflare**, accuracy falls from **26.3% on DoH to 7.2% on DoH/3**—a 73% relative reduction.*  
> * *On **AdGuard**, accuracy decreases from **26.2% on DoH to 11.2% on DoH/3**—a 57% relative reduction.*  
> * *However, on **Google**, accuracy decreases from **21.3% on DoH to 15.0% on DoH/3**—a reduction of only 30%.*  
>  
> *All four resolvers exhibit reduced fingerprintability under DoH/3. However, the magnitude of the reduction is resolver-dependent. Quad9, Cloudflare, and AdGuard show substantial privacy improvements because QUIC connection establishment and standard response framing conceal message boundaries.*  
>  
> *In contrast, Google showed a noticeably smaller reduction. Feature distribution analysis reveals that Google's downlink byte standard deviation remains substantial—over 750 bytes in DoH and 1,160 bytes in DoH/3—indicating that response-size variation remains observable in its tested configuration. In fact, Google is the only resolver where the 95% bootstrap confidence intervals for DoH and DoH/3 overlap.*  
>  
> *The primary takeaway is clear: changing the transport protocol from DoH to DoH/3 mitigates metadata leakage, but resolver-specific implementation choices strongly dictate the residual privacy margin."*

---

#### Slide 8: Model Comparison: AdGuard DoH, Global Workload
> *"Next, we benchmarked multiple machine-learning architectures on the representative AdGuard DoH Global slice.*  
>  
> *Our results reveal a stark contrast:*  
> * * **Random Forest** achieved **26.2% accuracy**.*  
> * * **XGBoost** achieved **26.5% accuracy**.*  
> * *Both tree ensembles perform comparably, well above the 1.0% random chance baseline, with the 0.3-point difference sitting well within seed-level variance.*  
> * *In sharp contrast, the **1D-CNN achieved 1.0%** and the **GRU achieved 1.4%**, both remaining at or near random chance.*  
>  
> *Why did deep sequence models collapse to chance? DNS transactions are micro-flows lasting only 15 to 40 packets. Unlike website fingerprinting where flows contain thousands of packets with rich sequential structure, DNS flows have compact temporal profiles. Deep neural networks struggle to generalize without extensive sequence depth, whereas tree ensembles effectively partition aggregate volume, packet-size statistics, and cumulative burst features.*  
>  
> *This confirms an important methodological lesson: architecture complexity does not guarantee performance; model selection must align with the physical dimensionality of the underlying network flows."*

---

#### Slide 9: Within-Network Leakage on Three Networks
> *"Slide 9 illustrates how within-network fingerprintability shifts across physical access networks:*  
> * *On **Airtel FTTH**, accuracy ranges between **21.3% and 45.2%** against a 1.0% chance baseline. High signal-to-noise ratios and consistent fiber latency preserve distinct per-domain flow silhouettes.*  
> * *On **Jio Cellular**, accuracy drops to between **4.1% and 15.7%** against a 2.0% chance baseline. Cellular radio scheduling, dynamic channel quality, and carrier-grade NAT queues introduce physical jitter that blurs fingerprint signatures.*  
> * *On **Campus Wi-Fi**, accuracy drops further to between **1.8% and 5.6%**, hovering close to the 2.0% chance baseline.*  
>  
> *Why is campus Wi-Fi fingerprinting so low? On campus, traffic routes through an institutional forward proxy. The proxy terminates TCP connections, multiplexes upstream requests, buffers packets, and encapsulates traffic within HTTP `CONNECT` tunnels. These middlebox dynamics naturally obfuscate flow timing and byte boundaries, acting as an unintended privacy shield.*  
>  
> *However, we emphasize that these mechanisms are technical explanations derived from feature shifts, rather than individually isolated experimental factors."*

---

#### Slide 10: Cross-Network Transfer: Airtel ↔ Jio
> *"Having shown that models achieve above-chance accuracy within their home network, we addressed our third research question: **Can an attacker train a model on one carrier and successfully deploy it against victims on another?***  
>  
> *We evaluated cross-network transfer across all network pairs. The results are decisive:*  
> * *Direct **Airtel $\leftrightarrow$ Jio cross-network transfer collapses to between 1.7% and 2.4%**, indistinguishable from the 2.0% random guessing baseline.*  
> * *Across all evaluated 50-domain pairwise transfer directions between Airtel, Jio, and Campus, accuracy remains confined within **1.7% to 2.7%**.*  
> * *Crucially, the 95% bootstrap confidence intervals overlap random chance on every single evaluated transfer slice.*  
>  
> *Why does transfer fail so completely? Two-sample Kolmogorov-Smirnov tests confirm extreme distribution shifts across network environments ($p < 10^{-15}$). For example, Jio clamps maximum packet sizes to 1,340 bytes due to cellular tunneling headers, compared to 1,500 bytes on Airtel. On campus, proxy tunneling reverses initial packet directions (`pkt_00` KS = 0.837). Models trained on residential broadband overfit to local channel characteristics that do not translate across carrier boundaries.*  
>  
> *I will now hand over to Aman, who will explain how multi-vantage pooled training addresses this collapse, our protocol reachability findings, and our final conclusions."*

---

### Member 3: Aman Kashyap
**Slides 11–15 | Generalization Recovery, Protocol Availability, Limitations & Defense**

#### Slide 11: Pooled Training: Resolver-Dependent Recovery
> *"Thank you, Rakesh.*  
>  
> *Having established that single-network models collapse across carrier boundaries, we investigated an important adversarial question: **Can an attacker overcome this limitation by pooling training data from multiple network vantages?***  
>  
> *We evaluated two pooling paradigms:*  
> 1. *First, **Pairwise Pooling** combining Airtel and Jio training data on 50 shared domains, tested on held-out temporal repeats:*  
>    * *On **Google Global**, composite accuracy recovers to **17.33%** (19.67% on Airtel held-out, 15.00% on Jio held-out).*  
>    * *On **AdGuard Global**, composite accuracy reaches **19.19%** (33.67% on Airtel held-out, 4.42% on Jio held-out).*  
>    * *On **Google India**, composite accuracy recovers to **16.33%**.*  
>    * *On **AdGuard India**, composite accuracy reaches **15.43%**.*  
> 2. *Second, we evaluated **Tri-Network Co-Training**, pooling training data from Airtel, Jio, and Campus simultaneously. Evaluated against composite held-out test sets across all three networks, co-training achieves a **mean composite accuracy of 20.67%**—more than **10 times above the 2.0% chance baseline**.*  
>  
> *The key finding here is twofold: while naive cross-network transfer fails completely, multi-vantage adversaries who capture traffic across diverse carrier vantage points can construct carrier-resilient classifiers. However, the extent of recovery remains resolver-dependent."*

---

#### Slide 12: DoH/3 Reachability on Jio and Campus Wi-Fi
> *"Slide 12 addresses a critical protocol availability finding that is often overlooked in academic literature: the real-world deployment viability of DoH/3.*  
>  
> *DoH/3 relies on HTTP/3 over QUIC, which operates over UDP port 443. During our experiments:*  
> * *On **Jio Cellular**, **3,000 out of 3,000 DoH/3 attempts timed out**, returning zero response packets.*  
> * *On **Campus Wi-Fi**, **3,000 out of 3,000 DoH/3 attempts also timed out**, returning zero response packets.*  
>  
> *Because of these systematic connection failures, DoH/3 fingerprinting evaluations could not be conducted on Jio or Campus.*  
>  
> *We maintain strict scientific rigor regarding what this result does—and does not—prove:*  
> * *It **does establish** zero observed reachability for direct UDP 443 DoH/3 queries under our tested network configurations.*  
> * *It **does not prove** deliberate censorship or state-mandated protocol blocking. In cellular networks, carrier-grade NAT middleboxes often drop unsolicited or long-lived UDP sessions. On enterprise campuses, perimeter firewalls enforce strict egress filtering, allowing outbound traffic only through HTTP forward proxies that do not support UDP tunneling.*  
> * *Furthermore, standard browser fallback mechanisms—where clients automatically fall back to DoH or TCP upon QUIC timeout—were not part of our standalone lookup testbed."*

---

#### Slide 13: Limitations & Interpretation Boundaries
> *"Like any rigorous empirical study, our research operates within clearly defined boundaries:*  
> 1. *First, **Closed-World Scope**: We evaluate closed-world domain classification across 100 domains on Airtel and 50 domains on Jio and Campus. This measures side-channel leakage bounds, but does not simulate open-world surveillance across millions of domains.*  
> 2. *Second, **Traffic Granularity**: We study isolated, standalone command-line lookups. Real user browsing involves parallel DNS queries and complex page subresources that may alter flow silhouettes.*  
> 3. *Third, **QUIC Reachability**: Total UDP 443 timeouts prevented us from assessing DoH/3 leakage behavior in cellular and enterprise proxy settings.*  
> 4. *Fourth, **Defense Evaluation**: Our mitigation experiments evaluated simulated offline feature adjustments—such as constant-rate padding (64 and 128 bytes) and timing jitter—rather than live, in-production RFC 8467 EDNS(0) deployments.*  
> 5. *Finally, **External Validity**: Our observations reflect three specific network environments in India during November 2026. While the underlying physical mechanisms are general, numerical accuracies may differ across global vantage points.*  
>  
> *These boundaries define the scope of our claims and highlight high-priority directions for future research."*

---

#### Slide 14: Conclusion & Takeaways
> *"To conclude, our research presents three central contributions:*  
>  
> * **01 — Metadata Leakage is Real:** While encryption successfully protects DNS message payloads, unencrypted physical metadata—packet lengths, burst profiles, and directional sequences—supports above-chance domain fingerprinting across all tested networks.*  
> * **02 — Resolvers Matter:** Transport upgrades matter, but resolver implementation is decisive. DoH/3 reduces leakage substantially on padded resolvers like Quad9 and Cloudflare (by up to 85%), but provides much smaller privacy gains on resolvers like Google where response sizes continue to vary.*  
> * **03 — Networks Matter:** Classifiers are heavily shaped by local access network physics. Cross-network transfer collapses to random chance (~2%), but multi-vantage pooled training successfully recovers attack accuracy to over 20%. Simultaneously, enterprise middleboxes and mobile CGNATs pose significant real-world barriers to modern QUIC adoption.*  
>  
> *Ultimately, encrypted DNS privacy cannot be evaluated by looking at cryptographic protocols in isolation—resolver implementations, channel physics, and middleboxes play an equally vital role."*

---

#### Slide 15: Questions & Defense
> *"This brings us to the end of our presentation.*  
>  
> *Our dataset, feature-extraction pipelines, and verification suite are openly structured for reproduction. We would like to express our gratitude to our course faculty and evaluators for their time and guidance.*  
>  
> *We are now ready to take your questions. Thank you."*

---

## 3. Handover Lines Between Team Members

To deliver a polished, cohesive team presentation rather than three disconnected talks, memorize these exact handover lines:

* **Kunal to Rakesh (End of Slide 5 $\to$ Start of Slide 6):**  
  > *"This completes our experimental setup and our end-to-end capture-to-classification architecture. I will now hand over to Rakesh, who will walk you through our evaluation methodology and headline empirical findings."*

* **Rakesh to Aman (End of Slide 10 $\to$ Start of Slide 11):**  
  > *"We have seen that fingerprinting accuracy varies sharply across networks and that naive cross-network transfer collapses to random chance. Aman will now explain how pooled training recovers signal, analyze our protocol reachability findings, and discuss research limitations."*

---

## 4. Technical Speaker Notes & Viva Defense Cheat Sheet

### Member 1: Kunal Khandelwal (Research Foundations & Architecture)

#### Key Numbers to Remember
* Total raw capture attempts: **34,400**
* Total usable traces: **22,407** (Airtel: **18,926**; Jio: **1,912**; Campus: **1,569**)
* Feature space: **44 numerical features** across **5 orthogonal groups**
* Domain workloads: **100 domains on Airtel**, **50 domains on Jio & Campus** (Tranco `L5PV4`)
* Repeats: **20 repeats on Airtel**, **10 repeats on Jio & Campus**

#### Anticipated Viva Questions & Model Answers
* **Q: If DNS payloads are AES-GCM encrypted, how can you identify the domain?**  
  *Answer:* *"Encryption hides payload plaintext, but does not alter the physical transport footprint. Different domains produce different numbers of DNS resource records (A, AAAA, CNAME chains), which create unique response packet lengths. Combined with directional handshake sequences and inter-arrival timing, these form a distinguishable statistical silhouette."*
* **Q: Why are there so many more Airtel traces (18,926) than Jio (1,912) or Campus (1,569)?**  
  *Answer:* *"Airtel tested 100 domains across 20 repeats and 4 resolvers, and all DoH and DoH/3 queries completed successfully. On Jio and Campus, our experimental design intentionally focused on 50 domains across 10 repeats and 3 resolvers. Furthermore, 100% of the 3,000 DoH/3 attempts on Jio and 3,000 on Campus timed out with zero return packets, which naturally reduced the usable trace count."*
* **Q: How did you ensure there was zero label leakage?**  
  *Answer:* *"We explicitly isolated labels (`LABELS = ['network', 'resolver', 'protocol', 'workload', 'domain', 'repeat', 'pcap_path']`) in `src/extract_features.py` (lines 27–35). IP addresses, port numbers, SNI hostnames, and MAC addresses were completely excluded from classifier feature matrices."*
* **Q: Why was Quad9 excluded on Jio and Campus?**  
  *Answer:* *"Quad9's endpoints experienced connection timeouts and reachability failures during initial vantage probing on those networks. To maintain a clean and reliable experimental matrix, Quad9 was excluded before running large-scale captures on Jio and Campus."*

---

### Member 2: Rakesh Mali (Methodology, Results & Generalization)

#### Key Numbers to Remember
* Airtel Headline DoH vs DoH/3:
  * **Quad9:** $45.2\% \to 6.6\%$ (85% reduction)
  * **Cloudflare:** $26.3\% \to 7.2\%$ (73% reduction)
  * **AdGuard:** $26.2\% \to 11.2\%$ (57% reduction)
  * **Google:** $21.3\% \to 15.0\%$ (30% reduction; CIs overlap: `[16.2%, 27.0%]` vs `[10.7%, 19.7%]`)
* Model comparison (AdGuard DoH Global): RF **26.2%**, XGBoost **26.5%**, 1D-CNN **1.0%**, GRU **1.4%**
* Within-network ranges: Airtel **21.3%–45.2%**, Jio **4.1%–15.7%**, Campus **1.8%–5.6%**
* Cross-network transfer: Airtel $\leftrightarrow$ Jio **1.7%–2.4%**; broader pairwise **1.7%–2.7%** (chance = 2.0%)

#### Anticipated Viva Questions & Model Answers
* **Q: Why use a fixed temporal holdout instead of 10-fold cross validation?**  
  *Answer:* *"Standard random $k$-fold cross-validation randomly mixes queries from the same collection hour across train and test sets. In network traffic, transient burst noise and local queue states correlate closely in time, causing models to overfit to network jitter and artificially inflating accuracy. A temporal holdout reserves the final two collection repeats strictly for testing, verifying that models generalize over time."*
* **Q: Why did deep learning models (CNN and GRU) perform so poorly (1.0%–1.4%)?**  
  *Answer:* *"DNS flows are micro-flows containing only 15 to 40 packets. They lack the long sequential token depth required for gradient descent in CNNs and recurrent units to converge. Tree-based ensembles like Random Forest and XGBoost excel at partitioning structured tabular features like total volume, size percentiles, and cumulative burst statistics."*
* **Q: Why did Google show a smaller reduction from DoH to DoH/3 than Quad9?**  
  *Answer:* *"Feature analysis in `dataset_v2.csv` reveals that Google's downlink byte standard deviation is over 750 bytes in DoH and 1,160 bytes in DoH/3—10 to 12 times larger than Quad9 ($\sigma = 63\text{ B}$) or Cloudflare ($\sigma = 77\text{ B}$). In Google's tested configuration, response sizes vary widely with domain record counts rather than being padded to fixed blocks, leaving residual leakage."*
* **Q: What proves that cross-network transfer failed?**  
  *Answer:* *"All off-diagonal transfer accuracies in our 3x3 transfer matrix fall to 1.7%–2.7%, and their 95% bootstrap confidence intervals overlap the 2.0% chance baseline. Two-sample Kolmogorov-Smirnov tests confirm extreme distribution shifts ($p < 10^{-15}$), such as cellular MTU clamping to 1,340 bytes on Jio and proxy TLS framing on campus."*

---

### Member 3: Aman Kashyap (Pooling, Protocol Availability, Defense & Limitations)

#### Key Numbers to Remember
* Pairwise pooling composite accuracy (Airtel + Jio held-out):
  * **Google Global:** **17.33%** (Airtel: 19.67%, Jio: 15.00%)
  * **AdGuard Global:** **19.19%** (Airtel: 33.67%, Jio: 4.42%)
  * **Google India:** **16.33%** (Airtel: 19.33%, Jio: 13.33%)
  * **AdGuard India:** **15.43%** (Airtel: 25.35%, Jio: 3.38%)
* Tri-network co-training mean composite accuracy: **20.67%** (10.3× above chance across Airtel, Jio, and Campus)
* DoH/3 reachability: **3,000 / 3,000 timeouts** on Jio, **3,000 / 3,000 timeouts** on Campus

#### Anticipated Viva Questions & Model Answers
* **Q: What does the 20.67% tri-network co-training result represent?**  
  *Answer:* *"20.67% is the arithmetic mean across all six composite held-out slices in `results/campus_analysis_20261120/c3_tri_network_pooled.csv` (Google Global, Cloudflare Global, AdGuard Global, Google India, Cloudflare India, and AdGuard India) evaluated on 50 shared domains. It demonstrates that multi-vantage adversaries pooling data across networks can overcome transfer collapse, achieving over 10 times above-chance accuracy on unseen composite traffic."*
* **Q: On Slide 11, why does the pairwise pooling table show Google and AdGuard instead of four resolvers?**  
  *Answer:* *"Quad9 was not reachable on Jio, and Cloudflare on Jio experienced carrier timeouts leaving only 15 usable traces across 5 domains. Therefore, pairwise pooling on Jio was evaluated on the two resolvers with full 50-domain coverage—Google and AdGuard—across both Global and India workloads."*
* **Q: Does 3,000/3,000 timeouts on Jio and Campus prove that QUIC is blocked?**  
  *Answer:* *"No, and we are very careful not to make that claim. Our empirical data establishes zero observed reachability for standalone UDP 443 lookups under our tested conditions. On campus, outbound web traffic must traverse an HTTP forward proxy that does not support UDP encapsulation. On Jio, mobile CGNAT middleboxes frequently drop unsolicited UDP traffic. We do not claim intentional censorship."*
* **Q: How did you evaluate defenses?**  
  *Answer:* *"As stated in Section 9 of our paper and on Slide 13, defenses were evaluated via offline feature-vector transformations in `scripts/run_airtel_all.py` (WP13). We simulated constant-rate padding (rounding sizes to multiples of 64 and 128 bytes), random padding ($\mathcal{U}[0, 128]$), and delay jitter. Constant padding reduced AdGuard accuracy from 26.2% to 18.7%, but did not eliminate leakage entirely because volume and burst counts remain predictive."*

---

## 5. Final Rehearsal Checklist & Delivery Rules

### Pre-Presentation Readiness
* [ ] **Kunal:** Can explain DoH vs DoH/3 in plain English; knows the 22,407 trace breakdown and 5 feature groups by heart; can explain the zero-leakage threat model without hesitation.
* [ ] **Rakesh:** Memorized the 4 headline resolver results on Slide 7; can articulate why temporal holdouts are superior to random $k$-fold; can explain why CNN/GRU collapsed to chance.
* [ ] **Aman:** Can explain the difference between pairwise pooling (15.4%–19.2%) and tri-network co-training (20.67%); knows the exact nuance of the QUIC reachability result; can defend the closed-world limitation in under 45 seconds.

### Three Rules for the Actual Defense
1. **Never Overclaim:** Always use precise scientific qualifiers: *"under our tested conditions"*, *"observed reduction"*, and *"plausible contributing mechanisms"*.
2. **Tell the Physical Story:** Evaluators love network physics. When explaining why models fail across networks, point to concrete physical factors: **cellular MTU limits (1,340 B)**, **proxy HTTP `CONNECT` encapsulation**, and **packet delay jitter**.
3. **Cross-Domain Team Knowledge:** Any member might be interrupted with a question about another member's section. All three members must know the complete pipeline from capture to classification.
