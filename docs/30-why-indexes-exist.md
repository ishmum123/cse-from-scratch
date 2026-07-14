# Why Indexes Exist

## The Problem

Scanning every row is fine until there are millions.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Indexes maintain a secondary lookup structure so queries can jump to relevant rows.

## Implementation

We build a minimal `index` model in Python.

Source: [`python/chapter30/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter30/main.py)

Run the implementation:

```bash
python python/chapter30/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter30/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter30/index.html)  ·  [run live](assets/browser/chapter30/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `index` designs trade correctness, performance, and maintainability.

---

**Continue → [Why B-Trees Won](31-why-b-trees-won.md)**
