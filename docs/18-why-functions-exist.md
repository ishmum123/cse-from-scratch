# Why Functions Exist

## The Problem

You write the same sequence of steps ten times.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Functions name reusable computations and hide their internal details behind an interface.

## Implementation

We build a minimal `function` model in Python.

Source: [`python/chapter18/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter18/main.py)  ·  [view in browser](assets/simulations/chapter18/sim.py)

Run the implementation:

```bash
python python/chapter18/main.py
```

## Simulation

Source: [`simulations/chapter18/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter18/sim.py)  ·  [view in browser](assets/simulations/chapter18/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter18/sim.py
```

A browser version is available at [`browser/chapter18/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter18/index.html)  ·  [run live](assets/browser/chapter18/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `function` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Recursion Exists](19-why-recursion-exists.md)**
