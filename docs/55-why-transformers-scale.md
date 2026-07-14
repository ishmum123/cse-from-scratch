# Why More Data and More Compute Keep Helping

## The Problem

In 2017, the best language models plateaued. Adding more training data to an LSTM or GRU improved performance — up to a point. Beyond roughly 1 billion tokens, the curves flattened. Bigger models didn't consistently help. The architecture itself seemed to be the bottleneck: sequential computation prevented using more GPUs efficiently, and the fixed-size hidden state limited what could be learned from more data.

Then transformers appeared. GPT-1 (2018): 117M parameters, trained on BookCorpus, decent performance. GPT-2 (2019): 1.5B parameters, 10× more data, qualitatively better — surprising generation quality. GPT-3 (2020): 175B parameters, 300B tokens, emergent capabilities that weren't predicted from smaller-scale experiments — arithmetic, few-shot learning, code generation. GPT-4 (2023): estimated trillions of parameters-equivalent, capabilities that none of the previous models had shown at any scale.

Something about transformers scales differently from all prior architectures. Why?

Any scalable architecture must:

- Train faster as you add more GPUs (parallelizable over both data and model)
- Improve predictably as you add more parameters and data
- Not have a hidden bottleneck that caps useful model size
- Generalize to new tasks without architectural changes

## What Would You Try?

Before reading on:

- RNNs process tokens sequentially. Why does this prevent full GPU utilization during training?
- If a model has 175B parameters and you process 300B training tokens, you're fitting a very complex function to a massive dataset. What determines whether this leads to generalization vs memorization?
- Neural scaling laws say "loss ∝ N^{-α}" where N is parameter count. What does this imply about the relationship between compute budget and optimal model size?

## Failed Attempts

### Attempt 1: Scale RNNs to More Parameters

Build a deeper, wider LSTM. Add more hidden dimensions, more layers. This worked for CNNs (deeper networks learned better image features), so why not for language?

RNNs don't parallelize over the sequence. Training a 1-billion-parameter LSTM on a 1-billion-token dataset requires 1 billion × (sequence length) sequential steps. You can parallelize over batch size (many sequences in parallel), but not over position within a sequence. A GPU running 10,000 threads in parallel is reduced to processing one position at a time when the computation is sequential. GPUs sit mostly idle. Adding more GPUs helps less than linearly because the bottleneck is sequential, not parallel.

### Attempt 2: Scale Convolutions — More Filters, More Layers

Convolutional language models (ByteNet, TCN) are fully parallelizable over position — no sequential dependency. Add more filters, more layers, wider kernels.

The context limitation (chapter 54): a convolutional model with window size W needs O(log_W(n)) layers to connect position 1 to position n. Each additional layer adds non-linearity and the potential for information loss. Very deep convolutional language models exist (WaveNet has 30 layers) but they don't show the same scaling behavior as transformers. The inductive bias of local connectivity seems to cap performance on global language understanding, regardless of depth.

### Attempt 3: Make Attention More Efficient Rather Than Scaling

Sparse attention, linear attention approximations, performers — all reduce the O(n²) attention cost to make longer sequences feasible. Train smaller-attention models at larger scale.

These approximations reduce the cost but also reduce quality. Exact attention (seeing every token-pair relationship) captures long-range dependencies that sparse attention misses. On benchmarks, efficient attention models consistently underperform full attention models of the same parameter count. You're trading the capability that makes attention powerful for the tractability that lets you scale. The result: competitive-but-not-best models. The empirical evidence is clear: on most tasks, exact attention at smaller scale beats approximate attention at larger scale.

## The Discovery

RNNs can't parallelize. Convolutions can't span arbitrary distances. Efficient attention trades quality for scale. Each approach fails to preserve the property most needed for scaling: exact global context with full parallelism.

Transformers preserve both. The architecture:

**Attention** (chapter 54): O(n²) computation but fully parallel over the sequence — every position's output computed simultaneously via matrix multiplication. Training a 1,024-token sequence uses the same number of serial steps as training a 1-token sequence (just with larger matrices). GPU utilization scales with matrix size, not sequence length.

