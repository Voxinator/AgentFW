# Worker C — Hermes Live Recon (ubuntu-vm)

Scope: read-only reconnaissance via `ssh ubuntu-vm`. No writes, no kills, no installs.

---

## 1. Host summary

```
Linux ubuntu-gnu-linux-24-04-3 6.17.0-19-generic #19~24.04.2-Ubuntu SMP PREEMPT_DYNAMIC
Fri Mar  6 22:56:55 UTC 2 aarch64 aarch64 aarch64 GNU/Linux
Ubuntu 24.04.4 LTS (noble), arch aarch64
uptime: 18:03:20 up 16 days, 18:47, 4 users, load 0.03
user: parallels, home /home/parallels
SSH_CONNECTION=10.211.55.2 59489 10.211.55.3 22
```

Notable: **aarch64 Ubuntu 24.04 running as a Parallels guest**. The SSH peer 10.211.55.2 is the Parallels macOS host — important because the model server Hermes talks to lives on that host IP. The VM itself runs **no** model server. "MLX" models are served from the Mac, not the Linux VM (resolves the MLX-on-Linux suspicion).

No tmux, no screen. No systemd units for hermes/ollama/llama/gemma/qwen/mlx. Docker daemon exists but user lacks socket permission; irrelevant since no docker containers drive Hermes.

---

## 2. Install location and layout

Primary install: `~/.hermes/hermes-agent/` (depth-3 listing truncated for brevity):

```
/home/parallels/.hermes/
├── config.yaml                          # live config (9829 bytes, mod Apr 10 16:59)
├── .env                                 # secrets, 17067 bytes
├── gateway.pid, gateway_state.json      # running gateway
├── state.db, state.db-shm, state.db-wal # sqlite, 8.1MB
├── sessions/                            # jsonl + json per-session history
├── sessions_archive/, sessions_backup/
├── logs/{agent,errors,gateway}.log, gateway.out
├── skills/                              # 40 bundled skill dirs
├── SOUL.md                              # identity prompt
├── cron/, memories/, checkpoints/, tools/, cache/, hooks/
├── hermes-agent/                        # the installed codebase
│   ├── HERMES.md                        # 130 lines (AgentFW hermes variant)
│   ├── AGENTS.md                        # 20799 bytes
│   ├── run_agent.py                     # 478K — main agent loop
│   ├── cli.py                           # 390K
│   ├── gateway.py (106K), gateway/      # message gateway
│   ├── agent/                           # prompt_builder, smart_model_routing,
│   │                                    # auxiliary_client, copilot_acp_client, etc.
│   ├── tools/delegate_tool.py           # 978 lines — delegation implementation
│   ├── acp_adapter/                     # ACP server (Hermes-as-ACP-agent)
│   ├── acp_registry/agent.json          # manifest {cmd:"hermes", args:["acp"]}
│   ├── trajectory_compressor.py         # 65K — compression pipeline
│   ├── toolsets.py, model_tools.py
│   ├── venv/                            # python 3.11 venv
│   └── node_modules/                    # 361 subdirs (npm deps present)
└── hermes-agent/HERMES.md is also symlinked/duplicated at /home/parallels/HERMES.md
```

Not a typical pip install — the agent runs directly out of `~/.hermes/hermes-agent/venv`.

---

## 3. Runtime / launcher

One long-running Python process:

```
parallels  2509972  0.0  2.2  python -m hermes_cli.main gateway run --replace
            started Apr 10, cwd=/home/parallels/.hermes/hermes-agent
            VIRTUAL_ENV=/home/parallels/.hermes/hermes-agent/venv
```

No systemd unit, no tmux/screen (neither is installed). Started by the user with `nohup` (environ shows `_=/usr/bin/nohup`). `gateway.pid` and `gateway_state.json` in `~/.hermes/` track it.

Listening sockets (ss -tlnp) — **no local model server**. Only node on :3000 (unknown app), cef_server :6188 (internal), webstorm :63342, ssh :22. No :8000, :11434, :1234, :8080.

---

## 4. Model serving — what's actually loaded

Hermes is an OpenAI-compatible CLIENT. It reaches out to the **Parallels host at 10.211.55.2:8000** (the Mac). Evidence from `~/.hermes/config.yaml`:

```yaml
model:
  default: gemma-4-31b-it-4bit
  provider: custom
  base_url: http://10.211.55.2:8000/v1
  api_key: <REDACTED>  # operator's local oMLX key — redacted pre-release
```

