# Why Raft Makes Consensus Understandable

## The Problem

You understand that consensus is necessary (chapter 42). You reach for Paxos. The paper is 18 pages of prose and mathematical argument, with no pseudocode. The follow-up "Paxos Made Simple" paper is still 14 pages. Every team that implements Paxos builds something slightly different, subtly wrong, or with undocumented assumptions. Leslie Lamport himself noted that the lack of a reference implementation caused years of confusion.

The distributed systems research lab at Stanford surveyed dozens of Paxos implementations and found that *none* of them correctly handled all of the edge cases described in the literature. Chubby (Google's lock service) is built on Paxos but required months of careful engineering and still needed extensions that Paxos didn't specify. Zookeeper's ZAB protocol is "Paxos-inspired" but different enough that Paxos proofs don't directly apply.

Correct consensus matters not just for academic elegance — it's the foundation of every replicated database, distributed lock, and leader election in production systems. Getting it subtly wrong means data loss or split-brain under real failure modes.

Any understandable consensus protocol must:

- Decompose into independently verifiable components
- Have a clear, correct leader election mechanism
- Specify exactly how the log is replicated and when entries are safe to apply
- Handle restarts, new nodes, and membership changes explicitly

## What Would You Try?

Before reading on:

- What's the minimum information a new leader needs to know before it can accept writes? Think about what could have committed while the old leader was alive.
- In Paxos, any node can propose at any time. What goes wrong? What if you restrict proposals to one elected leader?
- "A log entry is committed when a majority of nodes have it." What should a new leader do with entries it has that weren't committed?

## Failed Attempts

### Attempt 1: Allow Any Node to Initiate Rounds (Pure Paxos)

The flexibility of Paxos — any node can start a round at any time — sounds powerful. But it creates dueling proposers (chapter 42). In practice, every production Paxos system immediately adds a "distinguished proposer" constraint, essentially electing a leader anyway. But now you have undocumented constraints layered on a protocol that doesn't specify them, making correctness reasoning much harder.

### Attempt 2: Strong Leader but No Log Safety Rule

Elect a leader. All writes go through it. On receiving a write, the leader appends to its log and replicates to followers. Commit when a majority have it.

The problem surfaces at leader transition. The old leader committed entries 1–100. The new leader has entries 1–95. Does it have entries 96–100? Maybe — it depends on which nodes it asked. The new leader doesn't know if 96–100 were committed (seen by a majority) or just partially replicated. If it assumes they weren't committed and overwrites them, you lose acknowledged writes. If it assumes they were and applies them, you might apply writes the old leader hadn't finished.

Without a precise rule for what the new leader inherits, every implementation makes a different choice, and some are wrong.

### Attempt 3: New Leader Replays Everything from the Beginning

The new leader asks all nodes for their complete logs, takes the longest/most-complete one, and starts from there. Safe in theory: the longest log from a majority will include everything committed.

But "longest" isn't quite right. A crashed node might have an *uncommitted* long log — entries the previous leader was replicating when it crashed. Blindly taking the longest log and committing everything in it applies uncommitted entries, which the rest of the cluster never agreed to. The length heuristic is close but wrong, and it's not obvious *why* it's wrong without a precise definition of "committed."

## The Discovery

Paxos's flexibility makes it hard to reason about. Adding a strong leader helps, but the transition still requires precise rules about what the new leader can and cannot do.

Raft's insight: decompose consensus into three separate problems — *leader election*, *log replication*, and *safety* — and specify each exactly. The key innovation is a **term number**: a monotonically increasing counter that increments every time a new leader is elected. Every message carries the sender's term. If you see a higher term, you immediately defer. If a leader sees a higher term from a follower, it steps down. This prevents two leaders from coexisting: the old leader's messages have a lower term number and are ignored.

**Log replication** is explicit: the leader appends entries and sends AppendEntries RPCs to all followers, which include the entry and the index/term of the entry *before* it (a consistency check). A follower rejects if it doesn't have that preceding entry. The leader retries until the follower's log is consistent, then sends the new entries. A log entry is **committed** when the leader has replicated it to a majority — and the leader's *own* current term must be represented among those entries (no committing old-term entries by counting followers alone).

**Leader election** requires candidates to have a log "at least as up-to-date" as the majority they win votes from. "At least as up-to-date" means: higher last-log term, or same term and longer log. This guarantees the winner has all committed entries.

The formal name is **Raft** (Ongaro & Ousterhout, 2014 — the "In Search of an Understandable Consensus Algorithm" paper). Its authors verified it produces the same guarantees as Paxos and showed in user studies that students who learned Raft scored significantly higher on correctness questions than those who learned Paxos.

**Membership changes**: what happens when you want to add or remove nodes from a running Raft cluster? Adding node 6 to a 5-node cluster changes the quorum size: during the transition, some nodes think quorum = 3 (old config) and some think quorum = 4 (new config). Two different majorities might elect two leaders simultaneously. Raft's solution: joint consensus — a configuration entry committed to *both* old and new majorities simultaneously before switching. This is the hardest part of the protocol to implement correctly and the most likely to be subtly wrong in production implementations.

**Linearizability vs. sequential consistency**: Raft provides linearizability for single-key operations — every read sees the value of the most recent committed write, as if operations happened atomically at a single instant. But reads that go to followers (for read scaling) see stale data. Leader reads are linearizable but bottleneck on the leader. The solution: lease-based reads, where the leader holds a "lease" (a time-bounded guarantee that no new leader can be elected) and serves reads locally without a full round trip — but this reintroduces a dependency on clock accuracy, coming full circle to chapter 41.

**Snapshot and log compaction detail**: the log grows without bound — each committed operation is one entry. After months of operation, catching up a lagging replica means replaying the entire history. Raft specifies `InstallSnapshot` RPC: the leader serializes its entire state machine state into a snapshot file, transfers it to the lagging follower, and the follower replaces its log entirely with the snapshot plus any subsequent entries. The snapshot includes the index and term of the last included entry, so the follower can verify the transition without the old log. Getting snapshot installation right is delicate: the leader must not compact entries that a follower is currently receiving, and the follower must atomically swap its state (old snapshot + new log) to avoid partial state. etcd's implementation of InstallSnapshot was a source of correctness bugs through 2018 that required several patch releases.

**Pre-vote extension**: standard Raft has a liveness problem. A partitioned follower — one that can't reach the leader but also can't win an election — keeps incrementing its term and issuing timeouts. When the partition heals, it floods the cluster with RequestVote RPCs with a higher term, causing the current leader to step down unnecessarily. The **pre-vote** extension (not in the original paper, but in most production implementations): before incrementing its term, a candidate first asks peers if they would vote for it *if it did* start a real election. Only if a pre-vote majority says yes does it increment its term. Partitioned nodes that can't win pre-votes don't disrupt the cluster. etcd, TiKV, and CockroachDB all implement pre-vote.

**ReadIndex optimization**: full read linearizability requires a round-trip (the leader must confirm it's still leader before serving a read). The ReadIndex optimization: the leader records its current commit index as the "read index" for this request, then confirms leadership via a heartbeat, then serves the read once the state machine has applied up to the read index. This adds only one heartbeat delay (rather than a full Paxos-style write round trip) while maintaining linearizability. etcd uses ReadIndex for all reads; this is why etcd reads are slightly slower than a pure in-memory cache but correct under leadership changes.

## The Safety Proof in Detail

Raft's safety property: if a log entry is committed in term T, no future leader will have a conflicting entry at the same log index. Let's prove this informally.

Claim: if entry (index i, term T) is committed, any leader elected in term T' > T has that entry in its log.

Proof by induction on T'. Base case: T' = T+1. The new leader won the election in term T+1, meaning a majority of nodes voted for it. At least one of those voters was in the commit quorum for entry (i, T) — call it node X. Node X voted for the new leader, which means the new leader's log is "at least as up-to-date" as node X's log. Node X has entry (i, T). For the new leader's log to be "at most as up-to-date," it would need: last log index < i (impossible — the leader's log would be shorter at a position where X has an entry, so X would not vote for it), or equal last log index with lower term (impossible — X's last entry has term ≥ T, so the leader's must too, or X wouldn't vote). Therefore, the new leader has entry (i, T). Induction holds.

**The commit rule refinement**: a new leader cannot directly commit old-term entries just by counting acknowledgements. Consider: leader L1 in term 3 partially replicates entry [index 5, term 3] to 2 of 5 nodes, then crashes. New leader L2 in term 4 takes over, but doesn't have entry [5,3]. It starts appending new entries. If L2 counts "2 nodes have [5,3]" as a commit, it violates safety — those 2 nodes are a minority, not a majority. Raft's rule: a leader only commits entries from its *current term* via majority count. Old-term entries are committed *implicitly* when a current-term entry later in the log is committed (because the log is ordered). This is the subtlest part of Raft and the one most frequently misimplemented.

## Try It

<iframe src="../assets/browser/chapter43/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter43/index.html)

Before changing anything, predict:

- Kill the current leader. How many election rounds does it take to elect a new one? Does it depend on timing?
- Add entries rapidly, then partition the leader from all followers. What happens to uncommitted entries when the partition heals?
- A follower falls far behind. When it rejoins, does the leader send it all missing entries at once or one at a time?

## Raft in Production: What Actually Gets Implemented

The Ongaro paper specifies Raft at a high level. Production implementations diverge in documented ways:

**Batch AppendEntries**: the paper sends one AppendEntries per new log entry. Real systems batch multiple entries per RPC (typical batch: 64–512 entries). The consistency check (index+term of the preceding entry) is done once per RPC, not once per entry. This reduces RPC overhead by ~100× at high write throughput.

**Pipeline replication**: rather than waiting for a majority acknowledgement before sending the next entry, the leader pipelines AppendEntries RPCs — sending subsequent entries without waiting for the prior ones to commit. This keeps the network pipeline full. The commit point advances as acknowledgements arrive, but replication is continuous. This is how etcd achieves ~10,000 writes/second on commodity hardware.

**Parallel disk flush**: when a follower receives AppendEntries, it must persist the entries to disk (WAL write) before responding. On a spinning disk, this is 5–10ms. On NVMe SSD, 0.05–0.2ms. etcd uses `fdatasync()` for durability; some production Raft implementations use group commit to batch multiple followers' disk writes into a single `fsync()`, amortizing disk latency across many pending acknowledgements.

**Leader lease read optimization**: to serve linearizable reads without a round trip, the leader uses a "lease": the maximum election timeout minus a clock uncertainty bound. During the lease window, no new leader can exist (because election requires a timeout to expire, and the timeout is longer than the lease). The leader serves reads directly from its state without re-confirming leadership. This reduces read latency from 2×RTT (ReadIndex round trip) to 0 (local). The risk: clock skew (chapter 41) that makes the actual timeout shorter than expected invalidates the lease. Systems like TiKV implement lease reads but provide configuration options to disable them in clock-unsafe environments.

**Joint consensus encoding**: the membership change config entry is encoded as a two-phase commit in the log. First, the leader appends a "C_old,new" entry that activates joint consensus mode. Both old and new majorities must accept any entry while C_old,new is active. When C_old,new commits, the leader appends a "C_new" entry that completes the transition. etcd implements this, CockroachDB uses a simplified single-phase membership change that works for one-node-at-a-time changes.

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter43/index.html` (shared helpers in `browser/common/sim.js`). The right panel tracks `raftLeader` (an integer node index) and `raftTerm`; a crash randomly reassigns `raftLeader` to a surviving node and increments the term. `raftConflicts` counts ticks where no leader is available. The left panel (multi-master) allows any node to write each tick, accumulating `mlConflicts`. The "Write rate %" slider controls how often writes arrive, making the conflict difference between the two approaches visible over time.

## When It Breaks

**Election timeout collisions.** If all followers time out at the same time, they all become candidates simultaneously and split the vote — no one wins. Raft uses randomized timeouts (typically 150–300ms per node, each chosen randomly) to ensure one node usually starts its election first. But under pathological network conditions, repeated splits are possible, and the system makes no progress during them. Production clusters tune the timeout range based on network RTT. etcd recommends election timeout 5–10× the heartbeat interval, and heartbeat interval 0.5–20ms depending on disk latency — the election timeout must be significantly longer than a disk write so a leader under I/O load doesn't trigger false elections.

**Stale reads at follower.** Reads that go to followers for load distribution see stale data. How stale? At minimum, one heartbeat interval behind (the leader's latest commit isn't propagated until the next heartbeat). At worst, during a leader change, a follower might be many seconds behind. Applications that need read-your-writes consistency — "I wrote this record, I need to immediately read it back" — must route reads to the leader or use ReadIndex. Many applications accidentally use follower reads during testing (when the single-node cluster is also the leader) and only discover the staleness problem in multi-node production.

**Network partition + clock skew compound failure.** Lease-based reads (the optimization that lets the leader serve reads without a round trip) depend on the leader knowing its lease hasn't expired. The lease timer is based on the leader's local clock. If the leader's clock runs fast, it might serve reads past the end of its actual lease, after a new leader has been elected elsewhere. The new leader's writes are invisible to the old leader's clients. This is the exact failure mode chapter 41 warns about — clock drift. Raft explicitly notes that lease-based reads require "bounded clock drift" and must be disabled if NTP is unavailable or unreliable.

**Log divergence after asymmetric partition.** A leader partitioned from most nodes keeps accepting writes from clients (it thinks it's still leader) while a new leader is elected in the majority partition. When the partition heals, the old leader's entries are overwritten. Clients that received "OK" from the old leader lose those writes. The fix: clients must not trust a write until they hear from the new term's leader. Applications using Raft need to handle this retransmission case explicitly — etcd and CockroachDB both document this requirement.

**Snapshot and log compaction.** The Raft log grows forever — every committed write is an entry. After months of operation, replaying the full log from the beginning to reconstruct state would take hours. Raft requires log compaction: the state machine periodically snapshots its state, and log entries before the snapshot point are discarded. A new node joining the cluster (or a node far behind) receives the snapshot directly rather than replaying the full log. Snapshot installation and the preceding entries interact with the in-progress log in subtle ways — it's another correctness minefield that practical implementations handle differently.

## Transfer

- **etcd** (used by Kubernetes for all cluster state) is a Raft implementation. Every pod scheduling decision, config map update, and secret write goes through Raft consensus. The Kubernetes control plane's correctness depends entirely on etcd's Raft implementation being right.
- **CockroachDB and TiKV** use Raft per-shard to replicate data ranges. Each shard is an independent Raft group, giving you both partition tolerance and horizontal scale. CockroachDB maintains ~10,000 Raft groups per node in a large cluster — making per-group overhead critical to optimize.
- **Distributed tracing leaders** in systems like Jaeger use Raft-style election to decide which node collects and aggregates spans, without a hardcoded coordinator.
- **FoundationDB** (Apple's distributed key-value store, used for iCloud) uses a Paxos variant under the hood but documents its consensus layer in the Raft style for implementers — the decomposition-into-sub-problems approach is so clarifying that even non-Raft systems adopt the framing.

Try these:

1. A 5-node Raft cluster. The leader has log entries [1,2,3,4,5] with entry 5 uncommitted (only the leader has it). The leader crashes. Which nodes are eligible to win the election? Which are not? If nodes 2 and 3 both have entries [1,2,3,4] and nodes 4 and 5 both have [1,2,3], which node(s) can win?
2. Raft's safety proof depends on the "at least as up-to-date" vote rule. Construct a scenario where a candidate with a *shorter* log could win without this rule, and show what goes wrong (which previously committed entry gets overwritten).
3. Raft handles node restarts by replaying log entries. If your state machine isn't idempotent (applying an entry twice produces different results), what must you do? How does etcd handle this?
4. Joint consensus during membership change: a cluster transitions from {A,B,C} to {A,B,C,D,E}. During the joint configuration, a committed entry must be accepted by a majority of *both* the old config ({A,B,C} — 2 of 3) and the new config ({A,B,C,D,E} — 3 of 5). Which combinations of nodes form a valid commit quorum during this transition? What happens if D and E are slow to catch up?

**Raft and the understandability claim**: the original Raft paper explicitly set "understandability" as a design criterion — unusual for a systems paper. Ongaro ran a user study comparing Raft and Paxos comprehension. Students who learned Raft scored 14 percentage points higher on correctness questions about leader election and 6 points higher on log replication. The understandability claim was empirically validated, not just asserted. This matters: a protocol that engineers can implement correctly beats one with superior theoretical properties but frequent implementation bugs.

**What Raft doesn't specify**: the paper leaves several things to implementers. Exactly how long election timeouts should be (environment-dependent). How to integrate with client request retries (clients must be prepared to retry on leader change). How to handle reads that arrive during leadership transitions (implementation-specific consistency vs. latency tradeoff). What "applied" means — how to checkpoint the state machine in a crash-safe way. These gaps are not bugs in Raft; they're appropriate separations of concern. But they're where most production implementation bugs live.

---

**Continue → [Why Eventual Consistency Exists](44-why-eventual-consistency-exists.md)**
