# One Name for a Thousand Slots

## The Problem

A weather station records temperature every minute for a year. That's 525,600 readings. You need to:

- Store all of them
- Find the reading from minute 87,432
- Compute the average over any range

With what you know from chapter 2, you'd need 525,600 separate named variables: `temp_1`, `temp_2`, ..., `temp_525600`. Writing the code to sum them would itself be 525,600 lines long. And finding minute 87,432 requires searching through all variables by name.

The visceral cost: the code to process the data is larger than the data itself. You can't loop over separately-named variables. You can't compute an index and jump to minute N. The program is unwritable.

Any solution must:

- Store many values under a single name
- Access any element in constant time given its position
- Use positions that are computable — you can calculate index 87,432 from the number 87,432

## What Would You Try?

Before reading on:

- If you had 1,000 boxes numbered 1 to 1,000 sitting in a line, how would you find box number 743?
- What property of that physical arrangement makes retrieval instant?
- What's the tradeoff of putting all boxes in a line vs scattering them around a warehouse?

## Failed Attempts

### Attempt 1: A Linked Chain of Variables

Store each value in its own slot, and have each slot point to the next. You traverse from the start to find any element. This seems workable — you have one name (the "head" of the chain) and can walk to any position.

It fails at position lookup: finding element N requires walking N steps. Minute 87,432 means 87,432 pointer-follows. That's not "find by index" — it's "scan until you arrive." For random access, a linked chain is as slow as searching an unordered list. This failure matters most in access-heavy workloads: database rows, pixel buffers, sensor streams.

### Attempt 2: A Dictionary / Name–Value Store

Store each value under a name that encodes its position: `{"minute_1": 23.4, "minute_2": 23.1, ...}`. You can retrieve by name. But name lookup requires hashing or searching — it's O(log n) or O(n), not O(1). And the names themselves waste memory: `"minute_87432"` is 14 bytes just for the key, vs 4 bytes for the integer value it identifies. The overhead consumes more space than the data.

More fundamentally, this pushes the problem down a level: how does the dictionary itself store things? Eventually something has to commit to a layout in memory.

### Attempt 3: Compute a Formula to Find Each Value

What if you compute where each value *should* be? If value 1 is at address 1000, value 2 is at address 1004 (4 bytes later), then value N is at address `1000 + (N-1) * 4`. No traversal, no search — pure arithmetic.

This only works if the values live at *predictably spaced* addresses. That means they must be stored *contiguously* — one right after another, no gaps, no pointers between them. And that's exactly what an array is.

## The Discovery

Attempt 1 (linked chain) showed that pointer traversal gives sequential access but kills random access. Attempt 3 revealed the key: if elements are contiguous and same-size, position becomes arithmetic.

An **array** is a block of memory where elements are stored consecutively, each taking the same number of bytes. The element at index `i` lives at address `base + i * element_size`. This single formula is O(1) — it doesn't matter if there are 10 elements or 10 million. The cost of finding any element is the same.

The price: the size is fixed at creation (you must know how much contiguous space to reserve), and inserting in the middle requires shifting everything after the insertion point — O(n) work.

Formally: an array of `n` elements of type `T` (size `s` bytes each) starting at base address `b` stores element `i` at address `b + i·s`. Index computation is *pure arithmetic*, done in hardware in one instruction. This is why array access is the fastest data structure operation that exists.

## Try It

<iframe src="../assets/browser/chapter03/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter03/index.html)

Before changing anything, predict:

- If you access index 0 and then index 100, how many memory locations does the machine visit?
- What happens when you try to access an index beyond the array's length?
- If you insert an element at position 0, how many elements have to move?

## Implementation

The working model is dependency-free JavaScript that runs entirely in your browser — nothing to install. Open `browser/chapter03/index.html` to read or modify it (shared UI helpers live in `browser/common/sim.js`). Click any cell to see the formula `address = base + i × 4` flash in the status bar, showing why O(1) random access is guaranteed regardless of index. The sim is a read-only viewer — to experience the O(n) insertion cost, you would add a button that shifts elements right from the clicked cell to make room.

## When It Breaks

**Buffer overflows.** Accessing beyond the end of an array reads (or writes) memory that belongs to something else. In languages without bounds checking (C, C++), this is the most exploited class of vulnerability in history. The Morris Worm (1988), Heartbleed (2014), and countless others used buffer overflows to read secret memory or inject code.

**Fixed capacity.** Arrays must be sized at creation. Too small: data overflows. Too large: memory is wasted. Dynamic arrays (Python lists, Java `ArrayList`) work around this by doubling capacity when full — but the doubling operation is O(n) and causes occasional latency spikes. Real-time systems (game engines, audio buffers) avoid dynamic arrays in hot paths for exactly this reason.

**Cache misses during scattered access.** Arrays are cache-friendly when accessed sequentially. But if your access pattern jumps around randomly (access index 0, then 99,999, then 500, ...), each access may miss the CPU cache, making an O(1) operation much slower in practice. This is why columnar databases (reading one field for all rows) outperform row-oriented databases for analytical queries.

## Transfer

- **Image buffers.** A 1920×1080 pixel image is just an array of 2,073,600 integers. Pixel at row `r`, column `c` lives at index `r * 1920 + c`. Every image filter loops over this array sequentially.
- **Ring buffers in audio.** Audio cards maintain a circular array of samples. The write position advances, wraps around, overwrites old samples. O(1) access keeps audio latency predictable.
- **NumPy / pandas / GPU tensors.** Machine learning frameworks are built on arrays. A neural network weight matrix is a 2D array. The speed of matrix multiplication depends entirely on cache-friendly array layout.

Try these:

1. A 2D array is stored row-by-row in memory (row-major). If you traverse it column-by-column instead, why is it slower? What does this have to do with the cache?
2. Design a "dynamic array" that doubles in size when full. What's the amortized cost per insertion? Show your reasoning.
3. What would change if elements in an array were different sizes? How do languages like Python (which store any-type objects) handle this?

---

**Continue → [Why Memory Has Addresses](04-why-memory-has-addresses.md)**
