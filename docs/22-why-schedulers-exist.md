# Who Runs Next and Why It Matters

## The Problem

A laptop runs a music player, a compiler, a browser, and a backup process simultaneously. The CPU has 4 cores. All 4 programs want to run all the time. Without any coordination, each program tries to hold the CPU indefinitely — the compiler's loop never yields, the music player never gets a turn, and you hear silence while your laptop heats up compiling code.

But simply taking turns doesn't solve it either. The music player needs the CPU for 5ms every 20ms to stay smooth. The compiler can wait 200ms without anyone noticing. A backup process can wait hours. Equal time slices give each program 25% of the CPU — the music player gets its 5ms of every 20ms, fine; but the backup process also gets 25%, starving the compiler for no reason while wasting resources.

Any solution must:

- Guarantee forward progress — no process waits forever (starvation)
- Meet latency requirements for interactive tasks (music, UI)
- Maximize throughput for batch tasks (compilation, backups)
- Make the decision in microseconds — scheduling itself must be fast

## What Would You Try?

Before reading on:

- If you give every process an equal 10ms time slice, what determines how responsive the system feels to a user?
- A process that does heavy I/O (reading disk) voluntarily gives up the CPU while waiting. How does that change your model?
- What happens to a long-running process if every new process that arrives gets higher priority?

## Failed Attempts

### Attempt 1: Run Each Process to Completion

Run one process until it finishes, then the next. Simple, no overhead — no context switching mid-computation. A compiler that needs 30 seconds runs for 30 seconds, then the music player gets its turn.

The music player needs CPU every 20ms to fill its audio buffer. After 30 seconds of silence, you get a burst of audio — or more likely, the OS audio driver gives up and you hear 30 seconds of static. Any interactive task — keyboard input, mouse movement, video — becomes completely unresponsive while a batch job runs. This is cooperative multitasking as practiced on early Windows (pre-3.1). One hung program froze the entire system. Completion-order is optimal only when all tasks have equal urgency, which is never true.

### Attempt 2: Fixed Priority, Always Run Highest First

Assign each process a fixed priority. Scheduler always picks the highest-priority runnable process. Music player: priority 10. Browser: priority 7. Compiler: priority 5. Backup: priority 1.

Priorities solve urgency but create starvation. The backup process (priority 1) never runs if the browser (priority 7) is always runnable. In practice it might wait days. More subtly: a low-priority process holds a lock that a high-priority process needs. The high-priority process blocks waiting for the lock; the low-priority process never gets CPU to release it. This is **priority inversion** — and it famously brought down the Mars Pathfinder rover in 1997. The fix (priority inheritance) makes scheduling dramatically more complex.

### Attempt 3: Round-Robin with Equal Time Slices

Give each process a fixed time quantum (e.g., 10ms). Run process 1 for 10ms, then process 2, then process 3, cycling through. If a process finishes early or blocks on I/O, immediately move to the next.

This is fair (everyone gets equal time) and responsive (no process waits more than n×10ms where n is the process count). But equal time is not equal urgency. The backup process gets the same 10ms slice as the music player — resources wasted on the backup that the music player could use. The time quantum itself is a tradeoff: short quanta (1ms) make the system responsive but context-switch overhead dominates; long quanta (100ms) reduce overhead but hurt interactivity. Equal slices treat all processes as equivalent when they emphatically are not.

## The Discovery

Completion order starves interactive tasks. Fixed priority starves low-priority tasks and creates priority inversion. Round-robin wastes time on low-urgency tasks and can't express urgency at all.

The winner combines the insights: **priority** (urgency matters) + **time slicing** (no process monopolizes) + **dynamic adjustment** (actual behavior shapes priority over time).

Modern OS schedulers — Linux's Completely Fair Scheduler (CFS), for instance — assign each process a "virtual runtime": time it has actually used the CPU. The scheduler always runs the process with the *lowest* virtual runtime, which is the most "starved" process. Interactive processes (which block on I/O frequently) accumulate low virtual runtime naturally, so they get priority automatically without needing explicit priority labels. The scheduler also tracks "nice values" for user-requested priority hints. The result: interactivity emerges from fairness, not from special cases.

The key insight: **scheduling is a resource allocation policy, not a mechanism**. The mechanism (context switch, timer interrupt) is separate from the policy (who runs next). Separating them lets you change policy without touching the mechanism.

## Try It

<iframe src="../assets/browser/chapter22/index.html" width="100%" height="460" style="border:1px solid var(--md-default-fg-color--lightest);border-radius:8px;"></iframe>

[open in a new tab](../assets/browser/chapter22/index.html)

Before changing anything, predict:

- With 3 processes and a 10ms quantum, how long does a newly arrived process wait before its first turn?
- If one process is purely I/O-bound (it always blocks before its quantum expires), how does it affect CPU utilization for the others?
- What happens to total throughput as you make the time quantum very small (1ms)? Very large (1s)?

## Implementation

The full model is ~150 lines of dependency-free JavaScript — open `browser/chapter22/index.html` (and the shared helpers in `browser/common/sim.js`) to read or modify it. Everything runs in the browser; nothing to install. Look for three scheduler classes — `FIFOScheduler`, `PriorityScheduler`, and `CFSScheduler` — each implementing a `selectNext(runQueue)` method. The Gantt-chart rendering is separate so you can swap schedulers without touching the display logic.

## When It Breaks

**Priority inversion.** A low-priority thread holds a mutex. A high-priority thread tries to acquire it and blocks. A medium-priority thread, being runnable and higher than the low-priority one, keeps running, preventing the low-priority thread from releasing the mutex. The high-priority thread starves. Mars Pathfinder (1997) hit this: a high-priority bus management task was blocked by a low-priority meteorological task holding a shared mutex, with medium-priority communication tasks continuously preempting. The system reset repeatedly. Fix: priority inheritance temporarily elevates the mutex holder to the ceiling priority.

**Thundering herd.** When a resource becomes available (e.g., a new connection arrives on a listening socket), the OS wakes every sleeping process waiting for it. All race to handle it; only one wins; the rest go back to sleep. The wakeup storm wastes CPU and can crash systems under high connection rates. Linux `accept()` with `SO_REUSEPORT` and `epoll`'s `EPOLLEXCLUSIVE` flag were added specifically to fix this.

## Transfer

- **OS I/O schedulers** apply the same logic to disk requests. The "deadline" scheduler ensures requests don't starve by mixing throughput optimization (reordering requests to minimize seeks) with latency guarantees (every request must complete within a time bound).
- **Network packet scheduling** in routers uses weighted fair queuing — each flow gets a share of bandwidth proportional to its weight, preventing a single high-volume sender from starving others.
- **Real-time scheduling** (RTOS used in aircraft, medical devices) uses fixed-priority preemptive scheduling with rate-monotonic analysis to prove that all deadlines will be met. No fairness — correctness and determinism only.

Try these:

1. Implement round-robin scheduling with a time quantum. Measure average waiting time for 5 processes with burst times [2, 4, 6, 8, 10] ms, with quantum = 2ms vs quantum = 6ms.
2. Describe a scenario where a "nice" (low-priority) process should actually run before a high-priority one. What scheduling policy handles this case well?
3. Linux CFS tracks virtual runtime in nanoseconds. If two processes have virtual runtimes of 1,000,000 ns and 1,000,100 ns, which runs next? By how much would the chosen process's virtual runtime increase with a 4ms time slice?

---

**Continue → [Why Processes Exist](23-why-processes-exist.md)**
