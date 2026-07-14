# Why Locks Exist

## The Problem

Two threads change the same value and corrupt it.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Locks enforce mutual exclusion so only one thread touches shared state at a time.

## Implementation

We build a minimal `lock` model in Python.

Source: [`python/chapter25/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter25/main.py)

Run the implementation:

```bash
python python/chapter25/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter25/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter25/index.html)  ·  [run live](assets/browser/chapter25/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `lock` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Deadlocks Happen](26-why-deadlocks-happen.md)**
