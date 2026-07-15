# Slicing the Stream

## The Problem

In 1965, the US defense network sent messages as complete units — one message, one channel, occupied for the duration of the transmission. A 1MB file sent over a 56kbps link occupies that link for 142 seconds. While it's transmitting, no other message can use that link. If the link fails at second 141, the entire file must be retransmitted from the beginning.

More fundamentally: a network with dedicated channels (circuit switching, like the telephone system) reserves a path from sender to receiver for the duration of a call. If Alice's 1MB file is using the link, and Bob wants to send a 1KB urgent message, Bob waits 142 seconds. The link is physically reserved regardless of how much data is actually flowing — a silence in a phone call still occupies the circuit.

Any solution must:

- Allow multiple senders to share a single link without dedicating it to one
- Survive partial failures — if one link fails, the rest of the data should still arrive
- Avoid tying up a link for the duration of a large transmission
- Allow different messages to take different paths through the network

## What Would You Try?

Before reading on:

- If you could split a large file into 1,000 pieces, could piece 500 leave before piece 1 arrives at the destination? What would you need to reassemble them in order?
- A network has two paths from A to B: one fast but congested, one slow but free. If data travels as one chunk, it must choose one path. If data travels as small pieces, what's possible?
- What's the minimum information each piece needs to carry to be independently routable?

## Failed Attempts

### Attempt 1: Circuit Switching (Dedicated Channels)

Reserve a dedicated physical path from sender to receiver before any data flows (like a phone call). The circuit is exclusively yours for the duration.

This is exactly what the telephone network does — and why ARPANET was designed to replace it. The problem: a circuit reserved for a 10-minute file transfer occupies network capacity for 10 minutes even if data is only flowing 20% of the time (the rest is processing pauses, TCP acknowledgments, flow control). Statistical multiplexing — sharing one link among many senders — is impossible when links are dedicated. The US military's dependence on circuit-switched networks was a vulnerability: destroying a few key switching stations could partition the network. The original ARPANET requirement was a network that could survive partial nuclear damage and still route messages — circuit switching inherently fails this requirement.

### Attempt 2: Store-and-Forward Entire Messages

Send the complete message to an intermediate node, which stores it on disk, then forwards it to the next node. This is "message switching" — the predecessor to packet switching, used in telegraph networks.

Messages are self-contained and can take different routes. But storing large messages at each hop requires large storage at each intermediate node. A 100MB file at 10 hops requires 1GB of intermediate storage. More critically, a 100MB message occupies an outbound link for its entire transmission before the next hop starts transmitting. End-to-end latency is O(message_size × hops). For small messages, this is fine; for large ones, the tail latency is enormous. And if the message is corrupt or lost at hop 5, you must retransmit the entire thing from the source.

### Attempt 3: Fixed-Size Cells (ATM)

Asynchronous Transfer Mode (ATM), the 1980s–90s competitor to IP, used fixed-size 53-byte cells. Every message is split into 53-byte cells, each with a 5-byte header. Fixed size means routers can allocate fixed-size buffers, process cells in constant time, and guarantee quality-of-service.

The 53-byte size is notoriously mistuned: 48 bytes of payload + 5 bytes of header = 11% overhead for small payloads, and terrible efficiency for large data (the cell boundary means voice traffic payloads are 48 bytes while IP data payloads are 1,460 bytes — ATM over IP required segmentation/reassembly layers). ATM's fixed-size cells made hardware simpler but made software more complex. The 53-byte choice was a political compromise between European carriers (wanted 32 bytes) and US carriers (wanted 64 bytes) — neither got what they wanted. IP packets won because variable-size was more flexible, despite being harder to process in hardware.

## The Discovery

Circuit switching dedicates links for the full transmission duration, preventing sharing. Store-and-forward of entire messages creates huge latency and intermediate storage requirements. Fixed-size cells impose artificial size constraints and inefficiency.

The solution: **packets** — variable-length chunks of data (typically 512–1,500 bytes) with a header containing source address, destination address, sequence number, and length. Each packet is independently routable: a router receives a packet, reads the destination address, looks up its routing table, and forwards the packet toward the destination. The packet then leaves the router immediately — the router doesn't wait for later packets in the same message.

**Statistical multiplexing**: because packets are small, many different senders' packets are interleaved on each link. Bob's 1KB urgent message can be transmitted between Alice's packets 1 and 2 without waiting for Alice's 1MB file to finish. All senders share the link's bandwidth in proportion to their traffic, not in proportion to reserved circuits.

