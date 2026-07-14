# Why Clocks Lie

## The Problem

Every machine thinks it knows the time. They disagree.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Without a shared clock, distributed systems must reason about causality and ordering instead.

## Implementation

We build a minimal `clock` model in Python.

Source: [`python/chapter41/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter41/main.py)  ·  [view in browser](assets/simulations/chapter41/sim.py)

Run the implementation:

```bash
python python/chapter41/main.py
```

## Simulation

Source: [`simulations/chapter41/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter41/sim.py)  ·  [view in browser](assets/simulations/chapter41/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter41/sim.py
```

A browser version is available at [`browser/chapter41/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter41/index.html)  ·  [run live](assets/browser/chapter41/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `clock` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Consensus Exists](42-why-consensus-exists.md)**
