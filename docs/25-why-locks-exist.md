# The Price of Sharing

## The Problem

A bank's server runs two threads. Thread A processes a transfer: read balance (€1,000), subtract €200, write balance (€800). Thread B processes a concurrent transfer on the same account: read balance (€1,000), subtract €500, write balance (€500).

If Thread A reads first, then Thread B reads before Thread A writes, both see €1,000. Thread A writes €800. Thread B writes €500. The final balance is €500 — the €200 deduction from Thread A was silently lost. The account should have €300. You just created €200 out of nothing (or destroyed it, depending on who got the last write).

This isn't a hypothetical — it's the race condition that manifests in real banking systems, flight booking, and e-commerce checkout. In 2012, a race condition in Knight Capital's trading software caused trades to execute at wrong prices for 45 minutes, losing $440 million.

Any solution must:

- Prevent two threads from executing conflicting operations simultaneously
- Work without requiring threads to know about each other in advance
- Not deadlock (the solution to sharing can't permanently block all sharers)
- Be fast enough to not eliminate the benefits of threading

## What Would You Try?

Before reading on:

- The operation `balance -= 200` looks atomic in Python but isn't. What are the underlying CPU instructions, and where can a thread switch interrupt them?
- What's the minimum amount of code that needs to be "protected" — must every memory access be protected, or just some?
- If you protect a critical section with a flag variable (`locked = True`), what happens if two threads both check the flag at the same moment?

## Failed Attempts

### Attempt 1: Software Flag (Peterson's Algorithm Variant)

Use a boolean `locked` variable. Before entering the critical section, check `if not locked: locked = True; proceed`. After, set `locked = False`.

The check-then-set is two operations: read `locked`, then write `locked`. Between those two operations, another thread can read `locked` (gets `False`), both threads set `locked = True` and both proceed. The fix is Peterson's Algorithm: use two flags and a turn variable so each thread "defers" to the other if they arrive simultaneously. This works on paper but fails on modern hardware: CPUs reorder memory operations for performance. Without explicit memory barriers, the CPU may execute the writes and reads out of program order, breaking Peterson's correctness proof. Software mutual exclusion requires either disabling all CPU optimizations or inserting expensive memory fence instructions — effectively serializing memory operations, which destroys performance.

### Attempt 2: Disable Interrupts

On a single-CPU machine, mutual exclusion is simple: disable interrupts. No interrupt means no context switch means the current thread runs uninterrupted until it re-enables interrupts. This is exactly how early OS kernels worked.

Multi-core CPUs made this obsolete. Disabling interrupts on CPU 0 doesn't stop CPU 1 from running another thread simultaneously. With 16 cores, 15 other threads continue running. Even on a single core, disabling interrupts is only available to the OS kernel (user-space can't do it for security reasons), and a buggy kernel section that forgets to re-enable interrupts freezes the entire machine.

### Attempt 3: Atomic Test-and-Set in Hardware

Modern CPUs provide an atomic instruction: `test_and_set(addr)` reads the value at `addr` and writes 1, all as a single uninterruptible operation. Use this as a spinlock: loop calling `test_and_set(&lock)` until it returns 0 (meaning you just acquired it). When done, write 0 to release.

This actually works — it's the foundation of all software locks. But the busy-wait loop is the problem. A thread waiting to acquire a lock burns 100% of a CPU core checking the flag. If the lock-holder needs to wait for I/O, the spinner wastes CPU for the entire I/O wait. On a 4-core machine with 5 threads all trying to acquire one lock, 4 threads spin, burning 4 cores while 1 thread holds the lock but can't run because spinners are occupying the CPUs. Spinlocks are only correct when the wait is guaranteed to be extremely short (microseconds) and there are few contenders.

## The Discovery

Software flags race at the hardware level. Interrupt disabling doesn't work on multi-core systems. Spinlocks waste CPU.

The real solution uses the hardware's atomic test-and-set as the foundation but adds OS-managed blocking: when a thread can't acquire the lock, it doesn't spin — it tells the OS "I'm waiting for this lock" and the OS marks it as blocked, removing it from the scheduler's run queue. When the lock is released, the OS wakes one waiting thread.

