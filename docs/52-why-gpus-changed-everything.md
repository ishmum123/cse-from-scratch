# Ten Thousand Workers Instead of One Fast One

## The Problem

Training a neural network on ImageNet (1.2 million images, 1,000 categories) with a 2012-era CPU cluster took weeks. The computation is straightforward: multiply matrices, add biases, apply a nonlinearity, repeat millions of times. The math isn't complex. There's just a lot of it — for every training image, every layer performs a matrix multiplication involving millions of floating-point operations.

A top-of-the-line CPU in 2012 executed roughly 100 billion floating-point operations per second (100 GFLOP/s). Training AlexNet required about 1.5 × 10¹⁸ floating-point operations total (1.5 exaFLOP). At 100 GFLOP/s: 15,000 seconds — over 4 hours for one pass through the data, and training requires hundreds of passes. Weeks of wall time.

The GPU approach took 5 days on two GTX 580s. The same math, 250× faster.

Any hardware approach to this problem must handle:

- Millions of identical arithmetic operations with no data dependencies between them
- Very high memory bandwidth to feed those operations
- A programming model that expresses the parallelism without race conditions
- Efficient use of silicon: don't spend die area on control logic that isn't needed

## What Would You Try?

Before reading on:

- A matrix multiplication C = A × B of size 1,000×1,000 requires ~10⁹ multiply-add operations. Each output element is independent of all others. Can you do them in parallel?
- CPUs spend most silicon area on caches, branch predictors, and out-of-order execution. What could you do with that silicon if you removed those units?
- 1,000 simultaneous arithmetic units sound great. What's the bottleneck if they all need data but memory can only deliver data fast enough for 100 of them?

## Failed Attempts

### Attempt 1: Faster CPUs and More Cores

Add more CPU cores. A 16-core CPU can do 16 matrix multiplications simultaneously. At 100 GFLOP/s per core, 16 cores = 1.6 TFLOP/s.

The problem: each CPU core is designed to handle *different* tasks well — branch prediction, out-of-order execution, large private caches for varied access patterns. This generality uses ~80% of the transistor budget for control logic. The arithmetic units themselves are a small fraction of each core. For matrix multiplication — where there are no branches, memory access patterns are predictable, and every operation is identical — all that control logic is wasted silicon. More CPU cores is incremental improvement in the wrong direction.

### Attempt 2: Vectorized CPU Instructions (SIMD)

Modern CPUs have SIMD (Single Instruction, Multiple Data) units: AVX-512 on Intel can do 16 float32 multiply-adds per cycle. At 3GHz, that's ~48 GFLOP/s per core — a 16× improvement over scalar. With 8 cores, ~384 GFLOP/s.

Better, but still fundamentally limited. SIMD width is bounded by die area — you can't keep widening vectors indefinitely. And SIMD requires careful alignment and data layout; general matrix multiplication code using SIMD (like BLAS libraries) is complex to write and maintain. The performance ceiling with 8 AVX-512 cores is around 1 TFLOP/s — still 250× behind a 2012-era GPU at 1.5 TFLOP/s single-precision.

### Attempt 3: Cluster of CPU Servers with MPI

Distribute the matrix multiplication across 250 servers. Each handles 1/250th of the computation. With network coordination, results are gathered.

At small scale this works. The fundamental bottleneck: network communication. Synchronizing a matrix multiplication across 250 servers requires transferring partial results — gigabytes of data — over the network at multiple points. Even at 100Gbps, transferring 10GB between servers takes 800ms. A GPU completes the same operation in ~10ms using its internal high-bandwidth memory bus (900GB/s on a V100). The network is 80× slower than GPU memory bandwidth. Distributed CPU clusters scale capacity but are network-bandwidth-bound for data-intensive computations.

## The Discovery

More CPU cores adds control logic overhead. SIMD helps but hits width limits. CPU clusters are network-bound. All three approaches try to make general-purpose hardware do specialized work.

The GPU insight: for matrix multiplication, you don't need general-purpose cores. You need *thousands of simple arithmetic units* that execute the *same instruction* on *different data* simultaneously. This is the SIMT model (Single Instruction, Multiple Threads).

