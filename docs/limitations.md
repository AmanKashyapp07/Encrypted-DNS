# Research Scope & Methodological Limitations

This document articulates the explicit boundaries, experimental constraints, and methodological limitations of the encrypted DNS fingerprinting research conducted in this repository.

---

## 1. Threat Model & Traffic Representation Constraints

### 1.1 Isolated Single-Lookup Flows vs. Cascading Page Loads
* **Scope:** Every captured flow in this dataset corresponds to a single, isolated DNS resolution for a single domain name.
* **Limitation:** In authentic web browsing, visiting a webpage (e.g., `theverge.com` or `amazon.in`) triggers cascades of dozens of secondary DNS lookups for third-party scripts, advertising trackers, stylesheets, and Content Delivery Networks (CDNs).
* **Implication:** Single-lookup fingerprintability does not directly translate to page-load fingerprintability. An adversary observing full browsing sessions faces multiplexed overlapping flows and connection reuse, but can also correlate multi-query sequences.

### 1.2 Candidate Domain Pool Size (Closed-World Constraint)
* **Scope:** Evaluated on a closed-world candidate set of 100 domains (50 Global, 50 India on cellular).
* **Limitation:** Real-world DNS resolution operates against millions of active second-level domains. In a 1,000,000-class problem, the random guessing baseline is $10^{-6}$, and multi-class classifier precision may degrade substantially due to the base-rate fallacy.

### 1.3 Client Software Homogeneity
* **Scope:** All captures were executed using the [`q` DNS client v0.19.12](https://github.com/natesales/q).
* **Limitation:** Different DNS client implementations (e.g., `systemd-resolved`, Apple macOS native stub resolver, `dnscrypt-proxy`, Firefox internal DoH resolver, Chrome internal DoH resolver) utilize different HTTP/2 and QUIC library stacks, buffer configurations, and TLS cipher negotiation orders, which may produce distinct flow silhouettes.

---

## 2. Experimental & Network Constraints

### 2.1 Cellular DoH/3 Measurement Inaccessibility
* **Finding:** On Reliance Jio cellular, 100% of DoH/3 capture attempts ($3,000 / 3,000$) failed due to client timeouts on UDP port 443.
* **Limitation:** Because no DoH/3 packets were successfully exchanged over the Jio cellular path, we could not empirically measure whether QUIC suppresses fingerprinting on mobile networks. We could only characterize protocol availability and evaluate DoH (HTTP/2) fingerprintability.

### 2.2 Middlebox Attribution Limits
* **Observation:** Outbound UDP port 443 packets elicited zero response on Reliance Jio, while TCP port 443 to the exact same resolver IPs succeeded with up to 100% completion rate.
* **Limitation:** Passive client-side packet capture cannot observe the internal architecture or routing policies of carrier middleboxes. We describe this phenomenon as **"behavior consistent with carrier-level UDP port 443 filtering or blackholing"**, rather than asserting definitive knowledge of internal Deep Packet Inspection (DPI) vendor hardware.

### 2.3 Geographic and Vantage Point Coverage
* **Scope:** Captures were conducted from a fixed geographic vantage point in Northern India across Airtel broadband and Reliance Jio mobile cellular.
* **Limitation:** Transit routing, peering agreements, and anycast CDN server allocations vary across geographic regions and other Indian carriers (e.g., Vodafone Idea, BSNL).

---

## 3. Defense Evaluation Constraints

### 3.1 Simulated Feature Perturbation vs. Live Protocol Defenses
* **Scope:** All defense results reported in WP13 (`wp13_defence_simulations.csv`) are **offline mathematical simulations** applied by modifying feature values (e.g., rounding packet sizes, injecting synthetic random noise into inter-arrival times).
* **Limitation:** No live network defenses (such as RFC 7830 / RFC 8467 EDNS0 padding on upstream resolvers, or client-side proxy padding) were deployed or measured on the wire. Real-world protocol defenses interact with QUIC frame packing, congestion control, and connection coalescing in ways that offline feature perturbation cannot fully capture.

### 3.2 EDNS0 Padding Inconclusiveness
* **Observation:** In live resolver diagnostics (`docs/live_checks/`), EDNS0 padding options were not exposed in `q` client JSON responses.
* **Limitation:** The lack of exposed padding in client JSON records does not conclusively prove that upstream resolvers completely omit padding at the physical wire level. Confirming wire-level EDNS0 padding requires byte-level dissection of decrypted DNS payloads within the TLS/QUIC stream.

---

## 4. Ethical & Open Science Compliance

* **Passive Observational Capture:** Only client-initiated lookups were captured; no third-party network traffic was tapped or intercepted.
* **Privacy Minimization:** Client IP addresses, local machine hostnames, and MAC addresses are omitted from all committed data.
* **Reproducibility Guarantee:** All analytical workflows, feature tables, statistical models, and validation routines are committed and deterministically reproducible.
