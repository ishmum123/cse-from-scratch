# Why Query Planners Matter

## The Problem

The same query runs fast one day and slow the next.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

A planner chooses the cheapest way to execute a query using statistics and cost models.

## Implementation

We build a minimal `query planner` model in Python.

Source: [`python/chapter34/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter34/main.py)  ·  [view in browser](assets/simulations/chapter34/sim.py)

Run the implementation:

```bash
python python/chapter34/main.py
```

## Simulation

Source: [`simulations/chapter34/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter34/sim.py)  ·  [view in browser](assets/simulations/chapter34/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter34/sim.py
```

A browser version is available at [`browser/chapter34/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter34/index.html)  ·  [run live](assets/browser/chapter34/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `query planner` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Computers Need Addresses](35-why-computers-need-addresses.md)**
