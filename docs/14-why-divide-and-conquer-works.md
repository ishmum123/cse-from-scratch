# The Algorithm That Wins by Shrinking the Problem

## The Problem

You need to multiply two 1,000-digit numbers. A CPU handles 64-bit (20-digit) numbers in hardware, but numbers this large require software. The obvious approach: grade-school multiplication. Multiply every digit of the first number by every digit of the second, add up the partial products.

For two n-digit numbers, grade-school multiplication performs n² single-digit multiplications. For 1,000-digit numbers: 1,000,000 operations. For RSA encryption keys (2,048 bits ≈ 617 decimal digits): ~380,000 operations per multiply. Encrypt a message: thousands of such multiplications. The cost compounds.

More generally: many problems feel intractable because the input is large. The full problem has n² or n³ or 2ⁿ cost. But if you can *split* the problem, solve the pieces independently, and *combine* cheaply, you sometimes achieve far better than n².

Any solution must:

- Identify subproblems that are smaller instances of the same problem
- Ensure subproblems are independent (solving one doesn't require the other's result)
- Combine subproblem solutions efficiently — cheaper than solving from scratch
- Reach a base case that's trivially solvable

## What Would You Try?

Before reading on:

- You have 8 people and need to find the tallest. Obvious O(n): compare all. Can you do it by running the comparison "tournament-style"? Does it require fewer total comparisons?
- For large number multiplication: can you express (a × b) in terms of multiplications of smaller numbers?
- What happens if the combining step is too expensive? Does dividing still help?

## Failed Attempts

### Attempt 1: Divide Without Exploiting Structure

Split the array of n numbers into two halves. Solve each half separately. Combine. If the combine step costs O(n), the recurrence is T(n) = 2T(n/2) + O(n), giving O(n log n). That's the merge sort result from chapter 13.

But what if the original problem was already O(n)? Dividing an O(n) problem into two O(n/2) problems and combining in O(n) still gives O(n log n) — *worse* than the original. Divide and conquer isn't always beneficial; it helps when (a) the subproblems are strictly easier to solve in total than the original, or (b) the combination is cheaper than naive.

### Attempt 2: Divide Into More Than Two Parts

Instead of two halves, split into three or four parts. With more parts, each is smaller. For k parts of size n/k with O(n) combine: T(n) = kT(n/k) + O(n) = O(n log_k n). For k=3: O(n log₃ n). Better constant, same big-O. The number of parts changes constants but rarely changes the exponent.

The key question is whether *more splits* change the *shape* of the recurrence — specifically, whether the combine step grows slower than the gains from smaller subproblems.

### Attempt 3: Karatsuba's Insight — Three Multiplications Instead of Four

For multiplying two 2-digit numbers ab × cd (where a, b, c, d are single digits): grade school does 4 multiplications (a×c, a×d, b×c, b×d). Can we use 3?

Note: `ac` and `bd` are directly needed for the result. The middle term `ad + bc` appears as the cross-term coefficient. Observe: `(a+b)(c+d) = ac + ad + bc + bd`. So `ad + bc = (a+b)(c+d) - ac - bd`. We already computed `ac` and `bd`, so `ad + bc` requires only one more multiplication: `(a+b)(c+d)`. Three multiplications total instead of four.

This doesn't save much for 2-digit numbers. But apply recursively: use 3 multiplications of n/2-digit numbers instead of 4. The recurrence: T(n) = 3T(n/2) + O(n). By the Master Theorem: T(n) = O(n^log₂3) ≈ O(n^1.585). For 1,000-digit numbers: 10^1.585 ≈ 38,500 operations vs 1,000,000. A 26× speedup from one clever algebraic identity.

## The Discovery

Attempt 1 showed that dividing helps when subproblems are strictly cheaper in total. Attempt 2 showed that the number of parts changes constants, not the fundamental bound. Attempt 3 showed that the ratio of subproblems solved to subproblem size is what determines the speedup — reducing from 4 subproblems to 3 at size n/2 changed the exponent.

**Divide and conquer** is a paradigm, not an algorithm. It works when:

1. The problem can be split into subproblems of the same type but smaller size
2. The subproblems are independent (no shared state between them — this distinguishes D&C from dynamic programming in chapter 15)
3. The combination step costs less than solving the original

