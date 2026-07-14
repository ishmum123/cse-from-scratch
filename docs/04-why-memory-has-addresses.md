# Why Memory Has Addresses

## The Problem

You stored a value, but now you cannot find it again.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Every location in memory has an address, so the machine can fetch or store by number.

## Implementation

We build a minimal `address` model in Python.

Source: [`python/chapter04/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter04/main.py)  ·  [view in browser](assets/simulations/chapter04/sim.py)

Run the implementation:

```bash
python python/chapter04/main.py
```

## Simulation

Source: [`simulations/chapter04/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter04/sim.py)  ·  [view in browser](assets/simulations/chapter04/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter04/sim.py
```

A browser version is available at [`browser/chapter04/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter04/index.html)  ·  [run live](assets/browser/chapter04/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `address` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Copying Is Expensive](05-why-copying-is-expensive.md)**
