# Why Transformers Scale — Discovery Notes

- **Problem:** Recurrent models forget and cannot train in parallel.
- **Key idea:** Transformers replace recurrence with self-attention, enabling parallel training over whole sequences.
- **Python:** [`python/chapter55/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter55/main.py)
- **C++:** [`cpp/chapter55/main.cpp`](https://github.com/ishmum123/cse-from-scratch/blob/main/cpp/chapter55/main.cpp)
- **Simulation:** [`simulations/chapter55/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter55/sim.py)
- **Browser sim:** [`browser/chapter55/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter55/index.html)
- **Continue:** [Why KV Cache Exists](../docs/56-why-kv-cache-exists.md)
