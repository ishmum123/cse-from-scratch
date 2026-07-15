# The Tragedy of the Shared Pipe

## The Problem

In October 1986, the early internet collapsed. Network throughput dropped by a factor of 1,000 — from 32kbps to 40bps on some links — in a matter of seconds. The cause: congestion collapse. Every sender, upon seeing dropped packets, retransmitted. Retransmissions added more traffic. More traffic caused more drops. More drops caused more retransmissions. A feedback loop locked the network into a state of near-zero useful throughput despite maximum traffic.

The problem is not that the network was "too loaded." The problem is that TCP at the time had no mechanism for senders to back off when the network was congested. Each sender rationally maximized their own throughput — and the collective result was catastrophic for everyone. This is a tragedy of the commons: individually rational behavior destroys the shared resource.

Any congestion control mechanism must:

- Detect congestion before it becomes collapse
- Cause senders to back off in response to congestion signals
- Allow senders to ramp back up when congestion eases
- Be fair — no sender should be able to persistently starve others

## What Would You Try?

Before reading on:

- If every sender independently decides how fast to send, and the network never signals overload, what happens as more senders join?
- Packet drops are a signal that the network is congested. Can senders observe this signal without any changes to routers?
- If you reduce your send rate when you see congestion and increase it when you don't, what's the right ratio for each direction?

## Failed Attempts

### Attempt 1: Send at a Fixed Rate Matching Link Speed

Each sender probes the network with increasing speed until they hit the link's capacity, then maintains that rate. Simple, predictable.

When 10 senders each try to maintain a rate matching the link capacity, the aggregate rate is 10× the link capacity. The link's buffer fills. The buffer overflows. Packets drop. Each sender interprets the drop as a temporary glitch and retransmits — adding more load. With no mechanism to reduce rate in response to congestion, the network enters collapse exactly as described in 1986. Fixed-rate sending without feedback is the cause of congestion collapse.

### Attempt 2: Explicit Congestion Notification (ECN) Only

Add a bit to each packet header. When a router's queue is filling up, set the ECN bit on outgoing packets instead of dropping them. Receivers echo the ECN bit back to senders in ACKs. Senders reduce rate when they see ECN.

ECN is a real mechanism (RFC 3168) and it works — but it requires both endpoints to support ECN *and* all routers on the path to support it *and* them to be configured to set the bit. Deployment has been slow: a 2017 study found ECN enabled on only ~27% of web servers. More importantly, ECN alone doesn't tell senders *how much* to reduce. A single congestion signal triggers a rate reduction, but with no ramp-up mechanism, senders stay at the reduced rate forever. You need both: a reduction signal *and* a recovery algorithm.

### Attempt 3: Fixed Window with Additive Increase Only

Start with a small window. Increase by 1 packet per RTT. Never decrease. This avoids congestion collapse because new senders ramp up slowly.

But with no decrease on congestion signal, senders eventually fill any link. Slow ramp-up delays reaching the available capacity. The ramp-up is O(bandwidth-delay-product) RTTs, meaning on a high-bandwidth, high-latency path (say a satellite link), reaching full speed takes minutes. And without any decrease, all senders on a shared link ratchet up to saturation simultaneously. Additive increase alone doesn't work. Decrease on congestion is mandatory.

## The Discovery

Fixed rate with no feedback causes collapse. ECN alone provides a signal but no complete algorithm. Additive increase with no decrease reaches saturation and stays there.

The solution — TCP congestion control (Jacobson/Karels 1988, implemented in BSD TCP after the 1986 collapse) — uses packet loss itself as the congestion signal (no router changes required) and an asymmetric response:

**AIMD (Additive Increase, Multiplicative Decrease)**:
- **Slow start**: begin with `cwnd = 1 MSS` (one packet). On each ACK, increase `cwnd` by 1 MSS. This doubles `cwnd` per RTT (exponential growth) until either a loss occurs or `cwnd` reaches the slow-start threshold (`ssthresh`).
- **Congestion avoidance**: once `cwnd ≥ ssthresh`, increase `cwnd` by `1/cwnd` MSS per ACK — linear growth, adding approximately 1 MSS per RTT.
- **On loss**: set `ssthresh = cwnd/2`, set `cwnd = 1` (or `cwnd/2` in fast recovery variants), restart.

The asymmetry is intentional: +1 per RTT (slow), ÷2 on loss (fast). This ensures the network probes for available capacity slowly and backs off quickly. The mathematical result: AIMD converges to fair bandwidth sharing among competing flows — each flow gets an equal share of the bottleneck link, regardless of who arrived first or how long they've been running.

