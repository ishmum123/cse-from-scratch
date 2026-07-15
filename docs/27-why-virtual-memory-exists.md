# The Illusion of Infinite Memory

## The Problem

A 1960s computer has 64KB of physical RAM. A program needs 80KB to run. The obvious answer — "tell the programmer to write a smaller program" — doesn't scale. Programs that process data grow with the data. A database must hold its working set in memory to be fast. An image editor must hold the image. You can't shrink the problem to fit the hardware.

Even ignoring size, the addressing problem (chapter 23) showed that multiple programs need memory isolation. A 64KB physical address space with 4 programs running means each gets 16KB — on average. But programs have varying needs. A small utility might need 1KB; a database might need 48KB. Static partitioning wastes the space the utility doesn't use while denying it to the database. And if the database grows past its allocation, it crashes.

Any solution must:

- Let programs use more address space than physical RAM allows
- Give each program the illusion of a large, contiguous private address space
- Move data between RAM and disk transparently, without program involvement
- Handle programs whose memory needs change dynamically

## What Would You Try?

Before reading on:

- If a program needs 80KB but only 64KB of RAM exists, where does the other 16KB live, and how does the CPU access it?
- A program has 1GB of address space but only 64MB of that is actually being used. What should the OS avoid loading into RAM?
- If the CPU tries to access memory at address 0x5000 and that data is currently on disk, what must happen before execution can continue?

## Failed Attempts

### Attempt 1: Programmer-Managed Overlays

Divide the program into sections (overlays). At any time, only one overlay lives in RAM. The programmer explicitly calls `load_overlay(2)` to swap out the current overlay and load the next. IBM mainframe programs in the 1960s worked this way.

This works but demands the programmer track which code is in memory. Every function call might require an explicit overlay load. Large programs became difficult to structure because the programmer had to think about memory the way they think about algorithms. When data crosses an overlay boundary mid-computation, the programmer must save state, load the overlay, and restore state manually. Programming became memory management. The goal of virtual memory is precisely to eliminate this cognitive burden.

### Attempt 2: Swapping Entire Processes

When the OS needs memory, swap an entire process's address space to disk (write all its pages to a swap file), free the physical RAM, give it to another process. When the swapped process needs to run again, swap it back in.

This is cleaner — the programmer sees no complexity. But swapping an entire process is expensive. A 100MB process takes several seconds to swap out or in. During that time, the swapped process can't run. If the system needs to swap frequently (many processes competing for RAM), it spends more time swapping than computing — "thrashing" at the whole-process level. The fundamental issue: you move all 100MB even if only 1MB was actively needed in the next time slice. Granularity is too coarse.

### Attempt 3: Fixed-Size Segments

Divide each program into fixed named segments (code segment, data segment, stack segment). Each segment is a contiguous block. Move segments to disk independently.

Better granularity — a 1KB stack segment can be swapped independently from a 50MB data segment. But segments have variable sizes, which creates the external fragmentation problem (chapter 10 for binary trees illustrates similar structure issues). After swapping segments in and out, physical memory develops holes. A 10KB segment needs a contiguous 10KB hole; the OS might have 20KB free but spread across 5 non-contiguous 4KB holes. Compacting memory (moving all live segments together to eliminate holes) requires updating every pointer in every running program — prohibitively expensive.

## The Discovery

Overlays burden the programmer. Whole-process swapping is too coarse. Segments create fragmentation.

The root insight: granularity matters, and the grain must be small enough to avoid fragmentation, large enough to avoid overhead. Fix the grain to a power-of-two size: **4KB pages**. Divide every program's address space into 4KB pages. Divide physical RAM into 4KB frames. Map pages to frames via a **page table** maintained by the OS.

**Virtual memory**: the CPU generates a virtual address. Hardware (the MMU, memory management unit) splits it into page number and offset. The MMU looks up the page number in the page table — an array, one entry per virtual page — to get the physical frame number. The offset is unchanged. Physical address = frame × 4096 + offset. If the page table entry has a "present" bit set to 0, the page is on disk. The hardware raises a **page fault**. The OS catches the fault, reads the page from disk into a free frame, updates the page table, and restarts the faulting instruction. The program never knew.