**Pipeline parallelism**: while Alice's packet 1 is traveling from node 2 to node 3, packet 2 is traveling from node 1 to node 2, and Alice's source is sending packet 3. All three hops are active simultaneously. End-to-end latency for a 1,000-packet file approaches (transmission time for one packet × hops) rather than (transmission time for entire file × hops). At 1,000 packets and 10 hops: ~10× faster.

**Independent routing**: each packet can take a different path. If link A→B fails, packets can route via A→C→B. No reservation to cancel. This is the nuclear-survivability property ARPANET was designed for.

The formal name: **packet switching**, proposed by Paul Baran (RAND Corporation) in 1964 and Donald Davies (NPL) independently in 1965. The internet is packet-switched from its design to the present day.

## Try It

<iframe src="../assets/browser/chapter36/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter36/index.html)

Before changing anything, predict:

- Send a 10-packet file with circuit switching vs. packet switching. Which finishes first? By how much?
- Block one link mid-transfer in the packet-switched simulation. Do subsequent packets reroute? What happens to already-in-flight packets on that link?
- Inject Bob's 1-packet message while Alice's 10-packet file is mid-transfer. When does Bob's message arrive in each model?

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter36/index.html` (shared helpers in `browser/common/sim.js`). The left panel is circuit switching: each attempt sends `totalBytes` at once; a random draw against `lossRate` either delivers everything or nothing, incrementing `circuitDelivered` or `circuitAttempts` accordingly. The right panel sends `pktSize`-byte packets individually; each has an independent loss draw, so partial progress is preserved. The `lossRate` and `pktSize` sliders let you see directly how finer granularity improves delivery under loss.

## When It Breaks

**Out-of-order delivery.** Packets taking different paths arrive in different orders. If packet 3 takes a fast path and arrives before packet 2 (which took a slow, congested path), the receiver must buffer packet 3 and wait for packet 2 before delivering in-order. Without reordering buffers, data is corrupt. TCP handles this (chapter 37); UDP does not — UDP applications must either tolerate out-of-order delivery or reimplement ordering themselves. Video streaming applications often use UDP and simply play whatever arrives, causing occasional frame glitches rather than pausing to wait.

**Head-of-line blocking in router queues.** A router's outbound link has a finite queue. If a large packet is at the head of the queue, all subsequent packets (including small, latency-sensitive ones) wait behind it. This is the packet-level analog of a slow driver blocking a lane. Active Queue Management (AQM) algorithms like CoDel deliberately drop or delay packets to signal congestion and reduce queue depth, prioritizing latency over throughput. Used in home routers running OpenWRT with the `fq_codel` algorithm.

## Transfer

- **IP fragmentation.** Each network link has a Maximum Transmission Unit (MTU) — the largest packet it can carry. Ethernet's MTU is 1,500 bytes. A router connecting to a link with a smaller MTU must fragment oversized packets. The destination reassembles them. Fragmentation causes performance problems and can be exploited for DoS attacks; path MTU discovery (PMTUD) was introduced to let senders discover the smallest MTU on the path and send appropriately sized packets.
- **MPLS (Multiprotocol Label Switching).** Internet backbone carriers use MPLS to route packets by short fixed-length labels rather than full IP lookups. A label-switched path is precomputed for a traffic class; packets are labeled at the ingress router and forwarded by label at every subsequent hop. This gives the switching speed of circuit switching with the flexibility of packet switching.
- **Video streaming and adaptive bitrate.** MPEG-DASH and HLS chunk video into 2–10 second segments (coarse-grained packets). The player requests each chunk independently over HTTP. If the network is congested, it requests the next chunk at a lower bitrate. Packet-switching principles applied to application-layer chunking.

Try these:

1. A network sends a 1,000-byte message as (a) one packet or (b) 10 packets of 100 bytes each, over a 3-hop path. Calculate the end-to-end latency for each, assuming 10ms propagation delay per hop and 1ms transmission time per 100 bytes.
2. What is MTU? Why is Ethernet's MTU 1,500 bytes specifically? What happens when you try to send a 2,000-byte packet over Ethernet?
3. UDP packets can arrive out of order. Describe how a video conferencing application (like Zoom) handles out-of-order and missing packets at the application layer without using TCP.

---

**Continue → [Why TCP Exists](37-why-tcp-exists.md)**
