# The Hidden Tax of Multitasking

## The Problem

A server runs 100 threads on 4 cores. Every 1ms, the OS timer fires and switches each core to a different thread. This seems to give all 100 threads progress. But a benchmark shows the server doing 30% less useful work than expected. No bugs. No slow operations. Just switching.

The puzzle: if a context switch is just "save registers, load registers," it should take nanoseconds. The measured switch overhead on Linux is 1–10 microseconds, which sounds small — but at 1,000 switches/second per core, that's 1–10ms of overhead per core per second, already 0.1–1% of CPU time. That math doesn't explain 30% overhead. Something else is happening.

Any explanation must account for:

- The measured gap between "switch time" and "recovered throughput"
- Why two processes doing the same work on the same hardware run slower together than one does alone
- Why threads switch faster than processes in practice
- Why switching frequency has a non-linear effect on throughput

## What Would You Try?

Before reading on:

- A CPU has L1 cache (32KB, 1ns access) and RAM (16GB, 70ns access). If Process A runs and fills L1 with its data, what happens when Process B runs?
- The x86 CPU has a TLB (Translation Lookaside Buffer) that caches address translations. What happens to its contents on a process context switch?
- If a program's working set is 2MB but L1 cache is 32KB, how many cache misses does it generate on first access after a switch?

## Failed Attempts

### Attempt 1: Switches Are Just Register Saves

A context switch saves 16–32 registers (instruction pointer, stack pointer, general-purpose registers), sets the new stack pointer, loads the new registers. That's 64–256 bytes of memory operations. At memory bandwidth of 50GB/s, that's under 5 nanoseconds. Context switching should be essentially free.

This analysis is correct for what's measured as "switch time" in microbenchmarks, but completely misses where the actual cost lives. The 5ns save/restore is real. The subsequent 10ms of cache miss penalties is what kills throughput. The registers are cheap to save; the *state* those registers referred to — the working data in L1, L2, L3 cache — cannot be saved. It gets evicted when the new process's data fills the cache.

### Attempt 2: The OS Should Switch Less Frequently

Increase the timer quantum from 1ms to 100ms. Fewer switches means less overhead. Each process runs longer before being preempted.

Reducing switch frequency reduces switch overhead linearly — but increases latency for interactive tasks non-linearly. With 100 threads and a 100ms quantum, a new thread waits up to 10 seconds for its first turn (100 threads × 100ms). An HTTP request that should take 50ms waits 10 seconds before even starting. The quantum length is a tradeoff between throughput (long quantum) and responsiveness (short quantum). But making the quantum longer doesn't eliminate the cache pollution cost — it just makes each cache miss cost less per unit time. It doesn't address the root cause.

### Attempt 3: Use Thread-Local Storage for Hot Data

Move frequently accessed data to thread-local storage (TLS), allocated on each thread's stack. TLS doesn't need locks (no sharing) and is close to the thread's stack pointer, so it stays warm in cache.

TLS helps for truly per-thread data (random number seeds, error codes, current user ID in web server threads). But most work is inherently shared: the database connection pool, the request router, the in-memory cache, the hot data structures being computed on. Making these thread-local would require copying them per-thread, defeating the purpose of threading. TLS doesn't address the cache pollution from switching between threads that all touch the same shared data structures.

## The Discovery

The register save cost is real but tiny. The quantum length is a policy lever, not a root-cause fix. TLS helps thread-local data but doesn't address shared working sets.

The actual cost of a context switch has three components, ordered by magnitude:

