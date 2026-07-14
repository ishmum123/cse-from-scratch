# Where All the Arcs Meet

## The Problem

You've built a language model. The weights are trained. A single forward pass produces correct output. But one user sends a request. Then a thousand. Then a hundred thousand per day, each a different prompt, a different length, a different expected output length. You want low latency (the first token arrives in milliseconds) and high throughput (many users served per GPU-hour). You want to charge per token while keeping costs below revenue.

These goals conflict. Low latency wants dedicated resources — one GPU per user, always ready. High throughput wants batching — fill every GPU cycle with useful work, serve many users from one GPU. Dedicated resources scale cost linearly with users. Batching reduces cost but increases wait time.

A production inference server must resolve all of this while:

- Handling requests of variable input length (10 tokens to 100,000 tokens)
- Handling requests that generate variable output lengths (user didn't say how long)
- Running on fixed hardware (GPUs bought months ago)
- Maintaining correctness under all these conditions simultaneously

This chapter is where every earlier idea converges.

## What Would You Try?

Before reading on:

- If you batch 32 requests together, each with a different input length, what shape is the attention computation? (Hint: chapter 54's O(n²) cost.)
- When a request finishes generating, its GPU memory slot opens. But there are 100 more requests in the queue. Which one goes next? Does order matter?
- A 100K-token context costs much more KV cache memory (chapter 56) than a 1K-token context. Can you mix them in the same batch without the 100K request dominating memory?

## Failed Attempts

### Attempt 1: One Request at a Time (Fully Sequential)

Process each request to completion before starting the next. Maximum latency per user: the time for all requests ahead of them. At 100 requests/hour and 5 seconds each: request 100 waits 500 seconds. GPU utilization is 100% for that one request but 0% between requests (networking overhead). Throughput is the inverse of per-request latency. No parallelism.

This is fine for a developer running local experiments. It doesn't scale.

### Attempt 2: Static Batching (Fixed-Size Batches, Wait-to-Fill)

Collect N requests. Run them all together. Return all N results. Repeat.

The batch waits until N requests arrive — adding queuing latency. Within the batch, requests have different lengths. To run them together, you **pad** shorter sequences to the length of the longest — those padding positions do real compute that produces garbage output. A batch where one request is 8,192 tokens and the others are 100 tokens wastes ~98% of compute on padding. The long request determines the compute cost for everyone. And when the longest request finishes, all other batch members are already done — so the GPU waits idle until the next batch fills.

Static batching is the "obvious" answer and what early LLM serving used. It achieves parallelism but wastes it.

### Attempt 3: Padded Dynamic Batching (Variable Batch Size, Sorted by Length)

Sort requests by length. Group similarly-lengthed requests together. Less padding waste.

Better, but doesn't solve the fundamental problem: in autoregressive generation, you don't know when a request will finish. One request in the batch might be a 10-token response; another might be 2,000. The batch has to keep running until the *longest* response finishes — shorter responses finish early and sit idle (their GPU time is wasted). This is the "early completion" problem. And sorting introduces unfairness: short requests wait for a full batch of short requests rather than slotting into idle capacity from completed long requests.

## The Discovery

Sequential serving doesn't scale. Static batching wastes compute on padding and early completions. Dynamic batching with length sorting reduces padding but doesn't solve early completion.

The solution requires rethinking the granularity of batching. Instead of batching at the request level (group requests together for their full duration), batch at the **token level** (batch individual generation steps across all active requests).

**Continuous batching** (also called iteration-level batching or in-flight batching — Orca, 2022): the server maintains a set of *active requests*. At each generation step, it takes *one decoding step* for all active requests simultaneously — regardless of their positions in generation. When a request finishes (generates an EOS token), it's immediately removed from the active set. A new request from the queue takes its slot in the next step.

This eliminates early completion waste: a finished request is evicted immediately, not at the end of the batch. It also minimizes padding: requests don't need to be padded to each other's lengths because each request has its own independent attention computation over its own context (the KV cache from chapter 56 makes this efficient — each request's cache is separate).

The innovation that makes this possible: **paged KV cache** (vLLM, 2023). Different requests have different context lengths that grow unpredictably. If you pre-allocate max-context VRAM per request, you waste most of it (most requests don't use the maximum). PagedAttention (chapter 56's ending) allocates KV cache in pages of fixed size, mapping logical positions to physical pages via a page table — exactly how an OS manages virtual memory. This allows 100K-token and 1K-token requests to coexist in the same batch without the 100K request pre-claiming 100× more memory.

**Scheduling** completes the picture: priority queuing (SLA-sensitive vs. batch requests), request preemption (swap low-priority request's KV cache to CPU RAM when a high-priority request needs GPU memory), and admission control (reject requests when the server would be overloaded rather than queue indefinitely).

**Prefix caching**: many requests share a long system prompt ("You are a helpful assistant. Here are the company's 50-page policies: ..."). Computing the KV cache for that shared prefix is expensive. Prefix caching (also called prompt caching): compute the shared prefix's KV cache once, store it in a separate "prefix cache" shard, and reuse it for all requests that start with that prefix. This is analogous to a CDN caching a popular static asset close to users — the first request pays the cost, all subsequent requests hit the cache. vLLM's RadixAttention extends this to arbitrary prefix trees, where any shared subtree of tokens is reused. At production scale, prefix hit rates of 60–80% are common for API providers with fixed system prompts, cutting effective per-token compute cost nearly in half.

**Speculative decoding in depth**: the key insight is that the large model (verifier) can check K tokens in a single forward pass, which costs roughly the same as generating one token autoregressively. If the draft model generates K tokens and the verifier accepts most of them, the effective throughput is K× higher. Acceptance rate depends on how well the draft model approximates the verifier's distribution for a given output domain — for repetitive or formulaic text (code completions, structured outputs), acceptance rates of 70–90% are achievable. For creative text, rates drop to 30–50%. The overhead: the draft model adds ~20% memory and compute for the few steps where the verifier rejects. Net: ~2–4× latency improvement for common code completion cases, with almost no quality impact (the verifier's output is mathematically identical to non-speculative sampling — rejection sampling preserves the distribution exactly).

**Tensor parallelism inside inference**: the same tensor parallelism described in chapter 58 applies to inference servers, but with a critical difference. During training, batch sizes are large (256–4096) so computation dominates communication. During inference, batch size might be 1–32. At small batches, each all-reduce in the tensor-parallel layer takes nearly the same time as a large batch (communication overhead is fixed per message), but the compute that should hide it is much smaller. The inflection point: for A100s on NVLink, tensor parallelism is efficient only when the per-GPU compute time per layer exceeds ~2ms — at FP16, d_model=8192, this requires batch size ≥ ~8. Below this, tensor parallelism adds communication overhead without proportional compute benefit, and single-GPU or data-parallel serving is more efficient. This is why inference serving typically uses less tensor parallelism than training.

This is where the arcs converge:

- **Distributed systems** (chapters 41–50): multiple GPU servers, each running inference workers. Consensus and leader election for routing decisions. Sharding of model replicas across clusters. Replication for availability. Queues for request buffering.
- **System design** (chapters 46–51): caches everywhere (model weights in GPU VRAM, KV caches per request, prefix caches for shared prompts). CDN-like geographic routing to the nearest inference cluster. Rate limiting per user.
- **AI infrastructure** (chapters 52–59): the model itself: attention (54), transformers (55), KV cache (56), quantization (57), tensor parallelism (58), MoE routing (59). All running inside the inference server.

A request enters the queue. The scheduler picks the next step. The tensor-parallel model (chapter 58) forward-passes one token per active request. The KV cache (chapter 56) stores computed keys and values. MoE routing (chapter 59) sends each token to the right expert. The quantized weights (chapter 57) fit on the available GPUs. The next token is sampled. The token is streamed to the user. The cycle repeats.

## The Token Economics of Inference

Each token has a cost: the GPU compute to run the forward pass, plus the memory bandwidth to read all weights and KV cache. Understanding these costs drives every architectural decision.

**Compute cost per token**: for a transformer with L layers, d_model dimensions, and FFN hidden size 4×d_model, each token requires roughly 2 × L × d_model² × 4 FLOPs (two matmuls per FFN, two per attention projection). For GPT-3 (L=96, d_model=12,288): ~144 × 10¹² FLOPs = 144 TFLOP per token. An A100 does 312 TFLOP/s in BF16. Ignoring memory bandwidth: 144/312 ≈ 0.46ms per token at peak arithmetic throughput. But peak arithmetic throughput requires full utilization. At batch size 1 (single-user inference), GPU utilization is ~5% (memory-bound, not compute-bound). Actual time per token: ~5–10ms. Continuous batching brings utilization to 30–60%, reducing per-token time to ~1–2ms.

**Memory bandwidth cost**: at each decode step, every parameter must be read from VRAM to compute one token. GPT-3: 175B parameters × 2 bytes (BF16) = 350GB to read per step. A100 memory bandwidth: 2TB/s. Time to read all weights: 350/2000 = 175ms. This exceeds the compute time by ~400×. This means decode is *memory-bandwidth-bound*, not compute-bound, at small batches. To bring compute into balance with bandwidth, you need batch size = arithmetic_intensity / bytes_per_weight_access. For A100: 312 TFLOP/s / (2 TB/s) ≈ 156 FLOP/byte. An FP16 matmul with batch B: FLOP/byte = B. So you need B ≥ 156 to be compute-bound. At batch 1, memory is the bottleneck. At batch 256, compute is. Continuous batching targets the regime where batch stays above the compute-memory crossover.

**KV cache bandwidth**: beyond weights, the attention mechanism must read the KV cache for all previous tokens. At 2K-token context, L=96, 2 tensors (K,V), d_model=12,288, FP16: 2 × 96 × 2 × 12288 × 2 × 2048 bytes ≈ 18GB per decode step. Plus the 350GB for weights: ~368GB total per step. At 2TB/s: ~0.18ms per decode step, purely from memory reads. This matches empirical measurements: GPT-3-scale models produce ~10–15 tokens/second per A100 at batch size 1.

## Try It

<iframe src="../assets/browser/chapter60/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter60/index.html)

Before changing anything, predict:

- Compare static batching vs continuous batching throughput as request arrival rate approaches GPU capacity. At what arrival rate does the gap appear?
- Simulate a mix of short (50-token) and long (2,000-token) requests. Under static batching, does the long request hurt the short ones?
- Enable KV cache paging. At high concurrency (many parallel requests), how does memory utilization compare to pre-allocated KV cache?

## The Inference Server Stack

A production inference server is a composition of systems from throughout this course. Here is what the full stack looks like:

**Load balancer (chapters 47, 49)**: routes incoming HTTP requests to inference workers, typically by least-load or consistent hashing on request type (so prefix caches are maximally reused). Geographic routing (CDN-style, chapter 47) directs users to the nearest cluster.

**Request queue (chapter 48)**: incoming requests are placed in a priority queue before the scheduler picks them up. At-least-once delivery semantics ensure a server restart doesn't drop an in-flight request (the client retries from the queue). Visibility timeout — exactly the mechanism from chapter 48 — prevents a crashed worker from silently dropping a request.

**KV cache manager**: manages GPU VRAM as a pool of fixed-size pages. Tracks which pages belong to which request, shared prefix pages (read-only, reference-counted), and free pages. Implements FIFO or LRU eviction when the pool is full, with swap-to-CPU-RAM as a fallback. This is virtual memory management (chapter 27's OS analogy) applied to GPU memory.

**Tensor parallel worker group (chapter 58)**: each request is processed by a group of G GPUs running tensor-parallel layers. All-reduce communication happens via NVLink within the group. The worker group looks like a single GPU to the scheduler — it accepts a batch of tokens and returns logits.

**Sampler**: given the output logits from the model, samples the next token. Supports temperature, top-p (nucleus sampling), top-K sampling, and repetition penalties. Streaming output: each sampled token is immediately sent to the client without waiting for the full response — this is the "first token fast" user experience.

**Metrics and observability (chapter 41 distributed clocks)**: every component emits latency distributions, queue depths, KV cache memory utilization, and token throughput. Operators set SLA targets (e.g., p99 first-token latency < 500ms) and page on-call when violated. Correlating metrics across the distributed worker group requires synchronized timestamps — chapter 41's problem again.

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter60/index.html` (shared helpers in `browser/common/sim.js`). The simulation encodes the full scheduling loop: request arrival, page allocation, step dispatch, early eviction on completion, and re-admission from the queue. Compare the `staticBatch()` and `continuousBatch()` paths — the key difference is the eviction-on-EOS logic and the per-step vs per-request batching granularity.

## When It Breaks

**Head-of-line blocking on long contexts.** A single 100K-token request in the continuous batch occupies a large KV cache allocation. If memory is tight, shorter requests can't be admitted until the long request finishes. Preemption (swapping the long request's KV cache to CPU) is possible but adds latency. Chunked prefill (process the long input in segments, interleaving with decoding steps from other requests) is the current solution — compute the prefill in chunks, yielding to other requests between chunks. Chunk size is a tunable parameter: smaller chunks give better fairness to short requests; larger chunks improve prefill GPU utilization (prefill is compute-bound, while decode is memory-bound). Production systems set chunk size to ~4,096 tokens, balancing both.

**Memory fragmentation in paged KV cache.** PagedAttention solves contiguous allocation waste but creates a new problem: fragmented free pages. If 1,000 requests each allocate 2–3 pages, then complete and free their pages, the free list is fragmented into thousands of non-contiguous 16KB pages. A new request needing 50 contiguous pages can't be served even if total free memory is sufficient (because it's non-contiguous). The solution: PagedAttention's logical→physical page table means the request doesn't need *physically* contiguous pages — pages can be scattered, the table maps logical positions to physical pages. This is analogous to virtual memory in an OS: processes see a contiguous address space, physical pages can be anywhere in RAM. The page table is the key insight that makes non-contiguous allocation safe.

**Speculative decoding — latency vs throughput tradeoff.** A small "draft" model generates K candidate tokens quickly. The large "verifier" model checks all K candidates in a single forward pass (parallel, not autoregressive). If K candidates are accepted (most are), you generate K tokens in the time it takes to do one large forward pass — roughly K× speedup. But the draft model adds memory and management complexity, and the acceptance rate drops for difficult or creative outputs. Speculative decoding (Leviathan et al., 2022) trades model complexity for latency improvement, and is now standard in production serving for latency-sensitive paths.

**Priority inversion under mixed workloads.** A production inference server receives both interactive (low latency target, single user) and batch (high throughput target, offline jobs) requests. If a large batch job fills the request queue, interactive requests wait. Strict priority queues help, but can starve batch jobs indefinitely if interactive load is high. Multi-level queues with time-slice scheduling (give interactive requests X ms of GPU time per Y ms batch time) are the production solution — but tuning X and Y is an ongoing operational task, not a one-time configuration.

## Transfer

- **Web servers** faced the same static-vs-dynamic batching problem: Apache's process-per-request model was replaced by Nginx's event-loop model, which handles many connections in a single thread — continuous batching of HTTP requests. The inference serving revolution mirrors this exactly. In both cases, the shift was from resource-per-request to event-driven scheduling; in inference, "event" means "one token generated."
- **Database connection pools** are schedulers for a fixed resource (database connections) across variable demand (queries) — the same admission control and queuing problem, with connection eviction analogous to KV cache eviction. PgBouncer (Postgres connection pooler) uses the same priority eviction logic as vLLM's memory manager.
- **Streaming pipelines** (Kafka consumers, chapter 48) handle variable-rate input with a fixed processing rate by buffering — the queue that an inference server uses for incoming requests is the same structure, with the same thundering herd risk. When inference demand spikes, the request queue behaves exactly like a Kafka consumer group falling behind its producers: back-pressure, admission control, or dropping requests are the only options.
- **Operating system schedulers**: the CPU scheduler faces the same problem — many processes want a fixed resource (CPU time) with different priorities and remaining runtimes. Completely Fair Scheduler (Linux CFS) uses a red-black tree sorted by "virtual runtime" to ensure fair access. An inference scheduler's priority queue is CFS applied to GPU cycles, with preemption (KV cache swap-out) analogous to context switching.

Try these:

1. A continuous batching server has 80GB of KV cache. Each active request uses ~500MB at 2K tokens. What's the maximum concurrency? If 40% of capacity is prefix-cached (shared prefixes don't consume per-request memory), how does concurrency change?
2. Speculative decoding with K=5 candidate tokens and a 70% acceptance rate. Each speculative step runs both draft and verifier. What's the expected tokens-per-verifier-step? At what acceptance rate does speculative decoding break even with standard autoregressive decoding?
3. An inference server receives a mix of 200 interactive requests (target: 200ms first-token latency) and 50 batch requests (target: best-effort). Interactive requests take 50ms GPU time each; batch requests take 500ms each. Design a scheduling policy that guarantees the latency SLA for interactive requests. What's the maximum batch request throughput you can sustain?
4. Prefix caching hit rate is 60% for a system prompt of 4,000 tokens. Without caching, each request pays 4,000 prefill tokens. With 60% hit rate, the average prefill cost is 40% × 4,000 = 1,600 tokens. If the model processes 10 million requests/day at $0.001 per 1K prefill tokens, what is the daily cost savings from prefix caching?

Every piece of this course has led here: bits and information theory told us what can be communicated; sorting and search told us what can be found efficiently; trees and graphs gave us structure for relationships; systems gave us distributed coordination; AI infrastructure gave us how to run models at scale. The inference server is what it looks like when all of that runs together, serving millions of users, one token at a time.

The journey from "how does a computer store a number" to "how do ten thousand GPUs serve a trillion-parameter model" is one continuous chain of problems, each requiring the previous solution to make sense. You've walked the whole chain.

---

*You've reached the end of the core chapters. The concepts here — information, structure, algorithms, systems, distributed coordination, and AI infrastructure — form the backbone of modern computing. Every system you'll build touches most of them. Come back when something breaks; the chapter that explains it is probably here.*
