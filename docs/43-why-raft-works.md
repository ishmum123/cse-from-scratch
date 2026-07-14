# Why Raft Works

## The Problem

You need consensus, but Paxos is impossible to implement.

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

Raft separates leader election, log replication, and safety into understandable rules.

## Implementation

We build a minimal `raft` model in Python.

Source: [`python/chapter43/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter43/main.py)  ·  [view in browser](assets/simulations/chapter43/sim.py)

Run the implementation:

```bash
python python/chapter43/main.py
```

## Simulation

Source: [`simulations/chapter43/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter43/sim.py)  ·  [view in browser](assets/simulations/chapter43/sim.py)

Run the chapter simulation:

```bash
python simulations/chapter43/sim.py
```

A browser version is available at [`browser/chapter43/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter43/index.html)  ·  [run live](assets/browser/chapter43/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `raft` designs trade correctness, performance, and maintainability.

---

**Continue → [Why Eventual Consistency Exists](44-why-eventual-consistency-exists.md)**
