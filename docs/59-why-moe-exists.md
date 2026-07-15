# Specialists Instead of One Generalist

## The Problem

Scaling laws (chapter 55) say: more parameters → better model. A 1T-parameter model beats a 100B-parameter model on every task. But running a 1T-parameter model means every forward pass touches every weight: 1T multiplications per token. At inference time, you're paying the full 10× compute cost for every token in every request — whether that token is part of a Python function, a French poem, or a physics question.

A 1T dense model costs 10× more per token than a 100B model. At large inference volumes, that compute cost is a primary operational expense. You want the quality of 1T parameters with the cost of something smaller.

The question: is there a way to have 1T parameters but use only 100B of them per token?

Any selective computation scheme must:

- Route each token to the relevant subset of parameters
- Make routing decisions quickly (routing can't cost more than it saves)
- Ensure all experts are used — a model where 90% of parameters are never active is wasteful
- Train stably — routing decisions must be differentiable enough for gradient descent

## What Would You Try?

Before reading on:

- A language model processes tokens about "protein folding," "basketball statistics," and "17th century French literature." Is it plausible that different subsets of weights are more relevant to each topic?
- If you train 10 specialist networks (each on a different topic) and route each input to the most relevant specialist, what's the inference cost per token? What's the total parameter count?
- The routing decision is a function of the input token. For routing to be trainable, the gradient must flow back through it. But if routing is "send to expert 3" (a discrete decision), how would you differentiate it?

## Failed Attempts

### Attempt 1: Hard Topic Routing — Train Separate Specialist Models

Train 10 specialist models, one per topic. At inference, classify the input and route to the right specialist.

The classification step is error-prone: misclassified input (a chemistry question routed to the sports model) gets poor quality responses. Topics aren't clean categories — real text mixes topics constantly. The 10 specialists can't share knowledge: the protein model knows nothing about the chemistry context in a biology question. Models trained in isolation lack cross-domain generalization. And adding a new topic requires training a new specialist from scratch. This doesn't scale.

### Attempt 2: Ensemble Voting — Run All Experts, Take the Average

For each token, run all N experts. Average their outputs (or take the best one by some criterion). You get all experts' knowledge on every token.

The inference cost is N× — you're running all experts every time. This is exactly the opposite of what you wanted. It also typically doesn't outperform a single model of the same total parameter count, because the average of specialized models loses the specialization benefit. Ensembling is a training-time trick (combining many small models to reduce variance), not a way to get 1T-parameter quality at 100B-parameter cost.

### Attempt 3: Top-1 Gating — Route to a Single Expert, Hard

Compute a routing score for each expert, send the token to the highest-scoring expert only. Inference cost = 1/N of using all experts.

Training instability kills this approach. When all tokens route to expert 1 (because expert 1's router outputs are slightly larger due to random initialization), expert 1 gets all gradient updates, improves, routes even more tokens to itself, and experts 2–N never train. The model collapses: only one expert is active. You've built a 1/N-parameter model that thinks it's an N-expert model. Various entropy regularization tricks partially address this, but hard top-1 routing is highly sensitive to initialization and hyperparameters.

## The Discovery

Hard topic routing requires accurate topic classification. Ensemble voting has full inference cost. Top-1 hard gating collapses during training. The failures point to two requirements: routing must be *soft* during training (to allow gradient flow and prevent collapse) and *sparse* at inference (to achieve cost savings).

**Mixture of Experts (MoE)** with **top-K gating** (Shazeer et al., 2017, then scaled in GLaM, Switch Transformer, Mixtral):

Replace each feedforward layer with E experts (each is an independent FFN). A gating network G(x) produces E scores for each token x. Select the top-K experts by score (K=1 or K=2 typically). Compute weighted combination:

`output = Σ_{i ∈ TopK(G(x))} G_i(x) × Expert_i(x)`

The gradient flows through both the expert outputs (via the expert weights) and through the gating network (via the softmax on scores). Experts receive gradient only when selected, which is fine — they specialize by being selected for the tokens where they're most useful.

**Load balancing loss**: auxiliary loss term that penalizes routing imbalance. If expert 1 gets 80% of tokens and expert 7 gets 1%, the imbalance loss increases, pushing the router toward more uniform usage. This prevents the collapse seen in hard top-1.

Inference cost: with K=2 out of E=8 experts, each token uses 2 experts. Total active parameters per token: model_non_expert_params + 2 × expert_size. Total stored parameters: model_non_expert_params + 8 × expert_size. If experts are 60% of parameters, using 2/8 = 25% of them means inference cost is ~55% of the total parameter count while quality approaches the full parameter count. **Mixtral 8×7B**: 8 experts × 7B ≈ 46B stored, but only 2 experts active per token ≈ 13B active. Quality comparable to a dense 30B model at the cost of a 13B model.

## The Gating Function in Detail

The gating network G(x) is a linear layer followed by softmax: `G(x) = Softmax(x · W_g)` where W_g is a (d_model × E) matrix. The E scores are each token's "affinity" for each expert. TopK selects the K largest scores; the remaining E−K scores become zero (or are discarded). The selected scores are re-normalized to sum to 1, then used as weights for the expert outputs.

The gradient of the top-K operation: the top-K function is piecewise constant (switching which expert is selected is a discrete event), so its gradient with respect to the input is zero almost everywhere. How does the router learn? Through the *selected experts' gradients*: when expert i is selected for token x, the expert's output contributes to the loss, and the gradient flows back through G_i(x) (the gating weight for expert i). This updates W_g to be slightly more or less likely to select expert i for tokens similar to x. Over millions of steps, W_g learns which experts are useful for which token patterns. Experts not selected for a given token contribute zero gradient for that step.

**Noisy top-K**: Shazeer's original MoE paper adds tunable noise before the top-K: `G(x) = TopK(Softmax(x · W_g + ε))` where ε is sampled from a normal distribution scaled by a learned parameter. This noise encourages exploration during training — tokens that would narrowly miss an expert's top-K selection occasionally get selected due to noise, giving that expert a chance to learn and improve its score. Without noise (or without load balancing loss), the top-K selection is deterministic early in training, locking in routing distributions before experts have time to specialize. Noise is typically annealed to zero during the later stages of training.

**Expert parallelism at inference**: in a distributed MoE cluster, each expert lives on a different GPU. For a batch of tokens, the all-to-all communication step collects expert assignments and physically routes token embeddings to the correct GPUs, computes expert outputs, then routes results back. The all-to-all for a batch of B tokens, E experts, K active experts per token, and d_model dimensions sends B×K×d_model floats across the network — divided across E GPUs. At d_model=4096, FP16, B=1024, K=2, E=8: each all-to-all transfers 1024×2×4096×2 bytes / 8 = 2MB per GPU. At NVLink 600GB/s: 3μs per all-to-all. Negligible. At Ethernet 100Gbit/s (= 12.5GB/s): ~160μs — now significant relative to compute. This is why MoE at scale requires NVLink or InfiniBand between expert GPUs.

## Try It

<iframe src="../assets/browser/chapter59/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter59/index.html)

Before changing anything, predict:

- Watch the expert assignment over many tokens. Without load balancing, do experts get equal use?
- Enable load balancing loss. How does expert assignment distribution change?
- Reduce K from 2 to 1. Does quality (measured by output loss) change? Does inference speed?

## MoE Architecture Variants

Production MoE models have diverged significantly from the original Shazeer 2017 formulation:

**Switch Transformer** (Fedus et al., 2021 — Google): K=1 (single expert per token). Simplest routing, lowest communication overhead. Challenged assumption that K=2 was the minimum for quality — Switch Transformer showed K=1 achieves competitive quality at lower compute, at the cost of less "graceful" routing (one bad expert selection means zero contribution from that expert, vs K=2 where the other expert partially compensates). Used E=2048 experts across 2048 TPU cores — one expert per core — enabling expert parallelism at extreme scale without all-to-all overhead.

**GLaM** (Du et al., 2021 — Google): 64 experts, K=2, at 1.2T total parameters, 97B active per token. First MoE model to match GPT-3 quality at 1/3 the training compute. Demonstrated that the efficiency wins from MoE are real at scale, not just on benchmarks. Inference energy cost 1/2 that of GPT-3 for equivalent quality outputs.

**Mixtral 8×7B** (Mistral AI, 2023): 8 experts, K=2, 46B total, 13B active. Open-weight model. Made MoE practical for the wider community: runs on 2×A100 for inference (fits in 160GB VRAM). Community analysis showed expert specialization patterns correlate more with syntactic position (start of sentence, continuation, punctuation) than with semantic topics.

**DeepSeek-MoE** (2024): introduces "fine-grained experts" — many small experts (E=64, each ~0.5B parameters) with K=6. More granular routing means better specialization but higher all-to-all communication volume. Also introduces "shared experts": 2 always-active experts that every token uses in addition to the top-K routed experts, preventing total collapse of non-selected experts.

**Gemini 1.5** (Google, 2024): MoE architecture enabling 1M-token context at inference. The MoE efficiency allows fitting a larger model on the same hardware budget, and the larger model can store more contextual state — enabling the extended context window without proportionally higher compute cost per token.

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter59/index.html` (shared helpers in `browser/common/sim.js`). Each tick, `pickTopK(E, k)` selects the active experts: it assigns a random score to each of the `E` experts, sorts by score, and returns the top `k` indices as `activeExperts`. `drawDense()` lights all experts every tick; `drawMoE()` lights only the `activeExperts`. The FLOPs labels compare `denseFlops = numExperts * expertFlops` against `moeFlops = topK * expertFlops`. A real MoE also adds an auxiliary load-balancing loss to prevent all tokens routing to the same expert — the random scoring here ensures each run picks different winners.

## When It Breaks

**Expert capacity overflow.** On a single forward pass over a batch, some experts may receive more tokens than their "capacity" (max tokens per expert per batch). Tokens routed to overloaded experts are either dropped (no expert computation for that token) or processed by a backup expert. Both are correctness compromises: dropped tokens produce zero activations; backup experts reduce specialization. Expert capacity is a training-time hyperparameter that trades off load handling vs. memory allocation. Mistral's implementation caps expert capacity and drops overflow tokens, which works in practice but is architecturally awkward. Capacity factor = (tokens_per_batch / num_experts) × capacity_multiplier; setting multiplier to 1.0 means zero overflow but tight packing; 1.25 gives a 25% buffer. During training, dropped tokens receive zero gradient for their expert path — they are effectively skipped. This slightly reduces training efficiency but prevents memory overflow.

**Routing instability during fine-tuning.** A pre-trained MoE model has a stable routing distribution. When fine-tuned on a new task (instruction following, code, etc.), gradients push gating weights toward experts useful for the fine-tuning distribution, destabilizing routing for base capabilities. If the load balancing loss coefficient α is too low during fine-tuning, routing collapses — one or two experts handle most fine-tuning tokens and forget their pre-training distribution. If α is too high, routing is over-regularized and the model can't specialize for the fine-tuning task. Fine-tuning MoE models typically requires α 3–5× smaller than pre-training to allow task-specific routing while preventing collapse.

**Communication cost in distributed MoE.** When experts are distributed across GPUs (each GPU holds a subset), all-to-all communication is required: each GPU must send tokens to whatever GPU holds their assigned experts. At large scale (thousands of GPUs), all-to-all is expensive — it's the one communication primitive that scales with the number of nodes squared in the worst case. Google's Switch Transformer paper noted this as the primary scaling limitation for MoE beyond a few hundred experts.

**Expert specialization isn't guaranteed.** MoE models don't necessarily develop semantically interpretable expert specialization. Analysis of trained MoE models (including Mixtral) often shows experts specializing on syntactic or positional patterns rather than clean semantic topics — one expert handles sentence starts, another handles punctuation contexts, rather than "expert 3 handles physics questions." The efficiency gains are real regardless of interpretability, but it means you can't predict which expert a given domain will route to without empirical investigation.

**Why MoE and dense scaling laws diverge**: Chinchilla scaling law (chapter 55) says a dense model scales smoothly as `L(N) ≈ (N_c/N)^α`. But MoE breaks this: adding experts doesn't improve performance at the same rate as adding dense parameters. The reasons are two-fold. First, experts see fewer examples per step — if 8 experts each handle 1/8 of tokens, each expert trains on 1/8 the data, learning slower. Second, expert routing creates gradient sparsity: parameters in non-selected experts receive zero gradient on each step, so the effective learning rate is reduced. Empirically, MoE models need ~4× more tokens than a dense model with equivalent active parameters to match quality. The Chinchilla compute-optimal token count applies to dense models; MoE models are currently under-trained relative to their parameter counts.

**Granularity of experts**: MoE layers in production systems replace every FFN layer (fine-grained MoE) or only certain layers (coarse-grained). Switch Transformer replaced every FFN with a MoE layer. DeepSeek-MoE uses both "shared experts" (always active, every token) and "routed experts" (top-K activated). Shared experts prevent total expert collapse by ensuring a baseline of always-useful computation, while routed experts specialize on top. The shared+routed architecture typically outperforms pure routed MoE at the same total parameter count.

**MoE inference vs training cost asymmetry**: during training, all expert gradients can be batched efficiently across the large batch. During inference (online, low batch), tokens arrive one or few at a time. All-to-all communication between expert GPUs is expensive for small batches — communication overhead becomes dominant over compute. This means MoE models that train efficiently can be expensive to serve at low batch. Production serving of MoE models requires collocating all experts on a small number of NVLink-connected GPUs to minimize communication latency, or using speculative techniques that predict expert assignment before the token arrives.

## Transfer

- **Human expertise specialization**: organizations hire specialists rather than generalists for complex tasks — the same efficiency argument. A tax question goes to the tax expert, not the sales team. MoE is the neural network equivalent of staff specialization.
- **Database query routing** in sharded databases (chapter 49) is structurally similar: route each query to the shard that holds relevant data. MoE routes each token to the expert that has learned relevant patterns. The load balancing loss is equivalent to a rebalancing strategy that redistributes query load away from hot shards.
- **Adaptive computation**: conditional computation (Bengio, 2013) proposed that the network should "think harder" on difficult examples by using more layers or neurons. MoE is a realization of this: complex tokens might be routed to larger or more specialized experts, while common tokens use efficient generalist experts.
- **Multi-tenancy in cloud infrastructure**: cloud providers route requests to specialized servers (GPU for ML, memory-optimized for databases). The routing cost is amortized if each specialist handles many requests — the same argument for why K must be small (routing overhead per token must be small relative to expert computation).

Try these:

1. Mixtral 8×7B: each expert is 7B parameters, 8 experts total, non-expert parameters = 6B. With K=2, what fraction of stored parameters are active per token? What's the inference FLOP count relative to a dense 7B model? Relative to a dense 13B?
2. Load balancing loss: `L_aux = α × Σ_i f_i × P_i` where f_i is fraction of tokens routed to expert i and P_i is mean gating probability for expert i. If all tokens go to expert 1, what is L_aux? If evenly distributed across 8 experts? What does varying α do to training dynamics?
3. An MoE model with 16 experts and K=2. A token about quantum mechanics routes to expert 3 and expert 11. The next token (in the same sentence) about the same topic routes to expert 5 and expert 11. Is expert consistency across tokens a requirement for MoE to work? What would happen if the same concept always routed to different experts?
4. Design a MoE layer where experts have *different sizes* — 2 large experts (2B parameters each) and 6 small experts (500M each). Total stored = 7B. How would you design the gating to use large experts for "hard" tokens and small for "easy"? What signal tells you a token is hard?
5. Expert collapse analysis: at initialization, all experts have equal gating weights (1/E each). After one gradient step, why might routing start to become unequal? Trace through how a small random perturbation in expert quality could lead to collapse without load balancing.

**The open question of expert emergent behavior**: interpretability research on MoE models is ongoing. One finding from Mixtral analysis (Zoph et al., 2024): expert utilization statistics correlate with token position in the sentence rather than token semantics. Experts that are most active on "first token of a sentence" are different from those active on "middle of a compound noun phrase." This suggests the gating network learned to track syntactic state as a routing signal — not because anyone designed it to, but because syntactic position is a reliable predictor of which token statistics each expert has specialized on during training. This emergent syntactic routing is why MoE models show stronger grammatical consistency than same-size dense models: the syntactic-position experts provide a form of structured inductive bias.

**MoE and the future of scaling**: dense scaling hit a practical wall around 2022-2023 — training a 1T-parameter dense model requires O(1T) FLOP per token per step, and the hardware for this at reasonable training timescales (weeks, not years) doesn't yet exist. MoE breaks the coupling between parameter count and per-token FLOP: you can add parameters (more experts) without proportionally increasing compute, as long as K stays small. The scaling law for MoE models is still being characterized — early evidence suggests MoE parameter efficiency is real but requires approximately 4× more training tokens than a comparable dense model to reach equivalent loss. The next generation of frontier models (GPT-5, Gemini Ultra 2, etc.) are broadly expected to use MoE architectures at the FFN level, given the demonstrated efficiency gains at production scale.

---

**Continue → [Why Inference Servers Exist](60-why-inference-servers-exist.md)**
