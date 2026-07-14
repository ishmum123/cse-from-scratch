# Why One Computer Isn't Enough

## The Problem

One machine can no longer hold all the data or traffic.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Distributed systems partition work across independent machines connected by a network.

## Implementation

We build a minimal `distribution` model in Python.

Source: [`python/chapter40/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter40/main.py)

Run the implementation:

```bash
python python/chapter40/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter40/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter40/index.html)  ·  [run live](assets/browser/chapter40/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `distribution` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Clocks Lie](41-why-clocks-lie.md)**