1. **Register save/restore**: ~5ns. Negligible.
2. **TLB flush** (for process switches, not thread switches): the TLB caches virtual→physical address translations (chapter 27). A process switch installs a new page table. All previous TLB entries are invalid (wrong process's address space). The TLB is flushed. The new process's first N memory accesses all miss the TLB, each paying 20–100 cycles to walk the page table. For a 16-entry TLB and 100-cycle miss penalty, that's 1,600 cycles of address translation overhead. Modern CPUs use tagged TLBs (ASIDs, address space identifiers) to avoid full flushes — but support for ASIDs is finite.

3. **Cache pollution**: the expensive part. After the switch, the new thread's working data is not in L1 (32KB, ~4ns), L2 (256KB, ~12ns), or even L3 (8MB, ~30ns) cache. Every memory access misses L1 and hits L2 or L3 or RAM. The "warm-up period" — the time until the working set is back in cache — takes thousands to tens of thousands of memory accesses. A process with a 2MB working set and a 32KB L1 cache needs to re-access that 2MB after every switch. At 64 bytes/cache line and 100ns per miss: 2MB / 64 × 100ns = 3.1ms of cache miss time. For a 1ms quantum, that's 3× the quantum just to warm up.

This is why **threads switch faster than processes**: threads in the same process share an address space, so TLB entries stay valid across thread switches (same page table). Cache state is also partially shared — data in L3 that one thread warmed up may still be present when another thread in the same process runs. Thread switches incur cache displacement but avoid the TLB flush cost entirely.

And this is why **coroutines and async I/O** can outperform threads for I/O-bound work: they avoid the OS-managed context switch entirely, staying on the same CPU core, keeping the cache state warm, at the cost of cooperative yielding.

## Try It

<iframe src="../assets/browser/chapter28/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter28/index.html)

Before changing anything, predict:

- As the number of threads increases from 1 to 100 (with 4 cores), what shape does the throughput curve have? Linear? Sublinear? Why?
- If you set the time quantum very short (0.1ms), what fraction of CPU time is overhead? What happens to throughput?
- When you switch between threads in the same process vs. threads in different processes, which shows more throughput degradation? Why?

## Implementation

The full model is ~150 lines of dependency-free JavaScript — open `browser/chapter28/index.html` (and the shared helpers in `browser/common/sim.js`) to read or modify it. Everything runs in the browser; nothing to install. Look for the `CPU` class with a simulated L1 cache (fixed-size LRU map): each tick, the running thread accesses memory addresses from its working set, hitting or missing the cache. On a context switch, the cache is *not* cleared but competing working sets gradually evict each other's entries — the warm-up penalty emerges naturally from the simulation rather than being hard-coded.

## When It Breaks

**NUMA (Non-Uniform Memory Access) amplifies switch costs.** In multi-socket servers, each CPU socket has its own RAM bank. Accessing memory local to the socket takes 30ns; accessing the other socket's RAM takes 90ns. A process running on CPU 0 builds a cache warm in that socket's RAM. The scheduler moves it to CPU 4 (other socket). Now all its memory accesses pay 90ns instead of 30ns, even after the cache is warm. Linux's CFS scheduler has NUMA-aware load balancing to avoid cross-socket migrations, but under high load it still makes costly migrations.

**Voluntary vs. involuntary context switches.** A voluntary switch occurs when a thread blocks (I/O, lock, sleep). An involuntary switch occurs when the timer preempts a running thread. Voluntary switches are generally cheaper — the thread's working set is not in active use (it's waiting), so evicting its cache state is less costly. High involuntary switch rates (visible via `vmstat` as `cs` counter, or `perf stat -e context-switches`) indicate too many threads competing for too few cores. The fix is reducing thread count or increasing batch sizes so threads block less and compute more per time slice.

## Transfer

- **Go's goroutine scheduler.** Go's M:N scheduler maps goroutines onto OS threads. It switches goroutines cooperatively at function calls and channel operations — not via OS timer. Switch cost is ~100ns vs. OS thread switch at 1–10µs. Cache state is preserved because the OS thread doesn't change. This is why Go can handle 100,000 goroutines without the throughput collapse that 100,000 OS threads would cause.
- **CPU affinity pinning.** High-performance databases (Oracle Exadata, Scylla) pin threads to specific CPU cores. A thread that always runs on core 3 always finds its data in core 3's L1/L2 cache. This eliminates cache displacement from migration. At the cost of flexibility — if core 3 is busy and core 5 is idle, the pinned thread still waits.
- **Spectre/Meltdown and context switch overhead.** Post-Spectre mitigations (KPTI — Kernel Page Table Isolation) added up to 30% overhead to context switches on affected Intel CPUs. Syscalls that previously took 100ns took 130–140ns. The mitigation requires flushing TLB entries on every kernel entry/exit to prevent speculative side-channel reads across privilege levels.

Try these:

1. On Linux, run `perf stat -e context-switches,cache-misses ./your_program` on a single-threaded program and on a multi-threaded version. How do context switches and cache misses correlate?
2. What is "CPU cache warm-up time"? Write a micro-benchmark that measures the throughput difference between accessing an array immediately vs. accessing it after another process has run for 1ms.
3. Why does `taskset -c 0 ./program` (pin program to CPU 0) sometimes improve performance? When would it hurt?

---

**Continue → [Why Files Aren't Enough](29-why-files-arent-enough.md)**
