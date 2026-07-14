# Why CDNs Exist

## The Problem

Users on the other side of the world wait seconds for each request.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

CDNs place content near users, reducing latency and origin load.

## Implementation

We build a minimal `cdn` model in Python.

Source: [`python/chapter47/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter47/main.py)  ·  [view in browser](assets/simulations/chapter47/sim.py)

Run the implementation:

```bash
python python/chapter47/main.py
```

## Simulation

Source: [`simulations/chapter47/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter47/sim.py)  ·  [view in browser](assets/simulations/chapter47/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter47/sim.py
```

A browser version is available at [`browser/chapter47/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter47/index.html)  ·  [run live](assets/browser/chapter47/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `cdn` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Queues Exist](48-why-queues-exist.md)**
