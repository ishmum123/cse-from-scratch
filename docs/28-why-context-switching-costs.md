# Why Context Switching Costs

## The Problem

Switching between tasks costs more than the tasks themselves.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Saving and restoring registers, caches, and TLB state makes switching expensive.

## Implementation

We build a minimal `context switch` model in Python.

Source: [`python/chapter28/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter28/main.py)

Run the implementation:

```bash
python python/chapter28/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter28/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter28/index.html)  ·  [run live](assets/browser/chapter28/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `context switch` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Files Aren't Enough](29-why-files-arent-enough.md)**
