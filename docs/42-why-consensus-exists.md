# When Agreement Itself Is Hard

## The Problem

Five database replicas must agree on which transactions committed. If they disagree, two users querying different replicas see different account balances. The bank can't operate.

Simple fix: every replica independently processes writes and syncs later. But "sync later" means they diverge in the meantime. If replica 1 commits "transfer $500 from A to B" and replica 3 commits "transfer $500 from A to C" for the same dollars, syncing doesn't help — it produces a contradiction. Syncing works for divergence you can merge; it fails for decisions that must be *the same decision*.

So you add a coordinator: one node receives all writes and forwards them. Perfect — until the coordinator crashes. Now who decides? Replica 2 thinks it should take over. So does Replica 4. They start accepting different writes. When the original coordinator comes back, you have three histories.

Any agreement system must handle:

- Nodes that crash mid-decision and recover with incomplete state
- Network partitions where subgroups can't communicate
- Message reordering and duplication on unreliable links
- Agreement that must survive any minority of nodes failing

## What Would You Try?

Before reading on:

- If you need all 5 replicas to agree before committing, what happens when 1 crashes?
- If you only need 3 out of 5 to agree, what's the minimum number of failures you can tolerate while still guaranteeing agreement?
- A new leader takes over. It doesn't know what the old leader committed before crashing. What information does it need before accepting new writes?

## Failed Attempts

### Attempt 1: Require Unanimous Agreement

Every replica must confirm before anything commits. Intuitive: if everyone agrees, there's no disagreement.

One slow or crashed replica blocks the entire system. At 99.9% uptime per node, five nodes give 99.5% combined uptime — one node down every two days. And if a node crashes *after* saying "yes" but before the others hear it, the system is stuck: some nodes committed, some didn't, and you can't proceed without the crashed node's confirmation. Unanimous agreement is maximally consistent and minimally available.

### Attempt 2: Elect a Leader, Leader Decides

Pick one replica as leader. All writes go through it. The leader commits and tells followers.

Works great until the leader fails. Now you need to elect a new leader. But what if the old leader is only partitioned (slow network), not crashed? Two nodes might both think they're leader — a "split brain." The old leader commits writes to the nodes that can still see it; the new leader commits conflicting writes to the others. When the partition heals, you have two histories and no way to reconcile them automatically. Leader election without safeguards creates the exact problem you were trying to solve.

### Attempt 3: Simple Majority Vote

Require 3 of 5 to confirm. Faster than unanimous. More fault-tolerant than a single leader.

The problem is *who proposes* and *how you handle concurrent proposals*. If nodes 1 and 2 both decide to be leader and start proposing different values at the same time, you can have replica 3 vote for proposal A and replica 4 vote for proposal B. Neither reaches a majority. Nodes keep re-proposing. The system livelock: everyone voting, nobody winning. And if you're not careful about what a new proposer is *allowed* to propose, a node can propose a value that conflicts with what a *previous* round partially committed.

## The Discovery

Attempt 1 (unanimous) is safe but unavailable. Attempt 2 (single leader) is fast but splits under partition. Attempt 3 (majority vote) deadlocks on concurrent proposals and has subtle correctness bugs around committed history.

The insight that resolves this: separate *who proposes* from *what can be proposed*, and use ballot numbers to prevent stale leaders from interfering.

**Paxos** (Lamport, published 1998) establishes two phases. In Phase 1 (Prepare), a proposer picks a ballot number *n* higher than any it's seen, and asks a majority of acceptors: "Will you promise not to accept anything with a ballot lower than *n*?" If a majority promise, they also report back any value they already accepted in a prior ballot. In Phase 2 (Accept), the proposer picks a value — *but if any acceptor reported a prior accepted value, the proposer must use that value* — and asks the majority to accept it. If a majority accepts, the value is chosen.

