# Why Virtual Memory Exists

## The Problem

Programs expect memory that does not exist.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Virtual memory maps program addresses to physical pages, enabling isolation and swapping.

## Implementation

We build a minimal `virtual memory` model in Python.

Source: [`python/chapter27/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter27/main.py)

Run the implementation:

```bash
python python/chapter27/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter27/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter27/index.html)  ·  [run live](assets/browser/chapter27/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `virtual memory` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Context Switching Costs](28-why-context-switching-costs.md)**
