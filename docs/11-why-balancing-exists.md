# When the Tree Grows Only to the Right

## The Problem

You've built a BST (chapter 10). During testing, with random data, it's fast — O(log n) for everything. You ship it. In production, user IDs are auto-incrementing integers: 1, 2, 3, 4, ... They arrive in sorted order.

Your BST receives 1, then 2 goes right of 1, then 3 goes right of 2, then 4 goes right of 3. After 1 million insertions the tree is a million-node chain extending entirely to the right. Search depth: 1,000,000 comparisons instead of 20. The "tree" is a linked list.

The visceral cost: a production database index built on a BST with auto-increment primary keys degrades silently. First week: queries take microseconds. One year later: the same queries take seconds. No error, no crash — just slow death.

Any solution must:

- Guarantee O(log n) height regardless of insertion order
- Maintain the BST property throughout (all left descendants < node < all right descendants)
- Fix imbalance automatically during insert and delete — no manual rebuilding
- Keep the repair work itself cheap — O(log n) per operation

## What Would You Try?

Before reading on:

- A tree with n nodes has minimum height ⌈log₂(n+1)⌉ and maximum height n. What separates the minimum from the maximum case?
- If after every insert you checked the tree and rebuilt it from scratch in sorted order (like building a BST from a sorted array), that's O(n) per insert. Too slow — but what's the core idea?
- Instead of rebuilding the whole tree, could you fix just the part that became imbalanced?

## Failed Attempts

### Attempt 1: Rebuild from Scratch Periodically

Every thousand insertions, collect all values (in-order traversal), sort them, and rebuild a perfectly balanced BST. This gives perfect balance — for a moment. Then the next thousand insertions skew it again. Average depth is O(log n) over time, but individual queries can hit O(n) if they land just before a rebuild. Also: the rebuild is O(n) work every thousand operations — amortized O(log n) but with unpredictable latency spikes. Unacceptable for a database.

### Attempt 2: Track Balance Factor, Rebuild the Offending Subtree

After each insert, compute how unbalanced the tree is. If any node has left-subtree height minus right-subtree height exceeding some threshold, rebuild just that subtree. This limits the repair scope. But rebuilding a subtree of size k is O(k) — and the offending subtree might be the entire tree. Worst case: same as Attempt 1.

The deeper issue: rebuilding loses the existing structure entirely. You're creating nodes fresh from a sorted list. Any references to the old nodes are invalidated. Databases with live readers can't do this.

### Attempt 3: Local Surgery — Rotations

Instead of rebuilding, ask: can we fix imbalance with a small *local* rearrangement that preserves the BST property?

Consider: root A has right child B. B's right subtree is larger than A's left subtree — the tree leans right. Rotate A left: B becomes the new root, A becomes B's left child, and B's old left subtree becomes A's right child. The BST property is preserved (A is still less than B; B's old left subtree is between A and B). And this took O(1) pointer changes.

One rotation might not fix the whole tree, but if you apply rotations after every insert, tracing up from the insertion point to the root, you can maintain balance throughout.

## The Discovery

Attempt 1 and 2 showed that rebuilding is too expensive. Attempt 3 — rotations — is the key: **O(1) operations that locally fix imbalance while preserving the BST property**.

An **AVL tree** (Adelson-Velsky and Landis, 1962, the first self-balancing BST) maintains a **balance factor** at each node: height(right subtree) − height(left subtree). It requires this to be −1, 0, or +1 at all times. After every insert or delete, it walks up the tree from the modified point, updating balance factors. When it finds a node with balance factor ±2 (too skewed), it applies one or two rotations to restore balance.

There are four cases, each requiring 1–2 rotations:
- Left-left imbalance: single right rotation
- Right-right imbalance: single left rotation
- Left-right imbalance: left rotation then right rotation
- Right-left imbalance: right rotation then left rotation

Each rotation is O(1). At most O(log n) rotations per insert (one per level as you walk up). Total cost per insert: O(log n). Height is guaranteed ≤ 1.44 log₂(n) — always O(log n).

**Red-black trees** (used in most standard library implementations) use a two-coloring invariant instead of height tracking. They're slightly less balanced in the worst case but require fewer rotations per insert on average — better for insert-heavy workloads.

The key principle: fix imbalance *locally* and *continuously*, never let it accumulate.

## Try It

<iframe src="../assets/browser/chapter11/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter11/index.html)

Before changing anything, predict:

- Insert 1 through 10 in order into an unbalanced BST vs an AVL tree. What does each look like?
- What triggers a rotation? Watch for which insertion causes the first one.
- After 100 insertions in sorted order, what's the height of each tree?

## Implementation

The working model is dependency-free JavaScript that runs entirely in your browser — nothing to install. Open `browser/chapter11/index.html` to read or modify it (shared UI helpers live in `browser/common/sim.js`). Look for the `rotate` function and the balance-factor check that triggers it — those two pieces together are what keeps the AVL tree's height bounded while the plain BST beside it degenerates into a chain.

## When It Breaks

**Rotations invalidate concurrent readers.** A rotation changes which node is the root of a subtree — a structural change, not just a value change. Any thread concurrently reading that subtree may traverse a stale pointer into wrong territory. This is why concurrent balanced trees (like Java's `ConcurrentSkipListMap`) use lock-free algorithms, not simple AVL trees. Red-black trees in databases use coarse-grained write locks during rebalancing.

**Cascading rotations on delete.** Deleting a node from an AVL tree can require O(log n) rotations — one per level back to the root. Red-black trees guarantee at most 3 rotations per delete, which is why they're preferred over AVL in insert-delete-heavy workloads. This is a real practical difference in database index maintenance.

**B-trees for disk.** AVL and red-black trees are optimized for RAM, where any node access is fast. On disk, each node access is an I/O operation — expensive. B-trees (chapter 32) are the balancing solution for disk: each node holds many keys, so the tree is very wide and very short. A 4-level B-tree can hold billions of keys with at most 4 disk reads per search. PostgreSQL, MySQL, SQLite all use B-trees for indexes, not AVL or red-black trees.

## Transfer

- **`std::map` / `TreeMap` / `SortedDictionary`** in every major language are red-black trees. They give O(log n) insert/delete/lookup with sorted iteration, used wherever order matters.
- **Linux's completely fair scheduler** uses a red-black tree keyed by virtual runtime. Tasks are always runnable in O(log n) insert/remove, and the minimum-key node (next to run) is O(1) to retrieve. The scheduler runs millions of times per second — it must be fast.
- **Git's packfile index** uses a sorted, binary-searched structure (similar in spirit to balanced tree) to find object offsets in O(log n). Every `git log`, `git diff`, and `git status` touches this structure.

Try these:

1. An AVL tree has balance factor constraint |height(left) - height(right)| ≤ 1. A 2-3 tree requires all leaves at the same depth. How do these invariants differ, and what does each guarantee?
2. Write the pseudocode for a left rotation. Then trace through what happens to the BST property: if A < B and B has left child T (where A < T < B), where does T go after the rotation? Does the BST property hold?
3. A red-black tree has the property that every path from root to leaf has the same number of black nodes. Why does this guarantee O(log n) height? (Hint: consider the longest possible path.)

---

**Continue → [Why Hashing Exists](12-why-hashing-exists.md)**