An NVIDIA A100 GPU has 6,912 CUDA cores organized into 108 Streaming Multiprocessors (SMs). Every core in an SM executes the same instruction at the same time — no branch prediction needed, no out-of-order execution, minimal cache per core. The transistor budget goes to arithmetic, not control. Result: 312 TFLOP/s for tensor operations (matrix multiply-accumulate on 16-bit floats).

The key enabling piece is **high-bandwidth memory**: 2TB/s of memory bandwidth on an A100, vs ~50GB/s for a CPU. Matrix multiplication is memory-bandwidth-bound at large sizes — feeding data to the arithmetic units fast enough is the bottleneck. GPU memory is stacked and wide, physically close to the compute die, specifically to solve this.

The programming model (CUDA) maps computation to a grid of thread blocks: each thread computes one output element of the result matrix. Ten thousand threads run simultaneously, each independent. No shared state, no synchronization needed for the core computation. This is why the GPU model fits matrix multiplication so perfectly: the algorithm's independence structure matches the hardware's execution model.

## Try It

<iframe src="../assets/browser/chapter52/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter52/index.html)

Before changing anything, predict:

- Simulate matrix multiplication with 1 worker vs 1,000 workers on the same total work. How does wall-clock time scale with worker count?
- Add a "communication overhead" parameter simulating network sync. At what overhead does a distributed CPU approach start losing to the GPU?
- The simulation shows memory bandwidth saturation. At what arithmetic intensity does bandwidth stop being the bottleneck?

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter52/index.html` (shared helpers in `browser/common/sim.js`). The left panel uses `drawSerial()` — one node lights up per tick, advancing `serialStep` — while the right panel uses `drawParallel()`, which lights all `seqLen` nodes simultaneously, showing every pairwise connection at once. The strip chart accumulates throughput: the serial side processes one element per tick; the parallel side processes all elements per tick. The "Seq length" slider shows how the throughput gap widens with scale.

## When It Breaks

**Memory bandwidth, not FLOP count, is the real limit.** GPUs are marketed by TFLOP/s but most real workloads are memory-bandwidth-bound: fetching data to the arithmetic units can't keep up with how fast those units can compute. The roofline model captures this: a computation's performance ceiling is `min(peak FLOP/s, memory_bandwidth × arithmetic_intensity)`. For attention computation in transformers, arithmetic intensity can be as low as 1–4 FLOP per byte, meaning a 312 TFLOP/s GPU is limited to 2–8 TFLOP/s of effective throughput. This is why FlashAttention and other memory-efficient algorithms often outperform naive high-FLOP implementations.

**PCIe bottleneck between CPU and GPU.** Transferring data from CPU RAM to GPU memory uses PCIe, typically at 16–32 GB/s. A large dataset that doesn't fit in GPU memory must be transferred chunk by chunk. If transfer time exceeds compute time (low arithmetic intensity workloads), the GPU sits idle waiting for data. Optimal GPU programming keeps data on the GPU and minimizes CPU-GPU transfers.

## Transfer

- **Graphics rendering** (the original GPU use case) has the same structure: compute the color of millions of pixels independently. The parallelism maps naturally to SIMT, and game GPUs were already doing this at scale before ML research discovered the same hardware fit matrix operations.
- **Cryptocurrency mining** runs billions of SHA-256 hash computations independently — pure SIMT, no data dependencies. Crypto miners exhausted GPU supply twice (2017 and 2020) because the hardware characteristics are identical to ML training needs.
- **Scientific simulation** (weather modeling, molecular dynamics, fluid simulation) maps finite-difference and particle computations to GPU threads — the same data-parallel structure, predating ML's GPU adoption by years.

Try these:

1. An A100 has 312 TFLOP/s (BF16) and 2 TB/s memory bandwidth. At what arithmetic intensity (FLOP/byte) does the computation become compute-bound rather than memory-bound?
2. A matrix multiplication of 1,000×1,000 matrices. How many FLOP? If each GPU core does 1 FLOP/cycle at 1.5GHz, how many cores to complete in 1ms?
3. GPUs use 16-bit (FP16/BF16) arithmetic for training to double throughput. What precision loss does this introduce? When is it catastrophic (what kind of computation fails with FP16)?

---

**Continue → [Why Matrix Multiplication Is the Core Operation](53-why-matrix-multiplication-matters.md)**