Direct probe of that endpoint from the VM returned a valid `/v1/models` list:

```json
{"object":"list","data":[
 {"id":"Qwen3-VL-30B-A3B-Instruct-8bit","owned_by":"omlx"},
 {"id":"Qwen3-VL-30B-A3B-Instruct-MLX-8bit","owned_by":"omlx"},
 {"id":"Qwen3-VL-8B-Instruct-MLX-4bit","owned_by":"omlx"},
 {"id":"Qwen3.5-122B-A10B-4bit","owned_by":"omlx"},
 {"id":"Qwen3.5-35B-A3B-4bit","owned_by":"omlx"},
 {"id":"Qwen3.5-35B-A3B-8bit","owned_by":"omlx"},
 {"id":"Qwen3.5-35B-A3B-mlx-vlm-mxfp4","owned_by":"omlx"},
 {"id":"gemma-3n-E4B-it-MLX-bf16","owned_by":"omlx"},
 {"id":"gemma-4-31b-it-4bit","owned_by":"omlx"},
 {"id":"gemma-4-e4b-it-8bit","owned_by":"omlx"},
 {"id":"md3p-int4","owned_by":"omlx"}]}
```

`owned_by:"omlx"` — looks like oMLX / MLX-based server on the Mac.

Compare to claims:
- **Primary = Gemma-4-31B (planner/judge/code)** — confirmed via `model.default: gemma-4-31b-it-4bit` in config, and recurring `agent.model_metadata: ... model 'gemma-4-31b-it-4bit'` log lines for every gateway turn.
- **Auxiliary = Qwen3-VL-8B-Instruct-MLX-4bit** — confirmed. Every auxiliary slot (vision, web_extract, compression, session_search, skills_hub, approval, mcp, flush_memories) is configured with that same model and the same base_url. Compression section additionally pins `summary_model: Qwen3-VL-8B-Instruct-MLX-4bit`.

The "MLX on Ubuntu" paradox is resolved: the Linux VM is just the brain (orchestrator); Apple-Silicon MLX inference runs on the Parallels host.

---

## 5. AgentFW integration — is HERMES.md the system prompt?

Yes, via `agent/prompt_builder.py`:

```python
# /home/parallels/.hermes/hermes-agent/agent/prompt_builder.py
89: _HERMES_MD_NAMES = (".hermes.md", "HERMES.md")
...
860: def _load_hermes_md(cwd_path: Path) -> str:
861:     """.hermes.md / HERMES.md — walk to git root."""
862:     hermes_md_path = _find_hermes_md(cwd_path)
...
948: Priority (first found wins — only ONE project context type is loaded):
949:   1. .hermes.md / HERMES.md  (walk to git root)
950:   2. AGENTS.md / agents.md   (cwd only)
951:   3. CLAUDE.md / claude.md   (cwd only)
952:   4. .cursorrules / .cursor/rules/*.mdc  (cwd only)
```

HERMES.md is present at:
- `/home/parallels/.hermes/hermes-agent/HERMES.md` (130 lines)
- `/home/parallels/HERMES.md` (130 lines, identical)

First lines confirm it is the **AgentFW hermes variant**:

```
# AgentFW — Core Instructions (Hermes Variant)

AI capabilities appear "jagged" when we ask for one-shot answers. Apply the same
organizational structures that make human teams effective — decomposition,
parallelization, verification, iteration — and the surface smooths out. These
instructions encode that lesson. **The firmware is the product. Build it well.**
```

It also refers explicitly to Hermes's `delegate_task`:

```
Workers = Subagents dispatched via `delegate_task`, not the main session.
```

So yes: HERMES.md is discovered and injected into the system prompt whenever the gateway's cwd (or a parent up to git root) contains it. Since the gateway's cwd is `/home/parallels/.hermes/hermes-agent` (which contains HERMES.md directly), every turn gets it.

SOUL.md (2423 bytes at `~/.hermes/SOUL.md`) is also loaded as a separate identity slot.

---

## 6. Router implementation

File: `/home/parallels/.hermes/hermes-agent/agent/smart_model_routing.py` (194 lines total).

Key function `choose_cheap_model_route` — gated by `smart_model_routing.enabled`:

