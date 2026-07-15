# Readers and Writers, Without the Wait

## The Problem

A bank runs two things simultaneously: a customer withdrawing $200 (a write transaction) and the auditor generating a monthly report (a long-running read transaction scanning millions of rows). If writing requires exclusive locks on every row touched, the auditor's report holds read locks on those rows, preventing the withdrawal. If the withdrawal holds a write lock on the account row, the auditor can't read it. They block each other.

With 200 concurrent users, this is not a rare collision — it's the normal state. Every read blocks writes; every write blocks reads. A database that serializes all readers and writers on each row becomes a single-threaded system. PostgreSQL before MVCC handled 1,000 transactions/second. After MVCC: 10,000+.

Any solution must:

- Allow readers to see consistent data without blocking writers
- Allow writers to proceed without waiting for readers to finish
- Ensure each reader sees a stable snapshot (no phantom reads mid-transaction)
- Not leak unbounded amounts of old data

## What Would You Try?

Before reading on:

- If a reader sees a row mid-update (halfway between old and new value), what could go wrong in a financial report?
- What if instead of updating a row in place, you kept the old version around while writing a new one? What extra information would you need to store?
- Who gets to see the old version and who sees the new one?

## Failed Attempts

### Attempt 1: Read-Write Locks (Shared/Exclusive)

Use shared locks for reads (multiple readers coexist) and exclusive locks for writes (one writer, no readers). A read lock on a row blocks any write to it; a write lock blocks all reads and other writes.

