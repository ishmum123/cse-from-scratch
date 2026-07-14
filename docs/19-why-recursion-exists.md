# Why Recursion Exists

## The Problem

A problem contains a smaller version of itself.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Recursion solves a problem by reducing it to a base case and a self-similar sub-problem.

## Implementation

We build a minimal `recursion` model in Python.

Source: [`python/chapter19/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter19/main.py)  ·  [view in browser](assets/simulations/chapter19/sim.py)

Run the implementation:

```bash
python python/chapter19/main.py
```

## Simulation

Source: [`simulations/chapter19/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter19/sim.py)  ·  [view in browser](assets/simulations/chapter19/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter19/sim.py
```

A browser version is available at [`browser/chapter19/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter19/index.html)  ·  [run live](assets/browser/chapter19/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `recursion` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Stacks Exist](20-why-stacks-exist.md)**
