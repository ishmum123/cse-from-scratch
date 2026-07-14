# Why Load Balancers Exist

## The Problem

One server dies and the whole service disappears.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Load balancers spread traffic across many backends and hide failures.

## Implementation

We build a minimal `load balancer` model in Python.

Source: [`python/chapter39/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter39/main.py)

Run the implementation:

```bash
python python/chapter39/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter39/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter39/index.html)  ·  [run live](assets/browser/chapter39/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `load balancer` designs trade correctness, performance, and maintainability.

---

**Continue → [Why One Computer Isn't Enough](40-why-one-computer-isnt-enough.md)**
