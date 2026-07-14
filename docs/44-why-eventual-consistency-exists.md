# The Price of Always Being Right

## The Problem

Your e-commerce site has users in São Paulo, Singapore, and Stockholm. Every product page shows a "5,234 items sold" counter. To keep this number accurate everywhere, you could run all writes through consensus (chapter 43) — any increment must be agreed to by a majority of your global replicas before it's visible.

That majority includes nodes on other continents. A "sold" event in Stockholm must wait for acknowledgment from Singapore before it shows up anywhere. Best-case cross-continental round trip: ~150ms. The page that took 50ms to load now takes 200ms for every counter update, just to guarantee global accuracy. At high traffic, writes queue up waiting for consensus. Your "sold" counter slows your site to a crawl.

So you loosen the requirement. The counter in São Paulo can show 5,234. Singapore might show 5,241. Stockholm might show 5,229. Different users see different numbers, but all of them are *roughly* right. And after traffic dies down, all replicas will eventually agree on the same number.

Any system that trades consistency for availability must handle:

- Reads that return stale data without knowing it's stale
- Concurrent writes to the same data from different replicas
- Conflicts when replicas sync: which write wins?
- Application logic that depends on how "eventually" eventual really is

## What Would You Try?

Before reading on:

- If two replicas both accept a write to the same row simultaneously, then sync — what are the possible outcomes? What information do you need to pick the right one?
- A user adds an item to their cart on their phone. Before the write propagates, they open a laptop and see an empty cart. What should the system do?
- Amazon's shopping cart "add" and "remove" are different operations. Why might it be safer to only *apply* adds and treat removes separately?

## Failed Attempts

### Attempt 1: Last Write Wins (by Wall Clock)

Simplest resolution: when two replicas conflict, keep the write with the later timestamp. LWW is easy to implement and requires no coordination.

But clocks lie (chapter 41). A write from São Paulo at 14:23:00.100 might have *causally happened* before a write from Stockholm at 14:23:00.050 if the clocks are skewed. LWW silently discards causally later writes that happen to have earlier timestamps. You lose data, and the system gives no warning. Cassandra uses LWW by default; it's fast but requires either synchronized clocks (expensive) or accepting silent data loss on conflicts. Many Cassandra users have lost data this way without realizing it.

### Attempt 2: Sync Everything Periodically, Merge by Application Logic

Replicas accept all writes locally. Every minute, they sync their logs and run application-specific merge logic. This is flexible — the application can decide which write matters.

The problem is conflict detection. How do you know two writes conflict? If you only track the final state, you can't tell whether "value = 7" was written by user A overwriting user B, or by both independently arriving at 7. You need version history. And if the sync window is too long (minutes), clients read genuinely stale data — not "slightly stale" but "substantially wrong." The merge logic also has to be correct for every field, and different fields have different semantics. Building application-level merge for every entity type is engineering-intensive and error-prone.

### Attempt 3: Read Repair on Access

When a client reads, the system queries multiple replicas and returns the majority value. If replicas disagree, the system writes the majority value back to the minority replica — "repairing" the stale one.

Read repair works but delays your reads: you must wait for multiple replicas to respond. At 99th percentile, one replica is always slower. And it only repairs data that's actually read. Cold data (rarely accessed) stays stale until it's read, which is exactly the data your monitoring misses. CouchDB uses this approach; it's correct but introduces read latency that makes it unsuitable for high-throughput paths.

## The Discovery

LWW loses data. Application-level merge is complex and brittle. Read repair is correct but slow.

The underlying problem: you can't merge two writes without knowing their causal relationship. Was write A before B, B before A, or did they happen concurrently? Without that information, any merge is a guess.

**CRDTs** (Conflict-free Replicated Data Types) solve this by designing data structures whose merge operation is *always* correct, regardless of order or concurrency. The key insight: not all data types conflict. A counter where you can only *increment* never has a merge conflict — just take the maximum per-node counter and sum them. A set where you can only *add* elements never conflicts — just take the union.

The general pattern: define operations that are commutative, associative, and idempotent. Apply them in any order; the result is the same. G-Counters, 2P-Sets, OR-Sets, LWW-Registers — each is a CRDT for a specific data structure. Riak, Akka Distributed Data, and Redis (some data structures) use CRDTs for eventual consistency that never loses data.

For data that *doesn't* fit a CRDT, you commit to weaker guarantees explicitly: **eventual consistency** means "if no new updates are made, all replicas will converge to the same value — eventually." The formal name includes CAP theorem (Brewer, 2000): under partition, you choose between Consistency and Availability. Eventual consistency chooses Availability.

## Try It

<iframe src="../assets/browser/chapter44/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter44/index.html)

Before changing anything, predict:

- Partition the replicas for 10 seconds, then heal. How long before all replicas agree?
- What happens to a counter CRDT if you add the same increment twice (network retry)?
- Switch to LWW mode and make two conflicting writes simultaneously. Which wins? Is it the "right" one?

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter44/index.html` (shared helpers in `browser/common/sim.js`). Look for the `merge()` function — in CRDT mode it's element-wise max; in LWW mode it's timestamp comparison. The difference in those few lines illustrates the entire correctness gap.

## When It Breaks

**"Eventually" can be a long time.** Eventual consistency guarantees convergence but not *when*. During a network partition that lasts hours, replicas diverge for hours. Users see stale data for the partition duration. Systems that claim "eventual consistency" but have partition-heal times in the minutes-to-hours range are not eventually consistent in any useful sense for user-facing applications. Dynamo's original paper noted read-your-writes consistency as a common additional guarantee that eventual consistency alone doesn't provide.

**CRDT size blowup.** OR-Sets (observed-remove sets) must track every element *ever added*, because removing an element requires matching against the unique tag used when it was added. A set with high churn (add/remove frequently) grows unboundedly. Tombstone accumulation in Cassandra's eventual consistency model caused a famous performance degradation at Discord — their message delete rate produced so many tombstones that reads became slow even on small datasets.

## Transfer

- **DNS** is deliberately eventually consistent: a record change propagates through TTL-driven cache expiry over hours. Operators accept that some users resolve old IPs for the TTL window in exchange for global DNS availability without consensus overhead.
- **Social media "likes" counters** on Facebook, Twitter, and YouTube use eventually consistent counters — slightly wrong numbers are acceptable and consistency is never worth the latency cost.
- **Collaborative text editors** (Google Docs) use OT (Operational Transformation) or CRDTs to merge concurrent edits without consensus, giving each user immediate local feedback while converging to a shared document.

Try these:

1. Design a shopping cart CRDT. Users can add items and remove items. "Add then remove" and "remove then add" should produce the same result. What data structure works?
2. A G-Counter has 3 nodes with per-node counts [node1: 5, node2: 3, node3: 8]. Node 1 and node 2 merge. What's the result? Then that result merges with node 3. What's the total count?
3. Your system uses LWW with NTP-synchronized clocks. Clocks are accurate to ±5ms. Two conflicting writes happen 3ms apart. What's the probability LWW picks the wrong one? What's the correct answer?

---

**Continue → [Why Distributed Transactions Hurt](45-why-distributed-transactions-hurt.md)**
