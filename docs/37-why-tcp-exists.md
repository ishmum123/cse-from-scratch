# Reliable Delivery Over an Unreliable Network

## The Problem

IP delivers packets on a best-effort basis: it tries to route each packet to its destination, but makes no guarantees. Packets can be dropped (router queues fill up, links fail), duplicated (a router retransmits before getting confirmation), or reordered (different packets take different paths). On a loaded internet path, 1–2% packet loss is normal. On a bad mobile connection, loss can reach 5–10%.

Building a web browser that loads pages over raw IP is like trying to read a book where random sentences are missing, some sentences appear twice, and paragraphs arrive in random order. The browser would need to implement its own reliability layer — or web pages would be corrupted on every connection with packet loss.

Any reliability layer must:

- Detect lost packets and retransmit them
- Deduplicate — ignore packets received twice
- Reorder — deliver data to the application in the original sequence
- Not introduce excessive latency (retransmission should be fast but not wasteful)
- Work without modifying intermediate routers

## What Would You Try?

Before reading on:

- If the sender doesn't hear back, how does it know whether the packet was lost or just slow?
- If you retransmit too aggressively (resend every packet after 1ms), what happens to network load?
- If the receiver tells the sender "I got packet 7 but not packet 6," should the sender only retransmit 6, or 6 and all subsequent packets?

## Failed Attempts

### Attempt 1: Stop-and-Wait

Send one packet. Wait for acknowledgment (ACK). Only then send the next packet. If no ACK arrives within a timeout, retransmit.

This guarantees reliability (every packet is ACKed before moving on) and is simple to implement. The problem: the link is idle while waiting for the ACK. A San Francisco-to-London connection has a round-trip time (RTT) of ~150ms. A 1,500-byte packet takes ~0.012ms to transmit on a 1Gbps link. The link is idle 99.99% of the time, waiting for ACKs. Throughput: 1,500 bytes / 150ms = 80kbps on a 1Gbps link. 12,500× slower than the link capacity. Stop-and-wait's throughput is limited by RTT, not bandwidth.

### Attempt 2: Go-Back-N

Maintain a "window" of W unacknowledged packets in flight. Send packet 1, 2, 3, ..., W without waiting for ACKs. When packet 3 is lost, the receiver discards packets 4–W (out of order) and sends only ACK 2 (highest in-order received). Sender retransmits 3, 4, 5, ..., W from the point of loss.

Better utilization — multiple packets in flight. But Go-Back-N discards all packets received after the lost one, even if they arrived correctly. A single lost packet causes retransmission of the entire window. With a window of 100 packets and 1% loss rate, about 1 in 100 packets is lost, but ~100 packets are retransmitted each time — approximately 100% of data is retransmitted. Effective throughput collapses under any meaningful packet loss.

### Attempt 3: Selective Acknowledgment Without Flow Control

Use selective acknowledgment (SACK): receiver explicitly tells sender which packets it has and which are missing. Sender retransmits only missing packets. This eliminates the Go-Back-N waste.

SACK solves the retransmission efficiency problem. But without flow control, the sender transmits as fast as the link allows — regardless of how fast the receiver can process data. A server sending at 10Gbps to a smartphone that can process 1Mbps overflows the phone's receive buffer. Packets are dropped by the phone's network stack, triggering retransmissions — which also get dropped. The sender wastes bandwidth retransmitting into a full buffer. SACK tells you what to retransmit; it doesn't tell you how fast to send in the first place.

## The Discovery

Stop-and-wait wastes bandwidth while waiting for ACKs. Go-Back-N wastes bandwidth retransmitting correctly received packets. SACK without flow control overwhelms receivers.

Each failure adds one constraint. Together they define TCP:

**TCP (Transmission Control Protocol)** combines:

1. **Sequence numbers**: every byte of data has a position in the stream. The sender labels each segment with the sequence number of its first byte. The receiver knows exactly which bytes it has and which are missing.

2. **Cumulative ACKs + SACK**: the receiver ACKs the highest in-order byte received, plus optionally includes SACK blocks listing out-of-order bytes received. The sender retransmits only gaps.

3. **Sliding window**: sender maintains a window of unACKed bytes in flight. Window size determines how many bytes can be "in flight" simultaneously. Throughput ≈ window_size / RTT. A window of 1MB and RTT of 150ms gives ~53Mbps throughput — no longer bottlenecked by RTT as in stop-and-wait.

4. **Receiver flow control**: the receiver advertises its available buffer space in every ACK (`rwnd` field). The sender never sends more than `min(cwnd, rwnd)` bytes beyond the last ACK, where `cwnd` is the congestion window (chapter 38). This prevents overwhelming the receiver.

