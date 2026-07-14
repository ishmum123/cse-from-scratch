# Why Counting Exists

## The Problem

You can compare piles of rocks, but you cannot say *how many*.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Counting assigns a stable symbol to a quantity so it can be remembered and communicated.

## Implementation

We build a minimal `counting` model in Python.

Source: [`python/chapter01/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter01/main.py)

Run the implementation:

```bash
python python/chapter01/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter01/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter01/index.html)  ·  [run live](assets/browser/chapter01/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `counting` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Numbers Need Memory](02-why-numbers-need-memory.md)**
