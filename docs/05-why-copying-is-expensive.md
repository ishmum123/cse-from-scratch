# Why Copying Is Expensive

## The Problem

Moving data from one place to another takes forever.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Copying costs time proportional to size, so we pass references or reuse buffers when we can.

## Implementation

We build a minimal `copy` model in Python.

Source: [`python/chapter05/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter05/main.py)

Run the implementation:

```bash
python python/chapter05/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter05/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter05/index.html)  ·  [run live](assets/browser/chapter05/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `copy` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Locality Matters](06-why-locality-matters.md)**
