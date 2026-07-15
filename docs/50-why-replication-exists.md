# One Copy Is a Liability

## The Problem

Your database contains the entire order history for 10 million customers. It lives on one machine. At 2 AM, the machine's disk controller fails. The disk is unreadable. Your DBA spends 6 hours restoring from last night's backup — recovering everything up to midnight, losing 2 hours of orders. Customers who placed orders between midnight and 2 AM have no record of their purchase.

You restore from backup more carefully now. But two months later, the machine's power supply fails. Restoration takes 4 hours. You lose 4 hours of orders.

These are availability failures (the system is down) and durability failures (data is lost). They have the same root cause: the data exists in one place, and that place failed.

Any replication scheme must handle:

- Writes that must appear on multiple nodes without the write being "confirmed" until it's durable
- Reads that might go to any replica — which might be slightly behind
- A failed primary that must be replaced without losing committed writes
- Replicas that fall behind and must catch up without blocking the primary

## What Would You Try?

Before reading on:

- If you copy the data to a second machine after every write, what happens if the primary fails during a write — after the primary commits but before the replica receives it?
- If reads can go to any replica, and replicas might be 100ms behind the primary, what's the worst thing that can happen from a user's perspective?
- How many replicas do you need before a disk failure is no longer a significant durability risk?

## Failed Attempts

### Attempt 1: Nightly Backup to Cold Storage

Back up the database every night at midnight. Store the backup offsite. On failure, restore.

Recovery Time Objective (RTO) is hours — the restoration time. Recovery Point Objective (RPO) is up to 24 hours — you lose up to a day of data. For any transactional system, this is unacceptable. Backups also have their own failure modes: the backup job silently fails for three days, you discover this on the fourth day when you need to restore, and the backup is three days stale. Backups are necessary but not sufficient — they're for disaster recovery, not operational durability.

### Attempt 2: Synchronous Replication (All Replicas Must Confirm)

Before acknowledging a write to the client, the primary waits for all N replicas to confirm they've received and persisted the write. Zero data loss on primary failure: every committed write is on all replicas.

At 3 replicas with one in another data center (100ms away), every write waits 100ms for the remote replica. A system that handled 10,000 writes/second now handles ~100/second (one per 100ms round trip). Worse, if any replica is slow or unavailable, every write stalls. One replica going down brings the entire write path down. Synchronous full replication trades availability and throughput for zero RPO.

### Attempt 3: Asynchronous Replication (Replicas Catch Up When They Can)

Primary acknowledges the write immediately. Replicas receive updates asynchronously from a replication stream. Primary failure during a write that hasn't been replicated yet = data loss.

This is MySQL's default asynchronous replication. Replicas are typically 10–100ms behind the primary. If the primary crashes, you lose up to 100ms of writes. In some failure scenarios (disk controller starts failing slowly, writes are accepted but stream doesn't flush), the replica can fall hours behind before anyone notices. PostgreSQL had a well-known scenario where streaming replication silently fell behind during high write load, and the first indication was a primary failure with a 6-hour replication lag.

## The Discovery

Cold backups have high RPO/RTO. Synchronous full replication destroys throughput. Asynchronous replication loses data on failure.

The sweet spot: **semi-synchronous replication**. The primary waits for *at least one* replica to confirm before acknowledging the write. It doesn't wait for all replicas — just one. As long as at least one replica is healthy, writes proceed at single-replica latency (typically a few milliseconds on the same network). If the primary fails, at least one replica has every committed write.

Combined with a **quorum approach** (Raft from chapter 43, or semi-sync with failover): a write is "committed" when W nodes have it (W is configurable). With 3 nodes and W=2 (majority), you tolerate 1 failure. With 5 nodes and W=3, you tolerate 2 failures. The durability calculation: three independent disks at 99.99% uptime gives (1 - 0.9999³) ≈ 0.003% chance of simultaneous failure — durability sufficient for most systems.

**Read scaling** is the second benefit: route reads to any replica, reducing primary load. The tradeoff is **replication lag**: a read from a follower may return data 10–100ms older than the latest write. **Read-your-writes consistency** (you always see your own writes) requires routing your own reads to the primary or to a replica that's guaranteed to have your latest write — most frameworks track this via a replication position.

## Try It

<iframe src="../assets/browser/chapter50/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter50/index.html)

Before changing anything, predict:

- Kill the primary right after a write. Does the write survive? Which replica becomes the new primary?
- Increase replication lag artificially. Read from a follower immediately after writing to the primary. What do you see?
- Set W=1 (asynchronous). Kill the primary during a write batch. How many writes are lost?

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter50/index.html` (shared helpers in `browser/common/sim.js`). The sim compares availability of a single server against a replicated cluster. Each tick, a random draw against `failProb` determines whether the single server (`singleFailed`) or each of `numReplicas` nodes (`clusterNodes`) is up. `clusterAvail` is true when any replica survives (`clusterNodes.some(n => n)`). `singleUp` and `clusterUp` accumulate available ticks; their percentages feed the strip chart — raise `failProb` to see the cluster's availability advantage widen.

## When It Breaks

**Replication lag causes stale reads in critical paths.** A user updates their shipping address (write to primary). Their order confirmation page loads (read from replica). The replica is 200ms behind. The page shows the old address. The user assumes the update didn't work and tries again — double update. For "read your own writes," applications must route the immediately-following read to the primary or wait for the replica to catch up. This is a common source of subtle bugs in applications that don't account for replication lag.

**Split-brain during failover.** The primary goes down. An automated failover promotes replica B to primary. A network partition heals 10 seconds later — the old primary is back, also thinking it's primary. Both accept writes. You now have two primaries. Any system that doesn't have a fencing mechanism (STONITH — Shoot The Other Node In The Head, i.e., forcibly rebooting the old primary via out-of-band management) is vulnerable to split-brain. GitHub's database failover in October 2018 (the same incident that affected their Raft system) included a MySQL split-brain event that caused 24 hours of inconsistency.

## Transfer

- **PostgreSQL streaming replication** with Patroni or Stolon uses automatic failover with configurable synchronous_standby_names — the W=1 (or more) semi-sync approach in production at Zalando, Airbnb, and others.
- **MongoDB replica sets** implement a three-node quorum-based replication. The odd number ensures a clear majority for elections (chapter 42), and write concern `majority` gives semi-sync durability.
- **RAID arrays** are hardware replication — RAID 1 mirrors every write to two disks, RAID 6 stripes with two parity disks tolerating two simultaneous failures. The same durability math applies at the hardware level.

Try these:

1. You have 3 replicas with semi-sync (W=2). A network partition isolates replica C. Can the system still accept writes? Can replica C accept writes independently? What happens when the partition heals?
2. Replication lag is 50ms on average, 200ms at peak. A user writes and then reads within 10ms. What fraction of reads see the write? What architectural change guarantees they always see it?
3. Calculate: with 3 replicas at 99.95% disk annual reliability each, what's the probability of losing all copies simultaneously? What does this mean for annual expected data loss events?

---

**Continue → [Why Search Engines Exist](51-why-search-engines-exist.md)**
