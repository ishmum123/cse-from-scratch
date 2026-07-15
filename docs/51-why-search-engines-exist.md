# Finding a Needle Without Knowing What a Needle Looks Like

## The Problem

Wikipedia has 6.7 million English articles totaling 4GB of text. A user types "black hole event horizon temperature." Those four words appear in thousands of articles — some about astrophysics, some tangentially, some only because they contain the word "black" or "temperature" in unrelated contexts. The user expects the most relevant article ranked first, a response in under 100ms.

A SQL `WHERE content LIKE '%event horizon%'` on 6.7 million articles would scan every row, every byte. 4GB of text at ~500MB/s disk throughput: 8 seconds per query. At 1,000 simultaneous queries, that's impossible. And "LIKE" doesn't handle word boundaries, synonyms, typos, or relevance ranking. It finds strings, not concepts.

Any text search system must handle:

- Millions of documents with queries that must complete in milliseconds
- Ranking: among documents containing the query terms, which are most relevant?
- Partial matches, stemming, and linguistic variants ("runs", "running", "ran")
- Updates: new documents and edits without rebuilding the entire index

## What Would You Try?

Before reading on:

- Every word in every document maps to a list of documents containing it. How large is this mapping for English Wikipedia? What can you precompute to make queries fast?
- Two documents both contain "black hole." Document A has the phrase "black hole event horizon" in the title. Document B mentions "black" and "hole" in separate paragraphs. Which is more relevant? How would you score them?
- A user misspells "atmosfere." How would you still return results for "atmosphere"?

## Failed Attempts

### Attempt 1: Scan Every Document at Query Time

For each query, open every document, search for query terms, return matches. The "grep" approach.

4GB at 500MB/s = 8 seconds per query. Unacceptable at any scale. This is O(D × W) where D is total document size and W is query work per document. Parallelizing helps (split across 100 machines = 80ms), but it's expensive — you're burning 100 machines per query. The approach also gives you exact match only: "running" doesn't match "run." No ranking, just presence/absence.

### Attempt 2: Precomputed Document Frequency Table

Build a table: for each word, list which documents contain it. Query = look up each word's list and intersect. This is the inverted index concept.

The basic inverted index answers "which documents contain word X?" in O(log V + hits) time (V = vocabulary size). But it doesn't help with ranking. A document that uses the word "temperature" 50 times in unrelated contexts matches better by word frequency than a document that uses it once in a precise technical definition. Frequency alone produces poor rankings — the most common words ("the", "and") appear in everything. You need to weight words by how *informative* they are, not just how often they appear.

### Attempt 3: Weight by Raw Term Frequency

Score each document by how often the query terms appear. More occurrences = higher score.

A 1,000-word article that uses "temperature" twice scores the same as a 10-word article that uses "temperature" twice — but the short article is more dense. Also, "temperature" is a common word across physics documents; its presence is less informative than "Hawking radiation" which only appears in specialized astrophysics texts. Raw frequency doesn't account for document length (short documents are disadvantaged) or how rare the query term is across all documents (common terms are over-counted).

## The Discovery

Full scan is too slow. Basic inverted index doesn't rank. Raw frequency over-weights common terms and ignores document length.

The missing piece: two complementary ideas about what makes a word significant.

**TF-IDF** (Term Frequency–Inverse Document Frequency): a word is relevant to a document if it appears often *in that document* (TF) but rarely *across all documents* (IDF). The product penalizes common words automatically. "The" has near-zero IDF (appears in all documents) so it barely contributes to score regardless of TF. "Hawking radiation" has high IDF (rare term), so documents using it frequently score strongly for it.

The **inverted index** maps each unique term to a posting list: `[{doc_id: 42, tf: 3, positions: [14, 87, 203]}, ...]`. The positions enable phrase search ("event horizon" as a phrase, not just those two words anywhere). At query time, look up each query term's posting list, compute TF-IDF scores, sort descending. Elapsed time: milliseconds. The precomputation (building the index) is the expensive step — done offline and updated incrementally.

Modern systems (BM25 — Best Match 25) refine TF-IDF with document length normalization and a saturation function for TF (the 100th occurrence of a word matters less than the 1st). Elasticsearch, Solr, and Lucene all implement BM25 as their default ranking function.

## Try It

<iframe src="../assets/browser/chapter51/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter51/index.html)

Before changing anything, predict:

- Search for a very common word ("the"). How does its IDF affect the scores? Does any document rank highly?
- Search for a rare, specific word. How much higher does the top-ranked document score vs. the second?
- Add a document that uses your query term 10× more than any other. Does it rank first? What does this say about the saturation function?

## Implementation

The browser simulation is dependency-free JavaScript in `browser/chapter51/index.html` (shared helpers in `browser/common/sim.js`). The sim is a schematic of index selectivity, not a TF-IDF or BM25 scorer. Each tick a query runs: `scanTouched = numDocs` on the left (full scan), `idxTouched = Math.round(numDocs * matchRate / 100)` on the right (index lookup returns only matching docs). The "Match rate %" slider controls how selective the query is; at low selectivity the index saves dramatically, at high selectivity the gap narrows. A real inverted index also computes and ranks by relevance scores — this sim shows the I/O savings that make that ranking feasible.

## When It Breaks

**Inverted index staleness.** The index is built from documents at a point in time. When documents are updated or deleted, the index must be updated. For high-update-rate systems, full index rebuilds are too slow; incremental updates (add new posting list entries, tombstone deleted ones) are standard but accumulate deleted-entry garbage over time. Elasticsearch "merges" segments periodically to compact tombstones — a background process that competes with query throughput.

**Vocabulary explosion with user-generated content.** Allowing arbitrary text means the vocabulary can contain millions of unique tokens (typos, URLs, product codes). Posting lists for rare tokens are tiny but there are millions of them. Index size grows superlinearly with unique token count. Minimum document frequency filters (ignore terms that appear in fewer than 5 documents) bound this, but require tuning — too aggressive and you lose long-tail searches that are often highest-intent.

## Transfer

- **Google's PageRank** combined inverted-index retrieval with link graph analysis: TF-IDF finds candidate documents; PageRank scores them by how many authoritative pages link to them. The two-stage retrieve-then-rank pipeline is the foundation of web search.
- **Database full-text search** (PostgreSQL `tsvector`, MySQL FULLTEXT indexes) implements the same inverted index structure inside the database, enabling `WHERE to_tsvector(body) @@ to_tsquery('search terms')` to run in milliseconds on million-row tables.
- **Code search** (GitHub search, Sourcegraph) uses the same inverted index on source code tokens — identifiers, operators, string literals — enabling `function:findUser` queries across billions of lines of code in milliseconds.

Try these:

1. Build the IDF for a 1,000-document corpus where "machine" appears in 100 documents. What's the IDF? Now "quantum" appears in 3 documents. What's the IDF? Which is the more discriminating search term?
2. A query contains 3 words. The posting lists are lengths 10,000; 500; 20. In what order do you intersect them to minimize work? How does this compare to intersecting in the reverse order?
3. A search engine returns the top 10 results for "python tutorial." User clicks result 7 most often. How would you use this click signal to re-rank future results? What problems does this signal have?

---

**Continue → [Why GPUs Changed Everything](52-why-gpus-changed-everything.md)**
