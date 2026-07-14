# The Inevitable Tax of Not Knowing Where Things Are

## The Problem

A small-town library has 200 books arranged in the order they were donated — no system, no catalog, no shelving logic. A patron wants "A Tale of Two Cities." The librarian must walk the shelves and read each spine until they find it.

200 books: manageable, maybe 10 minutes. Now the library receives a donation and grows to 20,000 books, still in arrival order. Finding any book now takes on average 10,000 inspections. The library is technically functional — every book is findable — but practically unusable.

The visceral cost: a database with 10 million unsorted rows. "Find the customer named Garcia" means scanning 10 million records. At 1 million records/second, that's 10 seconds per query. With 1,000 users querying simultaneously: the server spends 10,000 seconds of CPU time per second of wall time. It cannot keep up.

Any solution must:

- Find a specific item without examining every other item
- Scale gracefully — doubling the collection shouldn't double search time
- Work correctly even when the item doesn't exist (must confirm absence, not just find presence)
- Handle arbitrary query keys, not just ones known at design time

## What Would You Try?

Before reading on:

- The library books are in a box, one by one. You're looking for a specific title. How many books do you open on average?
- What if you knew the book was definitely in the first half of the box? How would that change things?
- What would you need to know about the collection in advance to skip some inspections?

## Failed Attempts

### Attempt 1: Random Sampling

Instead of checking every item, check a random subset. If 1% of books are Dickens, checking 100 random books will probably find one. But this is probabilistic search, not deterministic search. For "find this *specific* title," sampling fails: you might sample 1,000 books and never hit the right one even though it exists. Correct search requires certainty. Sampling is for statistical questions, not retrieval.

### Attempt 2: Parallel Search (Multiple Librarians)

Send 10 librarians to search 10 sections simultaneously. This reduces wall-clock time by 10×. With 100 librarians, 100×. But it doesn't change the fundamental cost — the total work (number of books inspected) is the same. You've traded time for labor. For software: multiple CPU cores don't reduce total memory accesses. And linear search with 1,000 cores on 1,000,000,000 items still means each core scans 1,000,000 items. Parallelism is a multiplier on speed, not a change in algorithmic complexity.

### Attempt 3: Eliminate Early by Negative Information

If you know "all Dickens books are in boxes 1–30," you can skip boxes 31–200 when looking for Dickens. More structure = more skippable regions. This is promising — the question is: what structure eliminates the most work per fact known?

The most powerful version: if you know the collection is *sorted*, knowing the item is "less than the midpoint" eliminates the entire upper half. That's not 10 boxes skipped out of 200 — it's 100 boxes skipped with *one comparison*.

## The Discovery

Attempt 1 (sampling) fails because search requires certainty. Attempt 2 (parallelism) reduces time but not total work. Attempt 3 reveals the key: structure that lets us *skip large regions* based on a single test.

Linear search — examining elements one by one — is the baseline. It works on *any* collection regardless of structure. Its cost: **O(n)** comparisons in the worst case and on average (for uniform random key distribution). In a collection of n items, you examine n/2 items on average.

This is unavoidable without additional structure. If the collection has no organization, every item is equally likely to be the target at any position. You must check each one. The **lower bound for search on an unordered collection is Ω(n)** — no algorithm can do better in general.

The formal insight: search time is proportional to how much of the collection you must examine before you can make a definitive conclusion. Linear search must examine all items before concluding "not found." Any faster search requires structure that lets you conclude "not in this region" without checking every item in the region.

This chapter establishes the baseline. The next chapters establish what structure buys you — and how much.

## Try It

<iframe src="../assets/browser/chapter07/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter07/index.html)

Before changing anything, predict:

- Double the collection size. What happens to average search time?
- Search for an item that doesn't exist. How many comparisons does that require vs finding an item at the end?
- What's the best case for linear search, and how often does it occur in practice?

## Implementation

The working model is dependency-free JavaScript that runs entirely in your browser — nothing to install. Open `browser/chapter07/index.html` to read or modify it (shared UI helpers live in `browser/common/sim.js`). Look for the scan loop that increments a comparison counter on every element it inspects — that single counter is what makes the O(n) cost concrete and measurable.

## When It Breaks

**The baseline is unavoidable for truly unordered data.** Full-text search on a set of documents with no index must scan every document. `grep` without preprocessing is O(n × m) where n is documents and m is document length. This is why search engines maintain inverted indexes — they pay a one-time structuring cost to make all future searches faster.

**Linear search excels for tiny n.** For collections of 5–20 items, linear search often beats binary search in practice because it has no setup cost, no branch mispredictions, and excellent cache behavior (sequential memory access). The standard library `std::find` in C++ is linear search — because for small vectors, it's faster than alternatives despite worse asymptotic complexity.

**Searching the wrong thing.** If your keys are compound (searching for a customer by first name AND last name AND account number), linear search can still be faster than a complex index. The break-even point depends on data size and query frequency.

## Transfer

- **`grep`** is linear search on text. No index, no structure — it reads every line. For a 10GB log file, that's slow. For a 1KB config file, it's the right tool.
- **Port scanning.** Checking whether a network port is open is linear search: try port 1, try port 2, ... try port 65535. Tools like `nmap` make it parallel, but it's still fundamentally O(n).
- **Spam filters (before ML).** Early spam filters linearly scanned emails against a blacklist of keywords. As blacklists grew, they switched to hashing (chapter 12) to get O(1) lookup per word.

Try these:

1. You have a 10-element array and must find a specific value. What's the maximum number of comparisons? The minimum? The expected value if the item is equally likely to be anywhere?
2. Linear search on a linked list vs an array: same number of comparisons, but different constant factors. Why? What does this suggest about when to prefer each?
3. A "sentinel" value places the search target at the end of the array before searching, eliminating the end-of-array check on each iteration. How does this reduce constant factors, and does it change O(n)?

---

**Continue → [Why Ordering Helps](08-why-ordering-helps.md)**