The analysis tool is the **Master Theorem**: for T(n) = aT(n/b) + f(n) — a subproblems of size n/b with f(n) combination work — the solution depends on how f(n) compares to n^(log_b a):

- If f(n) < n^(log_b a) (subproblem work dominates): T(n) = O(n^(log_b a))
- If f(n) = n^(log_b a) (equal): T(n) = O(n^(log_b a) · log n)
- If f(n) > n^(log_b a) (combine dominates): T(n) = O(f(n))

Merge sort: a=2, b=2, f(n)=O(n), n^(log_2 2) = n. Case 2: O(n log n).
Karatsuba: a=3, b=2, f(n)=O(n), n^(log_2 3) ≈ n^1.585 > n. Case 1: O(n^1.585).
Binary search: a=1, b=2, f(n)=O(1), n^(log_2 1) = 1. Case 3: O(log n).

All three are the same paradigm; different parameters give different complexities.

## Try It

<iframe src="../assets/browser/chapter14/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter14/index.html)

Before changing anything, predict:

- Trace merge sort on an 8-element array. How many levels of recursion? How much work at each level?
- If you double the input size, how does the total work change for O(n log n) vs O(n²)?
- Where does divide and conquer *not* help — when does the combining step cost too much?

## Implementation

The working model is dependency-free JavaScript that runs entirely in your browser — nothing to install. Open `browser/chapter14/index.html` to read or modify it (shared UI helpers live in `browser/common/sim.js`). The sim is a schematic of the divide-and-conquer principle, not a general algorithm — it finds the maximum of an array: `buildDCSteps()` constructs a tournament bracket while an exhaustive scan checks every element, with `exMax` and `dcMax` tracking their comparison counts so you can watch the divide-and-conquer approach do the same work in fewer steps.

## When It Breaks

**Overhead for small inputs.** Recursive function calls have overhead — stack frame allocation, parameter passing. For very small inputs (n < 10), an O(n²) algorithm with tiny constants beats O(n log n) with recursive overhead. This is why Timsort switches to insertion sort below a threshold, and why most divide-and-conquer implementations have a base case at n ≤ 10–32.

**Subproblems aren't independent.** If solving one half requires a result from the other half, you can't parallelize or recurse freely. This is the boundary between divide-and-conquer and dynamic programming (chapter 15): D&C splits into non-overlapping subproblems; DP handles overlapping ones where the same subproblem appears in multiple branches.

**Parallelism doesn't always compose.** Divide and conquer looks parallelizable (solve both halves simultaneously). But if the combine step requires synchronization or if subproblems have data dependencies, parallel speedup diminishes. MapReduce is explicitly a divide-and-conquer framework — "map" is the divide, "reduce" is the combine — and its bottlenecks are exactly at the reduce step when reduce work dominates.

## Transfer

- **FFT (Fast Fourier Transform).** Transforms n samples into n frequency components. Naive: O(n²). FFT via divide-and-conquer: O(n log n). Enables audio compression (MP3), image processing (JPEG), and signal processing at scale. Every music streaming app uses FFT.
- **Parallel prefix sum.** Given an array, compute the running sum at each position. Naive: O(n) sequential. Divide-and-conquer on a parallel machine: O(log n) time with n processors. Used in GPU programming for aggregation.
- **Closest pair of points.** Given n points in 2D, find the two closest. Naive: O(n²) pairs. Divide-and-conquer: split vertically, solve each half, check points near the split line in a narrow strip. O(n log n) total.

Try these:

1. The recurrence T(n) = 4T(n/2) + O(n) (four subproblems of half size). What's the solution? Compare to merge sort's T(n) = 2T(n/2) + O(n). Why is more subproblems worse?
2. Implement Karatsuba multiplication for two 4-digit numbers (split into two 2-digit halves each). Trace through which multiplications are done and count them.
3. Binary search has recurrence T(n) = T(n/2) + O(1). Solve it using the Master Theorem. Why is O(1) combine work so powerful here?

---

**Continue → [Why Dynamic Programming Exists](15-why-dynamic-programming-exists.md)**
