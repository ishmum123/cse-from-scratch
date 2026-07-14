# When Waiting Waits Forever

## The Problem

A financial system processes two concurrent transfers. Transfer 1 moves money from Account A to Account B: acquire lock on A, acquire lock on B, move money, release both. Transfer 2 moves money from Account B to Account A: acquire lock on B, acquire lock on A, move money, release both.

Thread 1 acquires lock A. Thread 2 acquires lock B. Thread 1 tries to acquire lock B — blocked, Thread 2 holds it. Thread 2 tries to acquire lock A — blocked, Thread 1 holds it. Neither can proceed. Neither will ever proceed. The system freezes silently. No error is thrown. No timeout fires. Both threads simply wait, holding resources the other needs, until someone restarts the server and loses both transfers.

Any solution must:

- Prevent or detect this circular-wait scenario
- Not require threads to know about all locks they'll need in advance
- Not prevent legitimate concurrent locking
- Handle the real-world case where lock acquisition order is determined at runtime (e.g., "lock the smaller account ID first" — but which accounts are involved depends on the request)

## What Would You Try?

Before reading on:

- Draw a directed graph where nodes are threads and edges mean "Thread A is waiting for a resource held by Thread B." What graph property indicates a deadlock?
- If Thread 1 always acquires locks in order A→B and Thread 2 also acquires A→B, can they deadlock? What if Thread 2 acquires B→A?
- What would happen if every lock acquisition had a 5-second timeout? Would that prevent deadlock or just change it?

## Failed Attempts

### Attempt 1: Detect and Kill

Let deadlocks happen, detect them, and kill one of the deadlocked threads to break the cycle. Database systems like MySQL and PostgreSQL do this — they maintain a "waits-for" graph and detect cycles.

The problem for general systems: killing a thread leaves its resources in an unknown state. The thread was in the middle of a transfer — has the debit happened? The credit? Both? Neither? Rolling back the killed thread requires knowing what it did, which requires transaction semantics (chapter 32) — a heavyweight requirement just to handle deadlock. For databases with full ACID transactions, this is tractable. For arbitrary threaded programs with locks around arbitrary code, it's not.

### Attempt 2: Require All Locks Upfront (Two-Phase Locking Variant)

A thread must declare all resources it will need before starting, acquire all of them atomically, do its work, release all. "Atomic acquisition" means: try to acquire all needed locks at once. If any is unavailable, release all acquired ones and retry.

This eliminates circular wait — no thread ever holds a lock while waiting for another. But it has two practical problems. First, "atomic multi-lock acquisition" is not a primitive provided by most systems; implementing it correctly requires its own lock (which creates a new bottleneck). Second, a thread often doesn't know which resources it will need until it's partway through. A database transaction doesn't know which rows it will touch until it evaluates the WHERE clause — which requires reading the data — which requires holding locks. You can't acquire the lock before you know which row to lock.

### Attempt 3: Detect Using Timeouts

Every `lock()` call has a timeout. If waiting more than N seconds, assume deadlock, release held locks, return error. Simple, requires no graph tracking.

Timeouts don't distinguish deadlock from legitimate slow lock-holders. A thread holding a lock while doing a 10-second database query looks identical to a deadlocked thread. Timeout too short: false positives — slow operations abort unnecessarily. Timeout too long: real deadlocks take N seconds to detect, during which all blocked threads hold resources. And release-and-retry under contention can cause livelock: Thread 1 and Thread 2 repeatedly acquire A, time out waiting for B, release A, retry — and keep colliding indefinitely. Both are "alive" in that they keep running, but neither makes progress.

## The Discovery

Kill-and-rollback works only under full transaction semantics. Upfront declaration is impractical when resource needs are data-dependent. Timeouts can't distinguish deadlock from slow progress and create livelock.

The correct prevention requires understanding the four necessary conditions for deadlock (Coffman, 1971):

1. **Mutual exclusion** — resources can't be shared
2. **Hold and wait** — threads hold resources while waiting for others
3. **No preemption** — resources can't be forcibly taken
4. **Circular wait** — a cycle in the waits-for graph

