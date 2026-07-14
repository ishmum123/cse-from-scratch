# The Optimizer You Never See

## The Problem

A developer writes:

```sql
SELECT o.id, c.name FROM orders o JOIN customers c ON o.customer_id = c.id
WHERE c.city = 'Seattle' AND o.status = 'pending';
```

On Monday this runs in 50ms. On Friday it runs in 90 seconds. Nothing changed in the code. The query is identical. But 500,000 new orders were inserted this week. The query planner's statistics were stale, and it chose to scan the 50-million-row `orders` table first, then look up each `customer`, instead of starting with the small filtered set of Seattle customers and joining from there.

The same query can be executed in dozens of different orderings and algorithms. The planner's choice determines whether the query takes 50ms or 90 seconds — a 1,800× difference. And the planner can choose wrong.

Any planner must:

- Enumerate at least the most promising execution strategies
- Estimate the cost of each strategy accurately enough to pick the best one
- Use indexes when they help, skip them when they don't
- Do all this in milliseconds, not seconds

## What Would You Try?

Before reading on:

- For a join between a 50-million-row table and a 1,000-row table, which table should you iterate over first (the "outer loop")? Why?
- If there's an index on `customers.city`, does the planner always use it? What if only 50% of customers are in Seattle?
- The query planner doesn't know the exact data — it uses statistics. What statistics about a table would you want to know to estimate how many rows a WHERE clause returns?

## Failed Attempts

### Attempt 1: Always Use Available Indexes

If a column has an index and the query filters on it, use the index. Always. Simple rule, no statistics needed.

A table with 50 million orders has an index on `status`. Most orders are 'pending' (40 million rows). `WHERE status = 'pending'` matches 80% of the table. Using the index: 40 million index lookups → 40 million random row fetches. Total: 40 million random I/Os. Full table scan: one sequential pass, reading contiguously. Sequential I/O is 10–100× faster than random I/O on disk. The index makes this query 10–100× *slower*. A planner that always uses available indexes will catastrophically misperform on low-selectivity predicates. The rule must be "use the index when it's selective, skip it when it's not."

### Attempt 2: Estimate Row Counts from Table Statistics

Collect statistics: table row count, column cardinality, min/max values, histograms of value distribution. Use these to estimate how many rows each predicate will return. Choose the plan with the lowest estimated total cost (I/Os + CPU).

This is what real planners do — but the estimation is the hard part. `WHERE city = 'Seattle'` returns, say, 5% of customers (estimated from the histogram). `WHERE status = 'pending'` returns 80% of orders. Join these: which do you filter first? Correct: filter customers to Seattle (5% of 1,000 = 50 rows), then join to orders. The planner estimates 50 × (matching orders per customer) × (join cost per order). If the estimate of "orders per customer" is wrong — say the planner thinks 10 when the actual average is 500 — it underestimates the join cost by 50× and may choose the wrong order.

Estimation errors compound: a two-table join has two estimates to get right; a five-table join has five. Errors multiply. A join order that looks cheap based on wrong estimates can be 1,000× slower than the optimal order. This is why statistics must be kept current (via `ANALYZE` in PostgreSQL) and why complex queries with many joins can still produce bad plans despite accurate single-table statistics.

### Attempt 3: Try All Join Orderings

For n tables, there are n! possible join orderings. Try all of them, estimate the cost of each, pick the best. Guaranteed to find the optimal order.

For 5 tables: 120 orderings — feasible. For 10 tables: 3,628,800 orderings — planning might take longer than the query. For 15 tables: 1.3 trillion — impossible. Real queries in ERP systems, analytics platforms, and ORMs routinely join 10–20 tables. Exhaustive enumeration is not viable. PostgreSQL uses dynamic programming (for ≤ 8 tables) and then switches to a genetic algorithm (GEQO) for larger join counts. Neither is guaranteed optimal, but both are fast and usually good enough.

## The Discovery

Always using indexes fails on low-selectivity predicates. Row count estimation is necessary but compounds errors. Exhaustive enumeration is exponential and impractical.

The real planner is a cost-based optimizer running dynamic programming over a constrained search space:

1. **Statistics collection** (`ANALYZE`): for each table, compute number of rows, per-column histograms, null fractions, and most-common values. These are the inputs to estimation.

2. **Selectivity estimation**: for `WHERE city = 'Seattle'`, look up 'Seattle' in the city column's most-common-values list (or interpolate from the histogram). Multiply by table row count to get estimated rows.

3. **Plan enumeration**: for each join, consider: nested loop join (for each row in outer, scan inner), hash join (build hash table of inner, probe with outer — good for large joins), merge join (both sides sorted, linear merge — good when both sides already sorted). For each strategy, compute estimated cost: pages read × I/O cost + CPU cost per row processed.

