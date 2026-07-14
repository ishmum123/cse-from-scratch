# Doing Two Things at Once Inside One Program

## The Problem

A web server receives 1,000 connections per second. Each connection requires reading a request (fast), querying a database (slow — 50ms), and writing a response (fast). With one sequential execution thread, while the server waits 50ms for the database, it handles zero new connections. At 1,000 connections/second, it falls 50 connections behind every second. Within minutes, the queue is thousands deep and new users get no response.

The obvious fix: spawn a separate process per connection. Processes have their own memory space, so the database query in connection 1 doesn't block connection 2. But spawning a process costs ~1ms and ~10MB of memory. At 1,000 connections/second, that's 10GB of memory per minute just for process overhead. Process isolation — the feature that makes them safe — makes them expensive exactly here, because these 1,000 connections aren't independent programs that need isolation. They all need to share the same database connection pool, the same cache, the same configuration.

Any solution must:

- Allow multiple execution flows within one process
- Share memory between flows without copying (they need the same cache, pool, etc.)
- Be cheap enough to create per-connection or per-request
- Block on I/O in one flow without blocking all other flows

## What Would You Try?

Before reading on:

- If two execution flows share the same memory, what can go wrong if they both try to write to the same variable simultaneously?
- A program reads a file. While it waits for the disk, what else could it usefully do with the CPU?
- If you have 4 CPU cores and 1,000 concurrent connections, what's the minimum number of execution flows you need for full CPU utilization?

## Failed Attempts

### Attempt 1: Async Callbacks (Non-Blocking I/O Without Threads)

Register a callback for each I/O operation. When the OS finishes the I/O, it calls the callback. Only one execution flow (the event loop). No concurrency, no shared-state problems.

This works for I/O-bound work. Node.js is built on it. But the moment any operation is CPU-bound — image resizing, JSON parsing of a large payload, cryptographic key generation — it blocks the single event loop and all other connections stall. Callback-based code also devolves into deeply nested functions ("callback hell") that are hard to reason about. You can't use the simple sequential programming model: `result = query_database(); process(result)`. Every sequential step becomes a callback. Async callbacks solve I/O concurrency but abandon sequential code structure and can't use multiple CPUs.

### Attempt 2: Coroutines / Green Threads (Cooperative Multitasking)

User-space coroutines: `yield` at every I/O point, let the scheduler pick the next coroutine to run. Python's `async/await`, Go's goroutines (partially), and older Lua coroutines use variants of this.

Goroutines actually work well (Go's runtime handles this correctly). But the general cooperative model has the same CPU-blocking problem: one coroutine running a CPU-intensive task never yields, starving all others. Worse, calling any blocking system call (a library that does synchronous disk I/O, a third-party C library) blocks the entire thread running the coroutine scheduler. All coroutines on that thread freeze. This requires every library in the ecosystem to be async-aware — a hard constraint on legacy codebases and C extensions.

### Attempt 3: One Process Per Connection

Fork a new process for each incoming connection. Processes have separate address spaces so they don't interfere. OS can schedule them on multiple CPUs. The web server model used by Apache prefork and early CGI.

Isolation is genuine but expensive. A Python web server process uses 50–100MB of memory including interpreter state, imported modules, and connection pools. At 1,000 concurrent connections: 50–100GB of RAM just for process overhead. Startup cost (~5ms for a Python process fork) adds latency to every connection. The shared cache can't be shared — each process has its own copy of the LRU cache, so the same database row gets cached 1,000 times. The thing you most want to share (the cache, the connection pool) you can't, because process isolation prevents it.

## The Discovery

Async callbacks can't use multiple CPUs and require all code to be async-aware. Cooperative coroutines stall on any blocking call. Separate processes can't share state cheaply.

The right level of isolation is *not* between connections but between *execution contexts within a program*. What you need: multiple independent call stacks that share the same heap. Each call stack can block on I/O (the OS suspends it and schedules another), but they all see the same global cache, same connection pool, same configuration.

That's a **thread**: an independent execution context (its own stack, its own register file, its own program counter) that shares its process's memory. The OS scheduler treats threads as independently schedulable units — when thread 1 blocks on a `read()` system call, thread 2 runs. All threads in a process see the same virtual address space, so `shared_cache[key]` in thread 1 and `shared_cache[key]` in thread 2 are the same memory location.

The tradeoff is inescapable: shared memory is exactly why threads can cooperate efficiently, and shared memory is exactly why they can corrupt each other's data (chapter 25). The thread abstraction provides the execution independence without the memory isolation, which is both its power and its danger.

## Try It

<iframe src="../assets/browser/chapter24/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter24/index.html)

Before changing anything, predict:

- With 4 CPU cores and 100 threads all doing I/O-bound work (mostly sleeping), can the system handle all 100 concurrently? What about 100 CPU-bound threads?
- If two threads both increment a counter with `counter += 1`, how many increments does the counter actually reflect after both threads run?
- Thread creation vs process creation: which is faster, and why? What does a thread inherit from its parent that a process doesn't?

## Implementation

The full model is ~140 lines of dependency-free JavaScript — open `browser/chapter24/index.html` (and the shared helpers in `browser/common/sim.js`) to read or modify it. Everything runs in the browser; nothing to install. Look for the `Thread` class with its own stack frame and how the shared `counter` variable is incremented from multiple simulated threads. The race condition is reproduced by interleaving read–modify–write steps across threads before any locking is applied.

## When It Breaks

**Stack size limits.** Every thread gets a fixed stack allocation (default 1–8MB on Linux). Spawn 10,000 threads: 10–80GB of stack memory reserved (even if not used). The C10K problem (10,000 concurrent connections on a single server) exposed this: OS threads don't scale past a few thousand. Solutions: async I/O (event loop), or user-space thread schedulers (Go's M:N threading model maps many goroutines to few OS threads).

**CPU false sharing.** Two threads on separate CPUs each update a different variable, but those variables happen to be in the same 64-byte cache line. Every write by one CPU invalidates the cache line in the other CPU's cache. The CPUs spend most of their time coordinating cache coherency, not doing work — a benchmark showing 2 threads running slower than 1 is often this. Fix: pad structs so per-thread data falls in separate cache lines.

## Transfer

- **Database connection pools** use a fixed thread pool (say, 100 threads) to handle thousands of concurrent queries. Threads waiting on I/O yield the CPU; threads executing queries use it. The pool limits concurrent connections to the database, which has its own thread and connection limits.
- **JVM's thread model.** Java maps each Java thread to an OS thread (1:1). Project Loom (Java 21) introduces virtual threads — lightweight user-space threads that yield on blocking operations, solving the scale problem while preserving the sequential code style.
- **GPU computation.** A GPU runs thousands of threads simultaneously — but they all execute the *same* instruction on different data (SIMD). This is thread-level parallelism taken to an extreme, made possible by the GPU's highly regular shared memory model.

Try these:

1. Write a program that spawns 2 threads, both incrementing a shared counter 100,000 times. Run it 10 times. Do you always get 200,000? Why not?
2. What is a thread-local variable? How does it differ from a shared variable? Give an example of something that should be thread-local vs shared.
3. A program uses a thread pool of size 4 to handle tasks that each take 10ms. What is the maximum throughput (tasks/second)? What happens to throughput if tasks suddenly start taking 100ms each?

---

**Continue → [Why Locks Exist](25-why-locks-exist.md)**
