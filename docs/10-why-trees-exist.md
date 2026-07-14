# The Sorted Array That Couldn't Keep Up

## The Problem

Binary search (chapter 9) achieves O(log n) lookup on a sorted array. You've built a fast search system. Then the requirements change: records arrive continuously, and you need to insert each new one while keeping the array sorted for future searches.

Inserting into a sorted array is O(n): you find the right position (O(log n) with binary search), then shift every element after it forward to make room. With 10 million records and 1,000 insertions per second, each insertion shifts on average 5 million elements. The server can't keep up.

You try keeping a separate unsorted "inbox" for new arrivals and merging periodically — but now searches must check both structures. You try rebuilding the sorted array from scratch nightly — but daytime searches miss today's insertions. Every fix creates a new problem.

The visceral cost: sorted arrays give you fast search *or* fast updates, but not both simultaneously. As soon as data changes, sorted arrays make you choose.

Any solution must:

- Find any element in O(log n) time
- Insert any element in O(log n) time
- Delete any element in O(log n) time
- Maintain its properties automatically after each operation, with no rebuilding

## What Would You Try?

Before reading on:

- A phone directory is sorted by name. When a new entry arrives, what's the cost of inserting it? What would need to change about the *physical structure* to make inserts cheap?
- What if instead of one big sorted list, you broke it into many smaller sorted lists connected by "next bigger" pointers?
- Can you think of a structure where each element "owns" a region and sub-delegates to smaller structures?

## Failed Attempts

### Attempt 1: Sorted Linked List

A linked list maintains sorted order without contiguous memory: each node holds a value and a pointer to the next. Insertion is O(1) once you know *where* to insert (just update pointers). No shifting required.

But finding *where* to insert requires traversal: scan from the head until you find the right position, O(n). And search is also O(n) — no random access means no binary search. You've fixed inserts but broken search. Sorted linked lists have the worst of both worlds: no contiguous-memory random access, so no binary search; pointer indirection on every step, so poor cache behavior.

### Attempt 2: Hierarchical Sorted Lists (Skip List)

Add a "fast lane" — an extra level of pointers that skip over multiple elements. A node at the fast lane points to an element far ahead. Traversal at the fast lane skips large portions, then drops down to detail level. Add more levels for bigger skips.

This actually works and achieves O(log n) expected time. But it requires probabilistic balancing (each level has each element with probability 1/2), and the expected vs worst-case gap matters. More importantly, it's a workaround — it recreates binary search's halving behavior through multiple layers of pointers, rather than making the core structure directly support halving.

### Attempt 3: Embed the Binary Search Decision Into the Structure

In binary search, the decision at each step is: "is target less than, equal to, or greater than this element?" What if each element were itself a decision point, and its structure encoded "go left if smaller, go right if larger"?

Build a structure where each node has a value, a left child (all values less), and a right child (all values greater). This is the key insight — the binary search decision *becomes* the data structure.

## The Discovery

Attempt 1 (sorted linked list) eliminated shifting but lost random access. Attempt 2 (skip list) adds layers to recover search speed but is complex and probabilistic. Attempt 3 embeds the binary search logic into the nodes themselves — and this is exactly a **Binary Search Tree (BST)**.

A BST is a structure where each node stores a value and has at most two children. **BST property**: all values in the left subtree are less than the node's value; all values in the right subtree are greater.

- **Search**: start at root, go left if target < current, right if target > current, repeat. At each step, half the remaining tree is eliminated. O(depth) comparisons.
- **Insert**: search for where the new value would be. When you "fall off" a null child, that's where it goes. O(depth) comparisons, then one pointer assignment. No shifting.
- **Delete**: more complex (three cases: leaf, one child, two children), but O(depth).

If the tree is balanced — every node's left and right subtrees have similar size — then depth = O(log n), giving O(log n) for all operations.

The problem: insertion order determines shape. Insert 1, 2, 3, 4, 5 in sorted order and the tree degenerates into a linked list (every node goes to the right). Depth becomes O(n). The next chapter (11) solves this. This chapter's lesson: the BST gets the *structure right*; the next chapter gets the *balance*.

## Try It

<iframe src="../assets/browser/chapter10/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter10/index.html)

Before changing anything, predict:

- Insert values 1 through 10 in order. What shape does the tree take? What's the search depth for value 10?
- Insert the same values in random order. How does the shape differ?
- Delete a node with two children. What must happen to maintain the BST property?

## Implementation

The working model is dependency-free JavaScript that runs entirely in your browser — nothing to install. Open `browser/chapter10/index.html` to read or modify it (shared UI helpers live in `browser/common/sim.js`). Look for the recursive `insert` function that walks left or right at each node — that single conditional is the BST property, and watching the tree's shape diverge between sorted and random insertion orders is the chapter's core lesson.

## When It Breaks

**Degenerate insertion order.** Inserting already-sorted data into a BST produces a linked list. Search becomes O(n). This is not a theoretical concern — any real system receiving sorted data (timestamps, auto-incrementing IDs, alphabetically sorted imports) will degenerate. PostgreSQL's B-tree indexes handle this through rebalancing; a plain BST doesn't.

**No in-order traversal guarantee for deletion.** Delete and reinsert has the same problem: if you always replace a deleted node with its in-order successor, the tree skews right over time. Unbalanced BSTs in production are a common source of "why is this query suddenly slow" incidents.

**Concurrency.** BST operations touch multiple nodes. Inserting a new node requires modifying the parent's pointer. If another thread reads the parent at the same moment, it sees an inconsistent state. Concurrent BSTs require careful synchronization — a topic tree-based databases spend significant engineering on.

## Transfer

- **File systems (HFS+, ext4 directories).** Large directories store entries in a tree sorted by filename. Finding a file in a directory with 100,000 entries is O(log n), not O(n).
- **`std::map` / `TreeMap` in Java.** These are balanced BSTs (usually red-black trees). O(log n) for all operations, ordered iteration "for free" since in-order traversal visits elements in sorted order.
- **Expression trees.** Arithmetic expressions like `(3 + 4) * 5` are naturally represented as trees: `*` at root, `+` as left child with children `3` and `4`, `5` as right child. Compilers parse code into abstract syntax trees (ASTs) — trees for the same reason.

Try these:

1. What's the in-order traversal of a BST? What sequence of values does it produce, and why?
2. If you insert n random values into a BST, what's the expected height? (It's O(log n) in expectation for random data — why doesn't this solve the worst-case problem?)
3. Design a BST-based set that supports: insert, delete, "find the smallest element greater than X" (successor query). How do you implement successor efficiently?

---

**Continue → [Why Balancing Exists](11-why-balancing-exists.md)**
