# Why KV Cache Exists — Discovery Notes

- **Problem:** Generating one token at a time recomputes the same keys and values.
- **Key idea:** The KV cache stores past key/value tensors so autoregressive generation only computes the new token.
- **Python:** [`python/chapter56/main.py`](https://github.com/ishmum123/cse-from-scratch/blob/main/python/chapter56/main.py)
- **C++:** [`cpp/chapter56/main.cpp`](https://github.com/ishmum123/cse-from-scratch/blob/main/cpp/chapter56/main.cpp)
- **Simulation:** [`browser/chapter56/index.html`](https://github.com/ishmum123/cse-from-scratch/blob/main/browser/chapter56/index.html)
- **Continue:** [Why Quantization Exists](../docs/57-why-quantization-exists.md)
