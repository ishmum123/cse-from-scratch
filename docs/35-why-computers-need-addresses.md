# Why Computers Need Addresses

## The Problem

Two computers must talk, but they do not know each other exists.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Addresses uniquely identify machines on a network so messages can be routed.

## Implementation

We build a minimal `addressing` model in Python.

Source: [`python/chapter35/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter35/main.py)

Run the implementation:

```bash
python python/chapter35/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter35/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter35/index.html)  ·  [run live](assets/browser/chapter35/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `addressing` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Packets Exist](36-why-packets-exist.md)**
