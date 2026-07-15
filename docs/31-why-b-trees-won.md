# Designed for the Disk

## The Problem

Chapter 30 established that indexes need to minimize disk page reads, not comparisons. A binary search tree does this by binary search — each comparison halves the remaining candidates. With 50 million entries, log₂(50,000,000) ≈ 26 levels deep. Every level is a pointer chase to a new node. Every node is a random location on disk.

The problem: a well-designed BST uses 16–64 bytes per node (two child pointers, one key, one value pointer). A disk page is 4,096 bytes. A single disk read fetches 4,096 bytes, but a BST only uses 16–64 of them — the rest is wasted. Worse, the 26 levels of the tree require 26 sequential disk reads, each to a different random disk location. At 5ms per random disk read: 130ms per query. With 200 concurrent queries: 26 seconds of disk I/O per query in aggregate.

Any solution must:

- Use disk pages efficiently — one page read should deliver many useful keys
- Keep tree height low (fewer pages read per query)
- Support range queries (traverse in-order without excessive seeking)
- Maintain balance automatically as keys are inserted and deleted

## What Would You Try?

Before reading on:

- If a disk page holds 4KB and one key is 8 bytes, how many keys fit in one node if you pack them as tightly as possible?
- As you put more keys per node, how does tree height change for the same number of total keys?
- A BST with 50 million nodes is 26 levels deep. A tree where each node holds 500 keys would be how many levels deep?

## Failed Attempts

### Attempt 1: Cache the Entire BST in RAM

If the tree fits in RAM, there are no disk reads — pointer chases cost nanoseconds instead of milliseconds. For 10 million keys at 64 bytes each: 640MB. Feasible on modern servers.

This is the approach Redis takes for sorted sets (using a skip list) and what in-memory databases do. It works as long as your data fits in RAM. But a database managing 10TB of data has 10TB of index — it cannot fit in RAM. Even if today's working set fits, data grows. The in-memory approach defers the problem; it doesn't solve it. And it adds a failure mode: a server restart loses all in-memory index state, requiring a cold rebuild from disk.

### Attempt 2: Wide BST With Larger Nodes

Keep the BST structure but make nodes larger — one node = one disk page (4KB). Pack as many keys as fit: 4096 / 8 bytes ≈ 512 keys per node. Use binary search within each node to find the right child pointer. Tree height for 50 million keys with branching factor 512: log₅₁₂(50,000,000) = log(50M)/log(512) ≈ 3 levels. Three disk reads per query.

But a BST node with 512 keys has 513 child pointers. To maintain BST ordering, every one of those 513 subtrees can have any number of keys. When you insert a key and the root node is "full" (all 512 keys used), where does the new key go? The BST structure has no rule for splitting a node. You'd need to restructure the tree, invalidating 512 stored child pointers. The wide node idea is right, but BST balancing rules don't extend naturally to nodes with hundreds of keys.

### Attempt 3: B-Tree But Storing Data in All Nodes

A proper B-tree keeps keys and data in internal nodes as well as leaves. Each internal node holds some keys and their associated values, plus child pointers for keys that fall between them. This preserves the B-tree balancing invariant (each node is at least half full; split when full).

But storing data in internal nodes wastes page space on rarely-accessed keys. Internal nodes are traversal nodes — most queries pass through them without retrieving data from them. If each key–value pair is 64 bytes and each page is 4KB, an internal node holds 64 entries: branching factor 64, requiring log₆₄(50M) ≈ 3.5 ≈ 4 levels. If you store only 8-byte keys (no values) in internal nodes and 64-byte key–value pairs only in leaves, branching factor increases to 512 and height drops to 3 levels. Fewer levels = fewer disk reads = faster queries. Storing data in all nodes (the original B-tree) sacrifices this optimization.

## The Discovery

In-memory trees bypass disk but can't scale to data larger than RAM. Wide BST nodes lack the balancing rules for graceful splits. B-trees storing data in internal nodes waste internal node space on values that traversal doesn't need.

The winner separates structure from data: **B+ tree**. Internal nodes hold only keys (for routing) and child pointers. Leaves hold key–value pairs (or key–row-pointer pairs for secondary indexes). All leaves are linked in a doubly-linked list.

The consequences of this design:

- Internal nodes pack ~512 keys per 4KB page (8-byte keys), giving branching factor 512.
- log₅₁₂(50,000,000) ≈ 3 levels. Three disk reads per point query.
- Leaf nodes link left-to-right. A range query finds the left endpoint in 3 reads, then follows leaf pointers — sequential reads, which disk (and SSD prefetch) handle efficiently.
- Balancing: when a node overflows (too many keys), split it in half and push the median key up to the parent. If the parent overflows, repeat. Splits propagate upward but are rare in practice: a node splits only when it's completely full, and after splitting both halves are 50% full — they won't split again until they've received ~n/2 more keys.

