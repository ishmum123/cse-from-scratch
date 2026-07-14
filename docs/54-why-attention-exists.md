# Every Word Is Watching Every Other Word

## The Problem

Translate "The animal didn't cross the street because it was too tired." What does "it" refer to? The animal, obviously — because "tired" applies to animals, not streets. But to know this, you need to connect "it" to "animal" across eight intervening words, while also connecting "tired" to "it" (not to "street").

This is **coreference resolution**, and it's trivially obvious to humans. It's catastrophically hard for any algorithm that reads words one at a time without remembering the full context. A language model that processes "the animal didn't cross the street because it was too" and then predicts "tired" needs to know that "it" = "animal" and that animals get tired. That connection is 9 words back.

Before attention, language models used recurrent networks — LSTMs and GRUs — that maintained a hidden state updated one word at a time. By word 15, the hidden state has been overwritten 14 times. Long-range dependencies are systematically lost.

Any solution to context-dependent language understanding must:

- Connect each word to every other relevant word, regardless of distance
- Do this in parallel (not one word at a time) to enable efficient training
- Weight connections by learned relevance, not just proximity
- Scale to the length of the input without quadratic time

## What Would You Try?

Before reading on:

- An LSTM processes "The cat sat on the mat" one word at a time. By "mat," how much information about "The" remains in the hidden state after 5 updates?
- If you allowed every word to directly "look at" every other word and compute a relevance score, what would you need? What matrix would you build?
- A word's meaning depends on context. "Bank" in "river bank" vs. "bank account." What representation would capture this context-dependence?

## Failed Attempts

### Attempt 1: Recurrent Networks — Sequential Hidden State

LSTMs update a hidden state h_t = f(h_{t-1}, x_t) at each timestep. Gates control what to remember, forget, and output. This was state-of-the-art for language from 2014–2017.

The hidden state bottleneck: all context is compressed into a fixed-size vector (typically 512–1024 dimensions) that must carry all information from position 1 to position t. For long sequences, the gradient signal through time vanishes — earlier tokens barely influence training of later ones (the vanishing gradient problem). Even with LSTM gating, context windows beyond ~100 tokens are unreliable. And crucially: each step depends on the previous step's output, so computation is *sequential*. Training on a 1,000-word sequence requires 1,000 serial steps. You can't parallelize across the sequence, which means you can't exploit GPUs effectively (chapter 52).

### Attempt 2: Convolutional Context Windows

Apply convolutions over the sequence — a window of W words produces each output. Wider windows → more context. Stack convolutions for hierarchical context. This is fully parallelizable (all positions simultaneously).

The context is local by design. A window of 7 captures 7 adjacent words. To connect a word to one 100 positions away, you need log_W(100) stacked layers, and each layer adds distance — a 7-word window with 4 layers reaches 7^4 = 2,401 positions, but every step is an approximation that loses information. Convolutional models (ByteNet, WaveNet) are faster than RNNs but still struggle with very long-range dependencies. The window size is a design hyperparameter that can't be "learned" — it's a hard architectural constraint.

### Attempt 3: Hard Attention (Select One Word at a Time)

Instead of a fixed window, learn to select which position to "attend to" at each step. A pointer mechanism selects one input position per output step. Fully flexible: can attend to position 1 or position 999 regardless of output position.

