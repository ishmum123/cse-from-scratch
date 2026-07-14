# When the Filing Cabinet Breaks Down

## The Problem

A hospital stores patient records as files: one file per patient, named by ID. Finding patient 10042's file is instant — open `10042.txt`. But now a doctor needs "all patients over 65 who were prescribed metformin in the last 6 months." There's no file for that. There's no index. The only way is to open every patient file, read every record, and check each one. With 2 million patients, that's 2 million file opens and reads. At 1ms per file access, that's 33 minutes per query.

Now add concurrent access: 200 doctors query simultaneously, the billing system runs nightly batch updates, and a pharmacist adds new prescriptions in real-time. Files don't have locks per record — only per file. If the billing system locks the entire patient database file, no doctor can access any patient record for hours. If files aren't locked, two nurses simultaneously updating the same patient's record corrupt it.

Any solution must:

- Support queries on arbitrary combinations of fields, not just by filename
- Allow concurrent reads and writes at record granularity (not file granularity)
- Ensure partial writes don't corrupt records (crash-safety)
- Scale to millions of records without requiring full scans

## What Would You Try?

Before reading on:

- If you store all patients in one large CSV file, what's the cost of finding all patients in a given city? How does it change with record count?
- A write to a file is not atomic — the OS may crash mid-write. How would you detect and recover from a half-written patient record?
- If two processes both read a patient's balance, add 100, and write back, what's the minimum structure needed to prevent a lost update?

## Failed Attempts

### Attempt 1: One File Per Record, Directories as Indexes

One file per patient (already tried). Add directories as indexes: a directory `city/Seattle/` contains symlinks to all Seattle patients. A directory `age/65+/` contains symlinks to patients over 65. Query "Seattle patients over 65": intersect the two directories' contents.

Symlinks per patient per index attribute: at 2 million patients and 20 queryable attributes, 40 million symlinks. Adding a new index requires scanning all 2 million records. Updating a patient's city requires finding and updating every symlink. Multi-attribute queries (city AND age AND medication) require filesystem set-intersection operations that the OS doesn't provide. You re-implement a database using the filesystem, badly. Crash mid-update: symlink points to wrong patient, or symlink exists for a patient record that was half-written. The filesystem has no concept of multi-step atomic operations.

### Attempt 2: Append-Only Log File with In-Memory Index

Store all records as JSON lines in an append-only file. On startup, read the entire file to build an in-memory hash map (patient ID → file offset). Query by ID: look up offset in hash map, seek to that offset, read the record.

Append-only handles crash safety: incomplete writes at the end are detectable (truncated JSON). The hash map enables O(1) lookup by ID. But: range queries ("patients over 65") require scanning the entire in-memory hash map and sorting — O(n) again. The in-memory index is lost on restart (must re-read the whole file). The file grows forever (old versions of updated records are never removed without compaction). And the in-memory index limits the database to records that fit in RAM — a fundamental constraint.

### Attempt 3: Fixed-Width Records in a Binary File with Sequential Scan

Store records as fixed-width 512-byte structs in a binary file. Record N starts at byte N × 512. Lookup by ID: seek to byte ID × 512, read 512 bytes. O(1) lookup by numeric ID.

This is fast for ID-based lookup and enables binary search on sorted files. Crashes during write corrupt at most one record (partial 512-byte write). But: field queries still require sequential scan. Fixed width means either wasting space (padding short values) or silently truncating long ones. Adding a new field requires a migration that rewrites the entire file. Concurrent writes: if two processes both write record 42, they corrupt each other — there's no mechanism for record-level locking within the file.

## The Discovery

Directory symlinks are brittle, don't support multi-attribute queries, and lack atomic multi-step updates. Append-only logs handle crash safety but leave queries at O(n). Fixed-width records enable O(1) lookup but can't handle arbitrary queries or schema evolution.

Each attempt solves one problem and creates another. The pattern: files are a byte-stream abstraction. The operations they support natively — read, write, seek — are too primitive for structured data queries. A database is a specialized storage system that adds several layers above raw files:

