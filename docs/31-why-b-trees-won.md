# Why B-Trees Won

## The Problem

Your index works on disk, but disk blocks are large.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

B-trees keep many keys per node, minimizing disk reads and writes.

## Implementation

We build a minimal `b-tree` model in Python.

Source: [`python/chapter31/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter31/main.py)  ·  [view in browser](assets/simulations/chapter31/sim.py)

Run the implementation:

```bash
python python/chapter31/main.py
```

## Simulation

Source: [`simulations/chapter31/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter31/sim.py)  ·  [view in browser](assets/simulations/chapter31/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter31/sim.py
```

A browser version is available at [`browser/chapter31/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter31/index.html)  ·  [run live](assets/browser/chapter31/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `b-tree` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Transactions Exist](32-why-transactions-exist.md)**
