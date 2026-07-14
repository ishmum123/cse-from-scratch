# Why Graphs Matter

## The Problem

The world is not a list. Points connect to other points.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Graphs model relationships explicitly, unlocking searches over states, paths, and dependencies.

## Implementation

We build a minimal `graph` model in Python.

Source: [`python/chapter17/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter17/main.py)  ·  [view in browser](assets/simulations/chapter17/sim.py)

Run the implementation:

```bash
python python/chapter17/main.py
```

## Simulation

Source: [`simulations/chapter17/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter17/sim.py)  ·  [view in browser](assets/simulations/chapter17/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter17/sim.py
```

A browser version is available at [`browser/chapter17/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter17/index.html)  ·  [run live](assets/browser/chapter17/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `graph` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Functions Exist](18-why-functions-exist.md)**
