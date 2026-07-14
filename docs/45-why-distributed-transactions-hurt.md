# The Coordinator's Dilemma

## The Problem

A travel booking system charges your credit card and reserves a flight seat in a single operation. The charge happens in your bank's payment service. The reservation happens in the airline's inventory service. Both must succeed or both must fail — partial success (charged but no seat, or seat held but not charged) is a bug that costs real money.

On a single database, this is a transaction: either everything commits or everything rolls back. But here, two separate services with separate databases must both agree. You can't just tell service A to commit and then tell service B to commit — between those two messages, a crash leaves one committed and one not.

The problem is fundamental: to guarantee atomicity across two systems, someone must make a decision that both will honor. But if that decider crashes before telling one of them, you have a partially committed transaction with no way to know which way to resolve it without talking to the decider — who is down.

Any cross-service atomicity scheme must handle:

- Coordinator crashes after some participants commit but before others do
- Participant crashes after agreeing to commit but before actually committing
- Network partitions that prevent the coordinator from knowing participant status
- Systems that can't hold locks indefinitely while waiting for a decision

## What Would You Try?

Before reading on:

- If the coordinator sends "commit" to participant A but crashes before sending to participant B, and B is waiting — what should B do? It can't wait forever. If it aborts, is that safe?
- What if participants just acted independently — commit if they can, abort if not — and compared results afterward? What breaks?
- For a "book hotel + book flight" transaction, what if you treated them as separate transactions with a manual compensating step if one fails?

## Failed Attempts

### Attempt 1: Sequential Commits (Fire and Forget)

Commit the payment, then send the reservation request. If reservation fails, refund.

This is logically correct but not atomic — there's a window between payment committing and reservation completing where the system is inconsistent. The refund itself can fail (the payment service is down). Retrying the refund requires idempotency and its own failure-handling logic. Now you've built a complex, custom retry system that still doesn't guarantee atomicity. And it bakes in *business logic* (what to do on failure) that must be maintained separately from the transaction logic. This is how e-commerce sites end up with "pending" charges that never resolve.

### Attempt 2: Two-Phase Commit (2PC) — The Standard Answer

Phase 1 (Prepare): coordinator asks all participants "can you commit?" Each participant acquires locks, does the work, writes to a "prepared" state, and responds "yes." If all say yes, coordinator moves to Phase 2. Phase 2 (Commit): coordinator writes its decision to durable storage, then sends "commit" to all.

This works — unless the coordinator crashes between writing its decision and telling the participants. Now participants are "prepared": holding locks, waiting for a decision. They cannot abort on their own (the coordinator might have already told some others to commit). They cannot commit on their own (the coordinator might have been about to abort). They block until the coordinator recovers. This is the **blocking problem**: 2PC is not fault-tolerant in the face of coordinator failure. The coordinating service becomes a single point of failure.

In practice, 2PC locks resources for the duration of the uncertainty window. Under load, this causes lock contention cascades. One coordinator outage at booking.com in 2014 caused a cascade of "prepared but not decided" transactions that locked hotel inventory for hours.

### Attempt 3: Three-Phase Commit (3PC)

Add a phase: after the coordinator hears all "yes" votes, it sends "prepare to commit" before the actual commit. Participants acknowledge. Only then does it send the real commit.

Now participants can recover from coordinator failure by asking each other: "Did you see 'prepare to commit'?" If yes, they can commit. If no, they can abort. 3PC is non-blocking in theory.

But 3PC breaks under network partition. If the partition isolates some participants mid-decision, they may reach different conclusions about whether "prepare to commit" was received. Split-brain: some commit, some abort. 3PC avoids coordinator-crash blocking but reintroduces the consistency problem under partition. It's also more complex to implement correctly, so almost no production system uses it.

## The Discovery

2PC is correct but blocking. 3PC avoids blocking but splits under partition. The fundamental problem: you cannot have non-blocking atomic commitment across distributed systems under asynchronous messaging — this is a theorem (Skeen 1982). Any protocol that can handle coordinator failure without blocking requires synchronous communication or is not safe under partition.

