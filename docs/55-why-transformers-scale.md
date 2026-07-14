# Why Transformers Scale

## The Problem

Recurrent models forget and cannot train in parallel.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Transformers replace recurrence with self-attention, enabling parallel training over whole sequences.

## Implementation

We build a minimal `transformer` model in Python.

Source: [`python/chapter55/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter55/main.py)  ·  [view in browser](assets/simulations/chapter55/sim.py)

Run the implementation:

```bash
python python/chapter55/main.py
```

## Simulation

Source: [`simulations/chapter55/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter55/sim.py)  ·  [view in browser](assets/simulations/chapter55/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter55/sim.py
```

A browser version is available at [`browser/chapter55/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter55/index.html)  ·  [run live](assets/browser/chapter55/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `transformer` designs trade correctness, performance, and maintainability.

---

**Continue → [Why KV Cache Exists](56-why-kv-cache-exists.md)**