Hard attention is non-differentiable (you're making a discrete choice: attend to position i OR position j). Training requires reinforcement learning or REINFORCE gradient estimators — high variance, slow to converge. It also selects *one* position at a time: for "it was too tired," you might need to simultaneously reference "animal," "cross," "street," and "tired." Hard attention can't blend multiple source positions in one step. It was used in early neural machine translation (Bahdanau, 2014) but quickly superseded.

## The Discovery

Sequential RNNs compress context into a bottleneck and can't parallelize. Convolutions have hard context limits. Hard attention can't blend multiple references and isn't differentiable.

The resolution: make attention *soft* and *global*. Instead of selecting one position, compute a weighted blend of *all* positions, where the weights are learned to reflect relevance.

**Scaled Dot-Product Attention** (Vaswani et al., "Attention Is All You Need," 2017):

For each position, compute three vectors: Query (Q), Key (K), Value (V) — all linear projections of the input. The attention weight from position i to position j is:

`weight_{ij} = softmax(Q_i · K_j / √d_k)`

The output at position i is the weighted sum of all Values:

`output_i = Σ_j weight_{ij} × V_j`

Every position attends to every other position in one step. No sequential dependency — all attention weights can be computed in parallel as matrix multiplications (chapter 53): `Attention(Q, K, V) = softmax(QKᵀ/√d_k)V`.

The √d_k scaling prevents the dot products from growing large enough to push softmax into regions of vanishingly small gradient.

**Multi-head attention** runs H attention mechanisms in parallel, each learning different relationship types (syntactic, semantic, coreference, etc.). Heads specialize independently: one might track subject-verb agreement, another tracks pronoun antecedents.

The output for "it was tired": position "it" attends strongly to "animal" (high Q_it · K_animal score) and moderately to "tired" (high Q_it · K_tired score). The context for "it" now includes information from "animal" — the word has become context-aware.

## Try It

<iframe src="../assets/browser/chapter54/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter54/index.html)

Before changing anything, predict:

- Set "Window size" to 2 and "Seq length" to 10. The last token (query) in the left panel can only see 2 tokens. If an important referent is at T1, is it visible? What does the right panel show for the same T1?
- Increase "Seq length" from 4 to 16. In the right panel, watch the total number of weight bars — it grows as n. At what point does the fixed-window panel still show the same number of visible tokens?

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter54/index.html` (shared helpers in `browser/common/sim.js`). The sim is a schematic of attention's *reach*, not the QK^T arithmetic. `makeWeights(n)` produces the synthetic per-token weights for the right panel: for each of the n tokens it computes a distance-decayed base (`Math.exp(-dist * 0.3)`) plus a random boost on one "important" distant token, then normalises the array. `drawFixed()` colours tokens green/red based on whether they fall within the last `windowSize` positions; `drawFull()` renders proportional blue bars from those weights. The `seqLen` and `windowSize` variables (bound to the sliders) control both panels simultaneously.

## When It Breaks

**O(n²) memory and compute.** Attention computes all pairwise weights — an n×n matrix for a sequence of length n. For n=2,048: ~4M weights per head × 32 heads × 96 layers = ~12B numbers just for the attention matrices. For n=100,000 (long documents, protein sequences), this is 10¹⁰ elements per layer — impractical. Sparse attention (BigBird, Longformer) restricts which positions attend to which, trading expressiveness for tractability. FlashAttention (2022) reorders computation to avoid materializing the full n×n matrix, achieving the same result with O(n) memory.

**Attention heads can collapse.** All heads learn the same pattern — a common training failure where multi-head diversity is lost. This wastes model capacity and reduces expressiveness. Regularization through attention dropout and careful initialization prevents it, but it's an optimization landscape failure rather than an algorithmic one.

## Transfer

- **Protein structure prediction** (AlphaFold 2) uses attention over amino acid sequences, where "attending" corresponds to learning which residues are spatially close in the folded structure — long-range sequence dependencies that map to 3D spatial relationships.
- **Code understanding** (GitHub Copilot, CodeBERT) applies attention over token sequences of source code, where a variable name at line 1 might be attended to by its usage at line 200 — exactly the long-range dependency problem.
- **Retrieval-augmented generation** adds an attention-like mechanism between the query and retrieved documents: a cross-attention layer where the query "attends to" retrieved context, selecting relevant passages.

Try these:

1. Attention for a sequence of length 512 with d_k=64 and 8 heads. How many floating-point operations in the QKᵀ computation? How many for the softmax(QKᵀ)V step?
2. Explain why causal masking is needed for language model training (predicting next tokens). Draw the attention mask matrix for a 4-token sequence. Which positions are masked?
3. A single attention head has learned to copy: every token attends only to itself. What would Q, K, and V look like for this to happen? Is this useful? Is it the only way a head can "pass through" information unchanged?

---

**Continue → [Why Transformers Scale](55-why-transformers-scale.md)**
