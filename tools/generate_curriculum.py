#!/usr/bin/env python3
"""Generate the full Rebuilding Computer Science From Scratch curriculum scaffold."""

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import browser_sims
GITHUB_BASE = "https://github.com/ishmum123/cse-from-scratch/blob/main"

CHAPTER_SEEDS = [
    # Part I — Information
    {
        "title": "Why Counting Exists",
        "key": "counting",
        "problem": "You can compare piles of rocks, but you cannot say *how many*.",
        "idea": "Counting assigns a stable symbol to a quantity so it can be remembered and communicated.",
    },
    {
        "title": "Why Numbers Need Memory",
        "key": "number memory",
        "problem": "You can count, but every new number erases the last one.",
        "idea": "A register or variable holds a value so it can be reused later.",
    },
    {
        "title": "Why Arrays Exist",
        "key": "array",
        "problem": "You have a hundred numbers and no way to keep them in order.",
        "idea": "An array stores many values under one name at contiguous addresses.",
    },
    {
        "title": "Why Memory Has Addresses",
        "key": "address",
        "problem": "You stored a value, but now you cannot find it again.",
        "idea": "Every location in memory has an address, so the machine can fetch or store by number.",
    },
    {
        "title": "Why Copying Is Expensive",
        "key": "copy",
        "problem": "Moving data from one place to another takes forever.",
        "idea": "Copying costs time proportional to size, so we pass references or reuse buffers when we can.",
    },
    {
        "title": "Why Locality Matters",
        "key": "locality",
        "problem": "The machine reads one byte, then another far away, and wastes most of its time.",
        "idea": "Caches exploit spatial and temporal locality to keep nearby data fast.",
    },
    # Part II — Searching
    {
        "title": "Why Looking Is Slow",
        "key": "linear search",
        "problem": "You open a box and search every item one by one.",
        "idea": "Unordered search is linear; the only way to speed it up is to remove the need to look at everything.",
    },
    {
        "title": "Why Ordering Helps",
        "key": "ordering",
        "problem": "The items are scattered. Finding one is always a gamble.",
        "idea": "If data is sorted, you can reject whole regions of the search space at once.",
    },
    {
        "title": "Why Binary Search Exists",
        "key": "binary search",
        "problem": "Even scanning half the list is too slow when the list grows.",
        "idea": "Binary search halves the problem on every step by comparing to the middle element.",
    },
    {
        "title": "Why Trees Exist",
        "key": "tree",
        "problem": "You can sort, but inserts and deletes keep breaking your order.",
        "idea": "A tree keeps order while allowing fast inserts and deletes through branching.",
    },
    {
        "title": "Why Balancing Exists",
        "key": "balance",
        "problem": "Your tree works beautifully until someone feeds it sorted data.",
        "idea": "Balancing guarantees logarithmic height by restructuring the tree as it grows.",
    },
    {
        "title": "Why Hashing Exists",
        "key": "hash table",
        "problem": "You need near-instant lookups, but comparisons are expensive.",
        "idea": "A hash function maps keys directly to slots, trading space for O(1) access.",
    },
    # Part III — Organization
    {
        "title": "Why Sorting Exists",
        "key": "sort",
        "problem": "Data arrives messy, and every later step assumes order.",
        "idea": "Sorting arranges data so that searching, merging, and scanning become simple and predictable.",
    },
    {
        "title": "Why Divide and Conquer Works",
        "key": "divide and conquer",
        "problem": "Solving the whole problem at once is too hard.",
        "idea": "Breaking a problem into smaller independent pieces and combining their solutions tames complexity.",
    },
    {
        "title": "Why Dynamic Programming Exists",
        "key": "dynamic programming",
        "problem": "You keep solving the same sub-problem again and again.",
        "idea": "Memoization stores answers to overlapping sub-problems so each is solved only once.",
    },
    {
        "title": "Why Greedy Sometimes Works",
        "key": "greedy",
        "problem": "Every local choice looks correct, yet the final answer is wrong.",
        "idea": "Greedy algorithms work when local optimality guarantees global optimality.",
    },
    {
        "title": "Why Graphs Matter",
        "key": "graph",
        "problem": "The world is not a list. Points connect to other points.",
        "idea": "Graphs model relationships explicitly, unlocking searches over states, paths, and dependencies.",
    },
    # Part IV — Computation
    {
        "title": "Why Functions Exist",
        "key": "function",
        "problem": "You write the same sequence of steps ten times.",
        "idea": "Functions name reusable computations and hide their internal details behind an interface.",
    },
    {
        "title": "Why Recursion Exists",
        "key": "recursion",
        "problem": "A problem contains a smaller version of itself.",
        "idea": "Recursion solves a problem by reducing it to a base case and a self-similar sub-problem.",
    },
    {
        "title": "Why Stacks Exist",
        "key": "stack",
        "problem": "You need to remember where you came from.",
        "idea": "A stack stores return addresses and local state in last-in-first-out order.",
    },
    {
        "title": "Why Queues Exist",
        "key": "queue",
        "problem": "Tasks arrive in order and must be handled fairly.",
        "idea": "A queue processes items in first-in-first-out order, decoupling producers and consumers.",
    },
    {
        "title": "Why Schedulers Exist",
        "key": "scheduler",
        "problem": "Every process wants the CPU at the same time.",
        "idea": "A scheduler decides who runs next, balancing fairness, latency, and throughput.",
    },
    # Part V — Operating Systems
    {
        "title": "Why Processes Exist",
        "key": "process",
        "problem": "One crashing program takes down everything.",
        "idea": "Processes isolate programs with private memory and resources so failures stay contained.",
    },
    {
        "title": "Why Threads Exist",
        "key": "thread",
        "problem": "A single process has work it could do in parallel.",
        "idea": "Threads share memory within a process so multiple flows of execution can cooperate.",
    },
    {
        "title": "Why Locks Exist",
        "key": "lock",
        "problem": "Two threads change the same value and corrupt it.",
        "idea": "Locks enforce mutual exclusion so only one thread touches shared state at a time.",
    },
    {
        "title": "Why Deadlocks Happen",
        "key": "deadlock",
        "problem": "Two threads wait for each other forever.",
        "idea": "Deadlocks arise when threads hold resources while waiting for others in a circular chain.",
    },
    {
        "title": "Why Virtual Memory Exists",
        "key": "virtual memory",
        "problem": "Programs expect memory that does not exist.",
        "idea": "Virtual memory maps program addresses to physical pages, enabling isolation and swapping.",
    },
    {
        "title": "Why Context Switching Costs",
        "key": "context switch",
        "problem": "Switching between tasks costs more than the tasks themselves.",
        "idea": "Saving and restoring registers, caches, and TLB state makes switching expensive.",
    },
    # Part VI — Databases
    {
        "title": "Why Files Aren't Enough",
        "key": "file storage",
        "problem": "Reading a raw file for every query is unbearably slow.",
        "idea": "Databases organize records so they can be found, updated, and queried efficiently.",
    },
    {
        "title": "Why Indexes Exist",
        "key": "index",
        "problem": "Scanning every row is fine until there are millions.",
        "idea": "Indexes maintain a secondary lookup structure so queries can jump to relevant rows.",
    },
    {
        "title": "Why B-Trees Won",
        "key": "b-tree",
        "problem": "Your index works on disk, but disk blocks are large.",
        "idea": "B-trees keep many keys per node, minimizing disk reads and writes.",
    },
    {
        "title": "Why Transactions Exist",
        "key": "transaction",
        "problem": "A crash in the middle of an update leaves data half-changed.",
        "idea": "Transactions group operations so they either all commit or all roll back.",
    },
    {
        "title": "Why MVCC Exists",
        "key": "mvcc",
        "problem": "Readers and writers keep blocking each other.",
        "idea": "Multi-version concurrency control lets readers see a consistent snapshot without locking.",
    },
    {
        "title": "Why Query Planners Matter",
        "key": "query planner",
        "problem": "The same query runs fast one day and slow the next.",
        "idea": "A planner chooses the cheapest way to execute a query using statistics and cost models.",
    },
    # Part VII — Networking
    {
        "title": "Why Computers Need Addresses",
        "key": "addressing",
        "problem": "Two computers must talk, but they do not know each other exists.",
        "idea": "Addresses uniquely identify machines on a network so messages can be routed.",
    },
    {
        "title": "Why Packets Exist",
        "key": "packet",
        "problem": "A single message can be too large or too fragile to send whole.",
        "idea": "Packets split messages into small, independently routed units.",
    },
    {
        "title": "Why TCP Exists",
        "key": "tcp",
        "problem": "Packets get lost, duplicated, or arrive out of order.",
        "idea": "TCP adds sequence numbers, acknowledgments, and retransmissions for reliable streams.",
    },
    {
        "title": "Why Congestion Happens",
        "key": "congestion",
        "problem": "Sending faster makes the network slower for everyone.",
        "idea": "Congestion control adapts send rate to the network's actual capacity.",
    },
    {
        "title": "Why Load Balancers Exist",
        "key": "load balancer",
        "problem": "One server dies and the whole service disappears.",
        "idea": "Load balancers spread traffic across many backends and hide failures.",
    },
    # Part VIII — Distributed Systems
    {
        "title": "Why One Computer Isn't Enough",
        "key": "distribution",
        "problem": "One machine can no longer hold all the data or traffic.",
        "idea": "Distributed systems partition work across independent machines connected by a network.",
    },
    {
        "title": "Why Clocks Lie",
        "key": "clock",
        "problem": "Every machine thinks it knows the time. They disagree.",
        "idea": "Without a shared clock, distributed systems must reason about causality and ordering instead.",
    },
    {
        "title": "Why Consensus Exists",
        "key": "consensus",
        "problem": "Multiple machines must agree, but messages can be lost.",
        "idea": "Consensus protocols let a group agree on a value despite failures.",
    },
    {
        "title": "Why Raft Works",
        "key": "raft",
        "problem": "You need consensus, but Paxos is impossible to implement.",
        "idea": "Raft separates leader election, log replication, and safety into understandable rules.",
    },
    {
        "title": "Why Eventual Consistency Exists",
        "key": "eventual consistency",
        "problem": "Strict consistency across the world is too slow.",
        "idea": "Eventual consistency accepts temporary divergence in exchange for availability and partition tolerance.",
    },
    {
        "title": "Why Distributed Transactions Hurt",
        "key": "distributed transaction",
        "problem": "Distributed transactions stall when one node hesitates.",
        "idea": "Two-phase commit and sagas trade strong consistency for coordination overhead and fragility.",
    },
    # Part IX — System Design
    {
        "title": "Why Caches Exist",
        "key": "cache",
        "problem": "The database is fast, but the network to reach it is slow.",
        "idea": "Caches keep hot data close to consumers, trading freshness for speed.",
    },
    {
        "title": "Why CDNs Exist",
        "key": "cdn",
        "problem": "Users on the other side of the world wait seconds for each request.",
        "idea": "CDNs place content near users, reducing latency and origin load.",
    },
    {
        "title": "Why Queues Exist",
        "key": "message queue",
        "problem": "Spikes of traffic overwhelm the service.",
        "idea": "Queues absorb bursts and let consumers process work at their own pace.",
    },
    {
        "title": "Why Sharding Exists",
        "key": "sharding",
        "problem": "One database cannot store or serve all the data.",
        "idea": "Sharding splits data by key across many nodes so each owns a subset.",
    },
    {
        "title": "Why Replication Exists",
        "key": "replication",
        "problem": "A single copy of data is a single point of failure.",
        "idea": "Replication keeps copies on multiple nodes for durability and read scaling.",
    },
    {
        "title": "Why Search Engines Exist",
        "key": "search engine",
        "problem": "Users type vague words and expect instant, ranked results.",
        "idea": "Search engines index, tokenize, and score documents to answer free-text queries.",
    },
    # Part X — Artificial Intelligence Infrastructure
    {
        "title": "Why GPUs Changed Everything",
        "key": "gpu",
        "problem": "CPUs cannot train billion-parameter models in a human lifetime.",
        "idea": "GPUs execute thousands of parallel threads, turning matrix math from a bottleneck into a throughput engine.",
    },
    {
        "title": "Why Matrix Multiplication Matters",
        "key": "matmul",
        "problem": "Neural networks are mostly multiplications of large matrices.",
        "idea": "Efficient matrix multiplication determines how large and fast a model can be.",
    },
    {
        "title": "Why Attention Exists",
        "key": "attention",
        "problem": "A word's meaning depends on every other word in the sentence.",
        "idea": "Attention computes pairwise relevance so each token can gather context from the whole sequence.",
    },
    {
        "title": "Why Transformers Scale",
        "key": "transformer",
        "problem": "Recurrent models forget and cannot train in parallel.",
        "idea": "Transformers replace recurrence with self-attention, enabling parallel training over whole sequences.",
    },
    {
        "title": "Why KV Cache Exists",
        "key": "kv cache",
        "problem": "Generating one token at a time recomputes the same keys and values.",
        "idea": "The KV cache stores past key/value tensors so autoregressive generation only computes the new token.",
    },
    {
        "title": "Why Quantization Exists",
        "key": "quantization",
        "problem": "Models are too large to fit on consumer hardware.",
        "idea": "Quantization uses fewer bits per weight with minimal accuracy loss.",
    },
    {
        "title": "Why Tensor Parallelism Exists",
        "key": "tensor parallelism",
        "problem": "One GPU cannot hold a model, but many can if the work is split.",
        "idea": "Tensor parallelism splits layers across devices so a model larger than one GPU can still run.",
    },
    {
        "title": "Why MoE Exists",
        "key": "mixture of experts",
        "problem": "Every token activates the entire model, wasting computation.",
        "idea": "Mixture of Experts routes each token to a small subset of specialists.",
    },
    {
        "title": "Why Inference Servers Exist",
        "key": "inference server",
        "problem": "Thousands of users ask for completions at the same time.",
        "idea": "Inference servers batch, schedule, and stream requests to maximize throughput and minimize latency.",
    },
]

