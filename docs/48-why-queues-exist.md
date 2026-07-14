# Why Queues Exist

## The Problem

Spikes of traffic overwhelm the service.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Queues absorb bursts and let consumers process work at their own pace.

## Implementation

We build a minimal `message queue` model in Python.

Source: [`python/chapter48/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter48/main.py)

Run the implementation:

```bash
python python/chapter48/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter48/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter48/index.html)  ·  [run live](assets/browser/chapter48/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `message queue` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Sharding Exists](49-why-sharding-exists.md)**
