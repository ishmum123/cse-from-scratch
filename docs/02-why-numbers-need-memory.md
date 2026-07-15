# The Number That Vanishes When You Look Away

## The Problem

You've just counted 47 crates arriving at a warehouse. You turn around to receive the next shipment. When you look back: how many crates were there?

You know you counted. The act of counting happened. But the *result* is gone — it existed only in the moment of counting, in the state of your working memory, and working memory doesn't persist.

Now scale this up: a machine that computes the sum of 10,000 numbers, one at a time, must *hold* each running total between additions. Without somewhere to put intermediate results, each new addition starts from scratch. You can count forever but never accumulate.

Any solution must:

- Hold a value across time, not just in the instant of computation
- Allow that value to be *changed* — read the old value, compute, write the new one
- Be addressable — we need to know *which* stored value to use
- Be fast enough that storing/retrieving doesn't dominate the computation

## What Would You Try?

Before reading on:

- If you had to store the number 47 and retrieve it tomorrow using only physical objects, what would you use?
- A calculator can add 3 + 4 = 7. What must happen inside it to show you the answer after you press "="?
- What's the minimum amount of "stuff" you need to store a single bit — a value that's either 0 or 1?

## Failed Attempts

### Attempt 1: Recompute It Every Time

If you need the total again, just recount. Pure computation, no storage. This works for small tasks. It fails catastrophically at scale: if computing a value takes one second, and you need it 1,000 times, you spend 1,000 seconds instead of 1. Databases that don't cache query results, programs that recompute hash values on every comparison — these are real systems that suffer this failure. The insight: computation has cost, and paying that cost multiple times is waste. Storage trades space for time.

### Attempt 2: Keep It in Working Memory (the Stack)

Just hold it "in mind" — in a CPU register, in the call stack, in a local variable. This works for a single running value. It fails when you need to store *many* values, or values that outlast a single computation. A local variable dies when the function returns. A CPU register gets overwritten by the next instruction that needs it. The failure reveals that short-lived implicit storage isn't the same as persistent addressable storage.

### Attempt 3: Encode It in the Program Itself

Hard-code the result: instead of computing `sum = sum + x`, just write `sum = 47`. This works exactly once, for exactly that input. Change any input, and the hard-coded result is wrong. The failure: programs must be general. A program that works only for specific values it already knows is just a lookup table, not a computation.

## The Discovery

Attempt 1 showed computation has cost worth avoiding. Attempt 2 showed short-lived implicit storage isn't enough. Attempt 3 showed the result can't be baked in — it has to be *derived and then held*.

The solution is a **named location** in storage: a place with an address (or name), capable of holding a value that persists until explicitly changed. Read it. Compute something with it. Write the new value back. Repeat.

This is what a **variable** is — not just a convenience for programmers, but a fundamental requirement for any computation that accumulates, remembers, or builds on previous steps. In hardware, the simplest implementation is a **register**: a tiny set of flip-flops that hold one value (one word of bits) and can be read or written in a single clock cycle.

The formal idea: a variable is a binding between a *name* (or address) and a *location in storage*. The location holds a *value*. The value can change; the location persists. This is the origin of assignment — `x = x + 1` reads the location named `x`, adds 1, and writes the result back to the same location. The name doesn't change; the value does.

## Try It

<iframe src="../assets/browser/chapter02/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter02/index.html)

Before changing anything, predict:

- What happens to the running total when you reset it — where does the old value go?
- If two computations try to write to the same location at the same time, what would you expect?
- What's the difference in behavior between storing a value in a register vs writing it to disk?

## Implementation

The working model is dependency-free JavaScript that runs entirely in your browser — nothing to install. Open `browser/chapter02/index.html` to read or modify it (shared UI helpers live in `browser/common/sim.js`). The sim shows three registers `R0`–`R2`; the Store button executes `registers[activeReg] = inputVal`, while the "No Register" panel beside them always shows the current input and labels it "lost on change" — making the contrast between persistent and transient storage impossible to miss.

## When It Breaks

**Uninitialized reads.** Reading a variable before writing it produces garbage — whatever bits happened to be in that location from a previous use. C programs that forget to initialize variables have caused real security vulnerabilities: uninitialized memory can contain leftover secrets from a previous process (passwords, keys). Valgrind exists largely to catch this class of bug.

**Race conditions.** Two threads reading, modifying, and writing the same variable interleave their operations. Thread A reads 5, Thread B reads 5, both add 1, both write 6. The counter should be 7 but it's 6. This is a race condition, and it happens in every language without explicit synchronization. Real incident: the Therac-25 radiation therapy machine had race conditions in its control software that caused fatal overdoses in the 1980s.

**Storage lifetime mismatch.** A variable stored on the stack gets freed when the function returns. If you keep a pointer to it and use it later (a "dangling pointer"), you read memory that now belongs to something else. This class of bug (use-after-free) accounts for a majority of security vulnerabilities in C/C++ systems.

## Transfer

- **CPU registers** are the fastest variables — single-cycle access. Register allocation is one of the hardest compiler optimization problems: mapping program variables onto the limited physical registers without spilling to slower memory.
- **Database transactions** are a mechanism for making multi-step read-modify-write sequences appear atomic — so no other reader sees the intermediate state.
- **Redux / state management in UIs** is just a disciplined approach to mutable state: one store, explicit reads and writes, no implicit mutation.

Try these:

1. Write pseudocode for swapping two variables `a` and `b` without using a third temporary variable. What constraint does this require on the values?
2. A counter increments by 1 every millisecond. How long before a 32-bit counter wraps around? A 64-bit counter?
3. Why does "immutable by default" (like in Rust or functional languages) help avoid race conditions? What does it give up?

---

**Continue → [Why Arrays Exist](03-why-arrays-exist.md)**
