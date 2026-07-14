# The Shortcut That Makes Databases Fast

## The Problem

An e-commerce database has 50 million orders. A customer service agent queries: "Find all orders from user 847213." Without any special structure, the database reads every one of the 50 million rows, checks if `user_id = 847213`, and returns the matches. At 1 microsecond per row check, that's 50 seconds per query. With 200 agents running concurrent queries, the database is perpetually 10,000 seconds behind.

The data is on disk in insertion order — there's no particular reason order #50,000,001 is near orders for user 847213. Reading in insertion order to find a specific user is like searching a phone book by birth year to find someone's number.

Any solution must:

- Reduce query time from O(n) to something sub-linear
- Not require the underlying table to be reordered
- Allow multiple indexes on different columns (user_id, order_date, status, amount)
- Stay consistent when rows are inserted, updated, or deleted

## What Would You Try?

Before reading on:

- If you sorted all orders by user_id, how quickly could you find user 847213's orders? What algorithm would you use?
- Sorting the table reorders every row. What's a cheaper structure that stores user_id → row location without moving the actual rows?
- If the same user_id appears in 10,000 orders, what does your index return? A single location or many?

## Failed Attempts

### Attempt 1: Keep the Table Sorted by the Query Column

Sort all rows by user_id. Now binary search finds user 847213 in O(log n) comparisons — about 26 comparisons for 50 million rows. Fast.

Problem 1: the table can only be sorted one way. A query on user_id is fast; a query on order_date or status is still O(n). You have dozens of queryable columns. Problem 2: insertions destroy sorted order. Inserting order #50,000,001 for user 3 requires shifting all rows with user_id > 3 down by one position — O(n) work per insert. At 10,000 orders per minute, this is catastrophically slow. Keeping the table physically sorted is only viable for read-only data with one query pattern. Real tables are neither.

### Attempt 2: Hash Map from Column Value to Row ID

Build an in-memory hash map: `{847213: [row_id_1, row_id_2, ...], ...}`. Lookup is O(1) average. Insert adds to the list; delete removes from it.

Hash maps require the entire index to fit in RAM. A hash index on user_id for 50 million rows: 50 million entries × 8 bytes per pointer = 400MB — feasible for one index. But five indexes × 400MB = 2GB, plus the actual table data. More importantly, hash maps can't answer range queries. "All orders where amount > $500" has no O(1) or O(log n) answer in a hash map — you'd have to iterate every key. Database query patterns include range queries (dates, amounts, ages) constantly. A pure hash index is the wrong structure.

### Attempt 3: Separate Sorted File for Each Index

For each indexed column, maintain a separate sorted file of (column_value, row_location) pairs. Binary search on the sorted file finds the target value, then fetch the actual row by location. Multiple such files = multiple indexes on different columns.

This is conceptually right — this is what a B-tree index is, more or less. But a plain sorted file has the same insert problem as Attempt 1: inserting a new (value, location) pair in sorted order requires shifting half the file on average. And files have pages: reading a sorted file with binary search requires O(log n) page reads, and each page read may be a disk I/O. For large indexes, the number of disk reads per query determines performance — not the number of comparisons. A binary search on a file with one entry per page requires log₂(50,000,000) ≈ 26 disk reads per query. That's 26 × 5ms = 130ms per query on spinning disk. Not fast enough.

## The Discovery

Sorting the table breaks inserts. In-memory hash maps can't handle ranges or large data. Sorted files have expensive inserts and too many disk reads.

The constraint that sorted files violate is the disk I/O model: each page read costs ~5ms on disk (or ~0.1ms on SSD). Minimizing page reads is the dominant concern, not minimizing comparisons. The solution changes the data structure to minimize pages touched, not comparisons made.

**B-tree index**: a balanced tree where each node is exactly one disk page (4–16KB) and contains many keys (dozens to hundreds per page). A search traverses the tree from root to leaf — typically 3–4 levels for 50 million rows — reading one page per level. Total disk reads: 3–4. At 5ms per disk read: 15–20ms per query regardless of table size.

