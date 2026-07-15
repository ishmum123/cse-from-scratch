# Splitting the Model Across the Machines

## The Problem

GPT-4 is estimated to have a trillion parameters or more. Even at INT4 (0.5 bytes/parameter), that's 500GB. A cluster with ten A100s (10 × 80GB = 800GB) has enough aggregate VRAM, but no single GPU can hold the model. You need to split the model across GPUs — not just for storage, but for compute: the forward pass must touch every parameter, and no GPU can do that alone.

But splitting a model across GPUs introduces a problem you didn't have with one GPU: GPUs must communicate. After one GPU computes its partial result, the next GPU needs those results before it can continue. Communication is slow — even NVLink (the high-speed GPU interconnect) runs at ~600GB/s, while a single A100's internal memory bandwidth is 2TB/s. Every inter-GPU communication is ~3× slower than intra-GPU computation.

Any distributed inference/training strategy must:

- Divide the model so each GPU fits its partition in VRAM
- Minimize inter-GPU communication volume
- Keep all GPUs busy simultaneously (no GPU waiting for another)
- Scale linearly: doubling GPUs should roughly halve time

## What Would You Try?

Before reading on:

- A model has 96 layers. One obvious split: put layers 1–48 on GPU 1 and layers 49–96 on GPU 2. What's the problem with this split during inference? During training?
- A matrix multiplication W × x where W is very large. Can you split W across GPUs and compute the result without each GPU having all of W?
- Communication volume vs. computation volume: if you double the matrix size, computation grows as O(n²) but what grows slower? What does this imply about large-matrix parallelism efficiency?

## Failed Attempts

### Attempt 1: Pipeline Parallelism (Layer-Wise Split)

Assign each GPU a contiguous block of layers. GPU 1 runs layers 1–24, GPU 2 runs 25–48, GPU 3 runs 49–72, GPU 4 runs 73–96. Input flows sequentially through the pipeline.

At any given moment, only one GPU is active — the rest are waiting for the previous GPU to finish its layers. GPU 1 computes, then sends its output to GPU 2 and sits idle while GPU 2 computes. "Pipeline bubble" = (number of GPUs − 1) × (time per GPU stage) of wasted idle time. At 4 GPUs, you're idle 75% of the time. GPT-3 training at 1,024 GPUs with pure pipeline parallelism would waste 99.9% of GPU time. Micro-batching reduces bubbles (process multiple mini-batches to keep the pipeline full), but adds memory overhead (storing intermediate activations for all in-flight batches).

### Attempt 2: Data Parallelism (Replicate Model, Split Batch)

Each GPU has a full copy of the model. Split the training batch across GPUs — each GPU sees a different data subset. After each forward/backward pass, GPUs communicate their gradients and update weights synchronously.

Data parallelism is perfect for throughput: N GPUs gives ~N× effective batch size, proportional training speedup. But it requires each GPU to hold the full model. At 500GB model, data parallelism requires 500GB per GPU — you're back to the original problem. Data parallelism doesn't solve the "model too large to fit on one GPU" problem. It solves "training too slow" for models that do fit.

### Attempt 3: Expert Partitioning (Put Different Weights on Different GPUs)

Split the model by component: GPU 1 holds the embedding table, GPU 2 holds attention heads 1–8, GPU 3 holds attention heads 9–16, GPU 4 holds the feedforward layers. Each GPU specializes in its component.

The communication pattern is irregular and frequent. For a single attention block, the activations must visit GPU 2 and GPU 3 (for the full multi-head attention output), then combine their results, then go to GPU 4 for the FFN. Activation transfers between every attention head's computation introduces massive communication overhead. The communication isn't "one big transfer at the end" but "many small transfers constantly," which is exactly what GPU interconnects are bad at (fixed per-message overhead dominates small transfers).

## The Discovery

Pipeline parallelism idles GPUs. Data parallelism doesn't fit large models. Expert partitioning creates frequent small communications. All three fail to exploit the mathematical structure of matrix multiplication.

The key insight: a matrix multiply can be *split along either dimension* without requiring communication until the very end.

**Tensor Parallelism** (Megatron-LM, Shoeybi et al., 2019): split each large weight matrix across GPUs, either column-wise or row-wise.

For a column-wise split of weight W = [W_1 | W_2] across 2 GPUs: GPU 1 computes x × W_1 and GPU 2 computes x × W_2. Both receive the same input x (cheap broadcast). Their outputs are halves of the full result — concatenate them to get x × W. The concatenation is the only communication: one all-gather after the matmul, not before.

