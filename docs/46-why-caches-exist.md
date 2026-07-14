# Why Caches Exist

## The Problem

The database is fast, but the network to reach it is slow.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Caches keep hot data close to consumers, trading freshness for speed.

## Implementation

We build a minimal `cache` model in Python.

Source: [`python/chapter46/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter46/main.py)

Run the implementation:

```bash
python python/chapter46/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter46/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter46/index.html)  ·  [run live](assets/browser/chapter46/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `cache` designs trade correctness, performance, and maintainability.

---

**Continue → [Why CDNs Exist](47-why-cdns-exist.md)**
