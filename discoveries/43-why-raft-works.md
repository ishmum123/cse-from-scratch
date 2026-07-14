# Why Raft Works — Discovery Notes

- **Problem:** You need consensus, but Paxos is impossible to implement.
- **Key idea:** Raft separates leader election, log replication, and safety into understandable rules.
- **Python:** [`python/chapter43/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter43/main.py)
- **C++:** [`cpp/chapter43/main.cpp`](https://github.com/ishmum123/cse-from-scratch/blob/main/cpp/chapter43/main.cpp)
- **Simulation:** [`simulations/chapter43/sim.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/simulations/chapter43/sim.py)
- **Browser sim:** [`browser/chapter43/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter43/index.html)
- **Continue:** [Why Eventual Consistency Exists](../docs/44-why-eventual-consistency-exists.md)
