# The Wall a Single Machine Always Hits

## The Problem

A startup's database runs on the best server money can buy: 96 CPU cores, 12TB of RAM, 100TB of NVMe SSD. It serves 100,000 queries per second and stores 500TB of data. The service grows. At 200,000 queries/second and 1PB of data, the server can't keep up. There is no larger server to buy. The biggest machines available are already purchased.

The vertical scaling wall is real. In 2023, the maximum RAM on a single commodity server is ~24TB. The fastest single NVMe SSD is ~7GB/s throughput. No single machine can serve Google-scale search, process Twitter-scale timelines, or store Amazon-scale product catalogs. The only option is multiple machines.

But "multiple machines" introduces a new problem: they don't share memory. Machine A's RAM is invisible to Machine B. A write on Machine A is unknown to Machine B unless explicitly communicated. The entire model of programming — shared memory, locks, transactions — breaks down when machines are separated by a network.

Any distributed system must:

- Appear as a single system to clients (transparency)
- Continue operating when individual machines fail (fault tolerance)
- Scale capacity by adding machines (horizontal scalability)
- Maintain consistency — machines must agree on the state of shared data

## What Would You Try?

Before reading on:

- If Machine A and Machine B both serve reads, and a write comes in that updates a value, how do both machines end up with the updated value?
- A network partition separates Machine A from Machine B for 10 seconds. Users on A's side can write data that users on B's side can't see. When the partition heals, how do you reconcile the writes?
- If a write is sent to Machine A and the response never arrives (network timeout), did the write happen or not?

## Failed Attempts

### Attempt 1: Replicate Everything Synchronously

Every write goes to all N machines simultaneously. The write is only confirmed when all N machines have written it. All N machines always have identical data. Any machine can serve reads.

Strong consistency: every read sees the most recent write. But the write latency is limited by the slowest machine and the slowest network link. If any machine is unavailable, writes fail. In a 3-machine cluster, one machine's network outage stops all writes for the entire cluster. At N=10 machines spread across datacenters, the write latency is limited by the cross-datacenter RTT (~150ms). For systems requiring fast writes, synchronous replication across datacenters is too slow. And it doesn't scale write throughput: all N machines process every write — N machines handle no more writes/second than one.

### Attempt 2: Partition Data, No Replication

Divide data across machines: users with ID 0–999,999 on Machine A, 1,000,000–1,999,999 on Machine B. Each machine handles only its partition. Writes to Machine A don't touch Machine B. Writes scale linearly: 10 machines = 10× write throughput.

Partitioning solves scale but destroys fault tolerance. If Machine A crashes, all users with IDs 0–999,999 lose access to their data. No replication means no failover. A query that joins data from Machine A's and Machine B's partitions (e.g., "find all orders for user 500,000 along with their product details from the products table") requires a cross-machine join — a network round-trip mid-query. The query planner (chapter 34) has no information about data location. Cross-partition transactions are extremely difficult. This is "sharding without replication" — it scales until one shard fails.

### Attempt 3: Asynchronous Replication (Leader-Follower)

One machine is the leader and takes all writes. It asynchronously replicates to followers. Followers serve reads. If the leader fails, a follower is promoted.

This scales read throughput (many followers). Write throughput is still limited by one leader. More critically: asynchronous replication means followers may lag. A client writes to the leader, then reads from a follower — and doesn't see their own write because the follower hasn't caught up yet. If the leader crashes after a write but before replication, the write is lost. When a new leader is elected, different followers may have different "most recent" writes — which one wins? Asynchronous replication trades consistency for availability and cannot guarantee "read your own writes."

## The Discovery

Synchronous replication provides consistency but can't tolerate failures or scale writes. Partitioning scales writes but loses fault tolerance. Asynchronous replication scales reads but loses consistency.

Every attempt fails because it tries to achieve all three simultaneously. This is not a failure of engineering — it's a mathematical result.

**CAP theorem (Brewer 2000, Gilbert and Lynch 2002)**: a distributed system can guarantee at most two of:
- **Consistency**: every read sees the most recent write
- **Availability**: every request gets a response (not "wait indefinitely")
- **Partition tolerance**: the system continues operating despite network partitions

Network partitions *will* happen. They are not optional. A distributed system must be partition-tolerant. This leaves a choice between consistency (CP systems) and availability (AP systems) under partition.

Modern distributed systems are designed with this tradeoff explicit:

**CP systems** (Zookeeper, etcd, Google Spanner): during a partition, the minority partition stops serving writes (or all writes) to avoid inconsistency. Strong consistency guaranteed; availability sacrificed under partition.

