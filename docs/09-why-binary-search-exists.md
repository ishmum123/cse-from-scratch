# Why Halving Beats Hunting

## The Problem

You know sorted order enables faster search (chapter 8). Now you need to translate that insight into an algorithm.

A game: someone thinks of a number between 1 and 1,000,000. You can ask yes/no questions with one constraint: your only allowed question is "Is it [number]?" — you guess a number and they say "higher," "lower," or "correct."

Most people start at 1 and count up. After 500,000 guesses they hit the midpoint. Expected guesses: 500,000. Terrible.

The efficient player starts at 500,000. Gets "higher." Goes to 750,000. Gets "lower." Goes to 625,000. Within 20 guesses, they've found any number in 1,000,000. Not because they're lucky — because they're *halving* the remaining possibilities every guess, no matter what the answer is.

Any solution must:

- Use the "higher/lower" information to eliminate regions, not just single values
- Guarantee termination — converge to the answer in finite guesses
- Work in the worst case, not just the average case
- Be implementable correctly (boundary conditions are notoriously tricky)

## What Would You Try?

Before reading on:

- Starting at position `mid = (low + high) / 2` in a sorted array: if `array[mid] < target`, what can you conclude about where the target *isn't*?
- What happens to your search range on every comparison? Describe it precisely.
- If the range has just 2 elements left, what's the maximum number of comparisons needed?

## Failed Attempts

### Attempt 1: Always Start from a Fixed Position

Always check position 0 first, then position 1, then position 2... This is linear search wearing a sorted array. It ignores the ordering entirely. Even knowing `array[500] = 7` and `array[1000] = 42`, if you're looking for 35, you still start at 0 and scan. The sorted order is there but unused. Failure: doesn't exploit the structure at all.

### Attempt 2: Jump by a Fixed Step Size

Check index 0, then 100, then 200, ... Until you find an element larger than the target, then do linear search in the previous 100-element chunk. This is "exponential search" or "jump search" — better than linear. But the step size is fixed regardless of the remaining range. A step of 100 in a billion-element array finds the right 100-element chunk in 10 million steps, then does 100 more. Total: ~10 million. You could do ~30. Fixed steps don't adapt to the remaining uncertainty.

### Attempt 3: Try the Middle, Then Recurse on the Relevant Half

Check the exact midpoint. If less than target: target must be in the upper half. If greater: lower half. Recurse on the relevant half with a new midpoint. Each step cuts the remaining range exactly in half.

This works — but getting the implementation right is harder than it looks. Off-by-one errors: should you exclude the midpoint from the next range? Is `high = mid` or `high = mid - 1`? Does the loop run while `low < high` or `low <= high`? The wrong choice causes infinite loops or missed elements. The logic is simple but the boundary conditions demand precision.

## The Discovery

Attempt 1 (linear) ignores ordering. Attempt 2 (fixed jumps) uses ordering but doesn't adapt. Attempt 3 works — the halving insight is correct — but the implementation trap is real.

**Binary search**: given a sorted array of n elements and a target, maintain a search range `[low, high]`. At each step, compute `mid = low + (high - low) / 2` (not `(low + high) / 2` — that can overflow for large indices). Compare `array[mid]` to target:

- Equal: found, return mid
- Less: target must be in `(mid, high]`, so `low = mid + 1`
- Greater: target must be in `[low, mid)`, so `high = mid - 1`

Terminate when `low > high` (not found) or on match.

The range halves every iteration: n → n/2 → n/4 → ... → 1. How many halvings until you reach 1? That's log₂(n) halvings. Binary search takes **O(log₂ n)** comparisons — at most. For n = 1,000,000: at most 20 comparisons. For n = 1,000,000,000: at most 30.

The logarithm is the inverse of exponential growth: 2²⁰ = 1,048,576. Twenty questions to distinguish among a million possibilities.

The formal lower bound (chapter 8): any comparison-based search on a sorted array requires at least ⌈log₂(n+1)⌉ comparisons in the worst case. Binary search achieves this bound. It is optimal.

## Try It

<iframe src="../assets/browser/chapter09/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter09/index.html)

Before changing anything, predict:

- For an array of size 1024, what's the maximum number of comparisons in binary search? In linear search?
- What happens when you search for a value smaller than all elements? Larger than all elements?
- If you double the array size, how many more comparisons does binary search need vs linear search?

## Implementation

The working model is dependency-free JavaScript that runs entirely in your browser — nothing to install. Open `browser/chapter09/index.html` to read or modify it (shared UI helpers live in `browser/common/sim.js`). Look for the loop that halves `lo`/`hi` each step — and the intentional off-by-one variant right beside it so you can see exactly which boundary condition breaks first.

## When It Breaks

**Requires sorted order.** Binary search fails silently on unsorted arrays — it terminates without finding the element even if it exists. There's no error, just a wrong answer. This is a precondition violation: the algorithm's correctness depends on a property the caller must guarantee. Sorting costs O(n log n), so if you sort only to binary search once, you'd have been better off with linear search. Binary search pays only when searches are many and the data is already sorted or sorting is a one-time cost.

**Off-by-one bugs.** Even experienced programmers get binary search wrong. Jon Bentley (who popularized binary search via "Programming Pearls") found that most professional programmers could not write a correct binary search from memory. A common bug: `mid = (low + high) / 2` overflows when `low` and `high` are both near INT_MAX (in Java and C). The fix is `mid = low + (high - low) / 2`. Another: using `high = mid` instead of `high = mid - 1` causes infinite loops when `high - low = 1`.

**Doesn't generalize to linked structures.** You cannot binary search a linked list — computing the midpoint requires walking half the list, destroying the O(log n) advantage. Binary search requires O(1) random access to any index, which only contiguous arrays provide. This is a key reason why trees (chapter 10) exist: to get O(log n) search on dynamic data that can't live in a sorted array.

## Transfer

- **`git bisect`** uses binary search to find which commit introduced a bug. Given "oldest commit is good, newest is bad," it checks the midpoint commit, you test it, and it halves the remaining range. Finding the bad commit among 1,000 commits takes at most 10 steps.
- **Floating point root finding.** Bisection method: find a root of f(x) = 0 by maintaining an interval [a, b] where f(a) < 0 and f(b) > 0, and evaluating the midpoint. Converges to 1 decimal place per 3.3 iterations. Same algorithm, different domain.
- **System call `mmap` and OS page tables.** When the OS looks up which physical page corresponds to a virtual address, it walks a binary tree (page table) — the same halving structure, in hardware.

Try these:

1. Implement binary search to find the *first* occurrence of a value in a sorted array that may have duplicates. How does the termination condition change?
2. You're searching a sorted array of 1,000,000,000 elements. Binary search guarantees at most how many comparisons? What if linear search gets "lucky" and the element is in position 3 — is linear search faster in that case?
3. "Interpolation search" uses the value of the target relative to the endpoints to guess a better midpoint than the literal middle. When is it faster than binary search? When does it fail?

---

**Continue → [Why Trees Exist](10-why-trees-exist.md)**
