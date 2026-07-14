# Why Eventual Consistency Exists

## The Problem

Strict consistency across the world is too slow.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Eventual consistency accepts temporary divergence in exchange for availability and partition tolerance.

## Implementation

We build a minimal `eventual consistency` model in Python.

Source: [`python/chapter44/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter44/main.py)

Run the implementation:

```bash
python python/chapter44/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter44/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter44/index.html)  ·  [run live](assets/browser/chapter44/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `eventual consistency` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Distributed Transactions Hurt](45-why-distributed-transactions-hurt.md)**
