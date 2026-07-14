# Why Consensus Exists

## The Problem

Multiple machines must agree, but messages can be lost.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Consensus protocols let a group agree on a value despite failures.

## Implementation

We build a minimal `consensus` model in Python.

Source: [`python/chapter42/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter42/main.py)  ·  [view in browser](assets/simulations/chapter42/sim.py)

Run the implementation:

```bash
python python/chapter42/main.py
```

## Simulation

Source: [`simulations/chapter42/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter42/sim.py)  ·  [view in browser](assets/simulations/chapter42/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter42/sim.py
```

A browser version is available at [`browser/chapter42/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter42/index.html)  ·  [run live](assets/browser/chapter42/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `consensus` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Raft Works](43-why-raft-works.md)**
