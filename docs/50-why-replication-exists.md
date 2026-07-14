# Why Replication Exists

## The Problem

A single copy of data is a single point of failure.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Replication keeps copies on multiple nodes for durability and read scaling.

## Implementation

We build a minimal `replication` model in Python.

Source: [`python/chapter50/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter50/main.py)  ·  [view in browser](assets/simulations/chapter50/sim.py)

Run the implementation:

```bash
python python/chapter50/main.py
```

## Simulation

Source: [`simulations/chapter50/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter50/sim.py)  ·  [view in browser](assets/simulations/chapter50/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter50/sim.py
```

A browser version is available at [`browser/chapter50/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter50/index.html)  ·  [run live](assets/browser/chapter50/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `replication` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Search Engines Exist](51-why-search-engines-exist.md)**
