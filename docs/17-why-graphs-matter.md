# When the World Is Made of Connections

## The Problem

A delivery company has 500 cities and wants to find the shortest route between any two. You reach for an array — but an array stores a sequence of values, not *relationships between* values. You consider a tree — but a tree forces one parent per node, and a city can be connected to many others. You consider a sorted list of cities — but the distance from Boston to Philadelphia doesn't sort naturally alongside the distances from other pairs.

The fundamental issue: arrays, trees, linked lists, and hash tables model *collections of things*. But many real problems are about *relationships between things*:

- Which cities connect to which? (routing)
- Who is friends with whom? (social networks)
- Which tasks must complete before others? (build systems)
- Which web pages link to which? (search engines)
- Which packages depend on which? (package managers)

When the problem is fundamentally about relationships, no collection-of-things data structure fits. You end up with O(n²) comparison tables or brittle adjacency lists with no systematic way to traverse them.

Any solution must:

- Represent arbitrary pairwise relationships between entities
- Allow efficient traversal — follow relationships from one entity to its connected entities
- Support both direction (A→B is different from B→A) and weight (the distance from Boston to Philadelphia)
- Enable algorithms that discover global properties (shortest paths, reachability, cycles) from local structure

## What Would You Try?

Before reading on:

- You have 5 cities and a list of which cities are directly connected by roads. How would you represent this to answer "can I drive from city A to city B?"
- What data structure stores "Boston connects to Philadelphia (320 miles) and New York (215 miles)"? How does it generalize to 500 cities?
- If you need to find the shortest path, what do you need to know at each step of the search?

## Failed Attempts

### Attempt 1: Adjacency Matrix

Create an n×n matrix where entry `[i][j]` = the distance from city i to city j (or 0/∞ if no direct connection). Every relationship is stored; lookup is O(1). You can check "is there a road from Boston to Philadelphia?" in one operation.

The cost: n×n space. For 500 cities: 250,000 entries, manageable. For 10 million web pages: 10¹⁴ entries. At 8 bytes each: 800 terabytes for a single matrix. Most web pages don't link to most other pages — the matrix is 99.99% empty (sparse). You're storing a trillion zeros to represent a thousand links. This fails whenever the graph is sparse (and most real graphs are — social networks, web graphs, transportation networks all have much fewer than n² edges).

### Attempt 2: Flat List of All Pairs

Store each edge as a pair: `[(Boston, Philadelphia, 320), (Boston, NewYork, 215), ...]`. Use for relationships only when they exist; no space wasted on non-edges. This is good for storage. But finding all cities connected to Boston requires scanning the entire list: O(e) where e is the number of edges. For a web graph with 10 billion edges, that's 10 billion scans per "who links to this page?" query. Unworkable.

### Attempt 3: Adjacency List

For each node, store the list of its neighbors. Hash table or array indexed by node, each entry a list of (neighbor, weight) pairs. Boston's entry: `[(Philadelphia, 320), (NewYork, 215), (Albany, 175)]`. Finding all of Boston's neighbors is O(degree of Boston) — proportional to how many connections Boston actually has, not to the total number of cities.

Space: O(n + e) — one list per node, one entry per edge. For sparse graphs, e << n², so this is far cheaper than the adjacency matrix. And neighbor lookup is the exact operation that graph traversal algorithms (BFS, DFS, Dijkstra) need on every step.

## The Discovery

Attempt 1 (adjacency matrix) wastes space for sparse graphs but gives O(1) edge lookup. Attempt 2 (edge list) saves space but makes neighbor lookup O(e). Attempt 3 (adjacency list) gives O(degree) neighbor lookup at O(n + e) space — the right tradeoff for algorithms that traverse graphs edge by edge.

A **graph** G = (V, E) consists of:
- V: a set of **vertices** (nodes, entities)
- E: a set of **edges** (relationships) — pairs (u, v) for undirected, ordered pairs for directed

