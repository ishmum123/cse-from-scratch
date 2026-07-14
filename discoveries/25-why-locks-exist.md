# Why Locks Exist — Discovery Notes

- **Problem:** Two threads change the same value and corrupt it.
- **Key idea:** Locks enforce mutual exclusion so only one thread touches shared state at a time.
- **Python:** [`python/chapter25/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter25/main.py)
- **C++:** [`cpp/chapter25/main.cpp`](https://github.com/ishmum123/cse-from-scratch/blob/main/cpp/chapter25/main.cpp)
- **Simulation:** [`browser/chapter25/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter25/index.html)
- **Continue:** [Why Deadlocks Happen](../docs/26-why-deadlocks-happen.md)
