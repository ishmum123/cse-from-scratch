# Why Distributed Transactions Hurt — Discovery Notes

- **Problem:** Distributed transactions stall when one node hesitates.
- **Key idea:** Two-phase commit and sagas trade strong consistency for coordination overhead and fragility.
- **Python:** [`python/chapter45/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter45/main.py)
- **C++:** [`cpp/chapter45/main.cpp`](https://github.com/ishmum123/cse-from-scratch/blob/main/cpp/chapter45/main.cpp)
- **Simulation:** [`simulations/chapter45/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter45/sim.py)
- **Browser sim:** [`browser/chapter45/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter45/index.html)
- **Continue:** [Why Caches Exist](../docs/46-why-caches-exist.md)
