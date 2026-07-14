# Why Sending a Book Is Slower Than Sending Its Address

## The Problem

A video editing program loads a 4K frame into memory: 8.3 million pixels, 4 bytes each — about 33MB. It needs to pass this frame to a color grading function, then to a sharpening function, then to an encoding function.

If each function receives its own private copy of the frame, the program copies 33MB three times — nearly 100MB of data movement just to process one frame. At memory bandwidth of ~40GB/s, that's 2.5ms of pure copying overhead per frame. At 24 frames per second, 1.4 seconds of every minute is just copying data that never changed.

The visceral cost: for large data, copying is the bottleneck. The actual computation — the color grading, the sharpening — might take 0.1ms. The copying takes 25× longer.

Any solution must:

- Allow functions to access data without copying it
- Make clear who is allowed to modify what (to avoid surprising mutations)
- Be as cheap as possible to pass — ideally O(1) regardless of data size
- Not break when the original data moves or is freed

## What Would You Try?

Before reading on:

- If you gave a function the *address* of your data instead of a copy, what could go wrong?
- If two functions both receive the same address and both modify the data, whose modification wins?
- How would a library book lending system (one book, many readers, sign-in to check out) solve this?

## Failed Attempts

### Attempt 1: Always Copy

Every function gets its own private copy of its inputs. No sharing, no surprises. Functions can modify freely, can't affect each other.

This is safe but wasteful. For small data (an integer, a 16-byte struct) copying is essentially free. For large data (images, videos, database tables, ML model weights) copying dominates runtime. Python's early string handling copied strings on every operation — programs building strings in loops were O(n²) because each concatenation copied the existing string. The fix (StringBuilder / `str.join`) is exactly Attempt 3 below.

### Attempt 2: Global Variable

Put the data in one global location that every function reads and writes. No copying — everyone uses the same storage.

This creates a different problem: any function can modify the data at any time. Function A reads the frame, starts processing, function B modifies it mid-processing — now A's output is based on inconsistent state. In concurrent programs this is a race condition. Even in single-threaded programs, global mutable state makes execution order matter in non-obvious ways. Debugging becomes tracing who modified the global and when. Real codebases that relied on global state (early C programs, some FORTRAN scientific code) become unmaintainable as they grow.

### Attempt 3: Pass an Address (Reference / Pointer), With Rules

Pass the *address* of the data — a single integer (8 bytes on 64-bit systems) — instead of copying the data itself. The function can read through the address. Whether it can *write* is a separate policy decision, enforced by convention or by the language.

This solves the copying problem: passing a reference to a 33MB image takes 8 bytes and one instruction, regardless of image size. The cost is that the caller and callee now share the same memory — mutations in the callee are visible in the caller.

## The Discovery

Attempt 1 (copy always) is safe but O(n) cost for O(1) logical operation. Attempt 2 (shared mutable global) removes cost but breaks correctness. Attempt 3 splits the concerns: the *mechanism* (reference) is separate from the *policy* (who can write).

Passing a reference is O(1) for all data sizes. The question is what you do with it:

- **Read-only reference** (const pointer, immutable borrow): the callee can read but not write. Safe sharing. Many readers, zero writers.
- **Exclusive mutable reference**: only one writer at a time, no simultaneous readers. Safe mutation.
- **Copy-on-write**: share the reference until someone tries to write, then copy just before the write. Combines cheap sharing with safety.

Formally: **copying has cost Θ(n)** where n is the data size. Passing a reference has cost Θ(1). For large n, the difference is the difference between feasible and infeasible. The design space for any data-passing interface is: who owns the data, who can read it, who can write it, and when is it freed.

## Try It

<iframe src="../assets/browser/chapter05/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter05/index.html)

Before changing anything, predict:

- What happens to the total data transferred when you increase the number of function calls but switch from copy to reference passing?
- If a function receives a reference and modifies the data, who else can see that modification?
- What has to happen when the original data is freed but a reference to it still exists somewhere?

## Implementation

The working model is dependency-free JavaScript that runs entirely in your browser — nothing to install. Open `browser/chapter05/index.html` to read or modify it (shared UI helpers live in `browser/common/sim.js`). Look for the side-by-side cost counters that track bytes transferred for copy-mode vs reference-mode as data size grows — that's where the crossover point becomes visible.

## When It Breaks

**Dangling references (use-after-free).** You pass a reference to data. The owner frees the data. The reference is now pointing at memory that may hold something else entirely. Reading it returns garbage; writing corrupts another object. This is the most exploited class of bug in modern software. Chrome's "Site Isolation" project exists largely to contain the damage from use-after-free in the renderer.

**Unintended aliasing mutations.** You pass a reference intending the callee to read only. The callee modifies it. The caller's data has changed without the caller's knowledge. Python's mutable defaults in function signatures (`def f(x=[])`) are a famous instance of this: the list is shared across all calls.

**Reference counting cycles.** When objects hold references to each other (A points to B, B points to A), neither can be freed because each always has a reference count of at least 1. Python uses cycle detection garbage collection on top of reference counting to handle this. Languages without GC (C++) require manual breaking of cycles with weak pointers.

## Transfer

- **String interning.** Python and Java intern short strings — multiple variables with value `"hello"` may share the same memory. Passing the interned string is O(1); "copying" it is effectively a reference copy.
- **Zero-copy networking.** `sendfile()` in Linux sends a file directly from disk to network without copying into user-space. nginx uses this for static file serving — a major reason it's faster than early Apache configurations.
- **Rust's borrow checker.** Rust's core innovation is enforcing reference safety at compile time: exactly one mutable reference OR any number of immutable references, never both simultaneously. Eliminates dangling references and aliasing mutations without a garbage collector.

Try these:

1. Python function arguments are "pass by object reference." What does this mean for mutable vs immutable types? Demonstrate with a list and an integer.
2. Design a "copy-on-write" string. What state do you need to track? When exactly does the copy happen?
3. In C, `memcpy(dest, src, n)` copies n bytes. What's its complexity? What assumptions does it make about src and dest?

---

**Continue → [Why Locality Matters](06-why-locality-matters.md)**
