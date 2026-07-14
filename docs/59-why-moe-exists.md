# Why MoE Exists

## The Problem

Every token activates the entire model, wasting computation.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Mixture of Experts routes each token to a small subset of specialists.

## Implementation

We build a minimal `mixture of experts` model in Python.

Source: [`python/chapter59/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter59/main.py)

Run the implementation:

```bash
python python/chapter59/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter59/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter59/index.html)  ·  [run live](assets/browser/chapter59/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `mixture of experts` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Inference Servers Exist](60-why-inference-servers-exist.md)**