PART_RANGES = [
    ("Part I — Information", 1, 6),
    ("Part II — Searching", 7, 12),
    ("Part III — Organization", 13, 17),
    ("Part IV — Computation", 18, 22),
    ("Part V — Operating Systems", 23, 28),
    ("Part VI — Databases", 29, 34),
    ("Part VII — Networking", 35, 39),
    ("Part VIII — Distributed Systems", 40, 45),
    ("Part IX — System Design", 46, 51),
    ("Part X — Artificial Intelligence Infrastructure", 52, 60),
]


def slugify(title: str) -> str:
    """Create a URL-safe slug from a chapter title."""
    title = title.replace("'", "")
    title = title.replace("*", "")
    return re.sub(r"[^a-z0-9]+", "-", title.lower().strip()).strip("-")


def chapter_dir(num: int) -> str:
    return f"chapter{num:02d}"


def next_title(chapters, index: int) -> str:
    if index < len(chapters) - 1:
        return chapters[index + 1]["title"]
    return "Projects"


def next_slug(chapters, index: int) -> str | None:
    if index < len(chapters) - 1:
        return f"{index + 2:02d}-{slugify(chapters[index + 1]['title'])}.md"
    return None


def generate_docs(chapters):
    docs_root = ROOT / "docs"
    docs_root.mkdir(exist_ok=True)
    for i, ch in enumerate(chapters, start=1):
        slug = f"{i:02d}-{slugify(ch['title'])}.md"
        path = docs_root / slug
        nt = next_title(chapters, i - 1)
        ns = next_slug(chapters, i - 1)
        continue_line = f"**Continue → [{nt}]({ns})**" if ns else f"**Continue → {nt}**"
        content = f"""# {ch['title']}

## The Problem

{ch['problem']}

## Thinking

Before we name anything, ask yourself:

- What would happen if the missing piece were absent?
- What is the simplest system that could show this effect?
- Can you draw the interaction before reading the answer?

## Discovery

{ch['idea']}

## Implementation

We build a minimal `{ch['key']}` model in Python.

Source: [`python/{chapter_dir(i)}/main.py`]({GITHUB_BASE}/python/{chapter_dir(i)}/main.py)

Run the implementation:

```bash
python python/{chapter_dir(i)}/main.py
```

## Simulation

The simulation runs in the browser so you can interact with it directly.

Source: [`browser/{chapter_dir(i)}/index.html`]({GITHUB_BASE}/browser/{chapter_dir(i)}/index.html)  ·  [run live](assets/browser/{chapter_dir(i)}/index.html).

## Exercises

1. Change one parameter in the simulation and predict what will happen.
2. Draw the system before and after the discovery.
3. Name one real-world system that depends on this idea and one way it can fail.

## Engineering Notes

Real systems add noise, latency, and limits. The model we built is the simplest version; real `{ch['key']}` designs trade correctness, performance, and maintainability.

---

{continue_line}
"""
        path.write_text(content, encoding="utf-8")


