# Why Dynamic Programming Exists

## The Problem

You keep solving the same sub-problem again and again.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Memoization stores answers to overlapping sub-problems so each is solved only once.

## Implementation

We build a minimal `dynamic programming` model in Python.

Source: [`python/chapter15/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter15/main.py)  ·  [view in browser](assets/simulations/chapter15/sim.py)

Run the implementation:

```bash
python python/chapter15/main.py
```

## Simulation

Source: [`simulations/chapter15/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter15/sim.py)  ·  [view in browser](assets/simulations/chapter15/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter15/sim.py
```

A browser version is available at [`browser/chapter15/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter15/index.html)  ·  [run live](assets/browser/chapter15/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `dynamic programming` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Greedy Sometimes Works](16-why-greedy-sometimes-works.md)**
