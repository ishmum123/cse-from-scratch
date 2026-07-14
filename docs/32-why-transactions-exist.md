# Why Transactions Exist

## The Problem

A crash in the middle of an update leaves data half-changed.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Transactions group operations so they either all commit or all roll back.

## Implementation

We build a minimal `transaction` model in Python.

Source: [`python/chapter32/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter32/main.py)  ·  [view in browser](assets/simulations/chapter32/sim.py)

Run the implementation:

```bash
python python/chapter32/main.py
```

## Simulation

Source: [`simulations/chapter32/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter32/sim.py)  ·  [view in browser](assets/simulations/chapter32/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter32/sim.py
```

A browser version is available at [`browser/chapter32/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter32/index.html)  ·  [run live](assets/browser/chapter32/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `transaction` designs trade correctness, performance, and maintainability.

---

**Continue → [Why MVCC Exists](33-why-mvcc-exists.md)**