The key invariant: the "if any acceptor reported a prior value, use it" rule prevents a new proposer from overwriting something a previous round might have committed. Once a value is chosen by a majority, any future majority overlaps with it, so the constraint propagates forward. Split brain is impossible: two leaders with different ballot numbers can't both achieve a majority without one inheriting the other's constraint.

The formal name is **consensus** via **Paxos** (or its many descendants). A cluster of 2f+1 nodes tolerates f failures — majority quorums always overlap. Consensus is what makes replicated state machines possible: the same sequence of decisions on every node, as if there were one computer.

**Why quorums work**: any two majorities of a 2f+1-node cluster must overlap by at least one node. If majority A accepted a value in round r, and majority B is running round r+1's Phase 1, at least one node is in both A and B. That node will report the prior accepted value, and B's proposer is forced to propose it rather than something conflicting. This overlap — the quorum intersection property — is the mathematical bedrock of the whole protocol.

**Multi-Paxos**: running individual Paxos rounds for every write is expensive (two round trips per write). Multi-Paxos elects a stable leader and runs Phase 1 once for many rounds. The leader then reuses its Phase 1 promises for Phase 2 of each subsequent write, reducing two round trips to one. This is what practical systems actually implement — pure Paxos is rarely used directly.

**Byzantine vs. crash faults**: Paxos assumes nodes either follow the protocol correctly or crash. It doesn't handle *Byzantine* faults — nodes that send arbitrary, malicious messages (lie about their state). Byzantine Fault Tolerant (BFT) consensus requires 3f+1 nodes to tolerate f Byzantine nodes (vs 2f+1 for crash-fault tolerance). BFT is used in blockchain systems where nodes may be actively adversarial.

## The Math of Quorum Intersection

The safety guarantee of Paxos isn't intuitive — it's a mathematical consequence of quorum intersection. Let's make it concrete.

A cluster of N = 2f+1 nodes. A quorum is any majority: any set of f+1 nodes. Two majorities Q1 and Q2 must overlap: |Q1 ∩ Q2| ≥ 1. Proof: |Q1| + |Q2| = (f+1) + (f+1) = 2f+2 > 2f+1 = N. By pigeonhole, they must share at least one node.

Why does this matter? In Phase 2, value V is accepted by some quorum Q2. In any subsequent Phase 1, a different proposer contacts another quorum Q1. Since Q1 ∩ Q2 ≠ ∅, at least one node in Q1 accepted V in Phase 2 — and it reports this to the new proposer. The new proposer is forced to inherit V. Safety holds.

Now suppose you relax to non-majority quorums — say, any 2 nodes in a 5-node cluster. Two quorums of size 2: {A,B} and {C,D}. These don't overlap. One proposer can commit V to {A,B}; another can commit W to {C,D}. Both reach "quorum," but different values are chosen. Safety is violated. The majority requirement is exactly the minimum needed for overlap.

**Quorum read + write for strong consistency**: in a replicated key-value store, write quorum W and read quorum R must satisfy W + R > N. This ensures any read quorum overlaps any write quorum, so readers always see at least one node that received the latest write. At N=5, W=3, R=3 (3+3=6>5), you can tolerate 2 node failures on either operation. At W=4, R=2 (6>5), writes are slower but reads are cheaper. Dynamo-style tunable consistency (chapter 50) is this formula applied per-operation.

## Try It

<iframe src="../assets/browser/chapter42/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter42/index.html)

Before changing anything, predict:

- Kill the node that just won the last round. Does the system make progress? How many rounds does it take?
- Increase message loss to 50%. How often does Phase 1 fail to get a majority? What does the protocol do?
- A new proposer starts before the current one finishes. Trace what happens to the ballot numbers.

## Paxos Variants and Descendants

The original Paxos paper (Lamport, 1998) describes single-decree Paxos: consensus on a single value. Practical systems need multi-decree consensus (an ordered log of decisions). The variants:

