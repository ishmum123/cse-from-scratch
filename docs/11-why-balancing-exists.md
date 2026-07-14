# Why Balancing Exists

## The Problem

Your tree works beautifully until someone feeds it sorted data.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Balancing guarantees logarithmic height by restructuring the tree as it grows.

## Implementation

We build a minimal `balance` model in Python.

Source: [`python/chapter11/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter11/main.py)  ·  [view in browser](assets/simulations/chapter11/sim.py)

Run the implementation:

```bash
python python/chapter11/main.py
```

## Simulation

Source: [`simulations/chapter11/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter11/sim.py)  ·  [view in browser](assets/simulations/chapter11/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter11/sim.py
```

A browser version is available at [`browser/chapter11/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter11/index.html)  ·  [run live](assets/browser/chapter11/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `balance` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Hashing Exists](12-why-hashing-exists.md)**