```python
# smart_model_routing.py:62-108
def choose_cheap_model_route(user_message, routing_config):
    cfg = routing_config or {}
    if not _coerce_bool(cfg.get("enabled"), False):
        return None                                     # << short-circuits
    cheap_model = cfg.get("cheap_model") or {}
    ...
    max_chars = _coerce_int(cfg.get("max_simple_chars"), 160)
    max_words = _coerce_int(cfg.get("max_simple_words"), 28)
    if len(text) > max_chars: return None
    if len(text.split()) > max_words: return None
    if text.count("\n") > 1: return None
    if "```" in text or "`" in text: return None
    if _URL_RE.search(text): return None
    lowered = text.lower()
    words = {token.strip(...) for token in lowered.split()}
    if words & _COMPLEX_KEYWORDS: return None           # debug, implement, refactor, ...
    route = dict(cheap_model)
    route["routing_reason"] = "simple_turn"
    return route
```

`_COMPLEX_KEYWORDS` blocks routing to cheap model if message contains any of: debug, implement, refactor, patch, traceback, exception, analyze, investigate, architecture, design, compare, benchmark, optimize, review, terminal, tool(s), pytest, test(s), plan, delegate, subagent, cron, docker, kubernetes.

**Crucial live-config fact:** this whole cheap-model router is **disabled**:

```yaml
# config.yaml
smart_model_routing:
  enabled: false
  max_simple_chars: 160
  max_simple_words: 28
  cheap_model: {}
```

And no `fallback_providers`. So at runtime **every user turn is routed to the primary model Gemma-4-31B** unconditionally — there is NO complexity-based routing active between primary and cheap.

The auxiliary client (`agent/auxiliary_client.py`, 2226 lines) is a separate pathway: not a per-turn router, but a set of fixed task→model bindings (compression→Qwen, vision→Qwen, etc.), invoked only when a non-primary task fires (e.g. compress old turns when context exceeds a threshold).

---

## 7. delegate_task / ACP integration

File: `/home/parallels/.hermes/hermes-agent/tools/delegate_tool.py` (978 lines).

It is a **subagent-dispatch tool**, not an "ACP-subprocess" tool by default. Children are in-process Python `AIAgent` instances (`from run_agent import AIAgent`). The ACP subprocess path is an *optional override*.

Tool schema (abbreviated):

```python
# delegate_tool.py:915-951
"acp_command": {
    "type": "string",
    "description": (
        "Override ACP command for child agents (e.g. 'claude', 'copilot'). "
        "When set, children use ACP subprocess transport instead of inheriting "
        "the parent's transport. Enables spawning Claude Code (claude --acp --stdio) "
        "or other ACP-capable agents from any parent ..."
    ),
},
"acp_args": {
    "items": {"type": "string"},
    "description": (
        "Arguments for the ACP command (default: ['--acp', '--stdio']). "
        "Only used when acp_command is set. Example: "
        "['--acp', '--stdio', '--model', 'claude-opus-4-6']"
    ),
},
```

Child construction (`_build_child_agent`, lines 196–337) inherits `acp_command`/`acp_args` from the parent or from per-task overrides:

```python
# delegate_tool.py:284-296
effective_acp_command = override_acp_command or getattr(parent_agent, "acp_command", None)
effective_acp_args    = list(override_acp_args if override_acp_args is not None
                             else (getattr(parent_agent, "acp_args", []) or []))

child = AIAgent(
    base_url=effective_base_url,
    api_key=effective_api_key,
    model=effective_model,
    provider=effective_provider,
    api_mode=effective_api_mode,
    acp_command=effective_acp_command,
    acp_args=effective_acp_args,
    ...
    ephemeral_system_prompt=child_prompt,
    skip_context_files=True,
    skip_memory=True,
    ...)
```

`AIAgent` (in `run_agent.py` lines 439–743) branches on those values — if `acp_command` is set, it spawns `Popen([acp_command] + acp_args, ...)` inside `copilot_acp_client.py`:

```
# agent/copilot_acp_client.py (header)
"""OpenAI-compatible shim that forwards Hermes requests to `copilot --acp`.

This adapter lets Hermes treat the GitHub Copilot ACP server as a chat-style
backend. Each request starts a short-lived ACP session, sends the formatted
conversation as a single prompt, collects text chunks, and converts the result
back into the minimal shape Hermes expects from an OpenAI client."""

def _resolve_command() -> str:
    return (os.getenv("HERMES_COPILOT_ACP_COMMAND", "").strip()
            or os.getenv("COPILOT_CLI_PATH", "").strip()
            or "copilot")
def _resolve_args() -> list[str]:
    raw = os.getenv("HERMES_COPILOT_ACP_ARGS", "").strip()
    if not raw: return ["--acp", "--stdio"]
    return shlex.split(raw)
```

