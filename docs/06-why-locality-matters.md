# The Desk That Makes You Fast

## The Problem

A CPU can execute a billion operations per second. Main memory (RAM) can deliver data in about 60–100 nanoseconds. That gap sounds small, but at 1GHz, 100ns is *100 CPU cycles* — 100 instructions the CPU could have executed but instead had to wait.

Now imagine: your program sums a million numbers. Each number is 4 bytes. The array is 4MB. If every number access goes to RAM, you pay 100 cycles × 1,000,000 accesses = 100 million wasted cycles. The actual addition takes 1 cycle per number. Memory latency is 100× the compute cost.

The visceral cost: modern CPUs sit idle most of the time, not because there's nothing to compute, but because the data isn't there yet. A program that could run in 1 second takes 100 seconds because it goes to RAM for every byte.

Any solution must:

- Make frequently accessed data faster to reach
- Require no programmer intervention for common cases
- Not require knowing in advance which data will be needed
- Be transparent — programs should work correctly regardless

## What Would You Try?

Before reading on:

- A desk clerk works in an office building. Their files are in a filing room two floors down. What would a fast clerk keep on their desk vs leave in the filing room?
- Why would keeping *everything* on the desk be a problem?
- When the clerk fetches a file, should they bring just that file or bring nearby files too?

## Failed Attempts

### Attempt 1: Make RAM Faster

Just build RAM that operates at CPU speed. Problem: fast memory (SRAM) costs roughly 100× more per bit than slow memory (DRAM) and uses 6 transistors per bit instead of 1. A CPU-speed 16GB RAM would cost thousands of dollars and require enormous power. The physics of fast memory conflicts with the economics of large memory. We cannot make all memory fast — we can only make some memory fast.

### Attempt 2: Programmer-Managed Fast Storage

Let programmers explicitly move data to/from fast storage. "Load these 64 bytes into fast registers for the next loop." This is what early GPUs required (explicit texture loads), what CELL processor's SPUs required, what some DSPs still require. It works, but it makes programs fragile and hardware-specific. You can't write a general matrix library without knowing the exact cache hierarchy of the target CPU. The IBM CELL had theoretically superior performance but was notoriously difficult to program for exactly this reason.

### Attempt 3: Predict Future Accesses

If you know what data will be needed before it's needed, you can fetch it early ("prefetch"). This works in predictable loops: access `array[0]`, `array[1]`, `array[2]`... the pattern is obvious, the hardware can prefetch. But random access patterns defeat prediction. A hash table lookup has no predictable pattern — the address depends on the key being hashed. Software prefetching helps in known-stride loops but can't solve the general problem.

## The Discovery

Attempt 1 shows we can't make all memory fast. Attempts 2 and 3 show we can't always predict or manually manage. What *can* we observe?

Programs access data non-uniformly. They exhibit two kinds of regularity:

- **Temporal locality**: if you access a location now, you'll probably access it again soon (a loop variable, a frequently called function)
- **Spatial locality**: if you access address X, you'll probably access X+1, X+2, ... soon after (scanning an array, reading instructions sequentially)

The solution: keep a small, fast, automatically managed copy of recently and nearby-accessed memory between the CPU and RAM. When the CPU requests address X:
1. Check the fast copy. If X is there (**cache hit**), return it in ~1ns.
2. If not (**cache miss**), go to RAM, fetch X *and the surrounding ~64 bytes* (a **cache line**), store them in the fast copy, return X.

The fast copy is the **cache**. It exploits temporal locality by keeping recent accesses fast. It exploits spatial locality by loading a whole cache line — when you access `array[0]`, `array[1]` through `array[15]` (for 4-byte integers in a 64-byte cache line) come along for free.

Modern CPUs have 3 cache levels: L1 (~32KB, ~4 cycles), L2 (~256KB, ~12 cycles), L3 (~8MB, ~40 cycles), then RAM at ~100 cycles. Cache is why the clerk keeps a desk — not because the desk holds *everything* but because it holds *what was needed recently*, and recent need predicts future need.

## Try It

<iframe src="../assets/browser/chapter06/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter06/index.html)

Before changing anything, predict:

- Sequential array scan vs random-access of the same array: which is faster and by how much?
- If you access the same 10 elements repeatedly in a loop, what happens to cache hit rate over time?
- What happens to performance when your working set exceeds the L3 cache size?

## Implementation

The working model is dependency-free JavaScript that runs entirely in your browser — nothing to install. Open `browser/chapter06/index.html` to read or modify it (shared UI helpers live in `browser/common/sim.js`). Look for the cache-lookup function that checks L1 → L2 → L3 → RAM in order and tallies hits at each level — that chain is where temporal and spatial locality either pay off or don't.

## When It Breaks

**Cache thrashing.** If your working set is slightly larger than a cache level, every access evicts something that will be needed again soon. Hit rate collapses. This happens with matrix multiplications on large matrices — the naive triple-loop visits memory in cache-hostile order. The fix (loop tiling / blocking) restructures the computation to maximize reuse within cache, and it's why BLAS libraries are faster than naive code even when the algorithm is identical.

**False sharing.** Two CPU cores access *different* variables that happen to share a cache line. When Core A writes its variable, it invalidates the cache line on Core B, forcing B to reload — even though B's variable didn't change. Highly concurrent code that carefully avoids sharing data can still suffer this. The Linux kernel's lock contention work, Java's `@Contended` annotation, and Disruptor's ring buffer design all exist partly to defeat false sharing.

**Cache-side-channel attacks.** The time difference between a cache hit and miss is measurable by the program itself. Spectre and Meltdown (2018) used this: run code speculatively, observe which cache lines were loaded, infer what data was accessed — including data the program shouldn't have been able to see (other processes' memory, kernel memory). The entire CPU industry had to redesign pipeline speculation because of cache observability.

## Transfer

- **Database buffer pools.** PostgreSQL and MySQL maintain a buffer pool — a region of RAM that caches disk pages. Disk access is ~10ms; RAM is ~100ns; SSD ~100μs. The buffer pool is just a software cache for the disk, exploiting the same locality principle.
- **CDN edge caches.** Content delivery networks cache popular web content at edge servers near users. "Temporal locality" at internet scale: if user A requests `/image.jpg`, users B and C in the same city will probably request it soon too.
- **Branch prediction.** CPUs cache not just data but *decisions* — they predict which branch (if/else) will be taken and pre-fetch those instructions. Sorting data before processing can make branches more predictable, which is why some database operations sort input first even when order doesn't matter for correctness.

Try these:

1. You have a 1000×1000 matrix stored row-by-row. Summing all elements by iterating row-by-row vs column-by-column: which is faster and why?
2. Design a cache with capacity for 4 items using LRU (Least Recently Used) eviction. What data structure would you use? What's the cost per operation?
3. Why do hash tables (chapter 12) have poor cache behavior? What does this mean for choosing between a hash table and a sorted array for a small collection?

---

**Continue → [Why Looking Is Slow](07-why-looking-is-slow.md)**
