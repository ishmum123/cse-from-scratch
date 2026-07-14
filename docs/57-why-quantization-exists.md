# Fitting the Ocean into a Smaller Bottle

## The Problem

Llama 3 70B has 70 billion parameters. At FP32 (4 bytes per parameter), that's 280GB. At FP16 (2 bytes), it's 140GB. A high-end GPU — an NVIDIA A100 — has 80GB of VRAM. Even at FP16, Llama 3 70B doesn't fit on one A100. You need two. Two A100s cost roughly $30,000 and require dedicated infrastructure.

For a researcher or developer without a data center, running a 70B model is infeasible. Even for companies, serving many simultaneous requests requires many GPU-hours, and each GPU-hour at scale costs real money. A GPT-3-scale (175B) model at FP16 needs four A100s just to load — before any inference compute.

If you could represent each parameter with fewer bits without meaningfully degrading quality, models would fit on fewer GPUs, cost less to run, and become accessible to a wider community.

Any weight compression scheme must:

- Reduce memory footprint significantly (2–4× ideally)
- Preserve model quality for the tasks it will be used on
- Be fast to apply — ideally without full retraining
- Produce a model that runs efficiently on available hardware

## What Would You Try?

Before reading on:

- Neural network weights are typically small floats — most transformer weights fall in a range of roughly [-1, +1] with a near-Gaussian distribution. Do you need 32 bits to represent a value in that range?
- If you round each weight to the nearest value representable in 8 bits (256 possible values), what's the maximum absolute rounding error? Does the error matter equally for all weights?
- A model has 70B parameters. You quantize each from FP16 to INT8. What's the new size? What about INT4?

## Failed Attempts

### Attempt 1: Round All Weights to INT8 Naïvely

Convert every weight from FP16 to INT8 by scaling the range [min, max] of all weights to [−128, 127] and rounding. 2× size reduction.

INT8 has 256 distinct values. If a weight's true value is 0.1234 and the nearest INT8 value is 0.1250 (using the scale factor), the error is 0.0016. Small, right? The problem: errors accumulate through layers. Each layer has millions of such rounding errors; they compound multiplicatively through the attention computation and feedforward layers. Empirically, naïve INT8 quantization of all layers degrades perplexity (a measure of language model quality) by several points — enough to noticeably degrade generation quality. Some outlier weights with large magnitudes also distort the scale factor, wasting most of the 256 values on a range that only a handful of weights occupy.

### Attempt 2: Quantize Activations Too (Full Quantization)

Quantize both weights *and* activations to INT8. This enables INT8 matrix multiplication (hardware has native INT8 matmul on Tensor Cores). Better than quantizing weights alone because the full compute path is INT8.

Activations are harder to quantize than weights. Weights are fixed; you can compute their statistics offline and set scale factors once. Activations vary per input — the range of activation values for one prompt may be completely different from another. Dynamic quantization (compute scale factors at runtime per-batch) works but adds compute overhead. Static quantization (calibrate on representative inputs, fix scale factors) fails on inputs outside the calibration distribution. Activation outliers (LLM activations frequently contain large outliers, ~100× larger than typical values) make choosing a good scale factor nearly impossible — either you clip the outliers (losing information) or you waste precision range representing them (degrading precision for typical values).

### Attempt 3: Structured Pruning (Zeroing Out Weights)

Instead of representing weights with fewer bits, set some fraction of weights to exactly zero and store only the nonzero ones in sparse format. 50% sparsity = 2× compression.

Unstructured sparsity (set any individual weight to zero) rarely exceeds 50% without significant quality loss, and irregular sparsity patterns don't map well to GPU hardware — sparse matrix operations on GPUs often run slower than dense operations because the memory access pattern is irregular. Structured pruning (remove entire attention heads, layers, or neurons) maps to hardware better but requires architectural changes and often causes larger quality drops than weight quantization at the same compression ratio. NVIDIA's Ampere architecture added hardware support for 2:4 sparsity (2 zeros per 4 weights), giving 2× speedup for specifically that pattern — but it's limited.

## The Discovery

Naïve INT8 fails due to activation outliers and scale distortion. Full quantization fails because activations are input-dependent and contain outliers. Structured pruning wastes the structure of the hardware.

The key insight: not all parts of the model are equally sensitive to quantization. Weights are more quantizable than activations. Some layers are more sensitive than others. And the outlier problem can be solved by handling outliers separately.