Insert: find the correct leaf, insert the new key. If the leaf is full, split it into two leaves and insert the median key into the parent. Splits propagate upward but are rare (O(log n) per key in the amortized case). Insert cost: 3–4 page reads + 1 page write. Consistent.

Range query: find the left endpoint in O(log n) page reads, then follow leaf-level "next" pointers through contiguous leaf pages. Range traversal costs only as many page reads as there are matching entries, not log n per entry.

The formal name: **B+ tree** (the variant where all data is in leaves, internal nodes hold only keys for routing). Every major database engine — PostgreSQL, MySQL/InnoDB, Oracle, SQL Server — uses B+ trees as the default index structure.

## Try It

<iframe src="../assets/browser/chapter30/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter30/index.html)

Before changing anything, predict:

- With 1 million rows and no index, how many rows does the simulation scan for a single-value query? With a B-tree index?
- Insert 100 rows one at a time. Does the B-tree stay balanced? What operations maintain balance?
- Run a range query covering 10% of values. How many pages does the B-tree touch compared to a full scan?

## Implementation

The full model is ~160 lines of dependency-free JavaScript — open `browser/chapter30/index.html` (and the shared helpers in `browser/common/sim.js`) to read or modify it. Everything runs in the browser; nothing to install. Look for the `BTreeIndex` class: each node stores up to `order` keys and child pointers. The `search(key)` and `rangeSearch(lo, hi)` methods show the path through the tree with the number of nodes visited highlighted at each step.

## When It Breaks

**Index bloat slows writes.** Every insert into a table with 5 indexes requires 5 index updates. A bulk load of 10 million rows into a table with 5 indexes updates 50 million index entries. Standard practice: drop all indexes before bulk load, reload, then rebuild. MySQL's `DISABLE KEYS` / `ENABLE KEYS` does exactly this. Rebuilding a large index after load is faster than maintaining it incrementally during load because sorted bulk insertion (B-tree build) is O(n log n) vs. O(n log n) random inserts, but with far better cache behavior and no split-propagation overhead.

**Index selectivity and cardinality traps.** An index on a boolean column (true/false) with 50 million rows means ~25 million rows per value. The query planner (chapter 34) may choose *not* to use this index: reading 25 million index entries, then fetching 25 million table rows by pointer, is often slower than a full table scan (which reads contiguously). Low-cardinality indexes on large tables can make queries slower if the planner uses them incorrectly. `EXPLAIN` output showing an index scan with high row estimates is a warning sign.

## Transfer

- **Full-text search indexes (Elasticsearch, PostgreSQL `tsvector`).** Instead of indexing column values, index individual words in text. The "inverted index" maps each word to the list of documents containing it. It's a B-tree (or hash) where the key is a word and the value is a posting list. Used by every search engine.
- **Composite indexes and column ordering.** A composite index on `(user_id, order_date)` can answer queries on `user_id` alone or `(user_id, order_date)` together, but not on `order_date` alone. The first column in the index must appear in the query's WHERE clause. This ordering matters for index design.
- **Covering indexes.** An index that includes all columns a query needs can answer the query entirely from the index, never touching the table. PostgreSQL calls this an "index-only scan." A query `SELECT order_date FROM orders WHERE user_id = 847213` with a `(user_id, order_date)` index reads only index pages.

Try these:

1. Build a B+ tree from scratch supporting insert, search, and range query. Start with order (max keys per node) = 3 for easy visualization. Verify it stays balanced after 20 random inserts.
2. An index on `email` in a users table has 10 million unique values. An index on `country` has 200 unique values, with an average of 50,000 rows per country. For the query `WHERE country = 'US'`, should the database use the index? Explain the tradeoff.
3. What is an index "fill factor"? Why would you set it to 70% instead of 100%? When does it matter?

---

**Continue → [Why B-Trees Won](31-why-b-trees-won.md)**