**Position-independent MLP (Feed-Forward)**: applied independently and identically to each position. Another large matrix multiplication — also fully parallel.

**Residual connections + layer normalization**: keep gradients healthy through depth, enabling very deep networks (96 layers in GPT-3) to train without vanishing gradient.

The scaling laws (Kaplan et al., 2020) are the empirical payoff: loss decreases as a smooth power law in both parameter count N and training compute C, across 7 orders of magnitude. `L(N) ≈ (N_c/N)^{α_N}` with α_N ≈ 0.076. Double the parameters, lose roughly 5% of the loss. The law is smooth and shows no sign of a plateau through current scales. This is unprecedented: no prior architecture showed this behavior.

The implication: compute budget determines optimal model size. Chinchilla (Hoffmann et al., 2022) showed that most models were undertrained — for a fixed compute budget, train a smaller model for longer, not the other way around. GPT-3's 175B parameters trained for 300B tokens was suboptimal; the optimal would have been a ~70B model trained for ~1.4T tokens.

## Try It

<iframe src="../assets/browser/chapter55/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter55/index.html)

Before changing anything, predict:

- Double the number of layers. How does training time change? How does loss change?
- Reduce sequence length by half. Does training speed scale linearly? (It shouldn't, for attention — why not?)
- Compare the scaling curve for a transformer vs a simulated RNN. At what parameter count do they diverge?

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter55/index.html` (shared helpers in `browser/common/sim.js`). Look for the layer stack in `forward()`: attention → add+norm → FFN → add+norm. The residual connections are the `+` operations in `add+norm`, and they're what makes 96-layer training stable.

## When It Breaks

**Emergent capabilities are unpredictable.** Scaling laws predict loss, not capability. Some capabilities appear only above a certain scale threshold — "emergent abilities" that weren't present at smaller scales and weren't predicted. Arithmetic appeared around 100B parameters. Multi-step reasoning appeared around 500B. The mechanism is unclear. This makes it impossible to predict from small-scale experiments whether a given capability will appear at deployment scale. Research groups regularly get surprised by what their large models can and cannot do.

**Diminishing returns on specific tasks.** While aggregate language modeling loss decreases smoothly with scale, specific task performance can plateau, oscillate, or even regress (the "U-shaped" performance curve observed on some tasks as model scale increases). Scaling is not a universal solution: safety behaviors, factual accuracy, and calibration don't always improve with scale and sometimes require targeted techniques (RLHF, instruction tuning) that are independent of base model scale.

## Transfer

- **Biological scaling**: evolution increased primate brain size over millions of years, improving cognitive abilities roughly proportionally to neocortex volume. Transformer scaling may be a convergent discovery: "more of the same basic unit" is the most reliable path to greater capability in both biological and artificial neural networks.
- **AlphaFold** and **AlphaCode** applied the same scaling insight to biology and programming: transformer architectures trained on protein sequences and code, scaled to hundreds of millions of parameters, produced unprecedented performance on tasks no algorithm had previously approached.
- **Multimodal transformers** (DALL-E, GPT-4V, Gemini) extend the same architecture to images, audio, and video — inputs are tokenized differently but the same attention + scaling laws apply, showing the transformer is an architecture that generalizes across modalities.

Try these:

1. Chinchilla scaling law: for a compute budget of 10²³ FLOPs, what is the optimal model size and training token count? (Use N_opt ≈ (C/6)^{0.5} as an approximation.)
2. A transformer has 12 layers, 12 attention heads, d_model=768, FFN width=3072. Count the parameters in: (a) all attention projection matrices, (b) all FFN layers, (c) the output embedding.
3. "Emergent abilities" appear sharply above a threshold. What does this suggest about interpolating performance from small models to large? Why would a research team be wrong to predict GPT-4 capabilities from GPT-2 experiments?

---

**Continue → [Why KV Cache Exists](56-why-kv-cache-exists.md)**
