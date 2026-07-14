# When Every Clock Disagrees

## The Problem

You run an online store. Two customers click "buy" on the last item at nearly the same moment — one in Tokyo, one in Toronto. Your servers in each city record the event with their local timestamps. Tokyo says its order came first at 14:23:00.001. Toronto says *its* order came first at 14:23:00.001. Both timestamps are right by their local clocks. Both cannot be right about ordering.

You oversell. Someone is getting an apology email and a refund.

This isn't a software bug — it's physics. Clocks drift. A quartz crystal oscillates slightly faster or slower depending on temperature, age, voltage. Left alone, two servers' clocks diverge by tens of milliseconds per day. NTP (Network Time Protocol) corrects this but introduces its own problem: the correction happens over the network, which takes variable time. NTP can tell you the "true" time to within ~1–50ms, but it can't synchronize clocks perfectly, and it certainly can't deliver that correction instantaneously.

Any ordering system must handle:

- Clocks on different machines that drift and diverge
- Network corrections that arrive with variable delay
- Events that happen faster than clock resolution
- The need to order events without a global oracle that knows "real" time

## What Would You Try?

Before reading on:

- If two servers both timestamp an event at the same millisecond, which event came first? Can you know?
- NTP synchronizes clocks to ~1ms accuracy. If two events happen 0.5ms apart on different machines, what does that tell you about using wall-clock time for ordering?
- A database log has entries from three replicas, each with a timestamp. You want to replay them in causal order. What's missing from a timestamp alone?

## Failed Attempts

### Attempt 1: Trust Each Machine's Clock

Each server timestamps its writes. To determine ordering, compare timestamps. Simple, zero overhead.

The problem: clocks drift. Server A runs slightly fast; Server B runs slightly slow. After a week, they disagree by 500ms. An event on A at 10:00:00.000 might have happened *after* an event on B at 10:00:00.200 — but A's timestamp makes it look earlier. Google's Spanner team measured clock drift on their servers and found drifts of up to 6ms even with GPS clocks and atomic references. Consumer hardware is far worse. Trusting wall clocks for ordering gives you *apparent* ordering that doesn't reflect causality.

### Attempt 2: Use a Central Time Server

Route every timestamp request through a single authoritative server. Everyone agrees because they all ask the same source.

This works until you measure the overhead. A write operation now requires a round-trip to the time server before it can proceed. At 10ms per round-trip and 100,000 writes/second, you've added 1,000 seconds of latency to your system per second of real time — impossible. Worse, the time server becomes a single point of failure. The moment it goes down, every write in your distributed system stalls. You've serialized a distributed system through a bottleneck, defeating the reason you distributed it.

### Attempt 3: Vector Clocks (Track Causality Explicitly)

Instead of one number, give each node a vector of counters — one counter per node. When node A sends a message to node B, it includes its full vector. B takes the element-wise maximum and increments its own counter. Now you can tell: if A's vector is component-wise ≤ B's vector, A's event *happened before* B's.

This captures causality correctly. But it scales poorly: vector size grows with node count. At 1,000 nodes, every message carries 1,000 counters. Comparing vectors costs O(n). Storing them costs O(n) per event. And critically: you can only compare events that are causally related. Two events on independent nodes with no causal link are *concurrent* — vector clocks correctly say "I can't tell you which came first." That's honest, but it means ordering is still partial, not total.

## The Discovery

Attempt 1 fails because physical clocks are unreliable. Attempt 2 fails because central coordination is too expensive. Attempt 3 gets causality right but can't order unrelated events and grows with node count.

The insight: maybe the goal was wrong. You don't need *physical* time. You need a number that increases monotonically and that every node can agree on *after the fact*, even if it requires coordination.

**Lamport clocks** give each node a counter. The rules are simple:
1. Increment your counter before every event.
2. When sending a message, attach your current counter.
3. When receiving a message with counter C, set your local counter to max(local, C) + 1.

This guarantees: if event A *happened before* B (A caused B, directly or through a chain), then A's Lamport timestamp is strictly less than B's. The converse isn't true — a lower timestamp doesn't mean "happened before," just "might have." For total ordering, break ties by node ID. Now every event in the whole system gets a unique, comparable number.

The formal name is the **Lamport timestamp** (Leslie Lamport, 1978). Combined with physical clocks for rough calibration and logical clocks for causality, modern systems like Google's TrueTime bound the uncertainty explicitly — Spanner waits out the uncertainty window before committing, guaranteeing that if its clock says [T-ε, T+ε], it won't commit until after T+ε so causality holds even across data centers.

## Try It

<iframe src="../assets/browser/chapter41/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter41/index.html)

Before changing anything, predict:

- If you increase message delay in the simulation, what happens to how often logical ordering disagrees with arrival order?
- Two nodes with no messages between them both send to a third. Can you determine which sent first?
- What happens to Lamport timestamps if one node crashes and restarts with counter = 0?

## Implementation

The browser simulation is dependency-free JavaScript — open `browser/chapter41/index.html` to read or modify it (shared helpers in `browser/common/sim.js`). Look for the `receive(msg)` function that does the `max(local, incoming) + 1` step — that one line is the entire Lamport clock update rule.

## When It Breaks

**Clock skew during NTP correction.** When NTP corrects a fast clock, it can cause the system clock to *go backward* — or freeze while it catches up. Software that calls `gettimeofday()` and assumes it's monotonic breaks. Linux solved this with `CLOCK_MONOTONIC`, which never goes backward but isn't wall time. Cloudflare experienced this in 2017 when a leap-second correction caused their Go-based software to measure zero-length or negative-length intervals, causing a 1-hour global outage.

**Lamport clocks don't capture concurrency.** Two events with no causal relationship both get timestamps, and you *can* order them — but that order is arbitrary. For a shopping cart, "add item A" and "add item B" are truly concurrent and order doesn't matter. But for a bank balance, "deposit $100" and "withdraw $100" are also concurrent — and here, order matters enormously. Lamport timestamps tell you *a* total order; they can't tell you if that order is *the right* order for your semantics.

## Transfer

- **Git commits** use content-addressed hashes (chapter 13), not timestamps, for identity — because timestamps lie. Git's DAG of parent pointers *is* the causal order, independent of when your clock said it happened.
- **Database MVCC** (multi-version concurrency control) uses logical transaction IDs, not wall-clock time, to determine which version of a row a transaction should see.
- **Event sourcing systems** like Kafka assign monotonically increasing offsets within a partition — explicit logical time that makes ordering unambiguous regardless of producer clock drift.

Try these:

1. Three nodes, each processing 100 events per second with 10ms message latency between them. How often would pure wall-clock ordering produce wrong causal order? Estimate.
2. Implement Lamport clock increments for this scenario: A sends to B, B sends to C, C sends to A. Draw the timestamp sequence. Is the final total order consistent with causality?
3. TrueTime waits out clock uncertainty before committing. If uncertainty is [−7ms, +7ms], what's the minimum wait? What's the throughput cost at 10 commits/second per node?

---

**Continue → [When Agreement Itself Is Hard](42-why-consensus-exists.md)**
