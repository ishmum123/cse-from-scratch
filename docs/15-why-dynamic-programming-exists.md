# The Recursion That Kept Solving the Same Problem

## The Problem

A naive recursive Fibonacci implementation: `fib(n) = fib(n-1) + fib(n-2)`. Simple, correct, beautiful. Now compute `fib(50)`.

`fib(50)` calls `fib(49)` and `fib(48)`. `fib(49)` calls `fib(48)` and `fib(47)`. `fib(48)` is computed twice — once for each call. And `fib(47)` is computed three times. `fib(2)` is computed 12,586,269,025 times. The recursion tree has over 12 billion nodes for a sequence of 50 numbers.

On a modern laptop: `fib(50)` takes over a minute. `fib(60)` would take hours. `fib(100)` would take longer than the age of the universe.

The visceral cost: a correct algorithm that is unusable because it rediscovers the same answers billions of times. The problem isn't recursion — it's *repeated subproblems* that divide-and-conquer doesn't protect against.

Any solution must:

- Solve each unique subproblem exactly once
- Reuse stored results instead of recomputing
- Handle problems where subproblems overlap (not independent like D&C)
- Scale to solve problems of size n in polynomial time when the subproblem count is polynomial

## What Would You Try?

Before reading on:

- `fib(50)` has only 49 unique subproblems (fib(2) through fib(50)). How many total computations does naive recursion do? What's the ratio?
- If you wrote answers in a notebook as you computed them, how would that change the recursion?
- Can you compute Fibonacci bottom-up — start from fib(2) and fib(3), and work your way up to fib(50)?

## Failed Attempts

### Attempt 1: Deeper Recursion With More Parallelism

Assign `fib(48)` to a separate thread so both computations proceed simultaneously. This halves wall-clock time for that specific duplication. But `fib(47)` is still computed three times, `fib(46)` five times, and the redundancy grows exponentially. Parallelism reduces constant factors — it doesn't change the exponential structure. You'd need exponentially many threads to match the exponential redundancy.

### Attempt 2: Memoization (Top-Down Cache)

Before computing `fib(n)`, check if the answer is already stored. If yes, return it instantly. If no, compute it and store the result before returning. This converts the recursion from a tree (where branches duplicate) to a DAG (directed acyclic graph) where each node is computed once.

`fib(50)` now makes exactly 49 unique recursive calls, each doing O(1) work. Total: O(n) instead of O(2ⁿ). The same idea applies to any recursive algorithm with overlapping subproblems. This works perfectly — it's one of the two DP approaches.

### Attempt 3: Tabulation (Bottom-Up Iteration)

Instead of recursing down and caching, fill a table from the smallest subproblems up. Compute `fib(2)`, `fib(3)`, ..., `fib(50)` in order, each using previously computed values. No recursion, no call stack, no memoization overhead — just a loop.

```python
table = [0, 1]
for i in range(2, n+1):
    table.append(table[i-1] + table[i-2])
return table[n]
```

O(n) time, O(n) space. With a rolling window: O(1) space (only need the last two values). This is "dynamic programming" in its purest form — build up from subproblems.

## The Discovery

Attempt 1 (parallelism) doesn't fix exponential structure. Attempt 2 (memoization) works by caching top-down. Attempt 3 (tabulation) works by building bottom-up. Both are correct and efficient — the choice is a matter of implementation style.

The key insight: **dynamic programming applies when a problem has two properties**:

1. **Optimal substructure**: the optimal solution to the problem contains optimal solutions to subproblems. For Fibonacci, `fib(n)` is exactly `fib(n-1) + fib(n-2)` — no approximation, exact subproblem reuse.

2. **Overlapping subproblems**: the same subproblem appears in multiple branches of the recursion. For Fibonacci, `fib(48)` appears in both `fib(50)→fib(49)→fib(48)` and `fib(50)→fib(48)`.

This distinguishes DP from divide-and-conquer: D&C subproblems are *disjoint* (merge sort's left half and right half never share elements). DP subproblems *overlap* (Fibonacci subproblems are shared across branches). D&C doesn't benefit from caching; DP requires it.

Classic DP problems: shortest path in a graph (Bellman-Ford, Dijkstra), longest common subsequence (diff, sequence alignment), knapsack (packing with weight constraints), edit distance (spell checking, DNA alignment). Each decomposes into overlapping subproblems and uses optimal substructure.

The name "dynamic programming" is historically opaque — Richard Bellman invented it in the 1950s and chose the name to avoid bureaucratic scrutiny of his research ("dynamic" sounded impressive to funders). It has nothing to do with dynamic memory or programming languages.

## Try It

<iframe src="../assets/browser/chapter15/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter15/index.html)

Before changing anything, predict:

- Visualize the recursion tree for naive Fibonacci on n=10. Count duplicate nodes.
- Switch to memoized Fibonacci. How does the tree change? How many nodes remain?
- Increase n. At what point does naive recursion become visibly slow while DP stays instant?

## Implementation

The working model is dependency-free JavaScript that runs entirely in your browser — nothing to install. Open `browser/chapter15/index.html` to read or modify it (shared UI helpers live in `browser/common/sim.js`). Look for the memo-table lookup that short-circuits the recursive call — that single cache check is what collapses an exponential call tree into a linear one.

## When It Breaks

**The DP table doesn't fit in memory.** Some problems have O(n²) or O(n³) unique subproblems. Edit distance between two strings of length n and m requires an n×m table: for two 10,000-character strings, that's 100 million entries × 4 bytes = 400MB. Genome alignment (strings of length 10⁹) is completely infeasible naively. The "divide and conquer DP optimization" and "Hirschberg's algorithm" reduce space to O(n) for specific subclasses, but not all DP problems have such optimizations.

**DP requires knowing the subproblem structure in advance.** The memoization/tabulation approach only works if you can enumerate all subproblems before or during solving. Problems where the subproblem space is discovered lazily (like game trees of unknown depth) require different approaches (alpha-beta pruning, MCTS). DP is not a universal algorithm — it's a pattern that works when the problem structure matches.

**DP can give wrong answers when subproblems aren't truly optimal.** If the problem doesn't have optimal substructure — if the best sub-solution to part of the problem isn't part of the best overall solution — DP silently gives wrong answers. The traveling salesman problem (TSP) has a variant that seems to have substructure but doesn't: the optimal path from A to C through B isn't necessarily the optimal path from A to B concatenated with optimal path from B to C (because the overall path must visit all cities).

## Transfer

- **`diff` (git diff, Linux diff)** uses the longest common subsequence (LCS) DP to find the minimum set of edits between two files. Every `git status` and `git diff` output is DP.
- **Spell checkers and autocorrect** use edit distance (Levenshtein distance) DP: minimum insertions, deletions, substitutions to transform one string to another. Your phone's autocorrect is DP running thousands of times per second.
- **Protein folding (partial).** Certain simplified protein structure prediction models use DP on the sequence of amino acids. AlphaFold2 uses attention + gradient descent, but earlier methods were DP-based.

Try these:

1. Compute the edit distance between "kitten" and "sitting" by filling in the DP table by hand (7 × 8 grid). What does each cell represent?
2. A coin change problem: given coin denominations [1, 5, 10, 25] and amount n, find the minimum number of coins. Write the recurrence. Does it have optimal substructure? Overlapping subproblems?
3. The naive Fibonacci recurrence has 2ⁿ calls. The memoized version has n calls. What determines the number of unique subproblems? How would you count them for a new DP problem before implementing?

---

**Continue → [Why Greedy Sometimes Works](16-why-greedy-sometimes-works.md)**