**AP systems** (DynamoDB, Cassandra, CouchDB): during a partition, all nodes continue serving reads and writes. After the partition heals, conflicting writes are reconciled via conflict resolution (last-write-wins, vector clocks, application-level merge). Availability guaranteed; consistency sacrificed under partition.

The real design choice: which failures are acceptable? A banking system can tolerate unavailability (don't let transactions proceed if uncertain) but not inconsistency (don't lose money). A social media "like" counter can tolerate seeing a slightly stale count but must remain available (a user can always like a post). The CAP theorem doesn't say "pick two" arbitrarily — it says *decide which failures your application can tolerate* and design accordingly.

Beyond CAP: PACELC (2012) extends the model — even without partitions, there's a tradeoff between Latency and Consistency. A synchronous write to 3 replicas takes 3× longer than an async write to 1. Engineering distributed systems means choosing operating points in this space, not finding a solution that avoids tradeoffs.

## Try It

<iframe src="../assets/browser/chapter40/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter40/index.html)

Before changing anything, predict:

- With 3 nodes and synchronous replication, cut the network between node 1 and nodes 2–3. Can node 1 still accept writes? Why or why not (for CP behavior)?
- Switch to AP mode and repeat the partition. Can both sides accept writes? What happens to the conflicting values when the partition heals?
- Set replication lag to 500ms in async mode. Write a value and immediately read it from a follower. Do you see your write?

## Implementation

The full model is ~160 lines of dependency-free JavaScript — open `browser/chapter40/index.html` (and the shared helpers in `browser/common/sim.js`) to read or modify it. Everything runs in the browser; nothing to install. Look for the `Node` class with `mode` (cp / ap) and `replicationLog`. The `write(key, value)` method blocks until quorum in CP mode and returns immediately in AP mode. The `partition(nodeA, nodeB)` function severs the message channel between two nodes. The `heal()` function triggers reconciliation, where conflicting writes are resolved by last-write-wins based on logical timestamps.

## When It Breaks

**Split-brain.** In a partition, both sides of a cluster believe they are the leader. Both accept writes. When the partition heals, the two leaders have divergent state. Without careful conflict resolution, the cluster "merges" state in a way that loses one side's writes or produces inconsistent data. Raft and Paxos consensus algorithms prevent split-brain by requiring a quorum (majority) to elect a leader — the minority partition can't elect a leader, so only one leader exists at any time.

**Distributed transactions across shards.** If a transfer moves money from user A (shard 1) to user B (shard 2), the operation must be atomic across two machines. Two-phase commit (2PC) handles this, but as described in chapter 32, 2PC has a coordinator failure mode. Google Spanner uses TrueTime (GPS + atomic clocks providing bounded uncertainty) to order transactions globally, achieving linearizable distributed transactions at datacenter scale — but requires specialized hardware.

**Operational complexity.** Running 100 machines is not 100× harder than running one — it's qualitatively different. Partial failures (a machine that's slow rather than down), network partitions within the datacenter, version skew during rolling upgrades, data skew causing hot shards — none of these exist in single-machine systems. Distributed systems debugging requires distributed tracing (Jaeger, Zipkin), centralized logging (ELK stack), and metrics aggregation (Prometheus). The operational tooling investment is substantial.

## Transfer

- **DynamoDB's eventual consistency.** DynamoDB offers "eventually consistent" reads (default, sees writes within seconds) and "strongly consistent" reads (reads from the leader, 2× cost). This is the CAP tradeoff made explicit in an API: choose your consistency level per-request based on your application's needs.
- **CRDTs (Conflict-free Replicated Data Types).** Data structures designed so that concurrent updates on any node always merge without conflict. A counter CRDT: each node maintains its own increment count; the global count is the sum across all nodes. Two nodes can both increment concurrently; the merge is just addition. No conflict resolution logic needed. Used in collaborative editors (Google Docs), distributed caches, and mobile offline-first apps.
- **The fallacies of distributed computing.** Peter Deutsch's 1994 list: the network is reliable; latency is zero; bandwidth is infinite; the network is secure; topology doesn't change; there is one administrator; transport cost is zero; the network is homogeneous. Every single assumption is false in practice. Designing for distributed systems means designing for the failure of each of these assumptions.

Try these:

1. In a 5-node cluster using majority quorum (3-of-5), how many nodes can fail before writes become unavailable? Before reads (with strong consistency) become unavailable?
2. What is "read repair"? How does Cassandra use it to improve consistency without requiring synchronous writes?
3. A system has 3 datacenters. Writes must succeed in at least 2 datacenters before confirming. What consistency level does this provide? What availability does it sacrifice if one datacenter goes offline?

---

**Continue → [Why Clocks Lie](41-why-clocks-lie.md)**