The key insight: **losses are signals, not failures**. A dropped packet is the network saying "too much." The sender's response to that signal — halve the window — is the control mechanism. No router changes needed. All congestion control happens at the endpoints.

## Try It

<iframe src="../assets/browser/chapter38/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter38/index.html)

Before changing anything, predict:

- With 5 senders competing for one bottleneck link and AIMD enabled, do their throughputs converge to equal shares over time?
- Disable congestion control (send at fixed maximum rate). What happens to queue depth at the bottleneck? To aggregate throughput?
- One sender uses a small initial window. Another starts with a large window. After 10 RTTs, have their throughputs equalized?

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter38/index.html` (shared helpers in `browser/common/sim.js`). The left panel uses `floodWin` (fixed at maximum); the right panel uses `aimdWin`, which increments by 1 each tick and halves whenever the window exceeds `capacity`. The `dropRate(win, cap)` helper computes the fraction of dropped packets. Counters `floodDrops`/`aimdDrops` and `floodTotal`/`aimdTotal` accumulate in `frame()` and feed the strip chart — watch the AIMD side's sawtooth pattern emerge as you adjust the "Link capacity" slider.

## When It Breaks

**Bufferbloat revisited.** If routers buffer packets instead of dropping them, loss never occurs — the congestion signal never fires. Senders assume the network is uncongested and keep increasing `cwnd`. Latency balloons as queues fill to seconds of depth. Applications sensitive to latency (video calls, online games) become unusable. The fix: AQM algorithms (CoDel, FQ-CoDel) that drop packets based on queue latency rather than queue depth, providing the congestion signal before queues grow large. As of 2024, most Linux home routers with OpenWRT use FQ-CoDel by default.

**Incast collapse in datacenter networks.** A client requests data from 100 storage nodes simultaneously. All 100 respond at the same moment, overwhelming the client's inbound link. All 100 TCP flows experience loss at the same moment. All 100 simultaneously halve their windows and restart slow start. All 100 send one packet, then wait one RTO (minimum 200ms in classic TCP) before retransmitting. The client waits 200ms for a tiny response from 100 nodes. Total latency: 200ms for a request that should take 1ms. Fix: reduce RTO minimum for datacenter (where RTTs are microseconds, not milliseconds) or use request scheduling to stagger responses.

**BBR vs. Cubic unfairness.** TCP BBR and TCP Cubic (the default on Linux since 2.6.19) use different congestion signals. On a shared link, BBR flows can achieve higher throughput than Cubic flows by filling the buffer before Cubic's loss signal fires. This creates fairness problems when BBR and Cubic flows share a bottleneck — BBR flows take a disproportionate share. Google's BBRv2 attempts to fix this. The interaction between competing congestion control algorithms is an active area of research and deployment debate.

## Transfer

- **QoS and traffic shaping.** ISPs and enterprise networks shape traffic by congestion-controlling specific traffic classes (video, VoIP, bulk file transfer) at different rates. A 100Mbps link can be configured so VoIP traffic has guaranteed 1Mbps and never experiences the slow-start penalty, while bulk transfers use the remaining 99Mbps with standard AIMD.
- **QUIC's congestion control.** QUIC uses CUBIC or BBR for congestion control, same as TCP — but implemented in user space. This enables deployment and update without kernel changes. Google deploys BBRv2 for all YouTube and Search traffic over QUIC.
- **The Abilene collapse as a case study.** The 1986 congestion collapse affected ARPANET but the fixes (Jacobson's algorithm) shipped in BSD 4.3 Tahoe in 1988. The internet grew by three orders of magnitude in the 1990s without another congestion collapse, attributable to AIMD and the global deployment of TCP congestion control.

Try these:

1. Why is AIMD (additive increase, multiplicative decrease) provably fair, while MIMD (multiplicative increase, multiplicative decrease) is not? Sketch a graph of two flows' windows over time under each algorithm at a shared bottleneck.
2. Slow start doubles `cwnd` every RTT until `ssthresh`. For a 10Mbps link with 100ms RTT and initial `ssthresh = 32 MSS` (MSS = 1,460 bytes), how many RTTs does it take to reach 10Mbps?
3. What is the bandwidth-delay product (BDP), and why does it set the upper limit on TCP throughput for a given path? What does it take to saturate a 100ms RTT, 1Gbps link?

---

**Continue → [Why Load Balancers Exist](39-why-load-balancers-exist.md)**
