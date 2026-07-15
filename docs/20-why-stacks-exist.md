# The Structure That Remembers in Reverse

## The Problem

A function calls another function, which calls another, which calls another. Each call suspends the caller — "pause here, run this, come back, continue." When the deepest call returns, the system must know exactly where to continue in each suspended caller, and in what order.

Concretely: function A at line 42 calls B. B at line 7 calls C. C runs and returns. The system must return to B at line 8. Then B returns, and the system must return to A at line 43. Not to some other function — to A's suspended computation, with A's local variables exactly as A left them.

Without a systematic place to store "where to return and what state to restore," the machine would need to guess. This isn't a programming convenience — it's a fundamental requirement for any system where functions call functions.

The same problem appears elsewhere: undo operations (the last action must be undone first), browser history (back goes to the most recently visited page), expression evaluation (inner parentheses resolve before outer ones), recursive algorithms (the innermost recursive call returns first).

All of these share one structure: **last in, first out** — the thing most recently added is the thing removed first.

Any solution must:

- Store items in a sequence
- Always add to one end and remove from the same end
- Support O(1) add and O(1) remove — this happens on every function call and return
- Be last-in-first-out by construction, not by convention

## What Would You Try?

Before reading on:

- You're washing dishes and stacking them as they're cleaned. When you need a plate, which do you take from the stack?
- If function A calls B calls C, and C returns first, then B returns, then A returns — describe the order that "save A's state, save B's state, save C's state" then "restore" happens.
- Could you use a queue (first-in-first-out) for function calls? What would go wrong?

## Failed Attempts

### Attempt 1: A Fixed Set of "Return Registers"

Dedicate hardware registers to storing return addresses: register R1 for the first caller, R2 for the second, etc. Function A stores its return address in R1 before calling B. B stores its address in R2 before calling C. C returns: read R2, jump there (back to B). B returns: read R1, jump there (back to A).

This works for exactly 2 levels of nesting. What about 3? Or 30? You'd need 30 registers dedicated to return addresses. CPUs have a small fixed number of registers (16–32 general purpose). A function calling chain 50 deep would need 50 return address registers — far more than exist. In the 1950s, some architectures actually tried this and hit the limit immediately. Fixed registers don't scale to arbitrary nesting depth.

### Attempt 2: A Linked List of Call Records

When a function is called, allocate a new node on the heap: store the return address and local variables, link it to the previous call's node. On return, read the return address, free the node, follow the link back to the previous node. This works to arbitrary depth. But allocating and freeing heap memory for every function call is slow — heap allocation is O(1) amortized but has significant overhead (dozens of CPU cycles). A program that calls functions thousands of times per second can't afford heap allocation per call.

Also: heap memory is scattered across different cache lines. Reading local variables of the caller (after return) causes cache misses because the previous node may be far from the current position in memory.

### Attempt 3: A Contiguous Block With a Moving Top Pointer

Allocate a large contiguous block of memory once. Maintain a "top" pointer: where free space begins. To "push" (save a call record): write data at top, advance top by the record size. To "pop" (restore on return): retreat top by the record size, read the data. No allocation, no deallocation — just pointer arithmetic.

This is O(1) push and pop, contiguous in memory (cache friendly), and scales to depth limited only by the block size. The only risk: if calls nest deeper than the block allows, top runs off the end — stack overflow.

## The Discovery

Attempt 1 (fixed registers) fails because call depth is unbounded. Attempt 2 (heap-linked list) works but is too slow per operation. Attempt 3 gives O(1) push/pop with cache-friendly contiguous storage by using a fixed-size pre-allocated block with a moving top pointer.

This is the **call stack** — the system stack every program uses automatically. Each function call **pushes** a **stack frame** containing:

- The return address (where to jump when the function returns)
- The function's local variables
- Saved registers (if the CPU needs its registers for the new function)

Each function return **pops** the frame: restores the saved registers, jumps to the return address, and the stack top retreats.

As an abstract data type, a **stack** supports exactly three operations:
- `push(x)`: add x to the top — O(1)
- `pop()`: remove and return the top element — O(1)
- `peek()`: return top without removing — O(1)

