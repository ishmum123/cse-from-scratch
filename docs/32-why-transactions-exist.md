# All or Nothing

## The Problem

A bank transfer: subtract $200 from Account A, add $200 to Account B. Two writes to the database. The server crashes between the two writes: A has been debited but B hasn't been credited. $200 vanished. The database is now inconsistent — it reflects a state that should never exist.

This is not a hypothetical. The 2003 Northeast blackout caused thousands of partially committed database operations. Systems recovered to find balances wrong, inventory counts incorrect, and reservation records in impossible states — not because of bugs in application logic, but because the operating system killed processes mid-write when power cut out.

Any solution must:

- Make multi-step operations appear atomic — all succeed or none apply
- Survive crashes at any point in the sequence
- Allow concurrent users to run without seeing each other's half-finished operations
- Not serialize all operations (that would destroy performance)

## What Would You Try?

Before reading on:

- If you write to two database rows sequentially and crash between them, the database has an inconsistent state. What would you need to store *before* making the first write to be able to recover?
- Two users simultaneously try to book the last seat on a flight. How do you prevent both from succeeding?
- What's the difference between "the operation didn't complete" (network timeout) and "the operation completed but you didn't hear back"?

## Failed Attempts

### Attempt 1: Checksums and Timestamps

After every write, update a checksum and timestamp for the record. On recovery, scan all records and flag any whose checksum doesn't match. Detect corruption, alert administrator.

This detects corruption after the fact but doesn't prevent it or automatically fix it. You know $200 vanished but don't know whether to restore A's balance or apply B's credit. The audit trail is missing. More fundamentally, checksums don't handle the concurrent-access problem: two users booking the same seat concurrently can both read "1 seat available," both write "seat reserved," and both receive confirmations — no checksum violation, just a double-booking. Detection doesn't provide atomicity.

### Attempt 2: Application-Level Compensating Transactions

Write the debit. If anything fails before the credit, run a "compensating transaction" to reverse the debit. Many distributed systems (saga pattern) use this approach.

This works but requires the application to implement the reversal logic for every operation. The reversal itself can fail. If the debit failed and the compensating credit also fails, you're in a loop. The root problem: the application is now responsible for correctness properties that should be database responsibilities. "If step 3 fails, undo step 2, which means doing anti-step-2, which might conflict with a concurrent transaction that saw step 2 as committed..." — the complexity compounds. Sagas are appropriate in distributed systems where ACID transactions are unavailable; they're the wrong choice when a single database can provide atomicity directly.

### Attempt 3: Shadow Paging

Make all changes to a separate "shadow" copy of the database. When done, atomically swap the shadow with the primary by updating a single root pointer. Crash before the swap: shadow is discarded, original is unchanged. Crash after: the new root is in place, all changes are visible.

The single-pointer swap is genuinely atomic on disk (one-sector writes are atomic on most hardware). But maintaining two full copies of the database for every transaction is prohibitively expensive in storage and I/O. More importantly, concurrent transactions need separate shadow copies, requiring one full-database copy per concurrent transaction. Early PostgreSQL (pre-8.0) used shadow paging; it was replaced with WAL (write-ahead logging) because WAL uses far less space and handles concurrent transactions efficiently.

## The Discovery

Checksums detect but don't prevent. Compensating transactions push database responsibilities into application code. Shadow paging uses too much space for concurrent workloads.

The insight from all three failures: you need to record *intent* before acting, so you can always answer "did this complete or not?" — and undo if not.

**Write-Ahead Log (WAL)**: before modifying any database page, write a log record describing the intended change to a sequential log file. The log record includes the transaction ID, the before-image (original value), and the after-image (new value). Only after the log record is durably on disk does the actual page modification happen. The log is append-only — writes are sequential, which is fast.

On crash recovery: read the log from the last checkpoint. Redo all committed transactions whose page changes didn't make it to disk. Undo all incomplete transactions (those without a commit record in the log) using the before-images.

**Transaction**: a group of operations bracketed by `BEGIN` and `COMMIT` (or `ROLLBACK`). The database guarantees four properties — **ACID**:
- **Atomic**: either all operations commit or none are visible.
- **Consistent**: transactions move the database from one valid state to another (constraints are checked).
- **Isolated**: concurrent transactions don't see each other's uncommitted data.
- **Durable**: committed data survives crashes.

