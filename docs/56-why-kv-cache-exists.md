# Why KV Cache Exists

## The Problem

Generating one token at a time recomputes the same keys and values.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

The KV cache stores past key/value tensors so autoregressive generation only computes the new token.

## Implementation

We build a minimal `kv cache` model in Python.

Source: [`python/chapter56/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter56/main.py)

Run the implementation:

```bash
python python/chapter56/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter56/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter56/index.html)  ·  [run live](assets/browser/chapter56/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `kv cache` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Quantization Exists](57-why-quantization-exists.md)**
