Refactor the data processing pipeline to support streaming.
===PHASE2===
Step 2's implementation has a fundamental flaw — it assumed the data is sorted, but it's not. The approach doesn't work.
