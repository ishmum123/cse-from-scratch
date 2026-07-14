# Why Threads Exist

## The Problem

A single process has work it could do in parallel.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Threads share memory within a process so multiple flows of execution can cooperate.

## Implementation

We build a minimal `thread` model in Python.

Source: [`python/chapter24/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter24/main.py)  ·  [view in browser](assets/simulations/chapter24/sim.py)

Run the implementation:

```bash
python python/chapter24/main.py
```

## Simulation

Source: [`simulations/chapter24/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter24/sim.py)  ·  [view in browser](assets/simulations/chapter24/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter24/sim.py
```

A browser version is available at [`browser/chapter24/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter24/index.html)  ·  [run live](assets/browser/chapter24/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `thread` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Locks Exist](25-why-locks-exist.md)**