For the next layer (row-wise split): GPU 1 receives the first half of the concatenated result and multiplies it by the first half of the next weight. GPU 2 receives the second half. Their partial sums are added (all-reduce): one reduction per layer.

The communication volume per layer: one all-reduce of the activation tensor (not the weight tensors). Activation size = batch_size × sequence_length × d_model. At d_model=8,192 and batch=32, sequence=2,048: ~0.5GB per all-reduce. At 600GB/s NVLink, that's ~1ms per layer. A 96-layer forward pass has 96 all-reduces at 1ms each: ~96ms of pure communication, vs ~200ms of computation at full GPU utilization. Communication is ~32% of total time — acceptable efficiency.

Combining all three: **3D parallelism** (data × tensor × pipeline) is used by training runs at scale. GPT-3 training used 1,024 A100s: 64 tensor-parallel groups of 16 GPUs, each group using 8-way pipeline parallelism within, with data parallelism across the 8 identical pipelines.

## Try It

<iframe src="../assets/browser/chapter58/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter58/index.html)

Before changing anything, predict:

- Split a large matrix multiplication across 2 vs 4 GPUs using tensor parallelism. Does compute time halve with each doubling? Does communication time?
- At what model size does tensor parallelism start making sense vs fitting the model in one GPU?
- What happens to efficiency as you increase the number of GPUs from 4 to 8 to 16?

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter58/index.html` (shared helpers in `browser/common/sim.js`). `drawSingle()` shows one device holding the full `modelGB` and taking `baseTime` ms per step; `drawParallel()` splits the model across `K = deviceCount` devices: `perDevMem = modelGB / K` per device, `parallelTime = ceil(baseTime / K) + 5` (the +5 ms represents allreduce overhead). The `VRAM_CAP = 24` GB cap highlights when the single device is over-capacity. Use the "Model size (GB)" and "Device count" sliders to find where parallelism pays for itself despite the communication cost.

## When It Breaks

**Communication-compute overlap fails for small batches.** Modern GPU frameworks overlap communication with computation: while GPU 1 sends its partial result, GPU 2 starts computing on the next micro-batch. This overlap hides communication latency. But it only works at large batch sizes — small batches have short compute phases that don't cover the communication time. For single-request online inference (batch size = 1, chapter 59), tensor parallelism communication is proportionally much larger relative to compute, often making it inefficient for inference even when it's essential for training.

**NVLink topology matters.** NVLink connects GPUs in pairs or rings, not full mesh. An 8-GPU all-reduce must traverse multiple hops on a ring topology. Communication time scales with data size AND topology distance. A model that's efficient on 4 tensor-parallel GPUs (connected directly via NVLink) may be inefficient at 8 (where some communications require 3 hops). Production deployments carefully match tensor parallelism degree to NVLink connectivity topology.

## Transfer

- **MapReduce** is data parallelism: the "map" phase distributes computation across machines, the "reduce" phase aggregates results. The all-reduce in tensor parallelism is literally a reduce: sum partial results from all GPUs.
- **BLAS (Basic Linear Algebra Subroutines)** libraries on multi-socket CPUs use the same column/row split: each NUMA node owns a contiguous chunk of the matrix and contributes partial sums that are reduced across nodes.
- **Federated learning** applies a form of data parallelism to distributed private data: each participant trains on local data and contributes gradient updates, which are aggregated (all-reduced) to update the global model — without centralizing the data.

Try these:

1. A model layer has weight W of shape (8192, 8192) in FP16. Split across 4 GPUs using column parallelism. How much VRAM does each GPU use for this weight? What's the all-gather communication size for one forward pass with batch=32, seq=2048, d_model=8192?
2. Pipeline parallelism with 4 stages and micro-batch size 8: the "bubble" fraction (wasted idle GPU cycles) is (num_stages - 1) / (num_stages + num_micro_batches - 1). Calculate bubble fraction for 4 stages + 8 micro-batches. How many micro-batches would you need to get bubble fraction below 10%?
3. 3D parallelism: 128 GPUs arranged as 4-way data parallel × 8-way tensor parallel × 4-way pipeline parallel. A model requires 800GB to store all weights at FP16. How many GB of weights does each GPU hold?

---

**Continue → [Why MoE Exists](59-why-moe-exists.md)**