**Demand paging**: only load pages that are actually accessed. A 1GB program might only use 64MB of pages in its working set. The OS loads those 64MB on demand as page faults occur and evicts cold pages when RAM fills. The working set — pages recently accessed — stays in RAM; cold pages go to disk. Physical RAM becomes a cache for a much larger virtual address space.

## Try It

<iframe src="../assets/browser/chapter27/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter27/index.html)

Before changing anything, predict:

- If a program accesses its address space linearly (address 0, 1, 2, ...), when do page faults occur? After what pattern do they stop?
- If physical RAM has 16 frames and the program's working set requires 20 pages, what happens? What determines which 4 pages get evicted?
- What is the cost of a page fault in terms of orders of magnitude vs. a RAM access?

## Implementation

The full model is ~160 lines of dependency-free JavaScript — open `browser/chapter27/index.html` (and the shared helpers in `browser/common/sim.js`) to read or modify it. Everything runs in the browser; nothing to install. The sim shows `FRAMES = 16` physical frames: `physAllocate()` demands a contiguous block and fails once fragmentation sets in, while `virtAllocate()` scatters pages to any free frame — the frame grid highlights the difference between a failed physical allocation and a successful virtual one using the same underlying frames.

## When It Breaks

**Thrashing.** When the working set exceeds physical RAM, the OS evicts a page, the program immediately needs it again, loads it back, evicts another page that's immediately needed — spending nearly all time on page I/O. CPU utilization drops toward zero even as the disk runs at 100%. Early 1970s systems hit this routinely. The fix is working set management: track pages actively used in the last N time units; if their count exceeds available frames, don't just evict — throttle the process or add RAM. Linux's OOM killer is the last resort: kill a process to free memory rather than thrash indefinitely.

**TLB misses.** The page table lookup itself is expensive — it's a memory access to a large table. The TLB (Translation Lookaside Buffer) caches recent virtual-to-physical mappings in hardware. A TLB hit: address translation in 1 cycle. A TLB miss: walk the page table in memory, 20–100 cycles. A context switch (chapter 28) invalidates TLB entries for the old process, causing TLB misses on the first few accesses after each switch. Programs with poor spatial locality (random access to large sparse arrays) continually miss the TLB, paying 20–100× more per memory access. This is why NUMA-aware memory allocators and huge pages (2MB instead of 4KB) exist: fewer, larger pages mean fewer TLB entries needed for the same working set.

**Swap exhaustion.** If both RAM and swap are full, the OS has nowhere to put pages. On Linux, this triggers the OOM (Out Of Memory) killer, which selects a process to terminate based on memory usage, process priority, and other heuristics. In Docker containers with `--memory` limits and no swap, the container is simply killed. Production incidents where containers silently OOM-killed background workers without any error log are a common operational failure mode.

## Transfer

- **`mmap()` system call.** Programs can map files directly into their virtual address space. The OS backs the virtual pages with the file's data on disk. Accessing page 0 reads the first 4KB of the file; page 1 reads the next 4KB. Page faults load file data on demand. Large databases and key-value stores (LMDB, RocksDB in some configurations) use mmap to let the OS manage which parts of a large file are in RAM — the OS page cache becomes the database's buffer pool.
- **Copy-on-write (COW) fork.** When a process forks (chapter 23), the child gets the same page table as the parent, with all pages marked read-only. If either process writes to a page, the MMU raises a fault; the OS copies just that one 4KB page, gives the writer its own copy, marks both read-write. This turns a "copy 100MB address space" into "copy only the pages that diverge."
- **Address Space Layout Randomization (ASLR).** The OS randomizes the virtual addresses where a program's stack, heap, and libraries are loaded. This makes buffer overflow exploits harder: an attacker who jumps to a hardcoded address hits randomized space. ASLR is implemented in the virtual-to-physical mapping layer — physical layout is unchanged, but virtual layout varies per execution.

Try these:

1. On Linux, read `/proc/self/maps`. List 5 regions you see and explain what each is (text segment, stack, heap, vDSO, etc.).
2. LRU page replacement is optimal in theory but expensive in practice. What data structure would you use to implement exact LRU? Why do OS kernels use an approximation (clock algorithm) instead?
3. A program allocates 1GB with `malloc()` but only writes to 1MB of it. On Linux, how much physical RAM does this use? What system call lets you verify this?

---

**Continue → [Why Context Switching Costs](28-why-context-switching-costs.md)**
