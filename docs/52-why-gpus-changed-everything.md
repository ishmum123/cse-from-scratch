# Why GPUs Changed Everything

## The Problem

CPUs cannot train billion-parameter models in a human lifetime.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

GPUs execute thousands of parallel threads, turning matrix math from a bottleneck into a throughput engine.

## Implementation

We build a minimal `gpu` model in Python.

Source: [`python/chapter52/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter52/main.py)

Run the implementation:

```bash
python python/chapter52/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter52/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter52/index.html)  ·  [run live](assets/browser/chapter52/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `gpu` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Matrix Multiplication Matters](53-why-matrix-multiplication-matters.md)**
