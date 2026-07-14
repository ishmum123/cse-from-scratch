# The Warehouse Without Aisle Numbers

## The Problem

You're designing a warehouse management system. Workers drop packages anywhere there's space. When a customer orders their package, you need to retrieve it.

Without location labels, you search every shelf. Fast to store, slow to retrieve. But if you assign every shelf a number and record which package went to which shelf number, retrieval is instant.

Now think about computer memory. Your program stores a value. Later it wants that value back. How does the machine know where it put it?

Memory is just billions of transistors, each holding a 0 or 1. Without a way to identify *which* transistor (or byte) holds which value, the machine would have to search everything on every retrieval. For a 16GB machine that's 17 billion bytes to search every time you access a variable.

Any solution must:

- Give every storage location a unique identifier
- Allow the machine to go directly to any location given its identifier
- Make the identifier computable — arithmetic on it should navigate to adjacent locations
- Cost nothing to use — the addressing scheme must be as fast as the hardware

## What Would You Try?

Before reading on:

- You need to identify every byte in 4GB of memory. What's the minimum number of bits you need per address? (Hint: how many distinct addresses do you need?)
- If addresses are just sequential integers starting at 0, what's the address of the 1000th byte?
- What happens if two programs try to use the same address at the same time?

## Failed Attempts

### Attempt 1: Name Every Location by Content

Label each location by what it currently stores. To find `x = 47`, search for the location that currently holds 47. This fails immediately: many locations might hold 47, and the content changes — if you update `x` to 48, its name changes and all previous references become stale. You can't use content as an identifier because identifiers must be stable and content is the whole point of the system.

### Attempt 2: A Central Directory / Map

Maintain a table: "variable `x` is in location number 1042." Look up the variable name in the table, get the location number, go there. This is closer — location numbers are stable. But who manages the table? Looking up the table itself requires memory access, so you need to know where the table lives, which requires an address... and you've created a circular dependency. The table must be either at a fixed known address or itself addressed by content (failing Attempt 1). Also, the table lookup adds overhead to every single memory access — unacceptable.

### Attempt 3: Sequential Numbers, Hardware-Direct

Number every byte sequentially from 0 to N-1. The machine exposes these numbers directly to programs: "load the byte at address 1042" is a single hardware instruction. No lookup table, no indirection. The address is the location number, and the hardware uses it directly to select which byte to read.

This works — this is how memory actually works. But it exposes a problem: every program sees the same address space. Program A's address 1042 is the same physical byte as Program B's address 1042. If they both run at once, they corrupt each other.

## The Discovery

Attempt 3 is essentially correct but reveals a new problem — address collision between programs. The fix to that (virtual memory, chapter 29) builds on the addressing model, not against it.

The core discovery: **every byte of memory has a unique integer address**. Starting at 0, incrementing by 1, up to the size of memory. A 4GB machine has addresses 0 through 4,294,967,295. A pointer is just an integer that happens to be interpreted as an address.

This is why the array formula from chapter 3 works: if element 0 is at address `b`, then element `i` is at address `b + i * size` — because addresses are just numbers, and arithmetic on them navigates memory.

Why integer addresses and not names? Because the hardware *is* the memory. The CPU issues an address as an electrical signal on the address bus — a set of wires where each wire is 0 or 1. With 32 wires, you can represent 2³² = 4,294,967,296 different addresses. With 64 wires, 2⁶⁴. The address *is* the hardware signal, and hardware signals are numbers.

A **pointer** is a variable whose value is a memory address. It's an integer that tells you where to look, not what's there.

## Try It

<iframe src="../assets/browser/chapter04/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter04/index.html)

Before changing anything, predict:

- If a pointer holds address 1000 and you add 4 to it, what address does it now point to? What does this depend on?
- What is the "null pointer" (address 0) and why is it conventionally used to mean "no valid address"?
- What happens when you dereference a pointer to memory your program doesn't own?

## Implementation

The working model is dependency-free JavaScript that runs entirely in your browser — nothing to install. Open `browser/chapter04/index.html` to read or modify it (shared UI helpers live in `browser/common/sim.js`). Look for the pointer-arithmetic step that adds an offset to a base address — that one operation is the entire foundation of how arrays and pointers relate.

## When It Breaks

**Null pointer dereference.** When a pointer holds address 0 (or some other sentinel meaning "no valid address"), and you try to read or write through it, you're accessing memory you don't own. This crashes the program with a segfault. Null pointer dereferences are among the most common bugs in systems software — Tony Hoare, who invented the null reference, called it "my billion-dollar mistake."

**32-bit address space exhaustion.** 32-bit pointers can address at most 4GB. In the early 2000s, servers hit this limit — they couldn't use more than 4GB of RAM per process no matter how much physical memory was installed. The migration to 64-bit was driven entirely by this constraint. Any system designed with fixed-size pointers inherits a capacity ceiling.

**Pointer aliasing.** Two different pointers pointing to the same memory location. You update through one pointer, read through the other, and the value has changed "by itself." Compilers can't optimize across aliased pointers, and humans make logical errors. The `restrict` keyword in C is an explicit promise that no aliasing occurs, enabling aggressive optimization.

## Transfer

- **URLs** are addresses — not for bytes, but for resources. `https://example.com/page` tells a browser where to look, just like an address tells the CPU where to look. The similarity is intentional.
- **DNS** translates names to addresses, solving the same problem as Attempt 2 above — but at the network level, where the indirection cost is acceptable because network latency already dominates.
- **Pointers in data structures.** A linked list node holds a pointer to the next node. A tree node holds pointers to its children. All graph structures are just values connected by addresses.

Try these:

1. A 32-bit system can address 4GB. Why do 32-bit systems sometimes report less than 4GB of available user-space memory? (Hint: the OS also needs address space.)
2. What's the difference between a pointer and an array in C? In what sense are they the same?
3. If addresses are just integers, could you add two pointers together? What would that mean? Why is this usually an error?

---

**Continue → [Why Copying Is Expensive](05-why-copying-is-expensive.md)**
