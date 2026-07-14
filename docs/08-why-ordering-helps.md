# What a Dictionary Knew That a Pile of Papers Didn't

## The Problem

You've established (chapter 7) that searching an unordered collection costs O(n) — unavoidable without structure. The question now: what's the cheapest structure to add, and how much does it help?

Consider two scenarios:

1. 10,000 employee records dumped in a folder in no particular order. Find "Smith, Jane."
2. The same records sorted alphabetically. Find "Smith, Jane."

In scenario 1, you scan from the beginning. Average 5,000 records examined. In scenario 2, you can open to the middle of the folder, notice you're in the M's, know Jane Smith must be in the second half, jump to the 3/4 mark...

But wait — before we get to *how* to exploit the ordering, this chapter asks a simpler question: what does ordering *buy* you at all? What does knowing "everything to the left is smaller" let you conclude that you couldn't conclude before?

Any solution must:

- Turn a single comparison into useful information about where to look *next*
- Eliminate regions of the search space, not just individual items
- Work for any key type that has a natural ordering (numbers, strings, dates)
- Be exploitable without knowing the target's exact position in advance

## What Would You Try?

Before reading on:

- You're looking for page 347 in a 500-page book. How do you use the page numbers to navigate?
- Now the pages have no numbers but are in order by their content. How do you find a specific sentence?
- What specifically does the page number (or alphabetical order) let you *skip*?

## Failed Attempts

### Attempt 1: Order Just Makes Linear Search Faster on Average

Maybe sorted order helps because the target is easier to find "early." For a sorted list, once you pass where the target *would* be, you know it's absent and can stop. This improves the "not found" case — you stop as soon as you find an element larger than the target, rather than scanning the whole list.

But the average for "found" cases is still n/2 comparisons. For a random target in a sorted list, it's equally likely to be anywhere. Sorting alone, with linear scanning, saves work only on negative searches. The average case improves from n to about n/2 — a constant factor, not an asymptotic improvement. Good, but not transformative.

### Attempt 2: Build an Index (Knowing All Keys in Advance)

If you know every key, build a perfect lookup table: a dictionary where key → position. Then finding any item is one lookup. But this requires knowing all keys in advance, costs extra space proportional to the collection, and doesn't generalize to arbitrary ranges. And you still need to search the index if the keys aren't perfectly dense integers.

### Attempt 3: Use Order to Decide Direction, Not Just Confirm Position

In a sorted list, comparing the target to an element tells you three things: (1) it's this element (done), (2) it's to the left (smaller), or (3) it's to the right (larger). Information #2 and #3 are new — they eliminate an entire region of the search space with one comparison, and the size of that region depends on *where* you make the comparison.

If you always compare to the *middle* element, you eliminate *half* the remaining search space per comparison. This is qualitatively different from linear search, which eliminates exactly one element per comparison.

## The Discovery

Attempt 1 showed that ordering helps linearly (constant factor). Attempts 2–3 show the real power: ordering lets a single comparison give directional information — not just "found/not found" but "go left/go right."

In an unsorted collection, knowing that element #500 is not the target tells you nothing about where the target is. In a sorted collection, knowing that element #500 is *less than* the target tells you the target is in positions 501 through n. One comparison eliminates everything before position 501 — potentially half the collection, depending on where you compare.

This is why sorted data enables faster search: **a comparison against a sorted structure carries more information** than a comparison against an unsorted one. The information content (in bits) of "the target is greater than element at position X" is log₂(n - X) bits — it tells you exactly which elements are eliminated.

The formal tool here is the **comparison tree**: every search algorithm on an ordered set corresponds to a binary tree of yes/no comparisons. The minimum height of this tree, and hence the minimum number of comparisons, is ⌈log₂(n + 1)⌉. Ordering is what makes this logarithmic bound achievable. Without it, the tree is a chain and the bound is n.

Next chapter: how to exploit ordering most efficiently (binary search). This chapter's lesson: ordering is the enabler; how you use it determines whether you get O(n) or O(log n).

## Try It

<iframe src="../assets/browser/chapter08/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter08/index.html)

Before changing anything, predict:

- Compare search time on an unsorted vs sorted array for targets near the beginning, middle, and end. Does sorting help equally for all positions?
- When searching a sorted list for a value that doesn't exist, where do you stop?
- Sorting costs O(n log n). If you only search once, is it worth sorting first?

## Implementation

The working model is dependency-free JavaScript that runs entirely in your browser — nothing to install. Open `browser/chapter08/index.html` to read or modify it (shared UI helpers live in `browser/common/sim.js`). Look for the early-exit condition in the sorted-search path — the one line that lets a "not found" scan stop as soon as it passes where the target would be, instead of scanning to the end.

## When It Breaks

**Maintaining order during insertions is expensive.** A sorted array enables fast search but slow inserts — inserting element X in sorted position means shifting all elements after X forward by one. For n elements, that's O(n) work per insert. A collection that's searched rarely but updated often may be better left unsorted. This is the tradeoff that motivates trees (chapter 10): keep order cheap to maintain.

**Ordering requires a total order.** You can only sort elements that are comparable — every pair must be either less than, equal to, or greater than. Complex objects (graphs, images, functions) have no natural total order. You must either project them to a sortable key (e.g., sort images by file size) or use a different retrieval structure.

**Stable sorts matter when order has secondary meaning.** If you sort records by last name, what happens to records with the same last name? A *stable* sort preserves the original relative order of equal elements; an *unstable* sort doesn't. Using an unstable sort where stability is required is a bug that appears only with duplicate keys — often in production with real data, never in tests with small clean data.

## Transfer

- **Phone books.** Sorted alphabetically. Finding a name is fast (binary search). But they're printed — no updates allowed. The tradeoff: sorted for read speed, static to avoid insert cost.
- **B-tree database indexes** (chapter 32) maintain sorted order dynamically as rows are inserted and deleted. The cost of maintaining order is paid on every write; the benefit is fast range queries.
- **Merge join in databases.** If two tables are both sorted on the same column, joining them requires only one pass through each — O(n + m). Without sorting, a nested loop join is O(n × m). Sorting is often a worthwhile upfront cost when multiple operations will exploit the order.

Try these:

1. What's the minimum number of comparisons needed to find an element in a sorted list of 1,000,000 items? Show your work.
2. Insertion sort maintains a sorted sub-array and inserts each new element in order. What's its complexity? When would you choose it over merge sort?
3. A "sorted linked list" keeps elements in order through pointers. Can it be searched faster than O(n)? Why or why not?

---

**Continue → [Why Binary Search Exists](09-why-binary-search-exists.md)**
