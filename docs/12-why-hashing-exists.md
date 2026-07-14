# Why Hashing Exists

## The Problem

You need near-instant lookups, but comparisons are expensive.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

A hash function maps keys directly to slots, trading space for O(1) access.

## Implementation

We build a minimal `hash table` model in Python.

Source: [`python/chapter12/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter12/main.py)

Run the implementation:

```bash
python python/chapter12/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter12/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter12/index.html)  ·  [run live](assets/browser/chapter12/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `hash table` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Sorting Exists](13-why-sorting-exists.md)**