Break any one condition and deadlock is impossible. Mutual exclusion is usually non-negotiable (that's why we have locks). No preemption is often impractical. The two tractable targets: **hold and wait** (lock ordering) or **circular wait** (resource hierarchy).

**Lock ordering**: globally order all locks (by ID, by memory address, by name). All threads acquire locks in ascending order. Thread 1 must acquire A before B. Thread 2 must also acquire A before B. They may contend on A, but whoever acquires A will eventually acquire B; they can never deadlock. This is the standard solution in OS kernels and database engines. The Linux kernel enforces lock ordering with `lockdep`, a runtime checker that builds the actual acquisition order graph and warns when a new acquisition would introduce a cycle.

The formal guarantee: if all lock acquisitions are totally ordered, the waits-for graph is a DAG (directed acyclic graph). A DAG has no cycles. No cycles means no deadlock.

## Try It

<iframe src="../assets/browser/chapter26/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter26/index.html)

Before changing anything, predict:

- With two threads and two locks in opposite acquisition order, how quickly does deadlock occur? Does it happen every run?
- After switching to consistent lock ordering, does contention disappear, or just deadlock? What's the difference?
- If you add a third thread and a third lock in a random order, how many of the possible orderings lead to deadlock?

## Implementation

The full model is ~140 lines of dependency-free JavaScript — open `browser/chapter26/index.html` (and the shared helpers in `browser/common/sim.js`) to read or modify it. Everything runs in the browser; nothing to install. Look for the `transfer(from, to)` function: in the broken version, each thread acquires locks in the order (from, to); toggle the "ordered" flag to see the fix that always acquires the lower-ID lock first. The waits-for graph is drawn live as edges form and the cycle detector highlights the deadlock.

## When It Breaks

**Lock ordering is hard to enforce across codebases.** `lockdep` (Linux kernel) builds the ordering graph at runtime and detects violations. But `lockdep` only runs in debug kernels and can't check userspace code. In a large codebase, ensuring every developer acquires locks in consistent order is a policy problem, not a technical one. The kernel uses `lockdep` + code review + lock class annotations to maintain ordering across millions of lines.

**Distributed deadlock.** Deadlock across multiple machines (e.g., database servers waiting on each other's row locks) is far harder to detect. There's no shared memory to host a waits-for graph. Detection requires each node to periodically communicate its waits-for edges to a central coordinator, which builds the global graph and detects cycles. The latency of this communication means deadlocks persist for seconds before detection — during which all blocked transactions hold locks and block other transactions in a cascading freeze.

**Livelock and starvation aren't deadlock but look similar.** In a livelock, threads keep changing state but make no progress (the timeout-retry scenario). In starvation, one thread never gets a resource because others are always preferred. Both require diagnosis different from deadlock — the waits-for graph approach won't catch them, since the threads are technically making state transitions.

## Transfer

- **Linux `lockdep`.** The kernel deadlock detector annotates every lock acquisition with its "lock class" (which kind of lock, for what subsystem). At runtime, it builds the ordering graph and panics if a new acquisition would create a cycle. It caught thousands of real kernel deadlocks during development.
- **Database deadlock detection.** InnoDB (MySQL), PostgreSQL, and Oracle all maintain waits-for graphs within a transaction manager. When a cycle is detected, one transaction is chosen as the "victim" (typically the one with least work done) and rolled back. The victim gets an error; the application retries.
- **Dining philosophers problem.** The classic formalization: 5 philosophers, 5 forks, each needs two adjacent forks to eat. Naive implementation: each picks up left fork, then right — deadlock. Fix: one philosopher is "left-handed" (picks up right first) — breaks the symmetry, breaks the cycle.

Try these:

1. Implement the bank transfer deadlock in your language of choice. Run it 100 times and measure what percentage of runs actually deadlock (it's not 100% — why?).
2. Implement the fix: always acquire the lock for the lower account ID first. Verify deadlock no longer occurs.
3. What is a "lock-free" data structure? How does it avoid the need for locks, and what does it sacrifice?

---

**Continue → [Why Virtual Memory Exists](27-why-virtual-memory-exists.md)**
