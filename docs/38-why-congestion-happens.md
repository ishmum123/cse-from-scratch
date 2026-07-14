# Why Congestion Happens

## The Problem

Sending faster makes the network slower for everyone.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Congestion control adapts send rate to the network's actual capacity.

## Implementation

We build a minimal `congestion` model in Python.

Source: [`python/chapter38/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter38/main.py)  ·  [view in browser](assets/simulations/chapter38/sim.py)

Run the implementation:

```bash
python python/chapter38/main.py
```

## Simulation

Source: [`simulations/chapter38/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter38/sim.py)  ·  [view in browser](assets/simulations/chapter38/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter38/sim.py
```

A browser version is available at [`browser/chapter38/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter38/index.html)  ·  [run live](assets/browser/chapter38/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `congestion` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Load Balancers Exist](39-why-load-balancers-exist.md)**
