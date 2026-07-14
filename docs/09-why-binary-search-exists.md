# Why Binary Search Exists

## The Problem

Even scanning half the list is too slow when the list grows.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Binary search halves the problem on every step by comparing to the middle element.

## Implementation

We build a minimal `binary search` model in Python.

Source: [`python/chapter09/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter09/main.py)  ·  [view in browser](assets/simulations/chapter09/sim.py)

Run the implementation:

```bash
python python/chapter09/main.py
```

## Simulation

Source: [`simulations/chapter09/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter09/sim.py)  ·  [view in browser](assets/simulations/chapter09/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter09/sim.py
```

A browser version is available at [`browser/chapter09/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter09/index.html)  ·  [run live](assets/browser/chapter09/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `binary search` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Trees Exist](10-why-trees-exist.md)**
