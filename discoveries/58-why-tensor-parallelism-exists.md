# Why Tensor Parallelism Exists — Discovery Notes

- **Problem:** One GPU cannot hold a model, but many can if the work is split.
- **Key idea:** Tensor parallelism splits layers across devices so a model larger than one GPU can still run.
- **Python:** [`python/chapter58/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter58/main.py)
- **C++:** [`cpp/chapter58/main.cpp`](https://github.com/ishmum123/cse-from-scratch/blob/main/cpp/chapter58/main.cpp)
- **Simulation:** [`browser/chapter58/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter58/index.html)
- **Continue:** [Why MoE Exists](../docs/59-why-moe-exists.md)
