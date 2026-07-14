# Splitting the Table Too Big to Hold

## The Problem

Your social platform has 500 million users. Each user row holds profile data, settings, and stats — call it 1KB per user. That's 500GB of user data alone, before indexes, write-ahead logs, or replication copies. A single PostgreSQL instance handles this, but it's under constant pressure: 100,000 writes/second updating last-login timestamps, profile views, and message counts. Indexes on a 500M-row table take 30 seconds to create. Even index lookups on hot tables sometimes cause full-page I/O sweeps.

You add replicas (chapter 50). Reads scale. Writes don't — all writes still go to the single primary. At 100,000 writes/second, the primary I/O is saturated. You've hit the write ceiling of a single machine.

The data must be spread across multiple machines, each owning a subset. Any split strategy must handle:

- Routing a query for user X to the right machine, without asking all machines
- Adding or removing machines without rehashing and moving all data
- Queries that touch many users (full-table scans, analytics) efficiently
- Cross-shard operations like "find all users who follow user Y"

## What Would You Try?

Before reading on:

- If you split users across 4 databases by user ID (1–125M, 125M–250M, ...), what happens when user 300M queries the users they follow — some in shard 3, some in shard 2?
- A shard gets 10× more traffic than others because most of your active users have IDs in a certain range. How would you detect and fix this?
- You start with 4 shards and your data doubles. You want 8 shards. How do you migrate without downtime?

## Failed Attempts

### Attempt 1: Range-Based Sharding by ID

Shard 1 holds user IDs 1–125M, Shard 2 holds 125M–250M, etc. Routing is a simple range lookup: O(1), no coordination needed. Range queries ("all users with ID between X and Y") hit a single shard.

The problem is sequential ID growth. New users get monotonically increasing IDs. Shard 4 (the highest range) receives all new user writes. It's a hotspot — Shard 4 is 4× busier than Shard 1 during growth. The load is never balanced. The same pattern hits time-series data: if you shard logs by timestamp range, the current time range always receives all writes. This is called a "write hotspot" and is one of the most common sharding mistakes.

### Attempt 2: Hash-Based Sharding (`user_id % N`)

Assign user X to shard `X % N`. Perfectly uniform distribution — hash functions spread IDs evenly. Routing is still O(1).

Works until you need to change N. When N grows from 4 to 5, `user_id % 5` reassigns ~80% of data to different shards (almost every user moves). You must migrate 80% of a 500GB dataset while serving production traffic. This takes hours, during which queries go to the wrong shard unless you freeze writes (unacceptable) or run a complex dual-routing layer. `% N` is static by design.

### Attempt 3: Consistent Hashing Without Virtual Nodes

Map shard IDs onto a hash ring. Route each user to the nearest shard clockwise on the ring. Adding a new shard only moves ~1/N of data — only the items between the new shard and its predecessor.

Better — but the distribution is uneven. Hash positions on the ring aren't equally spaced. Shard A might own 30% of the ring, Shard B 15%, Shard C 40%, Shard D 15%. The load is unbalanced by the random ring positions. Removing a shard dumps all its traffic onto one neighbor, doubling that neighbor's load suddenly. Without a mechanism to spread positions more evenly, consistent hashing solves the migration problem but reintroduces the hotspot problem.

## The Discovery

Range sharding creates write hotspots. Hash sharding creates migration pain. Consistent hashing without adjustment creates uneven load.

The fix to consistent hashing's imbalance: **virtual nodes**. Instead of each physical shard having one position on the ring, give each shard V positions (Cassandra defaults to 256). With 4 shards × 256 positions = 1,024 evenly distributed points, the load imbalance drops to ≤1% vs the expected 25%. Adding a new shard inserts 256 new points, each stealing a small amount of data from many existing shards — instead of stealing all data from one neighbor.

**Consistent hashing with virtual nodes** is the industry standard for sharding. A shard addition or removal moves exactly 1/(number_of_shards) of data, from and to many different shards simultaneously, enabling parallelism. During migration, you run two lookups: the old ring (data not yet moved) and the new ring (data already moved) — the routing layer checks both.

Cross-shard queries remain hard: "find all users who follow user Y" requires querying every shard or maintaining a separate denormalized table. Sharding is chosen explicitly to sacrifice global query patterns in exchange for write scale. The data model often changes to avoid cross-shard joins: store follower lists with the user they're attached to, duplicating data rather than joining across shards.

## Try It

<iframe src="../assets/browser/chapter49/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter49/index.html)

Before changing anything, predict:

- With 4 shards and 100K users, approximately how many users land on each shard? Is the distribution exactly even?
- Add a 5th shard. What fraction of users are migrated? Is it close to 20%?
- Remove a shard. Which shards receive its data? Is it one shard or many?

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter49/index.html` (shared helpers in `browser/common/sim.js`). Look for the virtual node ring construction and the `findShard(key)` binary search on the ring. The migration visualization shows which physical shards send data to new shards when the cluster size changes.

## When It Breaks

**Cross-shard transactions are expensive.** If a transfer from User A (shard 1) to User B (shard 3) must be atomic, you need distributed transactions (chapter 45). Sharding and strong cross-entity consistency are in direct tension. Many sharded systems explicitly prohibit cross-shard transactions and require the application to handle them with eventual consistency or sagas.

**Hot keys bypass sharding entirely.** A "celebrity" user with 50 million followers gets 50× more reads than average users. Even with perfect hash distribution, that one user's data is on one shard, and that shard is a hotspot. Caching (chapter 46) is the solution for hot reads; for hot writes (a counter that increments 10,000 times/second), you need **write sharding**: split the counter across multiple shard keys, aggregate at read time. Twitter's "famous tweet" problem led to a dedicated "celebrity account" fast path outside the regular sharding scheme.

## Transfer

- **Cassandra and DynamoDB** use consistent hashing with virtual nodes as their core distribution mechanism. Every table is automatically sharded; the application never specifies which machine holds which row.
- **Vitess** (used by YouTube and GitHub) adds sharding middleware on top of MySQL, handling cross-shard query routing, transparent resharding, and connection pooling — the same problems we addressed but for relational workloads.
- **Search index shards** in Elasticsearch are consistent-hash-distributed: a document's shard is `hash(document_id) % num_primary_shards`. This is the hash sharding approach, which is why Elasticsearch warns you to set the primary shard count at index creation and not change it.

Try these:

1. You have 8 shards. A shard gets 3× more traffic than others. You want to split just that shard into 2. With consistent hashing, is this possible without rehashing everything? What's the migration scope?
2. A user's "following" list is on shard 3. The users they follow are spread across all 8 shards. Design a read that gets the latest posts from all followed users without a cross-shard join.
3. Your hash ring has 4 shards with 100 virtual nodes each. A new shard is added. How many of the 400 virtual node positions are redistributed? Approximately what fraction of data moves?

---

**Continue → [Why Replication Exists](50-why-replication-exists.md)**