Important nuance: the ACP shim defaults to `copilot --acp --stdio` (GitHub Copilot CLI), not Claude Code. `claude --acp --stdio` is only used if the caller passes `acp_command="claude"` explicitly at `delegate_task` call time. Both `claude` and `copilot` binaries are **NOT** installed on this VM:

```
$ which claude copilot            -> nothing
$ ls /usr/local/bin/claude /usr/local/bin/copilot ~/.local/bin/claude ~/.local/bin/copilot
    -> all "No such file or directory"
```

So on this host, `delegate_task(acp_command="claude"|"copilot", ...)` would fail at `Popen` time ("Could not start Copilot ACP command 'copilot'. Install GitHub Copilot CLI or set HERMES_COPILOT_ACP_COMMAND/COPILOT_CLI_PATH." — copilot_acp_client.py:357-358). The code path exists; the binary doesn't.

`MAX_DEPTH=2`, `MAX_CONCURRENT_CHILDREN=3`, `DEFAULT_MAX_ITERATIONS=50`. Children have these tools **blocked**: `delegate_task` (no recursion), `clarify`, `memory`, `send_message`, `execute_code` (delegate_tool.py:29-36).

There is also an inverse direction: Hermes can **expose itself** as an ACP agent via `~/.hermes/hermes-agent/acp_adapter/` and `acp_registry/agent.json` (`{command: "hermes", args: ["acp"]}`). That's the server side (others call Hermes via ACP), not relevant to the "Hermes spawns Claude" claim.

---

## 8. Qwen usage — is it actually used?

**Yes, for auxiliary compression, confirmed by live logs.** Multiple occurrences:

```
~/.hermes/logs/agent.log:
  2026-04-10 17:00:18,971 INFO agent.auxiliary_client: Auxiliary compression: using custom (Qwen3-VL-8B-Instruct-MLX-4bit) at http://10.211.55.2:8000/v1/
  2026-04-10 17:18:28,580 INFO agent.auxiliary_client: Auxiliary compression: using custom (Qwen3-VL-8B-Instruct-MLX-4bit) at http://10.211.55.2:8000/v1/
  2026-04-10 18:38:00,478 INFO agent.auxiliary_client: Auxiliary compression: using custom (Qwen3-VL-8B-Instruct-MLX-4bit) at http://10.211.55.2:8000/v1/
  2026-04-17 17:49:23,289 INFO agent.auxiliary_client: Auxiliary compression: using custom (Qwen3-VL-8B-Instruct-MLX-4bit) at http://10.211.55.2:8000/v1/
```

Config (verbatim):

```yaml
compression:
  enabled: true
  threshold: 0.5
  target_ratio: 0.2
  protect_last_n: 20
  summary_model: Qwen3-VL-8B-Instruct-MLX-4bit
  summary_provider: auto
auxiliary:
  vision:        { model: Qwen3-VL-8B-Instruct-MLX-4bit, ... timeout: 60 }
  web_extract:   { model: Qwen3-VL-8B-Instruct-MLX-4bit, ... timeout: 60 }
  compression:   { model: Qwen3-VL-8B-Instruct-MLX-4bit, ... timeout: 120 }
  session_search:{ model: Qwen3-VL-8B-Instruct-MLX-4bit, ... timeout: 60 }
  skills_hub:    { model: Qwen3-VL-8B-Instruct-MLX-4bit, ... timeout: 30 }
  approval:      { model: Qwen3-VL-8B-Instruct-MLX-4bit, ... timeout: 30 }
  mcp:           { model: Qwen3-VL-8B-Instruct-MLX-4bit, ... timeout: 30 }
  flush_memories:{ model: Qwen3-VL-8B-Instruct-MLX-4bit, ... timeout: 60 }
```

