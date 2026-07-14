# The Slot That Knows Where to Find Itself

## The Problem

Binary search on sorted arrays: O(log n). Balanced BSTs: O(log n). These are theoretically excellent — for a billion records, at most 30 comparisons. But in practice, those 30 comparisons still involve 30 memory accesses, 30 branch decisions, and 30 pointer dereferences. Modern CPUs can do billions of simple operations per second, but memory latency and branch misprediction slow each comparison down.

More fundamentally: O(log n) means the cost grows with the collection size. A collection 1,000× larger requires ~10 more comparisons. For most workloads, this is fine. But some workloads need lookup that's *completely independent of collection size*: Python's `dict["username"]`, checking if a URL was already crawled, Redis key lookup, a DNS resolver checking its cache. These operations need O(1) — constant time regardless of n.

Is this even theoretically possible? For n items, you need n lookups to each be O(1). That seems to require knowing exactly where each item is without searching.

Any solution must:

- Find any item in O(1) time on average
- Not require the key to be a contiguous integer (strings, tuples, any hashable type)
- Handle items not being found efficiently (not just present items)
- Use O(n) space, not more

## What Would You Try?

Before reading on:

- If all keys were integers from 0 to 999, how would you build an O(1) lookup? (Hint: arrays.)
- What goes wrong when keys are strings or arbitrary objects?
- Can you turn an arbitrary key into a number? What properties would that conversion need?

## Failed Attempts

### Attempt 1: Direct Address Table (Array Index = Key)

If all keys are integers in a known range [0, N), use an array of size N. Key k maps to array[k]. O(1) lookup, O(1) insert, O(1) delete. This is perfect — but only when keys are dense integers. Key space for strings: 256^max_length — astronomical. Storing an array indexed by every possible 10-character string requires 256^10 ≈ 10^24 entries. That's more bits than atoms in a human body. Direct address tables work for small dense key spaces; they're impossible for arbitrary keys.

### Attempt 2: Keep a Sorted Array, Search with Interpolation

Sorted array + binary search is O(log n). Interpolation search (smarter midpoint estimation) gets O(log log n) on uniformly distributed numeric keys. Still not O(1), but dramatically faster in practice. The problem: strings and compound keys don't interpolate meaningfully. "Alice" is not numerically between "Aardvark" and "Azimuth" in a way that helps you estimate its position. Interpolation is clever but domain-specific and non-general.

### Attempt 3: Convert Any Key to an Integer, Then Use an Array

What if we compute a number from the key — any key, any type — and use that number as an array index? A **hash function** does exactly this: takes an arbitrary key and returns an integer. `hash("username") = 4,782`. Use 4,782 as the array index.

The problem: 4,782 might exceed the array size. Fix: take it modulo the array size. Now "username" maps to slot `4782 % 1000 = 782`.

New problem: two different keys might hash to the same slot. `hash("password") % 1000` might also be 782. This is a **collision** and it's unavoidable — if you have more possible keys than slots, the pigeonhole principle guarantees collisions.

## The Discovery

Attempt 1 showed that O(1) lookup is possible with arrays when keys are integers — the slot *is* the key. Attempt 3 extends this: *compute* the slot from the key via a hash function.

A **hash table** (dictionary, map, unordered_map) has:

1. An array of `m` slots
2. A hash function `h(key)` → integer in [0, m)
3. A **collision resolution** strategy

Two main collision resolution strategies:

**Chaining**: each slot holds a linked list of all keys that hash to it. Lookup: hash the key, go to that slot, scan the list. Average list length = n/m (called the **load factor α**). When α is small (e.g., α ≤ 0.75), lists are short — average O(1) lookup.

**Open addressing**: when a slot is occupied, probe to the next slot (linear probing: slot+1, slot+2, ..., or quadratic probing: slot+1², slot+2², ...). All items stored in the array itself, no pointers. Better cache behavior than chaining; degrades faster as α approaches 1.

Average case: O(1) for insert, lookup, delete. Worst case: O(n) if many keys collide (all hash to the same slot). A good hash function makes this exponentially unlikely for random data.

Formally: a hash table achieves expected O(1) operations under **simple uniform hashing assumption** — each key is equally likely to hash to any slot, independent of others. Real hash functions (MurmurHash3, SipHash, xxHash) are designed to approximate this.

## Try It

<iframe src="../assets/browser/chapter12/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter12/index.html)

Before changing anything, predict:

- What happens to average lookup time as you add more items and load factor increases?
- Insert keys that all hash to the same slot. What does the structure look like?
- Compare chaining vs open addressing behavior as the table fills up.

## Implementation

The working model is dependency-free JavaScript that runs entirely in your browser — nothing to install. Open `browser/chapter12/index.html` to read or modify it (shared UI helpers live in `browser/common/sim.js`). Look for the hash function and the collision-resolution branch that follows it — toggling between chaining and open addressing in that one spot shows how each strategy degrades as the load factor rises.

## When It Breaks

**Hash collisions under adversarial input.** If an attacker knows your hash function, they can craft inputs that all hash to the same slot — turning O(1) into O(n) and denying service. In 2011, Perl, PHP, Java, and Python hash tables were all vulnerable to this attack (hash DoS). The fix is **randomized hashing** (SipHash, added to Python 3.3): salt the hash function with a random value at startup, so the attacker can't predict collisions. Every language shipping a hash table in 2024 uses some form of randomized hashing by default.

**Hash tables don't support range queries.** "Find all users with age between 25 and 35" requires scanning all slots — O(n). Trees (chapter 10) support this in O(log n + k) where k is the result count. This is why databases maintain *both* hash indexes (for equality lookups) and B-tree indexes (for range queries) on the same column.

**Resize cost.** When the table fills past the load factor threshold, you must resize (typically double) and re-hash all existing entries — O(n) work at that moment. Python dicts do this, causing occasional O(n) inserts. Systems needing predictable latency (real-time audio, trading systems) use pre-sized tables or consistent hashing (chapter 49) to avoid resize.

## Transfer

- **Python `dict` and `set`** are hash tables. `{}` literal creates a dict; `in` operator on a dict/set is O(1). This is why checking `x in set(items)` is O(1) and `x in list(items)` is O(n).
- **DNS resolver cache.** Mapping hostnames to IP addresses. A billion queries per day; each must be answered in microseconds. Hash table with randomized TTL-expiry is the only structure fast enough.
- **Deduplication.** Git uses SHA-1 hashes of file content as keys: if two files have the same hash, they're the same content. Storing only one copy, keyed by hash, gives content-addressed deduplication without comparing file bytes.

Try these:

1. You have 1,000 hash table slots and 750 items (load factor 0.75). With chaining, what's the probability that lookup requires more than 3 comparisons?
2. Design a hash function for strings. What properties must it have? What would a *bad* hash function look like?
3. A hash table gives O(1) average; a balanced BST gives O(log n) worst case. Which would you choose for: (a) user session storage (b) a flight booking index that supports "find all flights from NYC" (c) a word frequency counter on a 1GB text file?

---

**Continue → [Why Sorting Exists](13-why-sorting-exists.md)**