The practical resolution isn't a better protocol — it's a different model. **Sagas** (Garcia-Molina & Salem, 1987) decompose a distributed transaction into a sequence of *local* transactions, each with a corresponding *compensating transaction* that undoes it. Instead of atomicity across services, you get *eventual atomicity*: the system will, through compensation, reach a consistent state, just not immediately.

Book flight → Book hotel → Charge payment. If payment fails: cancel hotel reservation (compensation) → cancel flight (compensation). Each step is a local transaction. Each compensation is also a local transaction. No distributed locking, no coordinator, no blocking.

The tradeoff: sagas are *eventually consistent*, not immediately atomic. During execution, intermediate states are visible — a user might see "flight booked, hotel pending" for a few seconds. Applications must tolerate visible intermediate states, and compensations must be idempotent (the hotel cancellation might run twice on retry). Frameworks like Apache Camel, Axon, and AWS Step Functions implement saga orchestration.

## Try It

<iframe src="../assets/browser/chapter45/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter45/index.html)

Before changing anything, predict:

- As you raise "Crash prob %" from 0 to 60, which panel goes wrong first — Naive or 2PC? What does each failure look like?
- In the Naive panel, the coordinator commits Shard A then crashes. What state does Shard B show? Why can't the system self-recover?
- In the 2PC panel, a crash after Phase 1 leaves both shards yellow (PREPARED). Do they ever commit on their own? What would need to happen for them to make progress?

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter45/index.html` (shared helpers in `browser/common/sim.js`). The two paths are `runNaive()` — which simply flips `naiveState` to inconsistent when `Math.random() * 100 < failProb` — and `run2PC()`, which sets `tpcState.phase` to `'blocked'` on the same coin flip, leaving both shards in `'prepared'` with `blocked: true`. The `draw2PC()` function renders the orange highlight on held-lock shards and the `'BLOCKED (holding locks)'` status. The strip plot tracks `naiveInconsist` and `tpcBlocked` counts over time via the `strip.push()` calls in `frame()`.

## When It Breaks

**Compensation isn't always possible.** Sagas assume every action has a compensating action. But some actions are hard or impossible to compensate: you sent an email, triggered a physical shipment, or printed a receipt. The compensation can *notify* the user of the reversal, but it can't unsend the email. Sagas are only correct for actions where compensation is semantically valid. Mixing compensable and non-compensable actions in a saga requires careful ordering (put non-compensable steps last).

**2PC under high contention is slow.** The lock-holding window in Phase 1 means all participants block concurrent writes to the rows involved. Under heavy load, 2PC latency compounds: coordinator wait + all participant Phase 1 durations + network RTT × 4. At 100ms per round trip, a 3-participant 2PC takes at minimum 400ms. Google's Spanner uses a form of 2PC with Paxos-backed coordinators and commit-wait (chapter 41) to guarantee correctness, accepting that global-strong consistency costs ~250ms per transaction.

## Transfer

- **Stripe's payment system** uses idempotency keys as a form of saga: each step is retryable, and the payment intent tracks which steps have completed, allowing safe retry from any failure point.
- **Database change data capture (CDC)** with the outbox pattern is a saga primitive: write to your local database (local transaction) and publish an event; the event triggers the next saga step independently.
- **Airline overbooking** is an acceptance that "reserve seat" compensation (bumping a passenger) is cheaper than running 2PC across the booking and check-in systems — a deliberate saga tradeoff.

Try these:

1. Design a saga for "transfer money from account A to account B." What are the steps? What are the compensations? Is there an intermediate state where both accounts have the money? Neither?
2. 2PC with 5 participants, each holding a lock for up to 5 seconds during uncertainty. The coordinator crashes at a rate of once per hour. What's the expected lock-holding time per crash?
3. A saga runs: step 1 succeeds, step 2 succeeds, step 3 fails. Compensation for step 2 succeeds, compensation for step 1 fails permanently. What should the system do?

---

**Continue → [Why Caches Exist](46-why-caches-exist.md)**