**LLM.int8()** (Dettmers et al., 2022) decomposes the matrix multiplication: identify which activation dimensions have large outlier values, keep those dimensions in FP16, and quantize the remaining (typically 99.9%) to INT8. Mixed-precision matmul: INT8 for most values, FP16 for outlier dimensions. This preserves quality almost exactly while achieving 2× memory reduction for weights.

**GPTQ** (Frantar et al., 2022) uses a second-order optimization approach: quantize one weight at a time, then update the remaining weights to compensate for the introduced error. This is more accurate than rounding each weight independently because it corrects for the interaction of quantization errors. GPTQ achieves 3–4 bit quantization (INT4) with quality close to FP16 — 4× memory reduction.

**AWQ** (Lin et al., 2023) identifies that not all weights are equally important: the weights corresponding to high-magnitude activation channels matter more. Protect those weights (scale them before quantization to use their precision budget better), quantize everything else aggressively. 4-bit quantization with better quality than GPTQ in many benchmarks.

INT4 quantization: Llama 3 70B at 4 bits = 70B × 0.5 bytes = 35GB. Fits in one A100 with room for KV cache.

## Try It

<iframe src="../assets/browser/chapter57/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter57/index.html)

Before changing anything, predict:

- Set "Model (B params)" to 70. What does the FP32 memory bar show? Is it larger than a single A100's 80GB VRAM?
- With 70B params, drag "Quant bits" from 16 to 8 to 4. Watch both the GB figure and the tok/s estimate change. At what bit width does the model first fit in one A100?
- At INT4, does accuracy (the small bar at the bottom of each panel) drop noticeably from FP32?

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter57/index.html` (shared helpers in `browser/common/sim.js`). `drawModel()` renders both panels: it computes `fp32Mem = modelParams * 4` (bytes-per-param at FP32) and `intMem = modelParams * (quantBits / 8)`, and derives `intSpeed = Math.round(fp32Speed * (32 / quantBits))` as the proportional throughput gain. The memory bar height is `Math.min(100, Math.round(memGB * 3))` and the accuracy bar shows `Math.max(90, 100 - (32 - bits) * 0.5)` for quantized models. The `modelParams` and `quantBits` variables are bound to the two sliders.

## When It Breaks

**Accuracy cliffs at low bit widths.** Quality degrades smoothly from FP32 → INT8 → INT6 → INT5, then falls off sharply at INT4 and below for some tasks. The "accuracy cliff" is task-dependent: math reasoning and code generation degrade earlier than open-ended text generation. A model that scores 85% at INT8 might drop to 60% at INT3 on a math benchmark even though perplexity changes are modest. Downstream task evaluation matters more than perplexity metrics for deciding the quantization bit width.

**Quantization of quantization errors.** Quantizing a model that was fine-tuned (RLHF/instruction tuning) behaves differently than quantizing the base model. Fine-tuned models often have sharper weight distributions (some weights pushed further toward extreme values by RL), which increases quantization error for those weights. This is an active research problem with no universal solution; practitioners must evaluate each fine-tuned checkpoint separately.

## Transfer

- **Audio and image compression** (JPEG, MP3) are domain-specific quantization: represent pixel values or frequency coefficients with fewer bits, exploiting perceptual insensitivity to fine-grained numerical precision. The tradeoff is the same — fewer bits with minimal perceptual loss.
- **Fixed-point arithmetic in embedded systems** uses 8-bit or 16-bit integers instead of floats for all sensor data and control outputs — quantization is standard practice in devices with no FPU.
- **Model distillation** is a complementary technique: instead of quantizing a large model, train a smaller model to mimic the large model's outputs. Distillation changes architecture; quantization preserves it.

Try these:

1. A weight tensor has values uniformly distributed in [−0.5, 0.5]. You quantize to INT8 (256 levels). What's the average absolute quantization error? What if 1% of weights fall in [−5, 5]? How does the outlier 1% affect the scale factor and error for the other 99%?
2. GPTQ quantizes weights one column at a time and updates the remaining columns to compensate. What optimization are they solving? Why is this better than independent per-weight rounding?
3. A 70B INT4 model uses 35GB for weights plus 20GB for a 4096-token KV cache. What's the total memory requirement? Will it fit in two 40GB A100s? One 80GB A100?

---

**Continue → [Why Tensor Parallelism Exists](58-why-tensor-parallelism-exists.md)**