def generate_discoveries(chapters):
    disc_root = ROOT / "discoveries"
    disc_root.mkdir(exist_ok=True)
    for i, ch in enumerate(chapters, start=1):
        slug = f"{i:02d}-{slugify(ch['title'])}.md"
        path = disc_root / slug
        nt = next_title(chapters, i - 1)
        ns = next_slug(chapters, i - 1)
        continue_link = f"[{nt}](../docs/{ns})" if ns else nt
        content = f"""# {ch['title']} — Discovery Notes

- **Problem:** {ch['problem']}
- **Key idea:** {ch['idea']}
- **Python:** [`python/{chapter_dir(i)}/main.py`]({GITHUB_BASE}/python/{chapter_dir(i)}/main.py)
- **C++:** [`cpp/{chapter_dir(i)}/main.cpp`]({GITHUB_BASE}/cpp/{chapter_dir(i)}/main.cpp)
- **Simulation:** [`browser/{chapter_dir(i)}/index.html`]({GITHUB_BASE}/browser/{chapter_dir(i)}/index.html)
- **Continue:** {continue_link}
"""
        path.write_text(content, encoding="utf-8")


def generate_python_stubs(chapters):
    py_root = ROOT / "python"
    py_root.mkdir(exist_ok=True)
    for i, ch in enumerate(chapters, start=1):
        d = py_root / chapter_dir(i)
        d.mkdir(exist_ok=True)
        path = d / "main.py"
        content = f"""#!/usr/bin/env python3
\"\"\"{ch['title']} — minimal implementation stub.\"\"\"


def main():
    print("Chapter {i:02d}: {ch['title']}")
    # Implement the core idea from this chapter here.
    # Start with the simplest version that demonstrates the discovery.


if __name__ == "__main__":
    main()
"""
        path.write_text(content, encoding="utf-8")


