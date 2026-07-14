# Why Transactions Exist — Discovery Notes

- **Problem:** A crash in the middle of an update leaves data half-changed.
- **Key idea:** Transactions group operations so they either all commit or all roll back.
- **Python:** [`python/chapter32/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter32/main.py)
- **C++:** [`cpp/chapter32/main.cpp`](https://github.com/ishmum123/cse-from-scratch/blob/main/cpp/chapter32/main.cpp)
- **Simulation:** [`simulations/chapter32/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter32/sim.py)
- **Browser sim:** [`browser/chapter32/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter32/index.html)
- **Continue:** [Why MVCC Exists](../docs/33-why-mvcc-exists.md)
