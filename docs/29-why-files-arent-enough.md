# Why Files Aren't Enough

## The Problem

Reading a raw file for every query is unbearably slow.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Databases organize records so they can be found, updated, and queried efficiently.

## Implementation

We build a minimal `file storage` model in Python.

Source: [`python/chapter29/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter29/main.py)

Run the implementation:

```bash
python python/chapter29/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter29/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter29/index.html)  ·  [run live](assets/browser/chapter29/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `file storage` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Indexes Exist](30-why-indexes-exist.md)**