This is a **mutex** (mutual exclusion lock). The critical section — the code block that can only be executed by one thread at a time — is bracketed by `lock()` and `unlock()`. The OS guarantees that at most one thread holds the lock at any moment; all others block without burning CPU.

The formal model: a mutex has two states, held and free, and a queue of waiting threads. `lock()`: if free, take it; if held, join the wait queue and sleep. `unlock()`: if the wait queue is nonempty, wake the next thread and transfer ownership; else mark free. The invariant: between `lock()` and `unlock()`, the thread has exclusive access to the protected resource.

## Try It

<iframe src="../assets/browser/chapter25/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter25/index.html)

Before changing anything, predict:

- With 10 threads all incrementing a shared counter 1,000 times with no lock, what range of final values do you expect? With a lock?
- If Thread A holds a lock for 100ms while doing I/O, and Thread B is waiting, what is Thread B doing during those 100ms? What is the CPU doing?
- What happens if you make the critical section larger (protect more operations)? Smaller? Where's the tradeoff?

## Implementation

The full model is ~130 lines of dependency-free JavaScript — open `browser/chapter25/index.html` (and the shared helpers in `browser/common/sim.js`) to read or modify it. Everything runs in the browser; nothing to install. Look for the `BankAccount` class: one version with no protection (race condition visible in the counter drift) and one with a `Mutex` that queues waiters and wakes them on release. The spinlock variant is included to show CPU-cycle waste under contention.

## When It Breaks

**Deadlock.** Thread A holds Lock 1, waits for Lock 2. Thread B holds Lock 2, waits for Lock 1. Both wait forever. Deadlocks are covered in chapter 26, but the root cause is here: locks held while waiting for other locks create circular dependencies. Any solution — lock ordering, timeout, try-lock — involves constraining how code acquires multiple locks simultaneously.

**Priority inversion.** A low-priority thread holds a mutex. A high-priority thread blocks on it. A medium-priority thread, having no reason to block, runs and preempts the low-priority thread. The high-priority thread is now blocked indefinitely — it can't run until the low-priority thread finishes, but the low-priority thread can't run because the medium-priority thread keeps preempting it. Mars Pathfinder (1997) hit exactly this. Fix: priority inheritance — when a low-priority thread holds a mutex that a high-priority thread is waiting for, temporarily elevate the low-priority thread to the high-priority thread's priority.

**Lock granularity vs. throughput.** One global lock protects all shared data but serializes all threads — no benefit from multi-core. Fine-grained locks (one per data item) allow parallelism but increase complexity and deadlock risk. Early Linux used the Big Kernel Lock (BKL), a single lock for all kernel data. It was simple and correct but made Linux scale poorly on multi-core systems. Removing it took a decade of incremental refactoring.

## Transfer

- **Database row locks.** When you `UPDATE users SET balance = balance - 200 WHERE id = 42`, the database acquires a row-level lock on user 42. Concurrent transactions touching other users proceed in parallel; only a concurrent update to user 42 blocks. This is fine-grained locking applied to database rows.
- **Reader-writer locks.** Many readers can hold a lock simultaneously (read-only access doesn't conflict). Writers require exclusive access. A `RWMutex` gives concurrent reads at full speed while protecting writes. Used heavily in caches and configuration stores where reads vastly outnumber writes.
- **Go's `sync.Mutex` and the race detector.** Go's `-race` compiler flag instruments every memory access and reports when two goroutines access the same variable without a mutex. It's built into the standard toolchain — run `go test -race ./...` to catch races automatically.

Try these:

1. Write a thread-safe counter using a mutex. Then write one using Go's `sync/atomic` (or Python's `threading.Lock`). Measure the performance difference under high contention.
2. What is a "try-lock" operation? When would you prefer `try_lock()` over `lock()`? What new problem does it create?
3. A hash map protected by a single lock becomes a bottleneck under concurrent access. Describe a design using N locks (one per bucket) that allows N concurrent operations. What's the new risk?

---

**Continue → [Why Deadlocks Happen](26-why-deadlocks-happen.md)**
