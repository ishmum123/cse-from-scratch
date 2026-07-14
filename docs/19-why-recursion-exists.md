# The Problem That Contains a Smaller Copy of Itself

## The Problem

You need to traverse a file system: list every file in a directory, and every file in every subdirectory, and every file in every subdirectory's subdirectory, to arbitrary depth. The depth is unknown in advance — some directories are 2 levels deep, some are 10.

With a loop: you'd need a loop that loops over subdirectories, but each subdirectory might have subdirectories, requiring another nested loop, which might have more subdirectories... You don't know how many levels to nest. You can't write a fixed number of nested loops for a depth you don't know.

What you *do* know: processing a directory means listing its contents, and for each item that's a directory, processing *that directory* — which is the same task, applied to a smaller input.

The problem is self-similar: the task of traversing a directory tree is defined in terms of traversing smaller directory trees. Functions (chapter 18) give you the tool to express this.

Any solution must:

- Express "do X, and for each result, do X again on the result" without fixing the number of repetitions in advance
- Terminate — not recurse forever
- Handle structures of unknown depth
- Be implementable without inventing a new control flow construct (loops already exist, but they're not always the natural fit)

## What Would You Try?

Before reading on:

- "List all files in /home/user" — if /home/user has a subdirectory /home/user/docs, how do you list /home/user/docs? And if docs has a subdirectory, how do you list that?
- What's the smallest possible directory tree (the "base case" where no recursion is needed)?
- Can you express this with a while loop? What data structure would you need?

## Failed Attempts

### Attempt 1: Fixed-Depth Nested Loops

```
for item in directory:
    if item is file: print(item)
    else:
        for item2 in item:
            if item2 is file: print(item2)
            else:
                for item3 in item2:  # only 3 levels!
```

This works for trees of at most 3 levels. A 4-level tree has files the code never reaches. The program is wrong by construction — it makes an assumption about the structure that the world may not satisfy. Unacceptable: software that silently ignores data it doesn't know how to handle.

### Attempt 2: Explicit Stack with a While Loop

Maintain a list of directories yet to be processed. Start with [root]. While the list isn't empty: pop a directory, list its contents, add subdirectories to the list, print files. This works to arbitrary depth and is actually what recursive traversal compiles to (the stack in the next chapter is exactly this). It's correct but requires manually managing the "what to do next" list.

The code is also harder to read: the "what comes next" logic is explicit in the stack management instead of implicit in the call structure. For simple traversals it's manageable, but for complex recursive algorithms (like tree transformations that return values), maintaining an explicit stack requires rewriting the algorithm in a less-natural form.

### Attempt 3: A Function That Calls Itself

Define `traverse(directory)`: list contents; for each item, if it's a file, print it; if it's a directory, call `traverse(item)`. The function calls itself with a smaller input. Each call handles one directory and delegates subdirectories to new calls.

The problem: how does this terminate? If directory B contains directory C which contains directory B (a cycle), `traverse` loops forever. File systems don't have cycles (usually), but the question stands: what prevents infinite recursion?

## The Discovery

Attempt 1 (fixed depth) is incorrect for variable-depth structures. Attempt 2 (explicit stack) is correct but manual. Attempt 3 (self-call) is natural and correct if the recursion has a **base case** that terminates the descent.

**Recursion** is the technique of a function calling itself with a strictly smaller or simpler input. Every recursive function has two parts:

1. **Base case(s)**: the smallest inputs where the answer is known directly and no recursive call is needed. For file traversal: a directory with no subdirectories (just print its files and return).

2. **Recursive case**: reduce the current input to a smaller instance and call the function on that instance. For file traversal: call `traverse(subdirectory)` for each subdirectory.

Termination: if every recursive call reduces the input (by some well-founded measure — depth, size, count), and base cases don't recurse, the recursion always terminates.

Recursion is not a trick or a special language feature. It's the natural expression of **structural induction**: a problem is solved if we can solve it for the base case and, assuming the recursive calls work correctly, show the recursive case works too. This is mathematically rigorous.

Many data structures are defined recursively: a binary tree is either empty (base case) or a node with a left subtree and a right subtree (both trees — recursive case). Algorithms on recursively-defined structures are naturally recursive.

Recursion vs iteration: every recursive algorithm can be rewritten as iteration with an explicit stack (as Attempt 2 showed). Compilers sometimes do this automatically (tail call optimization). The choice is readability: recursive algorithms match recursive structure; iterative algorithms with explicit stacks are sometimes more efficient (no function call overhead) but harder to read.

## Try It

<iframe src="../assets/browser/chapter19/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter19/index.html)

Before changing anything, predict:

- Trace a recursive traversal of a 3-level directory tree. In what order are files printed?
- What happens if you remove the base case check? How many recursive calls occur before the program crashes?
- Compare recursive traversal vs explicit-stack traversal on the same tree. Is the order of visited nodes the same?

## Implementation

The working model is dependency-free JavaScript that runs entirely in your browser — nothing to install. Open `browser/chapter19/index.html` to read or modify it (shared UI helpers live in `browser/common/sim.js`). Look for the recursive `traverse` function that calls itself on each subdirectory — the base case check directly above that self-call is what guarantees termination, and removing it shows exactly how quickly infinite recursion crashes the stack.

## When It Breaks

**Stack overflow.** Each recursive call consumes a stack frame (local variables, return address — typically 64–512 bytes). Deep recursion — one call per node in a 100,000-node tree — uses 100,000 stack frames, potentially exceeding the stack limit (typically 1–8MB on most systems). In Python, the default recursion limit is 1,000 calls. Recursive traversal of a very deep directory tree (or a very deep linked list) will crash with a `RecursionError`. The fix: convert to iteration with an explicit heap-allocated stack, or increase the stack limit.

**No tail call optimization in Python or Java.** In languages that support tail call optimization (Haskell, Scheme, some Rust scenarios), a recursive call in tail position (last action before return) is compiled to a jump, consuming no extra stack space. Python and Java explicitly do not optimize tail calls, so recursive algorithms always consume stack proportional to recursion depth. This is a deliberate language design choice in Python — Guido van Rossum wanted readable stack traces.

**Exponential recursion without memoization.** Naive recursive Fibonacci calls `fib(n-1)` and `fib(n-2)`, both recursing into overlapping subproblems. Each call spawns two more, creating an exponential call tree (2ⁿ calls for fib(n)). This is the exact problem dynamic programming (chapter 15) solves. Recursion is a *structure*; whether it's efficient depends on the problem's subproblem structure. Recognize overlapping subproblems and add memoization.

## Transfer

- **HTML / XML parsing.** HTML is a nested structure (elements contain elements). Parsers are naturally recursive: `parse_element` parses the opening tag, calls `parse_element` for each child, parses the closing tag. The DOM tree is built recursively by a recursive algorithm.
- **Merge sort.** The divide-and-conquer sort from chapter 13 is recursive: `mergesort(array) = merge(mergesort(left_half), mergesort(right_half))`. The elegant O(n log n) complexity falls out of the recursive structure.
- **Mathematical induction proofs.** Proving `sum(1..n) = n(n+1)/2` by induction is exactly the structure of recursion: prove the base case (n=1: sum=1=1×2/2 ✓), assume it works for n-1, prove it for n. Recursion is induction applied to programs.

Try these:

1. Write a recursive function to compute the sum of a list of numbers. Identify the base case and recursive case. What's the maximum recursion depth for a list of length n?
2. "Mutual recursion": function A calls function B, and function B calls function A. Give an example problem where mutual recursion is natural. Does it always terminate?
3. Convert the recursive factorial function to an iterative version using an explicit stack. The stack should hold "what computation still needs to be done." What does each stack frame contain?

---

**Continue → [Why Stacks Exist](20-why-stacks-exist.md)**
