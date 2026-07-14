# Why Trees Exist

## The Problem

You can sort, but inserts and deletes keep breaking your order.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

A tree keeps order while allowing fast inserts and deletes through branching.

## Implementation

We build a minimal `tree` model in Python.

Source: [`python/chapter10/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter10/main.py)

Run the implementation:

```bash
python python/chapter10/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter10/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter10/index.html)  ·  [run live](assets/browser/chapter10/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `tree` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Balancing Exists](11-why-balancing-exists.md)**
