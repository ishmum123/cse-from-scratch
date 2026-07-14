# Why Numbers Need Memory

## The Problem

You can count, but every new number erases the last one.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

A register or variable holds a value so it can be reused later.

## Implementation

We build a minimal `number memory` model in Python.

Source: [`python/chapter02/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter02/main.py)  ·  [view in browser](assets/simulations/chapter02/sim.py)

Run the implementation:

```bash
python python/chapter02/main.py
```

## Simulation

Source: [`simulations/chapter02/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter02/sim.py)  ·  [view in browser](assets/simulations/chapter02/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter02/sim.py
```

A browser version is available at [`browser/chapter02/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter02/index.html)  ·  [run live](assets/browser/chapter02/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `number memory` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Arrays Exist](03-why-arrays-exist.md)**
