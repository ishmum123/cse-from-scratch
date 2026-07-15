# The Shortcut That's Occasionally Correct

## The Problem

Scheduling problem: you have a single conference room and n meeting requests, each with a start time and end time. Maximize the number of meetings you can hold (no two can overlap).

Dynamic programming says: consider all subsets of non-overlapping meetings, find the largest. For n=30 meetings: 2³⁰ = 1 billion subsets. Feasible for n=30, but a conference booking system might have n=10,000. Exponential is out.

Is there a shortcut that, for this specific problem, always finds the optimal answer without exploring all possibilities?

The temptation: "just pick greedily — always take the locally best option." But greedy fails for most optimization problems. For the coin problem (make change for 11 cents using coins [1, 5, 6]), greedy picks 6, then 5 → done with 2 coins. Wait: 5+6=11, that's correct. But for amount 11 with coins [1, 5, 6, 9]: greedy picks 9, then 1+1 → 3 coins. Optimal: 5+6 → 2 coins. Same problem type, different coin values, greedy fails.

The critical question: for *which* problems is greedy correct, and *why*?

Any solution must:

- Find the optimal solution without exhaustive search
- Run in O(n log n) or better (sort + single pass)
- Be provably correct — not "usually correct" but guaranteed optimal
- Identify *when* local optimality implies global optimality

## What Would You Try?

Before reading on:

- Back to the conference room: when you have to choose *which* meeting to take, what would you pick first — the shortest one? The earliest starting? The earliest ending?
- Try "shortest first" on: meetings at [9–11], [9–10], [10–11]. Does it maximize count?
- Try "earliest ending first" on the same set. What's the difference?

## Failed Attempts

### Attempt 1: Greedy by Earliest Start Time

Take the meeting that starts earliest. This sounds reasonable — get as much of the day as possible. But consider: one meeting spans 9am–6pm, and five meetings span 10am–11am, 11am–12pm, 12pm–1pm, 1pm–2pm, 2pm–3pm. Earliest start takes the 9am–6pm meeting and you get 1 meeting. Optimal: skip it, take the five 1-hour meetings. Earliest start fails because a long early meeting blocks many short later meetings.

### Attempt 2: Greedy by Shortest Duration

Take the shortest meeting first, then the next shortest that doesn't conflict. Short meetings seem to waste less time. But consider: shortest meeting is 9:00–9:05. It's immediately followed by another 9:00–9:05 (same time slot, different room — but we only have one room). They conflict. After taking 9:00–9:05, the next shortest might be 9:04–9:09, conflicting again. Meanwhile five 1-hour meetings from 10am–3pm are all non-conflicting. Shortest first can select poorly if short meetings cluster in a crowded time.

Counterexample: meetings [1–10], [2–3], [3–4]. Shortest first takes [2–3] and [3–4]: 2 meetings. But [1–10] ends last, so [2–3] and [3–4] are the correct greedy-by-earliest-end answer anyway. The algorithms coincide here. Find a counterexample: [1–3], [2–4], [3–5], [1–2]. Shortest first: [1–2] (duration 1), then [3–5] (next shortest non-conflicting) = 2 meetings. Earliest end: [1–2], [3–5] = 2. Same! Harder to construct a difference — maybe shortest and earliest-end are equivalent? No: [0–9], [1–4], [4–8], [8–9]. Shortest: [1–4] (dur 3)... actually this requires careful construction. The point: empirical testing isn't a proof.

### Attempt 3: Greedy by Earliest Finish Time

Take the meeting that finishes earliest, then the next meeting that starts at or after the previous one finished, repeat. Rationale: finishing early leaves maximum room for future meetings, regardless of start time or duration.

## The Discovery

Attempt 1 (earliest start) fails because blocking time matters, not start time. Attempt 2 (shortest) is approximately right in many cases but wrong in some — and we can't accept "approximately right" for a scheduling system. Attempt 3 (earliest finish) is provably optimal.

**Proof by exchange argument**: suppose the greedy solution picks meetings G₁, G₂, ..., Gₖ in order of finish time. Suppose an optimal solution picks O₁, O₂, ..., Oₘ with m > k. We'll derive a contradiction.

