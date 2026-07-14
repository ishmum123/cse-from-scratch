# Why Arrays Exist

## The Problem

You have a hundred numbers and no way to keep them in order.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

An array stores many values under one name at contiguous addresses.

## Implementation

We build a minimal `array` model in Python.

Source: [`python/chapter03/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter03/main.py)

Run the implementation:

```bash
python python/chapter03/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter03/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter03/index.html)  ·  [run live](assets/browser/chapter03/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `array` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Memory Has Addresses](04-why-memory-has-addresses.md)**
