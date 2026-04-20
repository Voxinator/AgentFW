# IMPL-4 — SOUL/USER/MEMORY Restructure Proposal

**Mode:** READ-ONLY analysis. No modifications performed.
**Date:** 2026-04-17
**Goal:** Find a way to give `HERMES.md` more prompt prominence WITHOUT discarding the user's customization to `SOUL.md`, `USER.md`, or `MEMORY.md`.

---

## 1. File Inventory (ubuntu-vm)

### `SOUL.md`
- **Path:** `/home/parallels/.hermes/SOUL.md`
- **Size:** 2,423 bytes
- **Lines:** 51
- **Mtime:** 2026-04-10 16:20:42 -0500 (a week old)
- **Summary:** Heavily customized identity file. Teaches the model that it is "Hermes" (Brian Taylor's personal local agent), that it is `kawaii`-presetted but anchored to competence, that its primary tool is `terminal`, that it should be skills-first, that it must use `curl -u` (not base64 headers) for basic auth, and that it has standing authority to push back on Brian. Also documents the parser-based tool-call format and memory semantics (capacity-limited, deferred reload). It is BOTH a persona document AND an operational manual.

### `USER.md`
- **Path:** `/home/parallels/.hermes/memories/USER.md` (loaded via `_memory_store.format_for_system_prompt("user")`)
- **Size:** 3,903 bytes (cap was raised 1,375 → 4,000 in April 2026 — sitting near cap)
- **Lines:** 10 (each line is a `§`-separated long record)
- **Mtime:** 2026-04-02 20:57:09 -0500
- **Summary:** Brian's profile facts. Includes (a) Gmail/bot account identifiers, (b) Chief of Staff Dashboard project context, (c) a very dense ABC Supply work-context dump (org chart, projects, priorities, vendors, OKRs, ~30 named people), (d) AI/income goal, (e) personal/household/maker/music/family profile, (f) a single household-task record (Wednesday garbage reminder).

### `MEMORY.md`
- **Path:** `/home/parallels/.hermes/memories/MEMORY.md` (loaded via `_memory_store.format_for_system_prompt("memory")`)
- **Size:** 2,243 bytes (cap raised 2,200 → 4,000 in April 2026 — well under cap)
- **Lines:** 8 (`§`-separated)
- **Mtime:** 2026-04-07 19:18:19 -0500
- **Summary:** Operational memory. Includes (a) a "CRITICAL ERROR HANDLING DIRECTIVE" about checking `success:true/false` on tool responses (this is really a behavior rule, not a memory), (b) April 2026 config-fix summary (memory caps raised, model swap to Qwen3-VL-8B, session_search timeout 30→60s, memory-chunking skill creation), (c) Dashboard project location moved to `/media/psf/Projects/chief-of-staff-dashboard`, (d) Dashboard tech-stack snapshot, (e) MemPalace install summary (557 memories, ChromaDB, search command).

### `HERMES.md` (the file we want to give more attention)
- **Path:** `/home/parallels/.hermes/hermes-agent/HERMES.md`
- **Size:** 12,060 bytes (5x larger than SOUL.md, 3x larger than USER.md)
- **Lines:** 210
- **Mtime:** 2026-04-18 12:12:35 -0500 (newest of the four — actively iterated)
- **Summary:** AgentFW core (Variant D — Hard Contract + Dispatch Scaffolding). Encodes: the `[TASK CLASS:]` first-line contract, classification criteria, planner-worker-judge architecture, the `delegate_worker` tool-call format, and the permission protocol. This is the harness specification. It IS the dispatch rule the user wants the model to obey.

---

## 2. Customization-Signal Analysis

### `SOUL.md` — what is sacred vs. generic

| Section | Signal | Sacred? | Notes |
|---|---|---|---|
| "You are Brian Taylor's personal Hermes agent" | Identity affirmation | **Yes** | Names Brian, ABC Supply, Discord. Bespoke. |
| "You run fully local — inference on oMLX, orchestration on Ubuntu VM, no cloud LLM fallback" | Operational truth | **Yes** | Model-architecture grounding; not generic. |
| "You are skills-first … propose a new skill or a patch when you solve something novel" | Operational preference | Templatable | Generic across Hermes-style installs but reflects Brian's preferred working style. |
| `terminal` + `curl -u "$EMAIL:$PASS"` (no base64 headers) | Operational rule | **Yes** | Bespoke fix for a known failure mode in this VM. |
| "Make one tool call at a time; you perform better sequentially than in parallel" | Operational rule | **Yes** | Empirical tuning for this local model. |
| "fallback parser in `run_agent.py` … Trust the loop" | Model-aware reassurance | **Yes** | Defends against second-guessing on raw-text tool calls. Very specific. |
| MEMORY paragraph (capacity, deferred reload, dashboard-decisions.md, mempalace) | Operational truth + boundary rule | **Yes** | The "don't edit dashboard-decisions.md" rule is a hard constraint. |
| `kawaii`-presetted + warm/playful + "match his register" | Persona / voice | **Yes** | Pure user customization. |
| "Push back when he's about to break something … standing authority" | Personality + permission | **Yes** | Bespoke teammate framing; the user is on record wanting this. |

**Verdict:** Almost everything in SOUL.md is bespoke. Persona language is somewhat tightenable (~10–15% reduction possible) but the operational rules are not — they're carrying real load.

### `USER.md` — what is sacred vs. trimmable

| Block | Sacred? | Notes |
|---|---|---|
| Personal Gmail / bot account identifiers | Yes | Identity. |
| Chief of Staff Dashboard summary | Mostly | Some duplication with the second Dashboard line and with MEMORY.md. |
| ABC Supply work dump (org chart + 30 names + projects + vendors) | Sacred but dense | Mostly references; the model needs the names but not necessarily ALL of them every prompt. Candidates for trimming: vendor list, full ProdOps roster, `2026 value streams` rolodex. |
| AI/income goal | Yes | User's stated motivation. |
| Personal/household/maker/music/family profile | Yes | Bespoke biographical context. Long, but the user explicitly invested in it. |
| Wednesday garbage reminder | **No — trimmable** | This is operational state, not a profile fact; should live in a job/scheduler, not USER.md. |

**Verdict:** USER.md sits near its cap. Real reductions are possible if we (a) move the garbage-reminder record out, (b) collapse the duplicated Dashboard mention, (c) move the project-roster (~20 names that are referenced rarely) to a `mempalace` lookup. Estimated reduction: 25–35% (~1.0–1.4 KB).

### `MEMORY.md` — what is sacred vs. trimmable

| Block | Sacred? | Notes |
|---|---|---|
| "CRITICAL ERROR HANDLING DIRECTIVE" | Sacred — but **misfiled** | This is a behavior rule, not a memory. Belongs in SOUL.md or HERMES.md, not in the rotating memory store. |
| April 2026 config-fix log | Trimmable | One-time event; could be archived once the new config is stable. |
| Dashboard location move | Trimmable / consolidatable | Duplicates the Dashboard tech-stack line below it. |
| Dashboard tech stack | Sacred | Active project. |
| MemPalace install summary | Sacred | The model needs to know `mempalace-search.sh` exists. |

**Verdict:** ~30% reduction possible by archiving the April-2026 config log and consolidating the two Dashboard lines. The "CRITICAL ERROR HANDLING DIRECTIVE" should be relocated to a more durable slot (it's currently fragile — it rides in MEMORY.md and could be evicted by the next memory cycle).

---

## 3. Attention-Geometry Recap

Confirmed via `run_agent.py:_build_system_prompt` (lines 2582–2740). The actual slot order is:

| Slot | Source | Approx size |
|---|---|---|
| 1 | `SOUL.md` (identity) | 2.4 KB |
| 2 | Tool guidance (MEMORY + SESSION_SEARCH + SKILLS) | ~2 KB |
| 3 | `nous_subscription_prompt` (if any) | varies |
| 4 | `TOOL_USE_ENFORCEMENT_GUIDANCE` + `GOOGLE_MODEL_OPERATIONAL_GUIDANCE` (Gemma branch) | ~1–2 KB |
| 5 | `system_message` (gateway) | varies |
| 6 | `MEMORY.md` block | 2.2 KB |
| 7 | `USER.md` block | 3.9 KB |
| 8 | External memory provider (mempalace block) | varies |
| 9 | **Skills index** (`build_skills_system_prompt`) | **~11.8 KB** |
| 10 | **`HERMES.md`** (context_files_prompt, walked from cwd) | **~12 KB** |
| 11 | Timestamp / Session ID / Model | small |
| 12 | `PLATFORM_HINTS[platform]` (CLI markdown hint) | small |

So worker α was correct: HERMES.md sits at **slot 10 of 12**, behind the 11.8 KB skills index. The recency zone (last ~200 bytes) goes to the platform hint, not HERMES.md. The sink-token zone (very start) is owned by SOUL.md.

For Gemma-class models to attend reliably to HERMES.md's first-line contract and the `delegate_worker` dispatch syntax, HERMES.md needs to be in the sink zone (start), the recency zone (very end), or significantly weighted by isolation (i.e., not buried directly behind 11.8 KB of low-attention skills enumeration).

---

## 4. Three Restructure Options

### Option A — Reorder prompt-builder slots only (no content changes)

**What changes**
- Edit `agent/run_agent.py:_build_system_prompt` to either:
  - **A1 (early):** Append `context_files_prompt` (HERMES.md) **immediately after** the SOUL.md identity block, ahead of memory/skills.
  - **A2 (late):** Append `context_files_prompt` (HERMES.md) **after** the `PLATFORM_HINTS` line, making it the absolute last block in the prompt.
- Optionally drop or shrink the `PLATFORM_HINTS` CLI markdown hint, freeing the recency zone.

**Cost**
- One small file edit (~10 lines moved). Reversible by reverting that one diff.
- Zero content loss in SOUL/USER/MEMORY.
- No churn for the user — they don't have to look at their files.

**Risk to user customization**
- **None.** All customized files are preserved bit-for-bit.

**Expected attention-geometry improvement**
- **A1 (early):** HERMES.md gets sink-zone proximity (slot 2 instead of slot 10). Strong improvement for first-token attention on the `[TASK CLASS:]` contract. Skills index stays where it is and continues to dilute middle-zone attention, but middle-zone is now uncontested for HERMES.md because HERMES.md is no longer there.
- **A2 (late):** HERMES.md gets the recency zone outright. Strong improvement for the last-instruction-wins effect that small-context models exhibit.
- **Both** dramatically reduce the "buried behind 11.8 KB of skills" problem.

**Reversibility:** Excellent — single-file revert.

**Recommended sub-variant:** A2 (late). The classification gate is the LAST thing the model should see before generating its first token of reply. Recency-zone placement is the cleanest win.

---

### Option B — Compress SOUL/USER/MEMORY (preserve semantics, cut bytes)

**What changes**
- **SOUL.md:** ~10–15% trim. Tighten the persona paragraphs without removing rules. Keep all bespoke operational guidance.
- **USER.md:** 25–35% trim. Move the Wednesday garbage reminder out (to a scheduler/job). Collapse the duplicate Dashboard line. Move the rarely-referenced ProdOps/vendor rolodex to `mempalace` (still searchable but not in every prompt).
- **MEMORY.md:** ~30% trim. Archive the April-2026 config-fix log. Collapse the two Dashboard lines. **Relocate the "CRITICAL ERROR HANDLING DIRECTIVE" to SOUL.md or HERMES.md** — it's a rule, not a memory.

**Combined byte savings:** ~2.5–3.0 KB out of the 8.6 KB SOUL+USER+MEMORY total — roughly a 30% reduction.

**Cost**
- Requires the user to review every cut. They flagged these as "highly customized" — that means a 1:1 review pass.
- Touches three of the user's most-personal files. High blast radius if a sacred line is trimmed by mistake.
- Mempalace migration of the rolodex needs a one-time mining pass.

**Risk to user customization**
- **Medium-high.** Even with careful preservation, every cut is a judgment call. If a worker (not the user) is the one cutting, there will be regret.

**Expected attention-geometry improvement**
- **Modest, alone.** The skills index (~11.8 KB) is the bigger middle-zone offender, and we are not touching it here. Trimming SOUL/USER/MEMORY by 3 KB only marginally rebalances the prompt. HERMES.md still sits at slot 10.
- **Strong, when combined with Option A.** A2 + B together produces a leaner prompt AND puts the harness rules at the recency edge.

**Reversibility:** Medium — file revert is possible if originals are kept in `~/.hermes/upgrade/v0.8/backups/` (which they appear to be, based on the find output). But once a memory cycle runs, MEMORY.md may have new content, and reverting reverses that too.

---

### Option C — Move SOUL.md content into a "system character" appendix at the end of HERMES.md, drop SOUL.md from its own slot

**What changes**
- Append a `# Character & Operating Stance` section to `HERMES.md` containing the SOUL.md persona content (the `kawaii`/`be a teammate`/`push back` paragraphs and the bespoke `terminal` + `curl -u` operational rules).
- In `prompt_builder.py:load_soul_md()`, return `None` (or set `skip_context_files=False` and use `skip_soul=True` semantics already supported at lines 956–957) so SOUL.md is no longer separately injected at slot 1.
- HERMES.md effectively becomes the combined operating manual + persona, occupying slot 10 (and, with Option A2, the recency zone).

**Cost**
- Restructures the conceptual model: "SOUL = persona, HERMES = harness" collapses into "HERMES = both."
- Requires careful merge; risk of duplication if both files contain similar guidance.
- The `prompt_builder.py` plumbing for "SOUL is identity" already exists (the `skip_soul` machinery and the `load_soul_md()` function imply it's been an explicit design choice). Removing it crosses an explicit line.

**Risk to user customization**
- **Low IF preserved verbatim in the appendix.** No content is lost; it is relocated.
- **Medium for the user's mental model.** The user has been treating SOUL.md and HERMES.md as separate concepts. Merging them removes a conceptual handle.
- The first-slot identity will fall back to `DEFAULT_AGENT_IDENTITY` (a hardcoded generic identity in `default_soul.py`). Brian's identity is no longer the sink-token block — it is in the HERMES.md slot. For Gemma this is actually a small WIN (closer to the recency end), but the model loses persona priming early.

**Expected attention-geometry improvement**
- **Strong if combined with Option A2.** HERMES.md (now ~14 KB with persona appended) sits in the recency zone. Both the harness rules and the persona get the last-instruction effect.
- **Mediocre alone.** Without the slot reorder, HERMES.md is still at slot 10, just bigger.

**Reversibility:** Medium. Restoring SOUL.md as a separate slot requires reverting the `prompt_builder.py` change AND splitting the appendix back out. Doable but multi-step.

---

## 5. Recommendation

**Adopt Option A2, then Option B as a follow-up. Defer Option C.**

### Justification

| Dimension | A2 alone | A2 + B | C |
|---|---|---|---|
| Effort to implement | ~10 lines in one file | A2 + multi-file user review | A2 + content merge + plumbing change |
| Risk to user's customization | **None** | Medium | Low (content) / medium (mental model) |
| Attention-geometry improvement | **Strong** (recency zone for HERMES.md) | Strong + leaner prompt | Strong + leaner prompt |
| Reversibility | **Excellent** | Good | Medium |
| Time-to-evidence | One reload | After review pass | After merge + reload |

**A2 is a strict Pareto win:** it costs nothing to the user's customization, can be done in one diff, and addresses the actual root cause (HERMES.md is not in the recency zone). The user can validate the effect within one session and revert in seconds if it underperforms.

**B is a worthwhile follow-up** once A2 has shown empirical lift. It is independent of A2, gets value of its own, but should not be done first because it requires user time that A2 does not, and because the cleaner prompt size matters more once HERMES.md is already attention-favored.

**C is preserved as a fallback** if A2 alone does not produce sufficient improvement. The user's signal that SOUL.md and HERMES.md are distinct concepts is worth preserving until proven otherwise.

### Bonus micro-fix
Independent of A/B/C: **drop or shrink `PLATFORM_HINTS[platform]`** (the CLI markdown hint at slot 12). It's currently the very last block in the prompt and the recency zone is wasted on it. If A2 is adopted, this hint moves immediately before HERMES.md and is fine; if A2 is not adopted, simply removing the hint frees the recency zone for HERMES.md to occupy naturally (since HERMES.md is already slot 10 and the hint is one of only two blocks behind it).

---

## 6. Questions for the User Before Implementing

These are decisions the user must make — not the worker.

1. **SOUL.md sacred lines.** Confirm that the persona paragraphs (`kawaii`-presetted, "push back when he's about to break something", "match his register") are content the user considers core, not legacy. If yes, Option B's SOUL.md trim is capped at ~10–15% (tightening prose only, no rule changes).

2. **SOUL/HERMES conceptual separation.** Does the user want SOUL.md and HERMES.md to remain distinct files? If yes → Option C is off the table. If the user is open to merging → C becomes viable as a fallback.

3. **USER.md project rolodex.** Is the ABC Supply org chart (Mike Mardis, Will Hyde, Cole Cummings, etc., ~30 named people) something Hermes needs in every system prompt, or is it acceptable to migrate the rarely-referenced names to `mempalace` and keep only the user's direct reports in USER.md? This is the single biggest USER.md trim opportunity (~1.0 KB).

4. **USER.md household-task slot.** The Wednesday garbage reminder is operational state. May the worker move it to a scheduled job (or to `dashboard-decisions.md`) and remove it from USER.md?

5. **MEMORY.md "CRITICAL ERROR HANDLING DIRECTIVE".** This is a behavior rule, not a memory. May the worker relocate it to SOUL.md (so it is not at risk of being evicted by the next memory cycle)?

6. **April 2026 config-fix log in MEMORY.md.** Now that the new config is presumably stable, may the worker archive this entry?

7. **`PLATFORM_HINTS` CLI markdown hint.** Is the CLI markdown formatting hint at slot 12 load-bearing for any current Hermes use case? If no, removing or shrinking it is the cheapest single win.

8. **A2 vs A1 placement preference.** A2 places HERMES.md at the recency zone (last block). A1 places it immediately after SOUL.md (sink zone). Both are improvements over status quo; the user may have a preference based on which behavior they care about most: A2 favors first-token classification compliance; A1 favors persona-and-harness coherence early in the prompt.

---

## Appendix: Confirmed assembly order in `run_agent.py:_build_system_prompt`

Source: `/home/parallels/.hermes/hermes-agent/run_agent.py` lines 2582–2740. Verbatim slot list:

```
1. SOUL.md (or DEFAULT_AGENT_IDENTITY fallback)
2. tool_guidance: MEMORY_GUIDANCE + SESSION_SEARCH_GUIDANCE + SKILLS_GUIDANCE
3. nous_subscription_prompt (if subscribed tools present)
4. TOOL_USE_ENFORCEMENT_GUIDANCE + GOOGLE_MODEL_OPERATIONAL_GUIDANCE (for gemma/gemini)
5. system_message (gateway-supplied, optional)
6. MEMORY.md (memory_store memory block)
7. USER.md (memory_store user block)
8. _memory_manager.build_system_prompt() — external mempalace block
9. build_skills_system_prompt() — the ~11.8 KB skills index
10. build_context_files_prompt() — HERMES.md walked from TERMINAL_CWD
11. timestamp / Session ID / Model / Provider line
12. PLATFORM_HINTS[platform] — final CLI/markdown hint
```

The minimal, no-content-loss change to put HERMES.md in the recency zone is to move the `prompt_parts.append(context_files_prompt)` block (currently after the skills_prompt append) to AFTER the `prompt_parts.append(PLATFORM_HINTS[platform_key])` block. That is Option A2.
