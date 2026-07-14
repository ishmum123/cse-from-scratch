# Why Attention Exists

## The Problem

A word's meaning depends on every other word in the sentence.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Attention computes pairwise relevance so each token can gather context from the whole sequence.

## Implementation

We build a minimal `attention` model in Python.

Source: [`python/chapter54/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter54/main.py)  ·  [view in browser](assets/simulations/chapter54/sim.py)

Run the implementation:

```bash
python python/chapter54/main.py
```

## Simulation

Source: [`simulations/chapter54/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter54/sim.py)  ·  [view in browser](assets/simulations/chapter54/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter54/sim.py
```

A browser version is available at [`browser/chapter54/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter54/index.html)  ·  [run live](assets/browser/chapter54/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `attention` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Transformers Scale](55-why-transformers-scale.md)**
