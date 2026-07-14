# Why Tensor Parallelism Exists

## The Problem

One GPU cannot hold a model, but many can if the work is split.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Tensor parallelism splits layers across devices so a model larger than one GPU can still run.

## Implementation

We build a minimal `tensor parallelism` model in Python.

Source: [`python/chapter58/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter58/main.py)  ·  [view in browser](assets/simulations/chapter58/sim.py)

Run the implementation:

```bash
python python/chapter58/main.py
```

## Simulation

Source: [`simulations/chapter58/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter58/sim.py)  ·  [view in browser](assets/simulations/chapter58/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter58/sim.py
```

A browser version is available at [`browser/chapter58/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter58/index.html)  ·  [run live](assets/browser/chapter58/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `tensor parallelism` designs trade correctness, performance, and maintainability.

---

**Continue → [Why MoE Exists](59-why-moe-exists.md)**
