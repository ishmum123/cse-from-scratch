# Why Queues Exist

## The Problem

Tasks arrive in order and must be handled fairly.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

A queue processes items in first-in-first-out order, decoupling producers and consumers.

## Implementation

We build a minimal `queue` model in Python.

Source: [`python/chapter21/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter21/main.py)  ·  [view in browser](assets/simulations/chapter21/sim.py)

Run the implementation:

```bash
python python/chapter21/main.py
```

## Simulation

Source: [`simulations/chapter21/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter21/sim.py)  ·  [view in browser](assets/simulations/chapter21/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter21/sim.py
```

A browser version is available at [`browser/chapter21/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter21/index.html)  ·  [run live](assets/browser/chapter21/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `queue` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Schedulers Exist](22-why-schedulers-exist.md)**