**Structured records with a schema.** Data is stored in named, typed columns. The schema is metadata that lets the system interpret bytes as integers, strings, dates.

**Indexes** (chapter 30) as separate structures that map field values to record locations, enabling sub-linear query time on indexed fields.

**Query language** (SQL) that expresses what data you want, not how to find it. The query planner (chapter 34) figures out which indexes to use.

**Transaction semantics** (chapter 32) that make multi-step operations atomic — either all succeed or all roll back.

**Concurrency control** (chapters 33, 25) at record granularity — many readers and writers can operate on different records simultaneously.

The database is not "files done better." It's a new abstraction level that files cannot provide: *structured, queryable, concurrent, transactional data*.

## Try It

<iframe src="../assets/browser/chapter29/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter29/index.html)

Before changing anything, predict:

- Compare query time for "find all records where age > 65" on a file store vs. a database with an index. How does the gap change as record count grows?
- If you crash mid-insert into the file store (after writing half the record), what does the next startup see? What does the database see?
- How does concurrent read performance compare between a locked file and a database with row-level locking?

## Implementation

The full model is ~140 lines of dependency-free JavaScript — open `browser/chapter29/index.html` (and the shared helpers in `browser/common/sim.js`) to read or modify it. Everything runs in the browser; nothing to install. Look for three storage backends: `FileStore` (linear scan array), `LogStore` (append-only array with in-memory index map), and `TableStore` (array of typed records with per-column indexes). The query executor tries each backend for the same query and displays the number of records examined — the gap between O(n) and O(log n) is visible immediately.

## When It Breaks

**Schema migrations are the hard part.** Once a database has millions of records, changing the schema (adding a column, changing a type) requires either a full table rewrite or careful versioning. `ALTER TABLE ADD COLUMN` in MySQL on a 500-million-row table used to take hours, locking the table the entire time. Online schema migrations (Pt-Online-Schema-Change, gh-ost) work around this by creating a shadow table, copying rows in background, and swapping tables at the end — but they add operational complexity and can take days on large tables.

**The N+1 query problem.** An application fetches 100 orders (`SELECT * FROM orders LIMIT 100`), then for each order fetches the customer (`SELECT * FROM customers WHERE id = ?`). That's 101 queries. A file-based system wouldn't do this — you'd read both files and join in memory. But the object-relational mapping layer hides the cost until the query log shows 10,000 queries per page load. The database did exactly what was asked; the application logic was wrong. Files make the join cost visible; ORMs hide it.

## Transfer

- **Key-value stores (Redis, DynamoDB).** Sacrifice query flexibility for extreme speed. Only lookup by primary key (like the fixed-width binary file), but in RAM with O(1) hash lookup. No joins, no range queries on non-primary keys. The right tool when your query pattern is always "fetch by ID."
- **Column-oriented databases (Parquet, Redshift, ClickHouse).** Store all values for one column contiguously rather than all values for one row. A query on one column reads only that column from disk, not all columns. For analytics (aggregating one column over billions of rows), this gives 10–100× speedup over row-oriented storage.
- **SQLite as a single file.** SQLite stores the entire database in one file but provides all the structured-query, transaction, and concurrency benefits. Used in iOS (one SQLite DB per app), Firefox (bookmarks, history), and countless embedded systems. The "files aren't enough" lesson: the file is the transport; SQLite is the abstraction that makes it usable.

Try these:

1. Store 1 million records in a CSV file and in SQLite. Measure time to answer "find all records where city = 'Austin'" in both. Now add an index to SQLite and repeat.
2. What is the difference between a relational database and a key-value store? Give a query that is trivial in one and impossible (or O(n)) in the other.
3. Why does `SELECT *` in production SQL hurt performance, even when you need all columns? (Hint: consider what the query planner can and can't optimize.)

---

**Continue → [Why Indexes Exist](30-why-indexes-exist.md)**
