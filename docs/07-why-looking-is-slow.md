# Why Looking Is Slow

## The Problem

You open a box and search every item one by one.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Unordered search is linear; the only way to speed it up is to remove the need to look at everything.

## Implementation

We build a minimal `linear search` model in Python.

Source: [`python/chapter07/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter07/main.py)  ·  [view in browser](assets/simulations/chapter07/sim.py)

Run the implementation:

```bash
python python/chapter07/main.py
```

## Simulation

Source: [`simulations/chapter07/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter07/sim.py)  ·  [view in browser](assets/simulations/chapter07/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter07/sim.py
```

A browser version is available at [`browser/chapter07/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter07/index.html)  ·  [run live](assets/browser/chapter07/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `linear search` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Ordering Helps](08-why-ordering-helps.md)**
