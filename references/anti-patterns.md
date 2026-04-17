# Anti-Patterns to Avoid

### One-Shot Hero Mode
Trying to solve everything in a single massive response. This is the single-turn chatbot failure mode. If the task is complex, decompose it. You'll recognize this when your response is ballooning past a screen and you're holding six sub-problems in your head simultaneously — that's when errors compound silently. The result is almost always a plausible-looking answer with subtle bugs buried in the middle third, where attention was thinnest.

### Flat Coordination
Multiple parallel efforts sharing the same context/state without hierarchy. This leads to risk-averse, incremental work. Use the planner-worker-judge pattern instead. In practice this looks like three sub-agents all reading and writing the same files with no one deciding priority or resolving conflicts — you get merge chaos and duplicated effort. The tell is when parallel workers start producing contradictory changes or when no single agent owns the final integration.

### Complexity Accumulation
Adding more coordination machinery when things aren't working. Often the fix is to simplify — cleaner isolation, clearer roles, less coupling between sub-tasks. You'll spot this when you're adding a third layer of orchestration to manage failures in the first two, or when your harness scaffolding outweighs the actual work product. If the coordination overhead exceeds the complexity of the task itself, you've gone wrong — strip it back to the simplest structure that still decomposes and verifies.

### Context Window Stuffing
Trying to hold everything in a single context. When context fills up, the right move is to summarize, restart with fresh context, and continue from the progress file. The judge restart pattern exists for this reason. The concrete symptom: you're pasting entire file contents "for reference" instead of reading the specific section you need, or you're carrying forward every prior conversation turn even though only the last decision matters. Performance degrades gradually — early instructions get quietly deprioritized as the window fills, and you won't notice until verification catches the drift.

### Invisible Assumptions
Working from assumptions the human can't see or challenge. Make everything explicit. The human's sniff-check only works if they can see what you're doing and why. A classic example: choosing a library or approach because it's "standard" without stating that choice, then building three layers on top of it. When the human finally reviews, the assumption is load-bearing and expensive to reverse. State your assumptions at the top of every plan and every worker output — if an assumption turns out wrong, catching it early is the difference between a restart and a rewrite.

### Patching Over Structural Problems
When something fundamental is wrong, patching individual symptoms creates compound errors. Restart the sub-problem cleanly. You'll recognize this when each fix introduces a new failure somewhere else, or when you're adding special-case handling for the third time in the same area. The sunk-cost instinct says "I'm almost there, one more patch." That instinct is wrong. A clean restart with the lesson learned is almost always faster than a fourth patch on a broken foundation.

### Role Collapse (The "I'll Just Do It Myself" Trap)
The main session drops from planner/judge into worker mode because it "already has the context" and it seems faster. This is the most common and most damaging anti-pattern. The context that planned the fix is the worst context to verify the fix — it carries its own assumptions into the review. In a real engineering team, the developer doesn't merge their own PR, the QA engineer didn't write the code, and the architect doesn't implement their own design. The same separation must hold for agents. **If you planned it, you don't implement it. If you implemented it, you don't verify it.**

### Self-Review
The same context that wrote code or made changes then runs verification checks on its own work. It will check for what it intended, not what happened. It will miss the same edge cases in both passes. Verification must come from a fresh context that evaluates artifacts cold, without access to the implementer's reasoning or intent. Note: a model's in-context pre-flight check before returning an artifact (re-reading its own diff, sanity-checking its output) is fine and model-provided — what Rule 3 prohibits is using the implementing context as the judge of record.

### Rubber-Stamp Compliance
Mechanically outputting protocol markers (`[TASK CLASS]`, `[CONTEXT HEALTH: OK]`) without performing the actual assessment. The marker appears but doesn't match reality — the classification doesn't fit the task complexity, or the health check says OK while the agent has been implementing directly for three tasks. Protocol markers are only useful if they reflect real decisions. The tell: the marker appears but the behavior it gates doesn't change.
