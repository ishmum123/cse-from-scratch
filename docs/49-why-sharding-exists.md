# Why Sharding Exists

## The Problem

One database cannot store or serve all the data.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Sharding splits data by key across many nodes so each owns a subset.

## Implementation

We build a minimal `sharding` model in Python.

Source: [`python/chapter49/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter49/main.py)  ·  [view in browser](assets/simulations/chapter49/sim.py)

Run the implementation:

```bash
python python/chapter49/main.py
```

## Simulation

Source: [`simulations/chapter49/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter49/sim.py)  ·  [view in browser](assets/simulations/chapter49/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter49/sim.py
```

A browser version is available at [`browser/chapter49/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter49/index.html)  ·  [run live](assets/browser/chapter49/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `sharding` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Replication Exists](50-why-replication-exists.md)**
