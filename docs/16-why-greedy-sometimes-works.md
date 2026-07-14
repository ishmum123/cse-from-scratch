# Why Greedy Sometimes Works

## The Problem

Every local choice looks correct, yet the final answer is wrong.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Greedy algorithms work when local optimality guarantees global optimality.

## Implementation

We build a minimal `greedy` model in Python.

Source: [`python/chapter16/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter16/main.py)

Run the implementation:

```bash
python python/chapter16/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter16/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter16/index.html)  ·  [run live](assets/browser/chapter16/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `greedy` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Graphs Matter](17-why-graphs-matter.md)**
