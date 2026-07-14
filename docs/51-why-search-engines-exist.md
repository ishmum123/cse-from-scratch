# Why Search Engines Exist

## The Problem

Users type vague words and expect instant, ranked results.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Search engines index, tokenize, and score documents to answer free-text queries.

## Implementation

We build a minimal `search engine` model in Python.

Source: [`python/chapter51/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter51/main.py)

Run the implementation:

```bash
python python/chapter51/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter51/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter51/index.html)  ·  [run live](assets/browser/chapter51/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `search engine` designs trade correctness, performance, and maintainability.

---

**Continue → [Why GPUs Changed Everything](52-why-gpus-changed-everything.md)**
