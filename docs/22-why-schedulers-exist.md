# Why Schedulers Exist

## The Problem

Every process wants the CPU at the same time.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

A scheduler decides who runs next, balancing fairness, latency, and throughput.

## Implementation

We build a minimal `scheduler` model in Python.

Source: [`python/chapter22/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter22/main.py)

Run the implementation:

```bash
python python/chapter22/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter22/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter22/index.html)  ·  [run live](assets/browser/chapter22/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `scheduler` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Processes Exist](23-why-processes-exist.md)**