Why it "won": PostgreSQL, MySQL (InnoDB), Oracle Database, SQL Server, SQLite, and virtually every filesystem (NTFS, ext4, HFS+, APFS) use B+ trees. Not because of theoretical optimality — LSM trees outperform B+ trees for write-heavy workloads — but because B+ trees handle the mixed read-write workload of most databases well, support range queries, and have predictable worst-case performance.

## Try It

<iframe src="../assets/browser/chapter31/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter31/index.html)

Before changing anything, predict:

- Insert keys 1–15 into a B+ tree with max node size 4. Watch when splits happen. Does the root ever split?
- How does tree height change as you insert from 16 to 64 keys with node size 4? From 64 to 256?
- For a range query covering 30% of inserted keys, how many nodes does the tree visit vs. a full scan?

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter31/index.html` (shared helpers in `browser/common/sim.js`). The sim is a schematic of depth and fan-out, not a full B+-tree implementation — `bstDepth(n)` computes `ceil(log₂(n+1))` for the BST side, and `btreeDepth(n)` computes `ceil(log_FANOUT(n+1))` for the B-tree side. The `FANOUT` slider (2–8) redraws both panels live; `drawBST()` and `drawBtree()` visualise the resulting page-chunked layout. A real B+-tree also splits nodes on overflow and maintains a leaf linked-list for range scans — this sim shows the depth savings that motivate those mechanisms.

## When It Breaks

**Write amplification on SSDs.** SSDs have a minimum write unit (page, 4KB) and erase unit (block, 128–512KB). A B+ tree update to one 4KB node triggers reads of the surrounding block, modification, and a write of the entire block. A single key insert can require erasing and rewriting 128KB. At high write rates, this "write amplification" wears out SSD cells and causes unpredictable latency spikes when garbage collection runs. LSM trees (Log-Structured Merge trees, used in RocksDB and Cassandra) address this by making writes sequential — always appending — at the cost of slower reads (must merge multiple sorted layers).

**Fragmentation on delete-heavy workloads.** When many keys are deleted, B+ tree pages become underfull (below 50% capacity). A leaf node with one entry still occupies a full 4KB page. Over time, pages that were densely packed become half-empty. Storage utilization drops. A 100GB database after a large delete operation may have 60GB of actual data in 100GB of pages. `VACUUM` in PostgreSQL and `OPTIMIZE TABLE` in MySQL rebuild the B+ tree, packing pages to high fill factors — but this is expensive and requires downtime or careful scheduling.

**Range query performance on SSDs vs. HDD.** The B+ tree's linked leaf traversal is optimized for sequential disk reads, which HDDs do cheaply (no seek between adjacent sectors). On SSDs, sequential and random reads have more similar latency. This makes LSM trees more competitive on SSDs — LSM's sequential-write design pairs well with SSD's sequential-read strength, while the B+ tree's advantage (sequential leaf traversal) is less distinct.

## Transfer

- **Filesystems.** The HFS+ and APFS filesystems use B-trees to store directory entries. `ls /some_dir` with 100,000 files is a B-tree range scan, not a linear directory scan. Ext4 uses a hash-tree for directories but a B-tree for the journal and extent tree.
- **InnoDB clustered index.** MySQL's InnoDB stores the entire table in a B+ tree sorted by primary key. The leaf nodes of the primary key B+ tree contain the full row data (not a pointer to a row). Secondary indexes store (secondary_key, primary_key) in their leaves. This means a secondary index lookup requires two B+ tree traversals: one for the secondary index, one for the primary key (the "double dip").
- **Write-optimized alternatives.** Fractal tree indexes (used in TokuDB/Percona): like B-trees but with message buffers in internal nodes that absorb writes. Writes are fast because they're buffered; the buffer is flushed lazily to lower levels. Reduces write amplification vs. B+ trees at the cost of more complex code.

Try these:

1. Implement a B+ tree with order 3 (max 3 keys per node) supporting insert and range search. Verify that after inserting 20 random keys, the tree is always balanced (all leaves at the same depth).
2. A database page is 8KB. Keys are 8 bytes, child pointers are 6 bytes, and the header takes 100 bytes. How many keys fit in an internal node? What is the tree height for 1 billion keys?
3. What is a "page split" and why is it expensive? How does a fill factor of 80% (instead of 100%) reduce split frequency in a B+ tree under sequential insert workloads?

---

**Continue → [Why Transactions Exist](32-why-transactions-exist.md)**