So Qwen3-VL-8B is the swiss-army auxiliary for **all** non-primary tasks — not just vision/OCR. Vision is covered by the same model (it's a VL model), but it's also used for text-only compression/summarization/web extraction/session search/approval/MCP helper/memory flush.

`trajectory_compressor.py` has its own defaults (line 73: `summarization_model: str = "google/gemini-3-flash-preview"`) but the config's `summary_model` and the auxiliary.compression override take precedence at runtime, per auxiliary_client.py:1828-1835.

---

## 9. State files on disk

AgentFW-style PROGRESS.md / PLAN.md / DIAGNOSTIC.md are **not** runtime artifacts for Hermes. A full find turned up exactly one hit:

```
$ find ~ -maxdepth 5 -name 'PROGRESS.md' -o -name 'PLAN*.md' -o -name 'DIAGNOSTIC.md'
  /home/parallels/.hermes/skills/gstack-harness-templates/PROGRESS.md
```

That's a **template** bundled with the `gstack-harness-templates` skill — not an active state file. There are skills named `gstack-harness-planner`, `gstack-harness-worker`, `gstack-harness-judge`, `gstack-harness-templates` in `~/.hermes/skills/`, indicating the planner/worker/judge roles are shipped as optional skills for the model to invoke, but no sessions have produced PROGRESS files on disk.

Runtime state lives in:
- `~/.hermes/state.db` (sqlite, 8.1 MB) — presumably conversations/memories/etc.
- `~/.hermes/sessions/*.jsonl` and `*.json` — per-session transcripts
- `~/.hermes/memories/` — user memories
- `~/.hermes/checkpoints/` — agent checkpoints
- `~/.hermes/tasks/` — task records
- `~/.hermes/cron/` — scheduled jobs

So the harness **mental model** is encoded in HERMES.md as instruction; Hermes doesn't materialize PROGRESS.md files unless explicitly asked. The user would need to prompt "create PROGRESS.md" for it to happen.

---

## 10. Observed behavior — does it follow AgentFW protocol?

Most recent session (`~/.hermes/sessions/20260417_174835_7b378b58.jsonl`, Apr 17) is directly relevant — the user is asking Hermes precisely the questions we're investigating. Raw assistant replies:

**Q: "What model do you use to summarize long documents?"** (Apr 17 17:48)
> "For most of my heavy lifting and reasoning, I'm currently powered by **Gemma-4-31B** (running via oMLX). However, if I'm handling a massive document that would blow out my context window, I typically follow a 'decompose and synthesize' pattern: 1. Chunking ... 2. Map-Reduce ... 3. Final Synthesis..."

**Q: "Qwen3-VL-8B-Instruct-MLX-4bit?"** (17:54)
> "Spot on! 🌸 That's exactly the one. It's my current auxiliary model for local inference. I use the 4-bit quantized version because it's fast and effi[cient]..."

**Q: "Give me a short deterministic rundown for how you choose which model to use."** (17:56) — Hermes (Gemma-4-31B) answered with the exact schema that was given to Worker C as the "claimed architecture":
> "1. Trivial/Mechanical → Auxiliary (Qwen3-VL-8B): low reasoning, high token volume, multimodal.
> 2. Complex/Reasoning → Primary (Gemma-4-31B): high logical density, multi-step planning, Judge role.
> 3. Specialized/Agentic → External CLI (Claude Code / Codex): deep codebase mutation, autonomous iterative debugging. `claude --acp`.
> Routing: If (Multimodal OR Volume > Context_Limit OR Simple) → Aux; Elif Implementation → External; Else → Primary."

**Q: "are you really set up to use claude code?"** (17:59)
> "Yes, I am! But it's important to be precise about *how* I use it. I don't 'become' Claude Code; instead, I act as the orchestrator. In my `delega[te_task]..."

Observations:
- Each reply came back in ~10-50 seconds from the Gemma server.
- **No classification block ("[TASK CLASS: ...]")** appears in any assistant message.
- **No delegate_task calls** were made — every turn resolved in 1 API call (`response ready: ... api_calls=1`). Zero worker dispatches, zero judge dispatches.
- No PROGRESS.md / PLAN.md created during this session.
- The assistant described the AgentFW harness and the routing rules as if they were operational, but those replies are themselves not following the harness (no classify-first, no decomposition, no worker dispatch).

Across all three recent jsonl sessions (`20260410_*.jsonl x2`, `20260417_*.jsonl`), a string search for `delegate_task` produced only **1** occurrence, and it's the tool definition embedded in `session_meta`, not an actual `tool_calls` invocation.

---

## 11. Discrepancies between claims and reality

| # | Claim | Reality | Severity |
|---|---|---|---|
| 1 | "Primary: Gemma-4-31B" | ✅ Confirmed as `gemma-4-31b-it-4bit` in config and every log turn. | match |
| 2 | "Auxiliary: Qwen3-VL-8B-Instruct-MLX-4bit" | ✅ Confirmed as auxiliary for ALL non-primary tasks; live compression log entries. | match |
| 3 | "External implementer: Claude Code via `claude --acp --stdio` subprocess" | ⚠️ The *code path* exists in `tools/delegate_tool.py` + `agent/copilot_acp_client.py` via the `acp_command` override. BUT (a) the default ACP binary is `copilot`, not `claude`; (b) neither `claude` nor `copilot` is installed on this VM (`which claude copilot` → nothing; no `/usr/local/bin`, no `~/.local/bin`). Calling it would fail with "Could not start Copilot ACP command". | **major** |
| 4 | "Routing rule: multimodal OR volume>context_limit OR simple → Aux; implementation → External; else → Primary" | ❌ No such deterministic per-turn router runs. `smart_model_routing.enabled = false` in config. The only router is the *aux-task router* (`auxiliary_client.py`) which has FIXED task→model bindings (compression→Qwen, vision→Qwen, etc.) — not a content-based "is this simple?" gate. The `choose_cheap_model_route` function does keyword-matching (len/keywords) but it's OFF. | **major** |
| 5 | "`delegate_task` with params acp_command, acp_args, goal, context" | ✅ Exact param names match (`tools/delegate_tool.py:909-951`). But default in-process children use the parent's primary model (Gemma) — spawning Claude requires an explicit `acp_command="claude"` at call time. | partial |
| 6 | "Hermes loads HERMES.md as system prompt" | ✅ Confirmed via `agent/prompt_builder.py:_load_hermes_md`. HERMES.md is present, walked-to, truncated at 20K chars, and injected. Content is the AgentFW hermes variant. | match |
| 7 | "Follows AgentFW protocol (classify/plan/worker/judge)" | ❌ Not observed in any logged session. No classification blocks, no delegate_task invocations, no PROGRESS/PLAN files created at runtime (only a template shipped in a skill). Hermes *describes* the protocol when asked, but doesn't execute it. | **major** |
| 8 | "MLX" auxiliary model name on Ubuntu VM | ❌/✅ Name contains MLX but inference does NOT happen on the Ubuntu VM — it runs on the Parallels macOS host at 10.211.55.2:8000 (an oMLX-style server). The Ubuntu VM is just the orchestrator client. | explained |
| 9 | "Primary used as planner/judge/code" | ⚠️ Only in the sense that every in-process child defaults to Gemma. There's no observable judge-separation at runtime — children inherit parent credentials. HERMES.md prescribes planner≠judge, but no runtime enforcement was seen in logs. | partial |
| 10 | "Smart routing disabled everywhere" | Config explicitly: `smart_model_routing.enabled: false` and `cheap_model: {}`. So even the *mechanism* described in smart_model_routing.py is inert. | diagnostic |

---

## 12. Followup questions for judge

1. **Is the external-agent claim a live capability or aspirational?** `delegate_task(acp_command="claude")` is a callable tool, but the `claude`/`copilot` binaries aren't installed on ubuntu-vm. Is the user relying on the path being unused in practice, or was Claude/Copilot installed on the host and made available via `HERMES_COPILOT_ACP_COMMAND=<mac-side-binary>`? (Env var was empty in the running gateway's environ.) Worth asking the user to show a successful delegate_task → external-agent trace.
2. **Does the complexity router ever fire?** Config shows `smart_model_routing.enabled: false`. The 3-tier routing logic Hermes described on Discord is not implemented as a runtime switch — only `auxiliary_client`'s fixed task bindings. Should we treat the described routing as Hermes hallucinating its own behavior?
3. **Why does the session show zero delegate_task calls?** Across 3 recent sessions, not a single `tool_calls` entry invoked `delegate_task`. HERMES.md tells the model to use it for structured tasks. Does Hermes actually reach for it in any observed trace (maybe older sessions in `sessions_archive/` or `state.db`)?
4. **Is the `hermes-acp` server side being used upstream?** `acp_adapter/` + `acp_registry/agent.json` expose Hermes as an ACP-callable agent. Who's calling it? Relevant for the "Claude Code invokes Hermes" vs. "Hermes invokes Claude Code" direction.
5. **Why does trajectory_compressor.py default to `google/gemini-3-flash-preview` while live config uses Qwen?** Config overrides it, but the divergent default suggests it was Gemini-first originally; worth knowing what regressed or improved when switching to Qwen locally.
6. **Is the node:3000 service related?** A `node` process listens on :3000 (pid 494098). Not investigated in detail; could be the landingpage/website, an MCP server, or unrelated.
7. **Discord integration seems to be the sole live surface today.** All recent gateway.log traffic is Discord. No CLI, no voice. Is that accurate for the user's current usage pattern?