The constraint: **LIFO** (last in, first out). The most recently pushed item is the first popped. This isn't an arbitrary choice — it's the constraint that makes function calls correct. Call A → B → C means C returns first (last called = first returned).

The stack is not just a data structure for function calls. Any problem where you need to reverse order, or where the solution to the outer problem depends on the solution to inner problems (recursion, parentheses matching, expression parsing), maps naturally onto a stack.

## Try It

<iframe src="../assets/browser/chapter20/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter20/index.html)

Before changing anything, predict:

- Push 5 items, then pop 3. What does the stack look like? In what order are items removed?
- Simulate a function call chain A→B→C→D. What does the call stack contain when D is executing?
- What happens to the stack when an exception is thrown in the middle of a call chain? (How do debuggers know "where" you are?)

## Implementation

The working model is dependency-free JavaScript that runs entirely in your browser — nothing to install. Open `browser/chapter20/index.html` to read or modify it (shared UI helpers live in `browser/common/sim.js`). The stack is a plain `stack` array; `stack.length` serves as the stack pointer, labeled `← SP (top)` on the canvas — push appends to the array, pop removes from the end, and the canvas redraws after each operation so the LIFO order is impossible to miss.

## When It Breaks

**Stack overflow.** The call stack has a fixed maximum size (typically 1–8MB on Linux/macOS; adjustable with `ulimit -s`). Deeply recursive algorithms (recursive traversal of a 100,000-node linked list) overflow the stack and crash with a segfault or `StackOverflowError`. This is a hard limit imposed by the OS. The fix: use an explicit heap-allocated stack (a list in Python) to implement the same algorithm iteratively — no depth limit except available heap memory.

**Stack smashing (buffer overflow → return address overwrite).** Stack frames contain both data (local variables, buffers) and control information (return addresses). If a local character buffer is overflowed by too much input, the bytes spill into the adjacent return address field. The attacker writes the address of their own code, which executes when the function returns. Stack smashing powered a generation of attacks (Morris Worm, Blaster, Sasser). Modern mitigations: stack canaries (random values that detect overwrites), non-executable stack (NX bit), and address space layout randomization (ASLR).

**Coroutines and green threads break the single-stack assumption.** Traditional stacks assume one thread = one stack. Coroutines (Python `asyncio`, Go goroutines) need to suspend mid-function and resume later — but the call stack doesn't support pausing at an arbitrary point. Go allocates a separate "goroutine stack" per goroutine and can grow it dynamically (starting at 2KB, growing as needed). Python's coroutines avoid this by only suspending at explicit `await` points, preserving the traditional call stack model for each `await` segment.

## Transfer

- **Undo/redo in text editors.** Each edit is pushed onto an undo stack. Ctrl+Z pops it. The last edit made is the first undone — LIFO by necessity, because undoing "type 'c'" before undoing "type 'b'" before undoing "type 'a'" would leave the document in an inconsistent state.
- **Browser back button.** Visiting pages pushes URLs onto the history stack. Back pops the top URL. Forward is a second stack (items popped from the history stack go onto the forward stack). Same data structure, same LIFO semantics.
- **Syntax parsing (compiler's recursive descent).** When a parser encounters `(3 + (4 * 5))`, it must match inner parentheses before outer ones. A stack tracks open parentheses: push on `(`, pop (and match) on `)`. Mismatched parens are detectable in O(n) time with a stack — any other structure is harder.

Try these:

1. Implement a function to check if a string of parentheses is balanced: `"((()))"` is balanced, `"(()"` and `"())"` are not. Use a stack. What's the time and space complexity?
2. The "towers of Hanoi" puzzle with 3 disks requires moving disks between pegs, never placing a larger disk on a smaller one. The solution is recursive. How many moves does it take for n disks? Write the recursive solution and identify the base case.
3. Convert the infix expression `3 + 4 * 5` to postfix (`3 4 5 * +`) using a stack (the "shunting yard algorithm"). Why is postfix evaluation easier than infix evaluation?

---

**Continue → [Why Queues Exist](21-why-queues-exist.md)**