Match greedily: G₁ finishes no later than O₁ (greedy picks earliest finish), so replacing O₁ with G₁ in the optimal solution still leaves a valid schedule (G₁ ends ≤ O₁'s end, so O₂ can still follow). Now "exchange" O₂ with G₂ by the same argument. Continue: after all exchanges, we have a valid schedule containing all of G₁, ..., Gₖ and m−k elements from the original optimal. This schedule has at least m meetings — but greedy said it couldn't add more after Gₖ. Contradiction. Therefore m = k: greedy is optimal.

Greedy works when there's a **greedy choice property**: a locally optimal choice is part of some globally optimal solution. This holds for interval scheduling because finishing early never prevents you from doing something you couldn't have done anyway. It fails for coin change because taking the largest coin can block smaller coins that would combine better.

Formalizing when greedy works: **matroid theory** provides the general condition. A matroid is a set system with an "exchange property" — greedy on a matroid is always optimal. Interval scheduling and minimum spanning trees have matroid structure. Knapsack and coin change with arbitrary denominations don't.

## Try It

<iframe src="../assets/browser/chapter16/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter16/index.html)

Before changing anything, predict:

- Try all three greedy strategies (earliest start, shortest, earliest finish) on the same set of meetings. Find an input where they disagree.
- For a set of 20 random meetings, does the earliest-finish greedy always find more meetings than random selection?
- What happens when all meetings start at the same time?

## Implementation

The working model is dependency-free JavaScript that runs entirely in your browser — nothing to install. Open `browser/chapter16/index.html` to read or modify it (shared UI helpers live in `browser/common/sim.js`). The sim demonstrates the coin-change problem: `greedySolve(amount, coins)` picks the largest denomination that fits at each step, while `dpSolve()` builds the optimal solution bottom-up — with the default coins [1, 4, 15, 20] and amount 30, greedy gets the wrong answer and the side-by-side coin rows show exactly where it diverges from the DP optimum.

## When It Breaks

**Greedy for coin change fails with non-standard denominations.** US coins (1, 5, 10, 25 cents) have a property called "canonical" — greedy works. Change for 30 cents: 25+5. But coins [1, 3, 4] and amount 6: greedy takes 4, then 1+1 = 3 coins. Optimal: 3+3 = 2 coins. Vending machines in countries with "non-canonical" coin systems have given wrong change using greedy algorithms.

**Greedy for weighted interval scheduling fails.** If meetings have values (the CEO's meeting is worth more to schedule than the intern's), earliest-finish greedy is wrong. The profitable variant requires DP: `opt(j) = max(value_j + opt(p(j)), opt(j-1))` where `p(j)` is the last meeting compatible with meeting j. Greedy optimizes count; DP optimizes value.

**Greedy Huffman encoding is optimal, but only for symbol-by-symbol codes.** Huffman coding greedily assigns shorter bit strings to more frequent characters. It's provably optimal among prefix-free codes on individual characters. Arithmetic coding breaks this constraint and achieves better compression — demonstrating that the "greedy within a constraint" result doesn't survive when the constraint is relaxed.

## Transfer

- **Dijkstra's algorithm** (shortest path in a weighted graph) is greedy: always extend the shortest known path. It's correct because edge weights are non-negative — negative edges break the greedy choice property (a currently-long path might become short via a negative edge). Bellman-Ford handles negative edges via DP instead.
- **Huffman encoding** (data compression) greedily builds an optimal prefix-free binary code. Used in JPEG, MP3, DEFLATE (gzip). Proof of optimality: exchange argument, same structure as interval scheduling.
- **Kruskal's and Prim's algorithms** (minimum spanning tree) are greedy on graphs. Both add the cheapest available edge/node that doesn't create a cycle. Provably optimal because spanning trees form a matroid.

Try these:

1. Prove that "earliest start time" greedy fails for interval scheduling by constructing a counterexample with exactly 3 meetings where greedy takes 1 meeting but optimal takes 2.
2. Greedy works for interval scheduling and minimum spanning trees. Does it work for the "weighted job scheduling" problem (meetings with different values)? What specifically breaks the greedy choice property?
3. Construct a set of coin denominations where US-style greedy (always take the largest coin that fits) gives the optimal answer. Then construct one where it fails. What distinguishes the two sets?

---

**Continue → [Why Graphs Matter](17-why-graphs-matter.md)**
