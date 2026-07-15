# The Buffer Between Fast Producers and Slow Consumers

## The Problem

A ticketing platform opens sales for a sold-out concert. At 10:00:00 AM, 200,000 people click "buy" simultaneously. Each purchase attempt needs to: verify the user's payment method, check inventory, reserve a seat, charge the card, send a confirmation email, and update analytics.

The checkout service can process 500 requests/second at full load. At 10:00:00, it receives 200,000/second — 400× its capacity. The service buckles: connection pools exhaust, response times climb to 30 seconds, then the service crashes. Users get error pages. When the service restarts, the traffic spike is still ongoing. It crashes again. The concert sells out anyway, but 80% of users got error pages instead of confirmation emails.

If only there were a way to receive 200,000 requests/second and process them at 500/second, without losing any.

Any work-buffering scheme must handle:

- Producers that arrive faster than consumers can drain
- Consumer crashes mid-work: the item must not be lost
- Delivery guarantees: at-least-once vs exactly-once
- Message ordering when it matters (and when it doesn't)

## What Would You Try?

Before reading on:

- If you put requests in a list and consumers pull from it, what happens if a consumer crashes after taking an item but before finishing it?
- When a producer writes faster than consumers read, the list grows. What happens when it's too large to fit in memory?
- Multiple consumers processing different items simultaneously — is that safe? What if the items have ordering dependencies?

## Failed Attempts

### Attempt 1: Synchronous HTTP with Client-Side Retry

The client sends a POST to the checkout service. If the service returns an error or times out, the client retries. Exponential backoff to avoid overwhelming a recovering service.

At 400× capacity, every request gets an error immediately and retries. Retries add to the already-overloaded queue. You've converted a 400× overload into ongoing retry storms. Backoff helps individual clients, but the aggregate load stays high — there are 200,000 clients all backing off and retrying over the next few minutes. The burst doesn't smooth out; it spreads into a sustained high load. And synchronous timeouts mean users wait on their browser, with no feedback that their request is queued.

### Attempt 2: In-Memory Queue in the Application

Add a `deque` to the application server. Requests go into the deque; a background thread processes them at capacity. The web tier accepts requests instantly (just enqueues them) and the processor runs at a sustainable rate.

Works until the server restarts. Everything in memory is lost. A 200,000-item queue that took 400 seconds to build vanishes in an instant. You've solved the overload problem but created a data loss problem. Also, with multiple application server instances, each has its own in-memory queue. Consumer 1 is processing items from server 1's queue; consumer 2 is processing from server 2's queue. You can't load balance consumers across servers — they're partitioned by accident.

### Attempt 3: Write to a Database Table as a Queue

Every request inserts a row into a "pending_work" table. Workers `SELECT ... WHERE status='pending' LIMIT 1 FOR UPDATE` to claim items. Mark as 'done' when finished. If a worker crashes, the status stays 'pending' and another worker eventually picks it up.

This is the "database as queue" antipattern. It works at low scale and is simple to reason about. But it has a fundamental performance problem: the `FOR UPDATE` lock serializes all workers through a single bottleneck. At high write rates, the pending table grows large, and `SELECT` scans become slow — O(n) on unlocked rows. Workers race to grab the same items, creating contention. Indexes help but don't eliminate lock contention. The database isn't designed for high-frequency delete-on-read patterns — tables fragment, autovacuum falls behind in PostgreSQL, and you spend engineering time fighting the database rather than processing work.

## The Discovery

Synchronous retry floods the server. In-memory queues lose data on restart. Database queues create lock contention at scale.

What's needed is a dedicated, durable buffer: receives items at producer speed, holds them durably (survives restarts), and delivers them to consumers at consumer speed. When a consumer takes an item and crashes before finishing, the item must go back to the front.

A **message queue** (Kafka, RabbitMQ, SQS) provides exactly this. The producer sends to the queue — fast, acknowledgment is just a write to the queue broker's durable log. The consumer reads from the queue at its own pace. The broker handles the buffer: if producers outpace consumers, the queue grows (bounded by configured limits); as consumers catch up, it drains.

The critical delivery guarantee mechanism: **visibility timeout** (SQS terminology) or **acknowledgment**. When a consumer takes a message, the broker marks it "in flight" but doesn't delete it. The consumer has T seconds to acknowledge. If the ack arrives, the broker deletes the message. If T expires without an ack (consumer crashed), the broker makes the message visible again — another consumer picks it up. This gives **at-least-once delivery**: every message is processed at least once, possibly more if the consumer crashes post-processing but pre-ack.

For **exactly-once** semantics (don't charge twice), the consumer must be idempotent: processing the same message twice has the same effect as once. Idempotency keys on payment operations are the standard solution.

## Try It

<iframe src="../assets/browser/chapter48/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter48/index.html)

Before changing anything, predict:

- Burst 1,000 messages at 10× consumer speed. How long until the queue drains? Does consumer speed double if you add a second consumer?
- Crash a consumer mid-processing. How long until its in-flight message reappears? Does any work get lost?
- Set visibility timeout very short (1 second) with a slow consumer. What happens?

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter48/index.html` (shared helpers in `browser/common/sim.js`). The sim is a schematic of queue depth dynamics, not a message broker. Each tick, `queueDepth` changes by `produceRate - consumeRate` (clamped to zero); when `produceRate > consumeRate`, depth grows and `drawQueue()` shows backlog building. The left panel (synchronous) stalls the producer whenever `stall = produceRate > consumeRate`, accumulating `syncStalls`. Use the produce/consume sliders to find the crossover point where backlog drains instead of accumulates.

## When It Breaks

**Poison messages cause consumer loops.** A message that consistently crashes or errors the consumer is re-queued indefinitely, blocking that consumer slot and burning compute. Solution: a **dead-letter queue** (DLQ) that receives messages after N failed attempts. Without a DLQ, a single malformed message can prevent any consumer from making progress. AWS SQS has a native DLQ configuration; RabbitMQ calls it a dead-letter exchange.

**Consumer lag becomes unbounded.** If consumers are consistently slower than producers (not just at peak, but sustainably), the queue grows until it hits storage limits. Kafka stores messages on disk with configurable retention, so bounded consumer lag for hours or days is normal — but eventually, if the lag grows faster than the retention window, consumers permanently fall behind and miss messages. Monitoring queue depth and consumer lag rate is essential.

## Transfer

- **Email delivery** uses queues ubiquitously: when you click "send," your email client hands the message to an SMTP server, which queues it, retries delivery to the recipient's server, and eventually either delivers or bounces — all asynchronously from the original send action.
- **CI/CD pipelines** (GitHub Actions, Jenkins) are queues: commits trigger jobs that enter a build queue and are consumed by available workers. The queue absorbs commit bursts (everyone pushing right before a deadline) without dropping builds.
- **IoT sensor data** from millions of devices lands in a queue (Kafka) before being processed by aggregation pipelines — decoupling the bursty, unpredictable arrival pattern from the batch analytics jobs that consume it.

Try these:

1. Your queue has 1,000 messages and 10 consumers each processing at 5 messages/second. How long to drain? Now one consumer crashes. How does the estimate change?
2. A payment processing consumer receives the same "charge $100" message twice (at-least-once delivery). Design an idempotency scheme that prevents double-charging. What storage do you need?
3. You have 100 order messages that must be processed in order (order 1 before order 2, etc.). Can you parallelize with multiple consumers? What architectural change would allow ordering while still allowing some parallelism?

---

**Continue → [Why Sharding Exists](49-why-sharding-exists.md)**