**Multi-Paxos**: elect a stable leader via Phase 1, then skip Phase 1 for subsequent rounds. The leader's Phase 1 promise covers all future ballot numbers as long as the leader holds the lease. This is the most common production approach.

**Fast Paxos** (Lamport, 2006): allows clients to send values directly to acceptors in certain non-conflicting cases, reducing latency from 2 round trips to 1.5. Falls back to classic 2-round-trip Paxos on conflict. Requires N ≥ 3f+1 instead of 2f+1 for the fast path to be safe.

**EPaxos** (Moraru et al., 2013): Egalitarian Paxos — no stable leader. Any node can commit non-conflicting commands in 1 round trip; conflicting commands take 2. Gives ~40% throughput improvement over Multi-Paxos in geo-distributed deployments where leader proximity matters.

**CASPaxos** (Rystsov, 2018): extends Paxos from consensus on values to consensus on state machine transitions. Each round proposes a function (not just a value) to apply atomically — enabling compare-and-swap semantics on top of the consensus layer without a separate state machine protocol.

**Viewstamped Replication** (Liskov & Cowling, 2012) and **ZAB** (Zookeeper's protocol) are parallel developments with the same safety properties as Paxos but developed independently and with different terminology. All three are provably equivalent in fault-tolerance guarantees.

## Implementation

The simulation is dependency-free JavaScript in `browser/chapter42/index.html` (shared helpers in `browser/common/sim.js`). Look for the two-phase structure: `prepare()` and `accept()` handlers, and the rule in `accept()` that checks whether a prior value must be inherited. That constraint — about eight lines — is the core of Paxos safety.

## When It Breaks

**Dueling proposers (livelock).** Two nodes keep outbidding each other's ballot numbers in Phase 1 without either reaching Phase 2. Paxos is safe (it won't choose conflicting values) but not guaranteed to *make progress* — it's not live in all executions. FLP impossibility (Fischer, Lynch, Paterson, 1985) proves no deterministic protocol can guarantee both consensus and liveness under asynchronous message delivery. Practical systems break ties by randomizing retry delays or using a stable leader. Multi-Paxos avoids dueling proposers by fixing a leader for many rounds — but now the leader election itself is an external problem not specified by Paxos.

