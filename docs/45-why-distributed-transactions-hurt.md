# Why Distributed Transactions Hurt

## The Problem

Distributed transactions stall when one node hesitates.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Two-phase commit and sagas trade strong consistency for coordination overhead and fragility.

## Implementation

We build a minimal `distributed transaction` model in Python.

Source: [`python/chapter45/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter45/main.py)  ·  [view in browser](assets/simulations/chapter45/sim.py)

Run the implementation:

```bash
python python/chapter45/main.py
```

## Simulation

Source: [`simulations/chapter45/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter45/sim.py)  ·  [view in browser](assets/simulations/chapter45/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter45/sim.py
```

A browser version is available at [`browser/chapter45/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter45/index.html)  ·  [run live](assets/browser/chapter45/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `distributed transaction` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Caches Exist](46-why-caches-exist.md)**
