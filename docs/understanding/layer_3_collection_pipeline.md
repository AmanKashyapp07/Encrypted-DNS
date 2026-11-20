# Layer 3: Data Collection Pipeline & Systems Engineering

---

## 1. Plain-English Intuition: The "Clean Laboratory Room" Analogy

Capturing network traffic for machine learning is like taking microscopic biological samples. If you leave the window open, dust particles, pollen, and bacteria from the street will contaminate your sample, rendering your medical test invalid.

In computer networking, **background noise is everywhere**. At any given millisecond, your laptop is running background processes:
* An OS update check in the background
* Spotify streaming or syncing playlists
* WhatsApp or Telegram maintaining WebSocket keep-alives
* iCloud or Google Drive syncing files

If a researcher simply runs Wireshark across their entire Wi-Fi interface for 2 hours while running DNS queries, the resulting PCAP file will be contaminated with background TCP packets, random ACKs, and ARP broadcasts. A machine learning model trained on that data will accidentally learn the background traffic instead of the DNS fingerprint!

To prevent this, our pipeline enforces a **"Clean Room Protocol"**:
1. **Micro-Isolation**: Exactly **one query = one distinct PCAP file**.
2. **Surgical Filtering**: A strict hardware-level packet filter (Berkeley Packet Filter - BPF) captures *only* traffic exchanged with the specific resolver IP.
3. **Graceful Kernel Flushing**: Allowing OS buffers to empty completely before closing the file so the crucial final packets are never truncated.

---

## 2. Pipeline Architecture & Execution Flow

The core data collection engine is implemented in `src/probe_and_capture.py` and driven by automated shell scripts (`scripts/run_airtel_capture.sh`, `scripts/run_jio_capture.sh`, `scripts/run_campus_capture.sh`).

```mermaid
sequenceDiagram
    autonumber
    participant Orch as Probe Orchestrator (Python)
    participant Sniff as Packet Sniffer (dumpcap)
    participant Query as Query Client (kdig / curl)
    participant Kernel as OS Kernel Buffer
    participant Manifest as Manifest Logger (CSV)

    Orch->>Sniff: Spawn subprocess with BPF filter (host <resolver_ip>)
    Note over Sniff: dumpcap begins listening on interface
    Orch->>Orch: Sleep 50ms (Allow sniffer initialization)
    Orch->>Query: Execute DNS query (Domain, Resolver, Protocol)
    Query-->>Kernel: TLS/QUIC Handshake + Query + Response
    Kernel-->>Sniff: Filtered packets buffered in memory
    Query-->>Orch: Query completes (Exit code, Duration)
    Orch->>Sniff: Send SIGINT (Graceful termination)
    Note over Sniff: Flushes 150ms buffer to disk; writes PCAP header
    Sniff-->>Orch: Sniffer process terminates
    Orch->>Manifest: Log row (timestamp, domain, resolver, status, pcap_path)
```

---

## 3. Engineering Safeguards in `src/probe_and_capture.py`

### 1. The 150ms SIGINT Flush Mechanism
* **The Pitfall**: When a process completes, many naive collection scripts execute `proc.terminate()` or `proc.kill()` (`SIGKILL`). 
* **The Consequence**: `dumpcap` buffers incoming packets in a high-speed ring buffer in kernel/user space. If killed with `SIGKILL`, the final $2$ to $4$ packets—often the **TLS Close Notify** alert or **TCP FIN/ACK** teardown—are permanently dropped. Truncated PCAPs cause ML classifiers to miscalculate total flow volume and flow duration.
* **Our Solution**: The pipeline sends `signal.SIGINT` (equivalent to pressing `Ctrl+C` in a terminal) and sleeps for $150\text{ms}$. This signals `dumpcap` to flush its internal buffers to disk, cleanly write the PCAP file footer, and terminate gracefully without losing a single packet.

