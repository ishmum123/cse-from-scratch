# Order Preserved Under Pressure

## The Problem

A print server receives jobs from 30 computers simultaneously. Without any coordination, every program calls "print now" and the printer driver processes whichever OS thread happens to win the race. Document A gets interleaved with Document B mid-page. The marketing report prints with the accounting spreadsheet's numbers on page 3.

Or worse: a web server gets 10,000 HTTP requests in a burst. Without ordering, either all 10,000 hit the database at once (crashing it) or arbitrary requests get dropped (wrong ones — the healthcheck gets through, user checkouts don't).

Any solution must:

- Preserve arrival order — earlier arrivals are served before later ones
- Decouple producers (who add work) from consumers (who process it) so they run at different rates
- Handle bursts without dropping items or corrupting order
- Allow the consumer to be slow without blocking the producer

## What Would You Try?

Before reading on:

- If two threads both try to add to a shared list at the same moment, what can go wrong without coordination?
- What's the difference between the producer knowing "I'm done" and the consumer knowing "there's something to do"?
- If the consumer is 3× slower than the producer, what happens to the queue size over time?

## Failed Attempts

### Attempt 1: Shared Array with a Counter

Keep a global array and a counter. Producer writes to `array[counter]`, increments counter. Consumer reads from `array[0]`, shifts everything down, decrements counter.

Looks fine for a single producer and single consumer. Add a second producer: both read `counter = 5`, both write to `array[5]`, one overwrites the other. The counter is now 6 but one item is lost. The array shift in the consumer is O(n) — 10,000 items means 10,000 shifts per dequeue. At scale, the consumer spends more time rearranging memory than doing real work. The shared counter without locks is a race condition; with locks, the shift makes it a bottleneck.

### Attempt 2: Separate "To-Do" and "In-Progress" Stacks

Producer pushes onto a "to-do" stack. Consumer pops from it, processes, pushes result to "done" stack. Stacks are simpler than arrays — no shifting, O(1) push/pop.

The ordering problem: a stack is last-in-first-out. The last job submitted is processed first. That's fine for some things (undo history, call stacks) but disastrous for fairness. The print job submitted at 9:00 AM waits behind every job submitted after it. In the burst scenario, old work perpetually gets preempted by new arrivals. Stacks solve the shifting cost but break the fairness constraint entirely.

### Attempt 3: Ring Buffer with Head and Tail Pointers

Preallocate a fixed-size array. Track `head` (next to read) and `tail` (next to write). Producer writes to `tail`, advances tail. Consumer reads from `head`, advances head. When either pointer reaches the end, wrap around.

This works and is how real queues are implemented in hardware and OS kernels. O(1) enqueue and dequeue, no shifting, FIFO preserved. The wrinkle: what happens when the buffer is full? `tail` catches up to `head`. You either block the producer (backpressure), drop the new item, or expand the buffer. Each choice is legitimate — but which is right depends on the application. A ring buffer doesn't make that decision; it forces you to.

## The Discovery

Attempt 1 loses items under concurrency and costs O(n) on dequeue. Attempt 2 (stack) destroys ordering. Attempt 3 is the real solution — a ring buffer with head/tail pointers — but revealing the deeper insight: the **queue** is not a data structure, it's a contract.

The contract: items are dequeued in the same order they were enqueued — **First In, First Out (FIFO)**. The ring buffer is one implementation. A linked list with head and tail pointers is another (unbounded, no wrap-around). A blocking queue adds the constraint that a consumer waiting on an empty queue sleeps until the producer signals it, rather than busy-polling.

The key decoupling: producers and consumers don't know about each other. The producer calls `enqueue(item)` and continues. The consumer calls `dequeue()` and gets the oldest item. Their execution rates are independent. A burst of 10,000 requests enqueues in milliseconds; the database consumer processes them at its own pace. Without this indirection, every producer and consumer must synchronize directly — O(n²) coordination for n parties.

## Try It

<iframe src="../assets/browser/chapter21/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter21/index.html)

Before changing anything, predict:

- If the producer runs 5× faster than the consumer, what does the queue length look like over time? Does it stabilize?
- What happens when the queue hits its capacity limit — does the simulation block, drop, or expand?
- If you pause the consumer and let the producer run freely for 10 seconds, then resume both, how long until the queue drains?

## Implementation

The full model is ~120 lines of dependency-free JavaScript — open `browser/chapter21/index.html` (and the shared helpers in `browser/common/sim.js`) to read or modify it. Everything runs in the browser; nothing to install. Look for the `RingBuffer` class: it implements head/tail pointers, wrap-around, and the enqueue/dequeue logic. The producer and consumer are separate `setInterval` callbacks to simulate independent rates.

## When It Breaks

**Unbounded queues under sustained overload.** If the producer consistently outpaces the consumer, a queue without a size limit grows until the process runs out of memory. This is a real failure mode in message brokers: RabbitMQ will happily accept messages faster than consumers process them, and the broker's memory fills until it starts dropping connections or crashing. The fix is backpressure — make the producer block or slow down when the queue is full — but many systems omit this and discover the failure in production.

**Head-of-line blocking.** FIFO ordering means one slow or stuck item blocks everything behind it. A web server's request queue with one request waiting on a slow database call delays unrelated fast requests behind it. HTTP/1.1 suffers from this — a stalled response on a TCP connection prevents subsequent responses from delivering even if they're ready. HTTP/2 multiplexing was designed specifically to break this constraint.

## Transfer

- **CPU run queues** in the OS scheduler are queues of runnable processes. When a process becomes runnable (e.g., its I/O completes), it joins the tail; the CPU picks from the head. Priority queues are a variant where the head is always the highest-priority item.
- **Network switch buffers** are queues of packets. When packets arrive faster than the outbound link can transmit them, they queue. When the queue fills, packets are dropped — this is the root mechanism behind TCP congestion (chapter 38).
- **Event loops** in Node.js and browsers are queues of callbacks. `setTimeout(fn, 0)` enqueues `fn` at the tail; the event loop dequeues and executes from the head. The single-threaded model works because the queue serializes all events.

Try these:

1. Implement a bounded ring buffer with blocking enqueue (producer sleeps when full) and blocking dequeue (consumer sleeps when empty). What synchronization primitives do you need?
2. A priority queue serves highest-priority items first. What ordering guarantee does it break compared to FIFO? Give a scenario where this is the right tradeoff.
3. You have a queue with average arrival rate λ and average service rate μ. Under what condition does the queue length grow without bound? (Hint: this is Little's Law.)

---

**Continue → [Why Schedulers Exist](22-why-schedulers-exist.md)**
