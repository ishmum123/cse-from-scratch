# Why the Nearest Copy Wins

## The Problem

A news site's front page shows today's top stories. The database query to build that page joins articles, authors, view counts, and tag metadata — 200ms for a fresh build. That's acceptable once. But 50,000 users hit the front page every minute. That's 833 requests/second, each waiting 200ms and running the same query against the same rows. The database receives 833 identical queries per second. At 10ms per query on a warm database, that's 8,330ms of DB compute per second — meaning you need at least 9 database replicas just to serve the front page. The page content changes maybe once per minute.

You're paying for ten databases to run the same 200ms computation 50,000 times per minute, producing an answer that's identical for all 50,000 users.

Any caching scheme must handle:

- Knowing when cached data is stale enough to re-fetch
- What to do when the cache is full (eviction)
- Cache stampedes when many requests miss simultaneously
- Data that's mostly read but occasionally written

## What Would You Try?

Before reading on:

- If you cache the front page for 60 seconds, what's the worst-case staleness a user can see?
- Your cache holds 1,000 items and gets a request for item 1,001. Which of the 1,000 should you evict? What information would help you decide?
- Ten requests arrive for the same key, all before the first one completes. How many database queries should actually run?

## Failed Attempts

### Attempt 1: Application-Level In-Process Cache

Store computed results in a dictionary inside the application server. Every server has its own cache. Lookups are nanoseconds — pure memory access, zero network.

Doesn't scale. With 20 application servers, you have 20 independent caches. A request to server 1 misses and hits the database. A request to server 2 for the same key also misses — it has no knowledge of what server 1 cached. At 20 servers with 1,000-item caches, you might have the same item cached 20 times and still miss 90% of requests if traffic isn't sticky to servers. More servers means more total cache memory but no better hit rate. Also, when a server restarts, its cache is empty — cold starts hit the database hard.

### Attempt 2: Cache Everything Forever

Never expire. Once computed, an item stays cached forever and is only invalidated when the underlying data changes. Perfect accuracy — you never serve stale data.

Cache invalidation is "one of the two hard things in computer science." When an article's view count changes, which cached responses include it? The front page, the article's own page, the author's page, the tag pages, the search results page. Every write to any table must know which cached keys might be affected and invalidate them all. As the data model grows, the dependency graph between cached keys and source rows becomes impossibly complex. Miss one invalidation and users see wrong data indefinitely. This is brittle enough that Phil Karlton's original quote about the two hard things became famous precisely because teams consistently underestimate the invalidation problem.

### Attempt 3: Time-Based Expiry with No Coordination

Each cache entry has a TTL (time-to-live). After TTL expires, the next request recomputes it. Simple, requires no invalidation logic.

The stampede problem: if the front page's cache entry expires and 100 requests arrive simultaneously, all 100 see a cache miss. All 100 query the database in parallel. The database receives 100 requests at once for the same data, takes 200ms each — now you've made your database problem *worse* than if you had no cache. Traffic patterns mean popular items expire during traffic peaks (peak traffic correlates with when content was freshly published, which is also when TTLs tend to expire). The "thundering herd" is a real failure mode: Reddit went down in 2013 when a cache TTL expiry caused a cascade of 40,000 simultaneous database queries.

## The Discovery

In-process caches don't scale horizontally. Eternal caches require impossible invalidation logic. TTL-only caches stampede at expiry. The failures point at what's actually needed: a shared cache layer that de-duplicates simultaneous misses, serves stale data while refreshing, and has a clear eviction policy.

**Memcached and Redis** implement the key pattern: a shared key-value store that all application servers query before hitting the database. A miss by *any* server updates the cache — all servers benefit. De-duplication of simultaneous misses ("request coalescing" or "dog-pile protection") ensures only one database query runs per missing key. **LRU eviction** (Least Recently Used) keeps the working set in cache: items not accessed recently are the first to go when memory is full.

The cache miss path: request → check cache → miss → acquire distributed lock for this key → query database → store in cache → release lock → respond. Any other requests for the same key during the query wait for the lock and then read the just-populated cache entry. One database query per unique missing key, regardless of how many simultaneous requesters.

**Cache-aside** (application checks cache, falls back to DB) is the most common pattern. **Write-through** (write goes to both cache and DB atomically) is used when you want cache hits immediately after writes. **Write-behind** (write goes to cache first, DB update is async) is used for high-write scenarios but risks data loss if the cache fails.

## Try It

<iframe src="../assets/browser/chapter46/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter46/index.html)

Before changing anything, predict:

- With a cache size of 10 items and 100 unique keys requested in random order, what's the steady-state hit rate?
- Increase the number of simultaneous requesters for an expired key. Does request coalescing reduce database queries proportionally?
- Compare LRU vs LFU (Least Frequently Used) eviction on a workload where 5 items are very popular and 95 others are accessed once. Which has a higher hit rate?

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter46/index.html` (shared helpers in `browser/common/sim.js`). The LRU cache is `cacheKeys`, a plain array used as an ordered list. On each request, `cacheKeys.indexOf(key)` checks for a hit; a hit splices the key to the back (most-recently-used), while a miss pushes the key and evicts the front entry when `cacheKeys.length > cacheSize`. The `cacheHits` and `cacheMisses` counters track throughput; the right panel's average latency blends `5ms` for hits against `dbLatency` for misses.

## When It Breaks

**Thundering herd on cold start.** When a cache server restarts or a new cache cluster is provisioned, it's completely cold. Every request misses. The database sees its full traffic load with no cache protection. Large systems warm the cache artificially before routing traffic — "cache warming" — but this requires knowing the working set and can take minutes. Facebook's memcache infrastructure required a dedicated warm-up protocol to avoid database overload on deployment.

**Cache invalidation bugs cause inconsistency.** Any write that should invalidate cache entries but doesn't produces users seeing wrong data for up to TTL. The longer the TTL, the worse the staleness. The more complex the data model, the more likely a write path misses an invalidation. Production systems have had "ghost prices" (wrong prices served from stale cache) for hours before detection. Monitoring cache hit rates and staleness separately is essential.

## Transfer

- **CPU L1/L2/L3 caches** follow the same principle: keep recently used data physically close to the processor to avoid expensive main-memory accesses. The hierarchy (L1 fastest/smallest, L3 slower/larger) matches the distributed pattern (in-process fastest, remote cache slower, database slowest).
- **Browser caches** use HTTP Cache-Control headers (TTL-based) and ETags (conditional validation) to store responses locally, reducing server load and latency for returning visitors.
- **DNS caches** at ISPs cache record lookups for the TTL specified in each record — the same tradeoff between freshness and query reduction, operating at global scale.

Try these:

1. A cache has TTL = 60s and receives 1,000 requests per second. The underlying computation takes 100ms. Without request coalescing, how many concurrent database queries would a cold start generate in the first second?
2. You need to cache user profile pages. Profiles change rarely (average once per week) but must show updates within 5 minutes. What TTL do you use? What's the expected database query rate reduction vs no cache?
3. Implement an LRU cache from scratch using a hash map + doubly linked list. What's the time complexity of get and put? Why does a plain hash map not suffice?

---

**Continue → [Why CDNs Exist](47-why-cdns-exist.md)**