WAL provides Atomicity and Durability. Consistency is enforced by constraint checking at commit time. Isolation is provided by concurrency control (chapter 33).

## Try It

<iframe src="../assets/browser/chapter32/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter32/index.html)

Before changing anything, predict:

- Simulate a crash mid-transaction (after the debit, before the credit). After recovery, what is the account balance? Is the state consistent?
- Commit a transfer, then simulate a crash before the WAL is flushed to disk. What happens on recovery?
- What happens to a `ROLLBACK` mid-transfer? Does the simulation use before-images or re-executing a reverse operation?

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter32/index.html` (shared helpers in `browser/common/sim.js`). Both panels animate a bank transfer between accounts (`noTxA`/`noTxB` on the left, `txA`/`txB` on the right), starting at `initA=100` and `initB=50`. The step buttons advance `noTxStep` and `txState` through debit, credit, commit, and rollback using `setTimeout` transitions. The "Crash" button leaves the left panel in a broken half-applied state, while the right panel rolls back to `initA` — the invariant `total === (initA + initB)` is displayed in both panels to make the difference visible.

## When It Breaks

**Durability vs. performance: `fsync` and the durable write problem.** The WAL only provides durability if the log is physically on disk before the transaction commits. The OS buffers disk writes; `write()` to a file may return before data hits the drive. Databases call `fsync()` to force the buffer to disk. `fsync` can take 1–10ms per call — which is why PostgreSQL's default write throughput is limited by `fsync` latency. Disabling `fsync` (not recommended for production) makes databases 10–100× faster but risks data loss on crash. AWS EBS and GCP Persistent Disk implement `fsync` synchronously in storage hardware, which is why cloud databases can get durable writes faster than on-premises HDDs.

**Long-running transactions and WAL bloat.** A transaction that runs for hours holds open a "snapshot" of the database state. The WAL cannot be truncated past the oldest active transaction's start point — old log records must be retained for recovery and for read snapshots. PostgreSQL's WAL can grow to tens of gigabytes with one long-running transaction. `pg_replication_slot`s that fall behind have the same effect. Monitoring active transactions and replication lag is routine operational hygiene.

**Distributed transactions and the two-phase commit problem.** A transaction spanning two databases (e.g., update the orders table and the inventory table, which live on different servers) requires distributed coordination. Two-phase commit (2PC): Phase 1, coordinator asks all participants "are you ready to commit?" Phase 2, if all say yes, coordinator tells all to commit. If the coordinator crashes between phase 1 and phase 2, participants are left in a "prepared" state — they've voted yes but don't know if the transaction committed. They hold locks indefinitely, blocking all other transactions on those rows. This is the "in-doubt transaction" problem. Distributed databases (Spanner, CockroachDB) use Paxos-based commit to avoid the 2PC single-coordinator failure mode.

## Transfer

- **SQLite's WAL mode.** SQLite can run in WAL mode: writes go to a WAL file; readers read from the main database file plus any relevant WAL entries. Readers never block writers; writers never block readers. Checkpointing periodically merges the WAL back into the main file. Used in iOS, Android, and countless embedded systems.
- **Event sourcing.** Application-level pattern that mirrors WAL: instead of storing current state, store an append-only log of events. The current state is always derived by replaying the log from the beginning (or a snapshot). Like WAL, this makes the intent of every change auditable and reversible.
- **Undo logs in MySQL/InnoDB.** InnoDB maintains a separate "undo log" for each transaction. If the transaction rolls back, the undo log provides the before-images to restore. The undo log also enables MVCC (chapter 33): old versions of rows remain readable via the undo log chain even after newer versions are written.

Try these:

1. Implement a minimal WAL in 50 lines: write log records to an array before updating a `state` object. Implement `crash()` (clears state, keeps log) and `recover()` (replays log to rebuild state). Test with a 3-step transaction and crash at each step.
2. What is a "checkpoint" in WAL? Why does the database need it, and what happens if it never runs?
3. `BEGIN; UPDATE orders SET status = 'shipped' WHERE id = 42; COMMIT;` — how many `fsync` calls does PostgreSQL make for this transaction in the default configuration?

---

**Continue → [Why MVCC Exists](33-why-mvcc-exists.md)**
