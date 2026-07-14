# Why Packets Exist

## The Problem

A single message can be too large or too fragile to send whole.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Packets split messages into small, independently routed units.

## Implementation

We build a minimal `packet` model in Python.

Source: [`python/chapter36/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter36/main.py)

Run the implementation:

```bash
python python/chapter36/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter36/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter36/index.html)  ·  [run live](assets/browser/chapter36/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `packet` designs trade correctness, performance, and maintainability.

---

**Continue → [Why TCP Exists](37-why-tcp-exists.md)**
