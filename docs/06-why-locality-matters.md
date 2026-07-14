# Why Locality Matters

## The Problem

The machine reads one byte, then another far away, and wastes most of its time.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Caches exploit spatial and temporal locality to keep nearby data fast.

## Implementation

We build a minimal `locality` model in Python.

Source: [`python/chapter06/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter06/main.py)  ·  [view in browser](assets/simulations/chapter06/sim.py)

Run the implementation:

```bash
python python/chapter06/main.py
```

## Simulation

Source: [`simulations/chapter06/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter06/sim.py)  ·  [view in browser](assets/simulations/chapter06/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter06/sim.py
```

A browser version is available at [`browser/chapter06/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter06/index.html)  ·  [run live](assets/browser/chapter06/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `locality` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Looking Is Slow](07-why-looking-is-slow.md)**
