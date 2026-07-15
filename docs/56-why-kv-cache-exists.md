# Never Recompute What You Already Know

## The Problem

A language model generates text one token at a time. Each new token requires a full forward pass through all layers. In attention (chapter 54), each new token computes Q, K, V vectors for itself — and then attends to *every previous token in the context*. The keys and values for previous tokens are recomputed from scratch at every step.

To generate the 100th token in a sequence: compute K, V for all 100 tokens (including the 99 you've already generated), compute attention weights, generate the next token. For the 101st: compute K, V for all 101 tokens. For the Nth token: O(N) work per step, with N growing.

A context of 8,192 tokens with 96 layers and 16 attention heads: at step N, you recompute (N × 96 × 16 × 2) key and value vectors — all to produce one new K, V pair per head per layer for the new token. By token 8,000, you're spending 99.99% of your compute recomputing values you already computed at step 1.

Any generation optimization must:

- Avoid recomputing unchanged values as the sequence grows
- Store the cache without consuming so much memory that you can't run the model
- Handle variable-length contexts without fixed pre-allocation
- Work across all layers and heads without changing the attention semantics

## What Would You Try?

Before reading on:

- For the Nth token, the K and V vectors for tokens 1 through N-1 are identical to what you computed at step N-1. Why recompute them?
- If you cache all K and V vectors for all previous tokens, what's the memory cost? For a 96-layer, 32-head model with d_head=128, and N=4,096 tokens, in FP16?
- Attention for the new token requires: Q_new × K_all. If you cache K_all, you only need to compute Q_new (a single vector). How does this change the computation?

## Failed Attempts

### Attempt 1: Full Recomputation Every Step

The naïve approach: no cache. For every new token, run the full forward pass over the entire context. Simplest to implement; no additional memory.

As shown above, this is O(N) work per token and O(N²) total for a sequence of N tokens. For N=4,096, generating the last token does 4,096× more attention computation than generating the first. For N=32,768 (modern long-context models), the last token does 32,768× more work than the first. Total generation time scales quadratically with context length. Generating 100 tokens with 4,096 context costs ~200,000 attention head evaluations. Generating 1,000 tokens costs ~1B. This makes long-context generation impractically slow.

### Attempt 2: Recompute Only the Last K Layers

Heuristic: the lower layers of the transformer learn stable, general representations. Cache those. Recompute only the top K layers each step, which supposedly refine the representation for the specific position.

This reduces computation but introduces a correctness problem. Attention in layer L+1 attends to the outputs of layer L from all previous tokens. If layer L's outputs for previous tokens aren't recomputed, and you're updating only layer L+1 with new token information — the cross-layer interaction is broken. Lower-layer representations of previous tokens *do* encode information that higher layers refine, but they're computed from the full residual stream which includes position information that doesn't change. This is a sound approximation only for shallow cross-layer dependencies, not for deep models where layer interactions are complex. Early versions of this idea (used in some efficient inference work) produced output quality degradation that was hard to characterize systematically.

### Attempt 3: Fixed-Size Sliding Window Cache

Keep only the last W tokens' K and V in cache. Attention can only see the W most recent tokens — a bounded-memory approach.

This is sliding window attention (used in Longformer, Mistral), not KV cache. It reduces memory and compute per step to O(W), but also caps context at W. If W=2,048 and the model has a 32,768-token context window, you've thrown away 30,720 tokens of potentially relevant context. For tasks requiring long-range reference (legal documents, codebases, book-length reasoning), this fails. It's an architectural constraint, not a caching optimization.

## The Discovery

Full recomputation is O(N²) in total. Partial recomputation breaks cross-layer correctness. Sliding windows cap context. The insight is simpler than any of these: don't recompute what didn't change.

For the Nth generation step, the K and V vectors for tokens 1 through N-1 are *exactly the same* as they were at step N-1. They don't change because those tokens' positions and content are fixed. Only token N's K and V are new.

**KV Cache**: store the K and V tensors for every previous token in every layer and every head. When generating token N, only compute Q_N, K_N, V_N. The attention for the new token uses Q_N against [K_1, K_2, ..., K_N] (cached K's plus the new one) and outputs a weighted sum of [V_1, V_2, ..., V_N] (cached V's plus new). Total computation: O(1) new K/V computation + O(N) attention score computation (dot products with N cached keys). The latter is unavoidable — you need to compute attention weights with all N positions — but the forward pass through the full model is now O(1) per step instead of O(N).

**Memory cost**: for a 96-layer model with 32 heads and d_head=128, each cached token requires 96 × 32 × 128 × 2 (K and V) = 786,432 FP16 values = ~1.5MB per token. For N=4,096 tokens: ~6GB of cache, on top of the model weights. For N=32,768: ~50GB. KV cache memory grows linearly with context length and is the primary memory bottleneck for long-context inference — not the model weights.

## Try It

<iframe src="../assets/browser/chapter56/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter56/index.html)

Before changing anything, predict:

- Enable KV cache and generate 100 tokens. Disable it and generate 100 tokens. How does latency per token change at token 50? Token 100?
- Increase context length. At what length does the KV cache memory exceed the model weights memory?
- What happens to the first token's latency? (Prefill phase has no cache — it must process all input tokens in parallel.)

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter56/index.html` (shared helpers in `browser/common/sim.js`). The sim is a schematic of recompute cost, not the KV cache data structure itself — `ops = hasCache ? 1 : (step + 1)` captures the key asymmetry: without caching, every decode step re-attends to all previous tokens; with the cache checkbox enabled, each step costs 1 operation. `drawTokens()` lights up tokens up to the current `step`, and `noKvRecompute`/`kvRecompute` counters accumulate total work to make the difference visible over a full generation pass.

## When It Breaks

**KV cache memory limits context.** For a Llama 2 70B model at FP16 with 40 heads and d_head=128, each token costs 40 × 128 × 2 × 2 bytes × 80 layers = ~1.6MB per token. A 100K-token context requires 160GB of KV cache — more than most GPU setups have for model weights, let alone cache. This is why models with advertised 100K or 1M context windows require enormous GPU deployments or specialized memory management (paged attention, offloading).

**PagedAttention and memory fragmentation.** Different requests have different context lengths, and context grows unpredictably during generation. Naive KV cache pre-allocates maximum context length per request, wasting memory for shorter requests and creating fragmentation. vLLM's PagedAttention (2023) applies OS virtual memory paging to KV cache: allocate memory in fixed "pages" and use a page table to map logical KV positions to physical pages. This dramatically improves GPU memory utilization and was a key enabling technology for serving many simultaneous requests efficiently.

## Transfer

- **Memoization** (chapter 23): KV cache is memoization applied to attention. The key insight is identical — don't recompute a pure function's output if the inputs haven't changed. Previous tokens' K and V are a pure function of those tokens' embeddings, which don't change.
- **Compiler register allocation**: keeping frequently-used values in registers (fast) rather than memory (slow) is the same principle at the hardware level — minimize re-fetching of values that haven't changed.
- **Prefix caching**: many production requests share a common system prompt. If the KV cache for the system prompt is stored and reused across requests, the prefill cost for that prefix is paid once. Anthropic's prompt caching and OpenAI's caching APIs expose this to users.

Try these:

1. Calculate KV cache size for Llama 3 70B: 80 layers, 8 GQA groups (grouped-query attention with 8 K/V heads instead of 64), d_head=128, FP16. How many GB per token? How many tokens fit in 80GB?
2. A KV cache is 60% full. A new request with a 4,096-token prompt arrives. You can't evict from in-progress requests. What are your options? (Consider: pre-allocation, token streaming, request queuing.)
3. Grouped-Query Attention (GQA) shares K and V heads across multiple Q heads. If 8 Q heads share 1 K/V head, how much does this reduce KV cache size compared to multi-head attention? What capability does this trade away?

---

**Continue → [Why Quantization Exists](57-why-quantization-exists.md)**