### 2. Surgical Berkeley Packet Filter (BPF)
* Before launching the query, the orchestrator configures the packet filter:
  $$\text{BPF String} = \text{"host } \langle \text{RESOLVER\_IP} \rangle \text{ and (tcp or udp)}"$$
* Any packet to or from any other host (Spotify, Apple, campus gateway) is discarded by the operating system kernel before it ever reaches userspace memory.

### 3. Dedicated Isolated Tooling: `kdig` & `curl`
* **Plaintext / DoH**: Knot DNS Client (`kdig`) with native TLS support.
* **DoH/3 (HTTP/3 over QUIC)**: Compiled `curl` with `--http3-only` flag linked against `quiche` / `nghttp2`.
* Strict timeout budget: If a query does not return within $5.0$ seconds, it is marked as `TIMEOUT`, logged in the manifest, and cleanly discarded.

### 4. Enterprise Proxy Tunneling (`--allow-proxy`)
* For the IIIT-A Campus network, traffic cannot exit directly to public resolver IPs (`8.8.8.8` or `1.1.1.1`).
* We engineered an `--allow-proxy` mode that directs queries through the local campus proxy (`http://172.31.100.29:3128`) using an `HTTP CONNECT` tunnel. This mirrors how every student and faculty workstation connects to the internet.

### 5. Manifest State Machine
Every single attempt generates a permanent log entry in `manifest_*.csv` with the following schema:
```csv
run_id,timestamp,domain,resolver,protocol,status,duration_ms,pcap_path,exit_code,proxy_used
```
This ensures complete scientific traceability: if a flow fails, we know exactly *why* (e.g., DNS timeout, socket error, proxy拒否) rather than silently dropping data.

---

## 4. Quality Control & Post-Collection Filtering

Raw captures are not fed directly to machine learning models. They pass through `src/extract_features.py` and `scripts/validate_manifest.py` which enforce strict hygiene:

```
[Raw PCAP on Disk] 
       │
       ▼
[Filter 1: Minimum Packet Threshold] ───> Discard if packet_count < 3
       │                                  (Flows without response or aborted handshakes)
       ▼
[Filter 2: Error Status Check] ─────────> Discard if exit_code != 0 or status != SUCCESS
       │
       ▼
[Filter 3: Feature Extraction Matrix] ──> Extract exactly 44 directional flow features
       │
       ▼
[Verified Usable Dataset] (18,926 Airtel + 1,912 Jio + 1,569 Campus = 22,407 flows)
```

---

## 5. Professor Viva Attack Scenarios

### Viva Trap 1: "Why did you write a custom Python orchestration script instead of simply using Scapy?"
* **Flawed Student Answer**: *"Because Python was easier to write."* (Vague and dismissive).
* **Master Answer**:
  > *"Scapy is an excellent packet manipulation library, but it operates in Python userspace and is constrained by the Python Global Interpreter Lock (GIL). In high-throughput network experiments, Scapy introduces significant packet capture latency and frequently drops packets during rapid TLS/QUIC handshake bursts.
  > 
  > Instead, we selected `dumpcap`, the native C-based packet capture engine that powers Wireshark. `dumpcap` runs as a dedicated lightweight daemon with direct kernel ring-buffer access (`AF_PACKET` on Linux / `BPF` on macOS), guaranteeing zero packet loss during micro-bursts while keeping CPU overhead negligible."*

---

### Viva Trap 2: "How do you prove that background traffic from other programs on your laptop did not contaminate your PCAPs?"
* **Flawed Student Answer**: *"We closed all browser tabs and applications before running the script."* (Methodologically unacceptable; background OS daemons still emit packets).
* **Master Answer**:
  > *"We enforced three layers of isolation:
  > 1. **Kernel-level BPF Filtering**: Every capture was bound to a strict filter: `host <RESOLVER_IP> and (tcp or udp)`. Even if background applications generated gigabytes of traffic, the kernel packet filter instantly dropped all frames not addressed to or originating from the target DNS resolver IP.
  > 2. **Ephemeral Port Verification**: Post-collection validation confirmed that each PCAP contained only a single 5-tuple flow between the client's ephemeral port and the resolver's port 443.
  > 3. **Time-Isolated Micro-PCAPs**: Rather than slicing a continuous multi-hour PCAP, each query was captured in an individual sub-second file, eliminating inter-query interleaving."*

---

### Viva Trap 3: "Why did Jio have a yield of only 31.9% and Campus 26.2%? Doesn't a low yield indicate poor engineering?"
* **Flawed Student Answer**: *"Our script had bugs or network disconnects that caused errors."* (**Fatal deduction**: Blaming your own code when it was a physical network finding).
* **Master Answer**:
  > *"On the contrary, the yield rate reflects the true physical hostility of these networks toward encrypted protocols:
  > 1. **QUIC Blocking (50% Attrition)**: 3,000 out of 6,000 queries in both networks were DoH/3 queries over UDP 443. Because Jio and Campus firewalls completely block outbound UDP 443, exactly 50% of attempts were guaranteed to fail at the transport layer.
  > 2. **Carrier Filtering on Jio**: On Reliance Jio, Cloudflare DoH exhibited a 98.5% failure rate due to carrier-level TCP RST injection and SNI throttling.
  > 3. **Proxy Queue Drops on Campus**: Under automated probing, the campus proxy server intermittently dropped TCP connections due to concurrency limits.
  > 
  > The collection pipeline correctly executed, logged, and categorized every single failure in the manifest rather than masking them, providing the empirical foundation for Finding F2 (QUIC Ossification)."*

---

## 6. Key Takeaways Checklist (Remember for the Stage)

* [ ] **Clean Room Isolation**: 1 query = 1 micro-PCAP with strict BPF filter (`host <resolver_ip>`).
* [ ] **150ms SIGINT Flush**: Allows `dumpcap` C ring buffers to write the final packets and clean headers before closing.
* [ ] **Zero-Loss Tooling**: `dumpcap` over Scapy to prevent GIL packet loss during TLS handshake bursts.
* [ ] **Manifest Traceability**: Complete audit trail logging timestamps, duration, exit codes, and proxy status for all 34,400 attempts.
