# The Invention of Forgetting What You Don't Need to Know

## The Problem

You're building software to process a customer order: validate the shipping address, calculate tax for the customer's state, charge the payment method, send a confirmation email, update inventory.

Without functions, you write all of this as one sequential block. It works for one order. Now you need to process 1,000 orders. You copy the 300-line block 1,000 times into a loop — but wait, that's insane. You use the loop. But inside the loop, the tax calculation is wrong for some states. You fix it. But now you have to find every place tax calculation appears — it's embedded in the middle of the single block, not isolated. There's only one place, but because validation and tax and payment are entangled, you can't change tax without risking breaking validation.

Now shipping address validation must be added to a mobile app that reuses none of your existing codebase. The validation logic is embedded in the 300-line block. Copy-paste? Now changes must be synchronized in two places. Any fix in one location must be manually applied to the other.

The visceral cost: code with no functional decomposition grows toward unmaintainability at a rate proportional to the square of its size — every part can affect every other part.

Any solution must:

- Allow a named, reusable computation
- Hide internal implementation details from callers — isolation, not just reuse
- Accept inputs and produce outputs, with no hidden dependencies on global state
- Be composable — the output of one can be the input of another

## What Would You Try?

Before reading on:

- The "validate shipping address" logic is 50 lines. How would you make it reusable across three different contexts without duplicating those 50 lines?
- If the validation logic needs to know the customer's country, how do you pass that information without making the caller set a global variable?
- What does the rest of the program need to know about how validation *works* internally?

## Failed Attempts

### Attempt 1: Copy-Paste Reuse

Copy the code wherever needed. This works initially. It fails when the code needs to change: you must find and update every copy. A study of the Apache web server codebase found that 20% of bugs were introduced in duplicate code that was only partially updated. Worse: copies drift — one copy gets a bug fix, another doesn't. The divergence compounds over time. Copy-paste is the original sin of software engineering.

### Attempt 2: Global Variables as "Communication Bus"

Set a global variable before a block runs, check it afterward. The validation block reads `global_country`, writes `global_validation_result`. No need to pass inputs/outputs — everything communicates through globals.

This works for single-threaded, single-call scenarios. It fails when two calls overlap (concurrent execution — both write to `global_validation_result`), when you need to call validation with different inputs (you overwrite the global before the first result is used), and when you want to test validation in isolation (tests must set up all required globals, making them fragile). Global mutable state is the architectural version of copy-paste: it creates hidden coupling between every part of the program that touches the same global.

### Attempt 3: Named Block With Explicit Inputs and Output

Define a block of code with a name. When you want to run it, *call* it by name. Pass inputs explicitly. Receive output explicitly. The internal logic is invisible to callers — callers know only the name, inputs, and output.

```python
def validate_address(street, city, state, country):
    # 50 lines of logic
    return is_valid  # caller sees only this
```

The caller doesn't know what those 50 lines do. The validator doesn't know who called it. This ignorance is the feature, not the bug.

## The Discovery

Attempt 1 (copy-paste) fails because changes require synchronized updates. Attempt 2 (globals) fails because implicit coupling defeats isolation. Attempt 3 gives the core properties: named, reusable, input→output, internal-details-hidden.

A **function** (also: procedure, method, subroutine, routine) is a named, parameterized computation with a defined interface. It takes **arguments**, performs computation, and returns a **result**. The internal mechanism is private to the function; the interface (name + argument types + return type) is the contract with callers.

Three properties make functions powerful:

1. **Encapsulation**: the function's internals are hidden. You can rewrite the validation logic to be 10× faster without changing any caller.

2. **Abstraction**: callers operate at a higher level. `validate_address(...)` says *what* happens, not *how*. Code becomes readable at the level of what it's doing (order processing) rather than how it's doing it (substring comparison, regex parsing, HTTP calls).

3. **Composability**: functions can call other functions. `process_order` calls `validate_address`, which calls `is_valid_zip_code`, which calls `lookup_zip_database`. Each level hides its implementation from the level above. This is how large software systems become comprehensible — no human needs to hold all 10 million lines in mind at once.

The formal model: a function is a mapping from inputs to outputs with an invariant that the same inputs always produce the same output (a **pure function**). Pure functions have no side effects and are trivially composable and testable. Impure functions (those that modify state, write to disk, or read from network) are necessary but harder to reason about.

## Try It

<iframe src="../assets/browser/chapter18/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter18/index.html)

Before changing anything, predict:

- A function is called 5 times with the same arguments. How many times does it execute its body?
- What happens when a function calls itself? (Foreshadowing chapter 19.)
- What's the cost of calling a function (overhead beyond the function's body)? Does it matter for simple functions?

## Implementation

The working model is dependency-free JavaScript that runs entirely in your browser — nothing to install. Open `browser/chapter18/index.html` to read or modify it (shared UI helpers live in `browser/common/sim.js`). The left panel shows copy-pasted logic repeated across sites while the right panel defines a single `compute(x)` function with multiple call sites; the `callCount` slider controls invocations, and `STEPS_PER_CALL = 3` lines light up per call to make the duplication cost concrete.

## When It Breaks

**Function call overhead.** A function call requires pushing arguments onto the stack, saving the return address, jumping to the function's code, and reversing all of this on return. For tiny functions called millions of times in tight loops (e.g., a comparator called by a sort), this overhead dominates. Compilers solve this with **inlining**: they copy the function body into the call site, eliminating the call overhead. Marking a C++ function `inline` or using `__attribute__((always_inline))` requests this explicitly.

**Too much abstraction.** Functions hiding everything behind interfaces can make code harder to debug — you see `validate_address(...)` in a traceback and don't know which of the 50 internal steps failed. Deep call stacks (functions calling functions calling functions, 30 levels deep) are hard to read in debuggers. There's a tension between abstraction for maintainability and transparency for debuggability. Over-engineered "enterprise" codebases famously have 15 levels of interface before any real work happens.

**Side effects make functions unpredictable.** A function that modifies a global, writes to a file, or sends a network request has effects beyond its return value. Two such functions composing can interact in unexpected ways. Testing is hard because you must also set up and check the side effects. This is why modern codebases push toward "functional core, imperative shell" — pure functions for logic, side-effect-bearing functions only at the boundaries.

## Transfer

- **Unix pipes.** `cat file | grep "error" | sort | uniq -c` is function composition in the shell. Each tool is a function: takes input (stdin), produces output (stdout), knows nothing about its context. The pipe operator composes them. This is the direct application of the function model to operating system tools.
- **HTTP endpoints / APIs.** A REST API endpoint is a function: URL + request body → response. The server's implementation is hidden. Callers know only the interface. Microservices are systems of functions that call each other over a network instead of a call stack.
- **Spreadsheet formulas.** `=SUM(A1:A10)` is a function call. `=VLOOKUP(B1, D:E, 2)` is function composition. Spreadsheets are functional programming for non-programmers — cell references are arguments, cells are named computations.

Try these:

1. A "pure function" always returns the same output for the same input and has no side effects. Is `random.randint(1, 10)` pure? Is `math.sqrt(4)` pure? Is `open("file.txt").read()` pure? What are the implications for testing each?
2. What is "referential transparency"? If a function call is referentially transparent, what can a compiler do with it that it can't do otherwise?
3. Design the function interface (name, parameters, return value) for: (a) checking if an email address is valid, (b) sending a confirmation email, (c) charging a credit card. Which are pure? Which have side effects?

---

**Continue → [Why Recursion Exists](19-why-recursion-exists.md)**