Variations:
- **Weighted graph**: each edge has a numerical weight (distance, cost, capacity)
- **Directed graph (digraph)**: edges have direction — (A, B) ≠ (B, A)
- **DAG** (directed acyclic graph): directed, no cycles — represents dependency ordering

Key algorithms on graphs:
- **BFS** (breadth-first search): visit all neighbors at distance 1, then distance 2, then distance 3, ... Finds shortest path in unweighted graphs. Uses a queue. O(n + e).
- **DFS** (depth-first search): go as deep as possible before backtracking. Finds cycles, topological order, connected components. Uses a stack (implicit via recursion). O(n + e).
- **Dijkstra's algorithm**: shortest path in weighted graphs with non-negative weights. Greedy (chapter 16): always extend the current shortest known path. O((n + e) log n) with a priority queue.

The graph isn't just a data structure — it's a model. Once you model your problem as a graph, decades of graph algorithms become immediately applicable.

## Try It

<iframe src="../assets/browser/chapter17/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter17/index.html)

Before changing anything, predict:

- Run BFS from a node. In what order do nodes get visited? What does the BFS tree look like?
- Run DFS from the same node. How does the visitation order differ?
- Add a cycle to the graph. How do BFS and DFS detect that they've revisited a node?

## Implementation

The working model is dependency-free JavaScript that runs entirely in your browser — nothing to install. Open `browser/chapter17/index.html` to read or modify it (shared UI helpers live in `browser/common/sim.js`). Look for the adjacency-list traversal loop inside BFS and Dijkstra — that neighbor-iteration step is where the graph structure directly determines which algorithm is appropriate and why Dijkstra needs a priority queue where BFS needs only a plain queue.

## When It Breaks

**Negative edge weights break Dijkstra.** Dijkstra's greedy assumption: once a node is "settled" (shortest path found), no shorter path exists. Negative weights violate this — a longer-looking path might become shorter via a negative edge later. For negative weights, use Bellman-Ford: O(n × e), slower but correct. Graphs with negative *cycles* have no well-defined shortest path (you can loop forever, decreasing cost each time).

**Graph traversal is O(n + e) but e can be O(n²).** Dense graphs (many edges) make O(n + e) effectively O(n²). For algorithms like "find all shortest paths between all pairs" (Floyd-Warshall), the complexity is O(n³) regardless of density. For n=10,000 cities: 10¹² operations. Choose algorithms that match your graph's density.

**Distributed graphs don't fit in one machine.** Facebook's social graph has 3 billion nodes and hundreds of billions of edges. No single machine holds all of it. Pregel (Google), GraphX (Spark), and similar systems distribute graph computation across many machines — but network communication between machines replaces pointer traversal, adding latency at every edge crossing. Graph algorithms that require frequent global state (like certain shortest-path variants) are especially painful to distribute.

## Transfer

- **`git` commit history** is a DAG. Each commit points to its parent(s). `git log`, `git merge`, `git rebase` are all graph traversals. Merge commits have two parents. The DAG structure ensures no commit can be its own ancestor.
- **Package managers (npm, pip, cargo)** resolve dependencies using topological sort on a DAG. "Install A before B if A depends on B" is a DAG edge. Cycles in dependency graphs are errors — package managers detect them via DFS.
- **Google's original PageRank** computes a score for each web page based on how many other pages link to it (in-degree in a directed graph), weighted by the scores of the linking pages. It's an eigenvector computation on the web's link graph — a matrix-vector operation on a 10-billion-node graph.

Try these:

1. Implement BFS on a graph starting from node 0. What data structure do you need? Write the pseudocode, then trace it on a 5-node example.
2. A graph has n nodes and e edges. What's the space required for an adjacency matrix? An adjacency list? When does the matrix use less space?
3. Topological sort: given a DAG, output nodes in an order where every node appears before the nodes it points to. How would you implement this using DFS? What happens if the graph has a cycle?

---

**Continue → [Why Functions Exist](18-why-functions-exist.md)**