4. **Dynamic programming**: compute the cheapest plan for every subset of tables, building up from single tables to the full query. This is O(2ⁿ) in table count but tractable for n ≤ 15.

5. **Plan execution**: the physical plan is a tree of operators (scan, index scan, hash join, sort, aggregate) that the executor evaluates top-down.

The planner's output is a **query plan**, visible via `EXPLAIN`. When the plan is wrong, `ANALYZE`, hints (MySQL), or explicit join order forcing (PostgreSQL `SET join_collapse_limit = 1`) are the levers.

## Try It

<iframe src="../assets/browser/chapter34/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter34/index.html)

Before changing anything, predict:

- For a join between a 1,000-row table (filtered to 50 rows) and a 50,000-row table, which plan — nested loop vs. hash join — does the simulator choose? Does it match your intuition?
- Set the selectivity of the filter to 80%. Does the planner change its decision to use an index?
- Introduce a stale statistic (make the planner believe the filtered table has 5,000 rows instead of 50). Does the plan change? Does it get worse?

## Implementation

The full model is ~140 lines of dependency-free JavaScript — open `browser/chapter34/index.html` (and the shared helpers in `browser/common/sim.js`) to read or modify it. Everything runs in the browser; nothing to install. Look for the `CostModel` class that estimates I/O and CPU costs for nested loop, hash join, and merge join given row counts and selectivity. The `PlanEnumerator` tries both join orderings and both index-scan and seq-scan options for each table, returning the plan tree with the minimum estimated cost and the actual simulated cost.

## When It Breaks

**Stale statistics cause catastrophic plans.** PostgreSQL autovacuum runs `ANALYZE` periodically, but on a fast-moving table it may be hours behind. A batch import of 10 million rows followed by an immediate query may catch the planner with pre-import statistics. The planner believes the table has 100,000 rows and chooses a nested-loop join; the actual 10,100,000 rows make it 100× slower than a hash join would have been. Explicitly run `ANALYZE table_name` after large imports.

**Parameter sniffing and plan caching.** Prepared statements cache the query plan based on the first set of parameters seen. `WHERE status = $1` is planned once with `status = 'cancelled'` (5,000 rows) and the plan is cached. Later executions with `status = 'pending'` (40,000,000 rows) use the same plan — tuned for 5,000 rows, catastrophically wrong for 40,000,000. SQL Server is notorious for this ("parameter sniffing"). Fix: periodic plan cache invalidation, `OPTION (RECOMPILE)` per execution, or statistics-aware plan caching.

**Correlated subqueries resist optimization.** `SELECT * FROM orders WHERE customer_id IN (SELECT id FROM customers WHERE city = 'Seattle')` looks like a set membership check, but naive execution re-evaluates the subquery once per outer row. The planner must recognize the correlated form and rewrite it as a join or semi-join. Not all planners do this correctly for all query shapes. An ORM generating correlated subqueries for `WHERE IN (SELECT ...)` is a common performance anti-pattern.

## Transfer

- **`EXPLAIN ANALYZE` in PostgreSQL.** The planner's `EXPLAIN` shows the estimated plan; `EXPLAIN ANALYZE` executes the query and shows actual row counts vs. estimated. When actual >> estimated, the statistics are stale or the estimation model is wrong. This is the primary tool for diagnosing slow queries.
- **Query hints.** MySQL and SQL Server support query hints (`USE INDEX`, `FORCE INDEX`, `OPTION (HASH JOIN)`) that override the planner's decision. PostgreSQL deliberately doesn't support most hints, preferring to fix the planner's statistics instead. Hints couple application code to physical layout — a schema change that makes the hinted index obsolete requires finding every query that references it.
- **Adaptive query execution (Spark, Trino).** Distributed query planners make estimates before execution. Adaptive execution re-plans mid-query based on observed intermediate row counts. If the planner estimated 1M rows at a join but the actual output is 50, it can switch from a distributed hash join to a broadcast join dynamically. This handles the compounding estimation error problem by correcting estimates at runtime.

Try these:

1. Run `EXPLAIN (ANALYZE, BUFFERS) SELECT ...` on a real PostgreSQL query. Find a row where "estimated rows" differs from "actual rows" by more than 10×. What does this suggest about the statistics?
2. For a join of tables A (1M rows), B (500 rows), C (10K rows), enumerate all 6 join orderings. For a filtering predicate that reduces A to 100 rows and C to 200 rows, which ordering is cheapest and why?
3. What is a "hash join"? Describe the build and probe phases. Under what conditions is it faster than a nested loop join? When is nested loop preferred?

---

**Continue → [Why Computers Need Addresses](35-why-computers-need-addresses.md)**