**Ballot number exhaustion and wraparound.** In some implementations, ballot numbers are represented as 32-bit integers. If a misbehaving or crashed proposer increments ballots rapidly — thousands per second — the counter can wrap around, producing ballot number 0. A ballot of 0 is accepted by any acceptor (it's the "lowest" valid ballot), enabling safety violations. Production implementations use 64-bit counters with epoch bits: the upper 32 bits are the node ID (unique), the lower 32 bits are the local counter. This guarantees global ordering without coordination, prevents wraparound, and embeds leader identity in the ballot number.

**Learner convergence after partition heal.** When a network partition heals, some nodes have committed a value (majority A accepted it) and some don't know it was committed (they were on the minority side). Paxos has no built-in "synchronization" mechanism — nodes learn a value only when told by a proposer. After a long partition, nodes behind must be explicitly caught up: either a new proposer runs Phase 1 and discovers the committed value, or a separate "learning" mechanism (like a direct state transfer) brings lagging nodes up to date. Protocols built on Paxos (Multi-Paxos, ZAB) add explicit leader-driven log catchup for exactly this reason.

**The coordinator failure window.** If a leader crashes between Phase 2 "accept" and broadcasting the decision, the system is stuck until a new leader runs Phase 1 and discovers whether a value was committed. This window — decided but not learned — requires every new leader to run a full Phase 1 before accepting new requests. GitHub's October 2018 outage was caused by a misconfigured Paxos-like system (MySQL orchestrator) that elected a new leader before the old one's state was safely propagated, creating 24 hours of database inconsistency.

**Performance cliff at high contention.** Each round of Paxos requires two round trips (Prepare + Accept), each requiring a majority to respond. At 10ms cross-datacenter latency, best-case throughput is 50 rounds/second per round trip × 0.5 = ~25 writes/second per consensus group. Real systems work around this with batching (many writes per Paxos round), pipelining (multiple in-flight rounds), and local leaders. Spanner achieves ~1,000 writes/second per shard with Paxos via aggressive batching — but pays ~7ms latency per write even with co-located replicas.

**The replicated state machine model**: consensus is the mechanism; the replicated state machine is the goal. Any deterministic computation (a key-value store, a database, a counter) can be replicated across N machines if all machines receive and apply the same *log of operations* in the same order. Consensus decides the order. Each machine applies the log sequentially, starting from the same initial state, producing the same final state. This is how etcd stores Kubernetes cluster state and how CockroachDB replicates database rows — the operation log is the source of truth, and all replicas are just materialized views of that log.

**Flexible quorums**: the 2f+1 requirement isn't absolute. With Flexible Paxos (Howard et al., 2016), Phase 1 and Phase 2 can use different quorum sizes, as long as any Phase 1 quorum intersects any Phase 2 quorum. A 5-node cluster with Phase 1 quorum size 4 and Phase 2 quorum size 2 satisfies this (4+2 > 5). This means writes only need 2 nodes (fast) as long as leader elections require 4 (safe). The tradeoff: lower write latency at the cost of higher leader election latency.

## Transfer

- **etcd and ZooKeeper** implement consensus (Raft and ZAB respectively) and are used as the coordination backbone for Kubernetes, Hadoop, and Kafka. Every cluster leader election in these systems runs consensus underneath.
- **Blockchain** replaces Byzantine fault tolerance for consensus among untrusted participants — each "block" is a consensus round, but among nodes that may actively lie rather than merely crash. Bitcoin achieves BFT consensus via proof-of-work, making Byzantine attacks computationally expensive rather than relying on a quorum.
- **Distributed locks** (like Redis REDLOCK) are a lightweight application of consensus: all nodes must agree that a lock is held before any single holder can proceed. REDLOCK uses a 3-of-5 quorum — the same majority intersection property as Paxos, applied to lock acquisition timing.
- **Google Spanner**: the first globally-distributed ACID database, using Paxos per shard with TrueTime (chapter 41) for external consistency. Every transaction uses consensus; TrueTime's bounded clock uncertainty provides global ordering that linearizes across data centers. This was considered theoretically impossible before Spanner demonstrated it at production scale.

Try these:

1. A 5-node Paxos cluster. Node 3 (the leader) crashes after sending Phase 2 to nodes 1 and 2 but before nodes 4 and 5 see it. Nodes 1 and 2 accepted. Trace what a new leader on node 4 discovers in Phase 1. What does it propose in Phase 2?
2. Why does Paxos need the ballot number to be *globally increasing* rather than just *per-proposer increasing*? Construct a scenario with 2 concurrent proposers using per-proposer ballot numbers where conflicting values are both accepted by a majority.
3. Multi-Paxos runs many consensus rounds efficiently by reusing Phase 1 across multiple values. What assumption lets it skip Phase 1 for subsequent rounds? What event invalidates this assumption and forces a new Phase 1?
4. FLP impossibility says no deterministic protocol guarantees both safety and liveness under asynchronous messaging. Raft and Paxos are deterministic protocols used in production. How do they avoid the impossibility result?

**Why Paxos wasn't replaced sooner**: Paxos works, and systems built on it (Chubby, Megastore, Spanner) have operated at massive scale for over a decade. The issue is implementation difficulty — the gap between the paper and a correct production implementation is large. The distributed systems community spent 20 years discovering and documenting subtleties that weren't in Lamport's original papers. Raft (2014) is essentially a clean documentation of how Paxos should be implemented, wrapped in a more teachable framing. The underlying math is equivalent. The practical value is that a developer reading the Raft paper can implement a correct system; a developer reading the Paxos papers historically could not.

---

**Continue → [Why Raft Makes Consensus Understandable](43-why-raft-works.md)**
