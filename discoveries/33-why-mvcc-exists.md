# Why MVCC Exists — Discovery Notes

- **Problem:** Readers and writers keep blocking each other.
- **Key idea:** Multi-version concurrency control lets readers see a consistent snapshot without locking.
- **Python:** [`python/chapter33/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter33/main.py)
- **C++:** [`cpp/chapter33/main.cpp`](https://github.com/ishmum123/cse-from-scratch/blob/main/cpp/chapter33/main.cpp)
- **Simulation:** [`simulations/chapter33/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter33/sim.py)
- **Browser sim:** [`browser/chapter33/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter33/index.html)
- **Continue:** [Why Query Planners Matter](../docs/34-why-query-planners-matter.md)