def generate_cpp_stubs(chapters):
    cpp_root = ROOT / "cpp"
    cpp_root.mkdir(exist_ok=True)
    for i, ch in enumerate(chapters, start=1):
        d = cpp_root / chapter_dir(i)
        d.mkdir(exist_ok=True)
        path = d / "main.cpp"
        content = f"""// {ch['title']} — minimal implementation stub.
#include <iostream>

int main() {{
    std::cout << "Chapter {i:02d}: {ch['title']}\n";
    // Implement the core idea from this chapter here.
    return 0;
}}
"""
        path.write_text(content, encoding="utf-8")


def generate_browser_stubs(chapters):
    browser_root = ROOT / "browser"
    browser_root.mkdir(exist_ok=True)
    for i, ch in enumerate(chapters, start=1):
        d = browser_root / chapter_dir(i)
        d.mkdir(exist_ok=True)
        path = d / "index.html"
        path.write_text(browser_sims.get_simulation_html(i, ch['title'], ch['idea']), encoding="utf-8")


def generate_mkdocs_nav(chapters):
    lines = [
        "site_name: Rebuilding Computer Science From Scratch",
        "theme:",
        "  name: material",
        "plugins:",
        "  - search",
        "nav:",
        "  - Home: index.md",
        "  - Philosophy: philosophy.md",
        "  - Roadmap: roadmap.md",
    ]
    for part_name, start, end in PART_RANGES:
        lines.append(f"  - {part_name}:")
        for i in range(start, end + 1):
            ch = chapters[i - 1]
            slug = f"{i:02d}-{slugify(ch['title'])}.md"
            lines.append(f"      - {ch['title']}: {slug}")
    (ROOT / "mkdocs.yml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_roadmap(chapters):
    lines = ["# Roadmap", ""]
    for part_name, start, end in PART_RANGES:
        lines.append(f"## {part_name}")
        lines.append("")
        for i in range(start, end + 1):
            ch = chapters[i - 1]
            mark = "x" if i == 1 else " "
            slug = f"{i:02d}-{slugify(ch['title'])}.md"
            lines.append(f"- [{mark}] [{ch['title']}]({slug})")
        lines.append("")
    (ROOT / "docs" / "roadmap.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_index(chapters):
    lines = [
        "# Rebuilding Computer Science From Scratch",
        "",
        "> Learn computer science the way humanity could have invented it.",
        "",
        "Not by memorizing algorithms.",
        "",
        "Not by copying tutorials.",
        "",
        "By rebuilding every invention from first principles.",
        "",
        "Every discovery begins with a problem.",
        "",
        "Every discovery ends with working code.",
        "",
        "## Start",
        "",
        f"- Read: Discovery 01 — {chapters[0]['title']}",
        "",
        "## Roadmap",
        "",
    ]
    for part_name, start, end in PART_RANGES:
        lines.append(f"- {part_name}")
        for i in range(start, end + 1):
            ch = chapters[i - 1]
            mark = "x" if i == 1 else " "
            lines.append(f"  - [{mark}] {ch['title']}")
    lines.extend(["", "[View the full roadmap](roadmap.md)"])
    (ROOT / "docs" / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_philosophy():
    content = """# Philosophy

- Discover before defining.
- Build before abstracting.
- No black boxes.
- Every chapter ends with code.

## Immutable Rules

### Rule 1

Every discovery begins with reality.

Never start with an algorithm.

Start with a problem.

### Rule 2

The learner should suffer the problem before seeing the solution.

Never introduce Hash Maps.

Instead ask:

> Why is searching becoming slow?

### Rule 3

Every discovery introduces exactly one new idea.

### Rule 4

Implement everything once.

Arrays. Linked Lists. Hash Tables. Heaps. Trees. Schedulers. Caches. Consensus.

Everything.

### Rule 5

Every abstraction must already have a concrete implementation.

Libraries come last.

### Rule 6

Every discovery must answer:

> Why couldn't the previous solution continue?
"""
    (ROOT / "docs" / "philosophy.md").write_text(content, encoding="utf-8")


def generate_asset_links(chapters):
    """Create symlinks under docs/assets/ so MkDocs serves browser files."""
    assets_browser = ROOT / "docs" / "assets" / "browser"
    assets_browser.mkdir(parents=True, exist_ok=True)
    for i, _ch in enumerate(chapters, start=1):
        cdir = chapter_dir(i)
        browser_src = ROOT / "browser" / cdir / "index.html"
        browser_link_dir = assets_browser / cdir
        browser_link_dir.mkdir(parents=True, exist_ok=True)
        browser_link = browser_link_dir / "index.html"
        if browser_link.exists() or browser_link.is_symlink():
            browser_link.unlink()
        browser_link.symlink_to(os.path.relpath(browser_src, browser_link_dir))


def main():
    generate_docs(CHAPTER_SEEDS)
    generate_discoveries(CHAPTER_SEEDS)
    generate_python_stubs(CHAPTER_SEEDS)
    generate_cpp_stubs(CHAPTER_SEEDS)
    generate_browser_stubs(CHAPTER_SEEDS)
    generate_mkdocs_nav(CHAPTER_SEEDS)
    generate_roadmap(CHAPTER_SEEDS)
    generate_index(CHAPTER_SEEDS)
    generate_philosophy()
    generate_asset_links(CHAPTER_SEEDS)

    # Ensure top-level asset directories exist.
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets" / ".gitkeep").write_text("")
    (ROOT / "diagrams").mkdir(exist_ok=True)
    (ROOT / "diagrams" / ".gitkeep").write_text("")


if __name__ == "__main__":
    main()
