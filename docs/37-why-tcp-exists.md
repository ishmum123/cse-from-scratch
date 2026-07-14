# Why TCP Exists

## The Problem

Packets get lost, duplicated, or arrive out of order.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

TCP adds sequence numbers, acknowledgments, and retransmissions for reliable streams.

## Implementation

We build a minimal `tcp` model in Python.

Source: [`python/chapter37/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter37/main.py)

Run the implementation:

```bash
python python/chapter37/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/chapter37/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter37/index.html)  ·  [run live](assets/browser/chapter37/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `tcp` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Congestion Happens](38-why-congestion-happens.md)**
