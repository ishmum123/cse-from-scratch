# When Words Weren't Enough

## The Problem

A shepherd leaves at dawn with his flock. By dusk he wants to know if every sheep returned. He has no numbers. He has no writing. All he has is his memory — and fifty sheep.

He tries to remember each face. He loses track. He tries to remember "a lot" vs "a little." Two sheep wander off and he cannot tell.

The cost: sheep are wealth. Missing one is a real loss. Without a way to *represent* quantity precisely, he cannot detect the loss, cannot trade fairly, cannot plan for winter.

Any solution must:

- Distinguish quantities that differ by exactly one
- Work without needing to keep everything in view simultaneously
- Be communicable — tell someone else the count, not just feel it
- Be repeatable — same flock, same answer, every time

## What Would You Try?

You are the shepherd. Before reading on:

- You have a pile of pebbles. How would you use them to track the flock?
- If you ran out of pebbles, what would you do differently?
- What happens when you need to communicate "47" to someone who wasn't there?

## Failed Attempts

### Attempt 1: Memory and Pattern Recognition

Humans are good at recognizing faces and patterns. The shepherd tries to memorize each sheep individually — a natural first instinct.

This works for five sheep. It fails at fifty. Human working memory holds about seven items. Beyond that, items blur together and errors compound. The failure reveals the key constraint: the solution cannot live entirely in biological memory. It needs an external representation.

### Attempt 2: Tally Marks Without Positional Value

Scratch marks on a rock — one mark per sheep. Easy to make, easy to verify on return. This works, until the shepherd has 1,000 sheep. Now he needs 1,000 marks, and counting the marks takes as long as counting the sheep.

The failure: representation size scales with the quantity. A good number system must let small symbols represent large quantities. Tally marks violate this.

### Attempt 3: Named Groups (Roman Numerals Style)

Group things: five pebbles becomes one kind of token, five tokens becomes another kind. This gets further — you can represent 500 compactly. But arithmetic is painful (try multiplying XLVII by XXIII). And you still need a new symbol for every new power.

The failure: no positional meaning. The value of a symbol doesn't depend on *where* it sits, so the system can't reuse a small set of digits for arbitrarily large numbers.

## The Discovery

Attempt 2 gave us external representation — crucial. Attempt 3 gave us grouping — also crucial. What neither had: *positional value*, where the same symbol means different amounts depending on its position.

Combine external representation + grouping + position: a symbol's value multiplies by the base for each position it moves left. With just ten symbols (0–9), you can write any quantity, no matter how large. The shepherd doesn't need more pebble types as his flock grows — he needs the same symbols arranged differently.

Counting, formally, is the act of establishing a **bijection** between a set of objects and an initial segment of the natural numbers {1, 2, 3, ...}. The final number reached is the cardinality — the size of the set. Positional notation (base 10, base 2, base 16) lets us write that cardinality with a bounded symbol set.

The deeper principle: what the shepherd invented wasn't just convenience. He invented the ability to *compare across time and space* — to tell a future self, or another person, exactly how many. Counting is the compression of a whole set into a single symbol.

## Try It

<iframe src="../assets/browser/chapter01/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter01/index.html)

Before changing anything, predict:

- What happens to the count when you remove items one at a time — does it stay accurate at zero?
- If you represent the same quantity in base 2 vs base 10, which takes more symbols? Why?
- What breaks first when the count grows very large?

## Implementation

The working model is dependency-free JavaScript that runs entirely in your browser — nothing to install. Open `browser/chapter01/index.html` to read or modify it (shared UI helpers live in `browser/common/sim.js`). Each stone starts with `counted: false`; clicking it sets `counted = true` and increments `count`, making the status display update to show how many have been claimed. The sim is a schematic of the one-to-one correspondence principle — to make it a full counting system, you would add tally and positional panels that update in lockstep with each assignment.

## When It Breaks

**Off-by-one errors.** Counting is deceptively easy to get wrong at boundaries. Do you count the sheep *leaving* or *returning*? Fence-post errors (counting intervals vs points) are one of the most common bugs in software — array indexing, loop bounds, date ranges all share this failure mode.

**Integer overflow.** Positional notation with a fixed number of digits has a maximum. A 32-bit unsigned integer wraps at 4,294,967,295. In 2004, a Comair flight scheduling system crashed because a counter field exceeded 32,767 — stranding 11,000 passengers over Christmas. The representation had a ceiling the designers forgot about.

**Floating point imprecision.** Once quantities become non-integer (fractions, measurements), positional notation introduces rounding. `0.1 + 0.2` in IEEE 754 floating point is `0.30000000000000004`. Financial systems that use floats for currency accumulate errors that compound into real money.

## Transfer

- **Inventory systems** use counting to detect shrinkage. Every barcode scan is a tally mark. RFID in warehouses automates the shepherd's pebble-swap.
- **Network packet sequence numbers** count transmitted packets so the receiver detects gaps. TCP's sequence numbers are a 32-bit counter — and wrap around, which must be handled.
- **Version control commits** are a count of changes. Git's SHA is a content hash, but commit graphs are ordered by their count from the root.

Try these:

1. A 3-bit counter can hold values 0–7. Draw what happens when it reaches 7 and you add 1. What real system does this behavior appear in?
2. Design a counting scheme for a library with more books than a 32-bit integer can hold. What would you change?
3. Why does "counting from zero" (0-indexed) avoid one fence-post problem while creating another? Give a concrete example.

---

**Continue → [Why Numbers Need Memory](02-why-numbers-need-memory.md)**