5. **Retransmission timeout (RTO)**: derived from measured RTT with a safety margin. If no ACK arrives within RTO, retransmit. Fast retransmit: if three duplicate ACKs arrive (receiver keeps ACKing the same sequence number), retransmit immediately without waiting for RTO.

The three-way handshake (SYN, SYN-ACK, ACK) establishes connection state before data flows. The four-way teardown (FIN, ACK, FIN, ACK) ensures both sides agree no more data is coming.

## Try It

<iframe src="../assets/browser/chapter37/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter37/index.html)

Before changing anything, predict:

- Set packet loss to 5% and compare stop-and-wait vs. TCP with a sliding window. How does throughput differ?
- Drop packet #7 mid-stream. Watch the sequence of ACKs and retransmissions. How many packets does TCP retransmit?
- Reduce the receiver buffer (rwnd) to a small value. Does the sender's window shrink? What happens to throughput?

## Implementation

The full model is ~180 lines of dependency-free JavaScript — open `browser/chapter37/index.html` (and the shared helpers in `browser/common/sim.js`) to read or modify it. Everything runs in the browser; nothing to install. Look for the `TCPSender` class with its `sendWindow`, `sackBlocks`, and `rto` fields. The `TCPReceiver` class maintains an `inOrderBuffer` and out-of-order buffer, generating cumulative ACKs and SACK options. The network layer randomly drops packets based on the configured loss rate.

## When It Breaks

**Head-of-line blocking at the stream level.** TCP delivers bytes in order. If packet 5 is lost, packets 6–100 sit in the receiver's buffer waiting for 5. The application can't read any of them until 5 arrives and is retransmitted (taking one RTT). For a video stream, this means freezing for 150ms even though the next 95 frames are sitting in the buffer. HTTP/1.1 over TCP multiplexes requests over one connection — one stalled response blocks all subsequent ones. HTTP/2 multiplexed streams over TCP but still suffered TCP-level head-of-line blocking. **QUIC** (HTTP/3) moves multiplexing below TCP by implementing a transport protocol over UDP — each stream's loss only blocks that stream, not others.

**Bufferbloat.** Home routers with large buffers queue packets rather than dropping them under load. TCP's congestion control detects congestion via packet loss; if packets are queued instead of dropped, TCP never sees the loss signal and keeps sending. Latency grows to seconds (packets queued for 10+ seconds). Latency-sensitive applications (video calls, gaming) break. CoDel (Controlled Delay) AQM drops packets not when the queue is full but when a packet has been queued for more than 5ms — providing the congestion signal without large queues. This is the root of the bufferbloat problem, characterized by Jim Gettys around 2011.

**TIME_WAIT state accumulation.** After a TCP connection closes, the initiating side enters TIME_WAIT for 2 × MSL (Maximum Segment Lifetime, typically 60–120 seconds) to ensure delayed packets from the old connection don't confuse a new connection on the same port tuple. A high-throughput server making many short connections (REST APIs, health checks) accumulates thousands of TIME_WAIT sockets. At 65,535 source ports per destination IP, TIME_WAIT exhaustion prevents new connections. Fix: `SO_REUSEADDR`, TCP `tw_reuse`, or HTTP keep-alive to reuse connections.

## Transfer

- **TLS over TCP.** TLS (Transport Layer Security) runs on top of TCP, adding encryption and authentication. The TLS handshake requires 1–2 additional RTTs after the TCP handshake — a 300ms RTT connection needs 450–600ms before sending any data. TLS 1.3 reduced the handshake to 1 RTT (or 0-RTT for resumptions), adding ~150ms less than TLS 1.2.
- **QUIC (HTTP/3).** Google's QUIC protocol reimplements TCP's reliability features in user space over UDP. This allows deployment without OS kernel changes, enables per-stream loss recovery (no head-of-line blocking), and combines TLS with the transport handshake (0 or 1 RTT to connect). Chrome has used QUIC since 2013; HTTP/3 standardized it in RFC 9000 (2021).
- **TCP BBR (Bottleneck Bandwidth and Round-trip propagation time).** Google's 2016 congestion control algorithm. Instead of using packet loss as the congestion signal (which causes bufferbloat), BBR models the bottleneck bandwidth and RTT directly, aiming to fill the pipe without filling the buffer. BBR achieves much higher throughput on long-fat-network paths (intercontinental, satellite) where classic cubic/Reno underperform.

Try these:

1. The "bandwidth-delay product" is `bandwidth × RTT`. For a 1Gbps link with 150ms RTT, what TCP window size is needed to saturate the link? Why does the window size matter?
2. Explain the three-way handshake. Why are three messages needed instead of two?
3. A client and server are communicating via TCP. The server sends 10 segments of 1,460 bytes each. The client receives all 10 but the ACK for segments 3–5 is lost. What does the server do? What does the client see?

---

**Continue → [Why Congestion Happens](38-why-congestion-happens.md)**