Shared locks among readers are fine — concurrent reads never conflict. But a long-running reader (the auditor's report, running for 30 minutes) holds shared locks on every row it touches. Any writer trying to update those rows blocks for 30 minutes. In practice, the auditor's report prevents all updates to any account it has read. With millions of rows and one long reader, the entire database becomes read-only for 30 minutes. The throughput collapse is not a bug — it's the correct behavior of the lock model. Locks are the wrong abstraction for this problem.

### Attempt 2: Snapshot at Transaction Start (Full Copy)

When a transaction starts, take a full copy of all database data. The transaction reads from its private copy; writers modify the live data. Readers never block writers because they're reading their own snapshot.

Works for small databases. A 100GB production database would require 100GB per transaction snapshot — infeasible. Even with copy-on-write optimization (only copy pages that have been modified), a long-running transaction touching many pages accumulates enormous snapshot storage. Worse: the snapshot is stale from the moment it's taken. A transaction that runs for 30 minutes has a 30-minute-old view of the world. For the monthly report, that's acceptable. For a transaction that should see recent data, it's wrong. Full snapshot copies are too expensive and too inflexible.

### Attempt 3: Timestamped Append-Only Records

Instead of updating rows in place, append a new version with a "valid from" timestamp. Reads filter by timestamp: "show me the version valid at time T." Old versions are kept alongside new ones.

This gives each reader a consistent view at their start timestamp. But plain append-only means: every update doubles storage (old and new version coexist indefinitely). A row updated 100 times has 100 versions on disk, each consuming space. Queries must scan all versions of a row to find the one valid at the reader's timestamp. With no cleanup mechanism, the table grows without bound. And with timestamps rather than transaction IDs, the system is vulnerable to clock skew (chapter 41) — two transactions with the same timestamp can conflict in non-deterministic ways.

## The Discovery

Read-write locks force readers and writers to block each other. Full copies are too expensive. Append-only without cleanup is unbounded.

The correct design uses transaction IDs (monotonically increasing integers, not wall-clock time) and version chains with a garbage collector:

**MVCC (Multi-Version Concurrency Control)**: every row version is tagged with the transaction ID that created it (`xmin`) and, if deleted or superseded, the transaction ID that ended it (`xmax`). When a transaction reads a row, it applies a **visibility rule**: "show me the version where `xmin` ≤ my snapshot ID and `xmax` > my snapshot ID (or doesn't exist)." This gives every reader a consistent snapshot of the database as of its start transaction ID, regardless of concurrent writes.

Writers create new row versions without touching the old ones. The old version remains visible to readers whose snapshot predates the write. No blocking. The writer and reader operate on different row versions simultaneously.

**Cleanup (vacuum)**: when no active transaction can see an old version (its `xmax` < the oldest active snapshot ID), it's dead space. PostgreSQL's `VACUUM` scans for dead tuples and marks them as free space for reuse. Without vacuum, dead tuples accumulate indefinitely (the "table bloat" problem).

The result: readers and writers never block each other. Writers only block other writers (to avoid write–write conflicts, which still require locking). In PostgreSQL, a read-only query like the auditor's report can run for hours without blocking a single write.

## Try It

<iframe src="../assets/browser/chapter33/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter33/index.html)

Before changing anything, predict:

- Start a long reader transaction, then start a writer that updates the same row. Does the reader see the update?
- Commit the writer and run a new reader. Does it see the updated value? Does the old reader?
- After many updates, look at the version chain for a single row. How many versions exist? What happens when you run vacuum?

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter33/index.html` (shared helpers in `browser/common/sim.js`). The MVCC side maintains a `versions` array of `{txId, value}` objects; a "Writer writes" button calls `unshift()` to prepend a new version and `pop()` to trim old ones, so the array always shows the most-recent-first version chain. The left panel (locking) blocks all readers when `writerActive` is true; the right panel (MVCC) always serves `numReaders` operations per tick regardless of writer state. `lockTotal` and `mvccTotal` counters accumulate throughput and feed the strip chart.

## When It Breaks

**Long-running transactions bloating the table.** A transaction open for hours holds its snapshot ID. VACUUM cannot reclaim any dead tuples created after that snapshot — they might still be needed by the long transaction. A single hours-long transaction can cause gigabytes of dead tuple accumulation in a busy table. PostgreSQL logs warnings: `WARNING: oldest xmin is far in the past` and `autovacuum: found X dead row versions in table`. Monitoring for long-running transactions (via `pg_stat_activity`) and setting `idle_in_transaction_session_timeout` are standard operational practices.

**Transaction ID wraparound.** PostgreSQL uses 32-bit transaction IDs (XID). With 2³² ≈ 4 billion possible IDs, a database that processes 1 billion transactions per day would exhaust the XID space in 4 days — except XIDs are recycled in a modular fashion. When wraparound is imminent (within 10 million XIDs by default), PostgreSQL forces aggressive vacuuming. If wraparound actually occurs without vacuum, the database enters "transaction ID exhaustion" mode and becomes read-only to prevent data loss. This happened to Sentry in 2015 (publicly documented post-mortem). Monitoring `pg_database.datfrozenxid` and `age(datfrozenxid)` is critical for large PostgreSQL deployments.

**Serializable anomalies under Snapshot Isolation.** MVCC as described gives Snapshot Isolation (SI), not full Serializability. SI allows the "write skew" anomaly: two transactions each read the same data, each make disjoint writes based on what they read, and together violate a constraint that neither write alone would. Example: "at least one on-call doctor must be available." Transaction 1 reads: 2 available. Transaction 2 reads: 2 available. Transaction 1 sets doctor A to off-call. Transaction 2 sets doctor B to off-call. Both commit. Zero doctors on call — a constraint violated that neither transaction detected. PostgreSQL's Serializable Snapshot Isolation (SSI) detects and prevents this with additional tracking overhead.

## Transfer

- **PostgreSQL MVCC in practice.** Every row in PostgreSQL has hidden system columns: `xmin` (inserting transaction), `xmax` (deleting transaction), `ctid` (physical location). `SELECT xmin, xmax, ctid, * FROM my_table` reveals the MVCC version information directly. Running `VACUUM VERBOSE` shows how many dead tuples are reclaimed.
- **MySQL InnoDB undo logs.** InnoDB implements MVCC via undo logs: the current row version is always in the main table; old versions are in a chain of undo log records. Reading an older snapshot requires traversing the undo chain. This is the opposite of PostgreSQL (which stores all versions in the table and garbage-collects). InnoDB's approach means reads of current data are faster; reads of old snapshots require more work.
- **Git as MVCC for files.** Each commit is an immutable snapshot. Branches are concurrent writers creating diverging version chains. Merge is conflict resolution. `git blame` traverses the version chain. Garbage collection (pruning unreachable objects) is git's equivalent of VACUUM.

Try these:

1. Two concurrent transactions both read a row with value 100. Transaction 1 writes 150. Transaction 2 writes 80. Both commit. In PostgreSQL's MVCC, which value survives? What if Transaction 2 tried to `UPDATE ... WHERE value = 100` — would it see the original or updated value?
2. What is "write skew"? Give an example where two transactions each make valid writes but their combined effect violates a constraint. Does MVCC prevent this? Does SSI?
3. On PostgreSQL, query `SELECT age(datfrozenxid) FROM pg_database`. What does this number represent, and what's the risk if it keeps growing?

---

**Continue → [Why Query Planners Matter](34-why-query-planners-matter.md)**
