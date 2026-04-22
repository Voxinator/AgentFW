#!/usr/bin/env bash
# probe-variantH-stage.sh — Stage/unstage the r7.6-P1A Gemma-MoE chat-template
# correctness fixes on top of Variants G / F / D. Unified implementation of:
#   - inv-3 F3A' : Gemma parser prefix-tolerant fallback (relaxed detection
#     gate at run_agent.py:~8633 + new PIPE_PATTERN_PREFIXLESS regex in
#     environments/tool_call_parsers/gemma_parser.py).
#   - inv-2 G1   : Channel-marker content normalizer + empty-synthesis
#     trailer in run_agent.py's empty-follow-up fallback at ~8908-8940.
#
# USAGE:
#   ./probe-variantH-stage.sh stage      # apply both patches (backup .probe-r7.6-orig)
#   ./probe-variantH-stage.sh unstage    # restore .probe-r7.6-orig backups
#   ./probe-variantH-stage.sh status     # show md5 + marker counts
#
# SAFETY:
#   * Idempotent (checks for unique markers before insert).
#   * Backups use `.probe-r7.6-orig` suffix — LAYERS on top of existing
#     .probe-r7.5-orig, .probe-r7.4-orig, .probe-d-orig. Does not overwrite.
#   * Layers on variantG (r7.5-A1) and variantF (r7.4 β-fuse) — stage those
#     separately first via probe-variantG-stage.sh / probe-variantF-stage.sh.
#     variantH stages INDEPENDENTLY on whatever base run_agent.py currently
#     contains; the markers don't clash with r7.5 or r7.4 markers. The stacking
#     rule is operational (you probably want G+F underneath) rather than a
#     hard dependency of H.
#   * Aborts on mid-stage failure; requires manual recovery (no auto-rollback).
#
# CHANGE 1 — inv-3 F3A' Gemma parser prefix-tolerant fallback:
#   (a) run_agent.py detection gate (~L8633): accept closers / prefix-less
#       starts in addition to the current opening-sentinel-only trigger.
#   (b) environments/tool_call_parsers/gemma_parser.py (~L26-30 + parse()):
#       add PIPE_PATTERN_PREFIXLESS; try it after primary PIPE_PATTERN yields
#       no matches. Also relax has_pipe detection so prefix-less content
#       reaches the parse-regex loop.
#
# CHANGE 2 — inv-2 G1 channel-marker content normalizer + synthesis trailer:
#   In run_agent.py's empty-follow-up fallback block (~L8908-8940), when the
#   final assistant message is content-empty AND the penultimate (or any
#   preceding) assistant's content is channel-marker-only, REPLACE the
#   back-patch-and-break path with: leave the original messages alone, set
#   final_response to the diagnostic string
#   "[child session exited with no synthesis — content was channel-marker
#   pollution only]", and break. This makes the empty-synthesis state
#   structurally recorded rather than masked by "Calling the X tool..." back-
#   patches.
#
# DISCOVERY NOTES:
#   - gemma_parser.py location: environments/tool_call_parsers/gemma_parser.py
#     (confirmed via find; 137 lines total).
#   - run_agent.py total: 9461 lines. Detection gate at line 8633 ("<|tool_call>"
#     in _raw); empty-follow-up fallback at 8908+.

set -euo pipefail

REMOTE_HOST="ubuntu-vm"
REMOTE_RUNAGENT="~/.hermes/hermes-agent/run_agent.py"
REMOTE_GEMMA_PARSER="~/.hermes/hermes-agent/environments/tool_call_parsers/gemma_parser.py"
BAK_SUFFIX=".probe-r7.6-orig"

die() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "[probe-variantH-stage] $*"; }

ssh_run() { ssh "$REMOTE_HOST" "$@"; }

md5_remote() { ssh_run "md5sum $1 2>/dev/null | awk '{print \$1}'" 2>/dev/null || true; }

cmd_stage() {
  log "Staging Variant H (r7.6-P1A Gemma-MoE chat-template correctness)..."

  ssh_run "bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail
cd ~/.hermes/hermes-agent

# ------------------------------------------------------------------
# CHANGE 1(a) + CHANGE 2 — patches on run_agent.py
# ------------------------------------------------------------------
if grep -q '_r76_channel_marker_only' run_agent.py; then
  echo "  run_agent.py: already patched (idempotent no-op)"
else
  [[ -f run_agent.py.probe-r7.6-orig ]] || cp run_agent.py run_agent.py.probe-r7.6-orig

python3 - <<'PYEOF'
import io, sys, re

path = "run_agent.py"
with open(path, "r") as f:
    src = f.read()

# ---- CHANGE 1(a): detection gate relaxation at ~L8633 -----------
# Current:
#     if "<|tool_call>" in _raw or "[Calling tool:" in _raw:
#         _parsers.append("gemma")
# New: additionally trigger on the bare <tool_call|> closer OR a bare
# call:\w+{ prefix-less form. Both are Gemma Format 1 with the opening
# sentinel stripped by the oMLX chat-template layer (inv-3 §1.3).
gate_old = (
    '                    if "<|tool_call>" in _raw or "[Calling tool:" in _raw:\n'
    '                        _parsers.append("gemma")'
)
gate_new = (
    '                    # r7.6-P1A inv-3 F3A\': accept half-sentinel /\n'
    '                    # prefix-less Gemma Format 1 in addition to the full\n'
    '                    # sentinel pair. Gemma 4 26B MoE on oMLX emits the\n'
    '                    # pattern "call:fn{...}<tool_call|>" with the opening\n'
    '                    # "<|tool_call>" stripped; the parser\'s prefix-less\n'
    '                    # fallback recovers these.\n'
    '                    if ("<|tool_call>" in _raw\n'
    '                            or "[Calling tool:" in _raw\n'
    '                            or "<tool_call|>" in _raw\n'
    '                            or re.search(r"(?m)^call:\\w+\\{", _raw) is not None):\n'
    '                        _parsers.append("gemma")'
)
if src.count(gate_old) != 1:
    print(f"ERROR: detection gate anchor not unique (count={src.count(gate_old)})")
    sys.exit(1)
src = src.replace(gate_old, gate_new, 1)

# The detection gate now uses `re.search(...)` but `re` is already imported
# at the top of run_agent.py (confirmed on this build). If a future rebase
# moves imports, the sanity-check below will catch a NameError at runtime.

# ---- CHANGE 2: channel-marker normalizer + empty-synthesis trailer ----
# Current structure at ~L8908-8936:
#     final_response = assistant_message.content or ""
#     if not self._has_content_after_think_block(final_response):
#         fallback = getattr(self, '_last_content_with_tools', None)
#         if fallback:
#             ...
#             for i in range(len(messages) - 1, -1, -1):
#                 msg = messages[i]
#                 if msg.get("role") == "assistant" and msg.get("tool_calls"):
#                     tool_names = [...]
#                     msg["content"] = f"Calling the {', '.join(tool_names)} tool..."
#                     break
#             final_response = self._strip_think_blocks(fallback).strip()
#             self._response_was_previewed = True
#             break
#
# New behavior: insert a channel-marker-pollution detector at the top of the
# `if fallback:` block. When the penultimate tool-calling assistant's content
# (which the fallback would otherwise back-patch) is channel-marker-only or
# when any of the assistant chain has channel-marker content, skip the back-
# patch and set final_response to the diagnostic trailer. This is surgical:
# only affects sessions where the model produced exclusively harmony-template
# leakage as visible content — normal sessions hit the unchanged back-patch
# path.
#
# Implementation: add two module-level helper functions (via a helper installed
# onto the class). For minimal blast radius we stuff them into module-level
# constants+function at the top and reference from the patched block.

helper_marker = "_r76_channel_marker_only"
helpers_block = (
    '\n# --- r7.6-P1A inv-2 G1 channel-marker helpers ----------------------\n'
    '# Detect harmony-format channel-marker leakage in assistant content. When\n'
    '# the Gemma 4 26B MoE on oMLX produces exclusively "<channel|>" /\n'
    '# "thought\\n<channel|>" / "<|channel|>" variants as visible content, the\n'
    '# empty-follow-up fallback must not back-patch the penultimate turn with\n'
    '# "Calling the X tool..." — that masks the empty-synthesis state. This\n'
    '# helper tells the fallback path to emit a diagnostic trailer instead.\n'
    'import re as _re_r76\n'
    '_R76_CHANNEL_MARKER_ONLY_RE = _re_r76.compile(\n'
    '    r"^\\s*(?:"\n'
    '    r"(?:<\\|?channel\\|?>\\s*)"\n'
    '    r"|(?:thought\\s*<\\|?channel\\|?>\\s*)"\n'
    '    r"|(?:<\\|?channel\\|?>\\s*thought\\s*<\\|?channel\\|?>\\s*)"\n'
    '    r")+\\s*$",\n'
    '    _re_r76.IGNORECASE | _re_r76.DOTALL,\n'
    ')\n'
    'def _r76_channel_marker_only(s):\n'
    '    """True iff s is empty or pure channel-marker leakage."""\n'
    '    if s is None:\n'
    '        return True\n'
    '    if not isinstance(s, str):\n'
    '        s = str(s)\n'
    '    if s.strip() == "":\n'
    '        return True\n'
    '    return bool(_R76_CHANNEL_MARKER_ONLY_RE.match(s))\n'
    '\n'
    '_R76_EMPTY_SYNTHESIS_TRAILER = (\n'
    '    "[child session exited with no synthesis — content was channel-marker '
    'pollution only]"\n'
    ')\n'
    '# --- end r7.6-P1A inv-2 G1 helpers ---------------------------------\n'
)

# Insert the helpers block immediately AFTER the first import block. We anchor
# on the first `class AIAgent` definition (most robust anchor in this file).
class_anchor = 'class AIAgent'
if class_anchor not in src:
    print("ERROR: could not locate 'class AIAgent' anchor for helper insertion")
    sys.exit(1)
if src.count(helper_marker) != 0:
    print("ERROR: helper marker already present before insert — idempotency check failed")
    sys.exit(1)
src = src.replace(class_anchor, helpers_block + '\n' + class_anchor, 1)

# Now patch the fallback block. We target the exact back-patch sequence. The
# current code is:
#     fallback = getattr(self, '_last_content_with_tools', None)
#     if fallback:
#         logger.debug("Empty follow-up after tool calls — using prior turn content as final response")
#         self._last_content_with_tools = None
#         self._empty_content_retries = 0
#         for i in range(len(messages) - 1, -1, -1):
#             msg = messages[i]
#             if msg.get("role") == "assistant" and msg.get("tool_calls"):
#                 tool_names = []
#                 for tc in msg["tool_calls"]:
#                     if not tc or not isinstance(tc, dict): continue
#                     fn = tc.get("function", {})
#                     tool_names.append(fn.get("name", "unknown"))
#                 msg["content"] = f"Calling the {', '.join(tool_names)} tool{'s' if len(tool_names) > 1 else ''}..."
#                 break
#         final_response = self._strip_think_blocks(fallback).strip()
#
# We replace the block with a channel-marker-gated version that routes to the
# trailer path when pollution is detected. Anchor on a unique multi-line
# substring of the original.

fallback_old = (
    "                        fallback = getattr(self, '_last_content_with_tools', None)\n"
    "                        if fallback:\n"
    "                            logger.debug(\"Empty follow-up after tool calls — using prior turn content as final response\")\n"
    "                            self._last_content_with_tools = None\n"
    "                            self._empty_content_retries = 0\n"
    "                            for i in range(len(messages) - 1, -1, -1):\n"
    "                                msg = messages[i]\n"
    "                                if msg.get(\"role\") == \"assistant\" and msg.get(\"tool_calls\"):\n"
    "                                    tool_names = []\n"
    "                                    for tc in msg[\"tool_calls\"]:\n"
    "                                        if not tc or not isinstance(tc, dict): continue\n"
    "                                        fn = tc.get(\"function\", {})\n"
    "                                        tool_names.append(fn.get(\"name\", \"unknown\"))\n"
    "                                    msg[\"content\"] = f\"Calling the {', '.join(tool_names)} tool{'s' if len(tool_names) > 1 else ''}...\"\n"
    "                                    break\n"
    "                            final_response = self._strip_think_blocks(fallback).strip()\n"
)

fallback_new = (
    "                        fallback = getattr(self, '_last_content_with_tools', None)\n"
    "                        if fallback:\n"
    "                            logger.debug(\"Empty follow-up after tool calls — using prior turn content as final response\")\n"
    "                            self._last_content_with_tools = None\n"
    "                            self._empty_content_retries = 0\n"
    "                            # r7.6-P1A inv-2 G1: detect channel-marker-only\n"
    "                            # pollution in the assistant chain. If found, do\n"
    "                            # NOT back-patch — emit a diagnostic trailer so\n"
    "                            # the empty-synthesis state is structurally\n"
    "                            # recorded rather than masked by a plausible-\n"
    "                            # looking 'Calling the X tool...' stub.\n"
    "                            _r76_pollution_hit = False\n"
    "                            for _r76_m in messages:\n"
    "                                if _r76_m.get(\"role\") != \"assistant\":\n"
    "                                    continue\n"
    "                                if _r76_channel_marker_only(_r76_m.get(\"content\") or \"\"):\n"
    "                                    _r76_pollution_hit = True\n"
    "                                    break\n"
    "                            if _r76_pollution_hit:\n"
    "                                # Leave messages[] untouched — no back-patch.\n"
    "                                # Final response carries the diagnostic trailer\n"
    "                                # verbatim; the probe check.py G2 detector\n"
    "                                # sees the polluted-content chain directly.\n"
    "                                final_response = _R76_EMPTY_SYNTHESIS_TRAILER\n"
    "                            else:\n"
    "                                for i in range(len(messages) - 1, -1, -1):\n"
    "                                    msg = messages[i]\n"
    "                                    if msg.get(\"role\") == \"assistant\" and msg.get(\"tool_calls\"):\n"
    "                                        tool_names = []\n"
    "                                        for tc in msg[\"tool_calls\"]:\n"
    "                                            if not tc or not isinstance(tc, dict): continue\n"
    "                                            fn = tc.get(\"function\", {})\n"
    "                                            tool_names.append(fn.get(\"name\", \"unknown\"))\n"
    "                                        msg[\"content\"] = f\"Calling the {', '.join(tool_names)} tool{'s' if len(tool_names) > 1 else ''}...\"\n"
    "                                        break\n"
    "                                final_response = self._strip_think_blocks(fallback).strip()\n"
)

if src.count(fallback_old) != 1:
    print(f"ERROR: fallback anchor not unique (count={src.count(fallback_old)})")
    sys.exit(1)
src = src.replace(fallback_old, fallback_new, 1)

# Final sanity: markers present.
marker_count = src.count("_r76_channel_marker_only")
# Expect: 2 (def + call in pollution loop).
if marker_count < 2:
    print(f"ERROR: expected >=2 _r76_channel_marker_only marker hits, got {marker_count}")
    sys.exit(1)
trailer_count = src.count("_R76_EMPTY_SYNTHESIS_TRAILER")
if trailer_count < 2:
    print(f"ERROR: expected >=2 _R76_EMPTY_SYNTHESIS_TRAILER hits, got {trailer_count}")
    sys.exit(1)

with open(path, "w") as f:
    f.write(src)

print(f"  run_agent.py: applied Change 1(a) detection gate + Change 2 trailer "
      f"({marker_count} marker hits, {trailer_count} trailer hits)")
PYEOF
fi

# ------------------------------------------------------------------
# CHANGE 1(b) — patches on gemma_parser.py
# ------------------------------------------------------------------
if grep -q 'PIPE_PATTERN_PREFIXLESS' environments/tool_call_parsers/gemma_parser.py; then
  echo "  gemma_parser.py: already patched (idempotent no-op)"
else
  [[ -f environments/tool_call_parsers/gemma_parser.py.probe-r7.6-orig ]] \
    || cp environments/tool_call_parsers/gemma_parser.py \
          environments/tool_call_parsers/gemma_parser.py.probe-r7.6-orig

python3 - <<'PYEOF'
import sys

path = "environments/tool_call_parsers/gemma_parser.py"
with open(path, "r") as f:
    src = f.read()

# --- CHANGE 1(b).1: add PIPE_PATTERN_PREFIXLESS after PIPE_PATTERN ---
pattern_anchor = (
    '    PIPE_PATTERN = re.compile(\n'
    '        r"<\\|tool_call>call:(\\w+)\\{(.*?)\\}<tool_call\\|>|"\n'
    '        r"<\\|tool_call>call:(\\w+)\\{(.*)",\n'
    '        re.DOTALL,\n'
    '    )\n'
)
pattern_insert = (
    '    PIPE_PATTERN = re.compile(\n'
    '        r"<\\|tool_call>call:(\\w+)\\{(.*?)\\}<tool_call\\|>|"\n'
    '        r"<\\|tool_call>call:(\\w+)\\{(.*)",\n'
    '        re.DOTALL,\n'
    '    )\n'
    '\n'
    '    # r7.6-P1A inv-3 F3A\': prefix-less fallback for Gemma 4 26B MoE on\n'
    '    # oMLX, which emits Format 1 with the opening <|tool_call> sentinel\n'
    '    # stripped by the chat-template layer. Try this pattern AFTER the\n'
    '    # primary PIPE_PATTERN yields no matches — keeps backward compat\n'
    '    # with full-sentinel emissions.\n'
    '    PIPE_PATTERN_PREFIXLESS = re.compile(\n'
    '        r"^call:(\\w+)\\{(.*?)\\}<tool_call\\|>|"\n'
    '        r"^call:(\\w+)\\{(.*)",\n'
    '        re.DOTALL | re.MULTILINE,\n'
    '    )\n'
)
if src.count(pattern_anchor) != 1:
    print(f"ERROR: PIPE_PATTERN anchor not unique (count={src.count(pattern_anchor)})")
    sys.exit(1)
src = src.replace(pattern_anchor, pattern_insert, 1)

# --- CHANGE 1(b).2: relax has_pipe detection ---
# Current: has_pipe = "<|tool_call>" in text
# New: also True when the bare closer or bare call-prefix appears.
detect_old = '        has_pipe = "<|tool_call>" in text\n'
detect_new = (
    '        # r7.6-P1A inv-3 F3A\': accept half-sentinel and prefix-less forms.\n'
    '        has_pipe = (\n'
    '            "<|tool_call>" in text\n'
    '            or "<tool_call|>" in text\n'
    '            or re.search(r"(?m)^call:\\w+\\{", text) is not None\n'
    '        )\n'
)
if src.count(detect_old) != 1:
    print(f"ERROR: has_pipe anchor not unique (count={src.count(detect_old)})")
    sys.exit(1)
src = src.replace(detect_old, detect_new, 1)

# --- CHANGE 1(b).3: add prefix-less fallback in parse() loop ---
# Insert a second pass after the primary finditer loop for has_pipe. Anchor
# on the closing brace of the "if has_pipe:" block — specifically the
# "if has_bracket:" that follows it.
primary_anchor = "            if has_bracket:"
fallback_insert = (
    '            # r7.6-P1A inv-3 F3A\': if the primary full-sentinel pattern\n'
    '            # yielded no matches, try the prefix-less pattern. Runs only\n'
    '            # when has_pipe was True (at least one sentinel form appeared).\n'
    '            if has_pipe and not tool_calls:\n'
    '                for match in self.PIPE_PATTERN_PREFIXLESS.finditer(text):\n'
    '                    name = match.group(1) or match.group(3)\n'
    '                    raw_args = match.group(2) or match.group(4) or ""\n'
    '                    if not name:\n'
    '                        continue\n'
    '                    args = self._parse_pipe_args(raw_args)\n'
    '                    for k, v in args.items():\n'
    '                        if isinstance(v, str):\n'
    '                            args[k] = self._clean_pipe_quotes(v)\n'
    '                    tool_calls.append(\n'
    '                        ChatCompletionMessageToolCall(\n'
    '                            id="call_" + uuid.uuid4().hex[:8],\n'
    '                            type="function",\n'
    '                            function=Function(\n'
    '                                name=name,\n'
    '                                arguments=json.dumps(args, ensure_ascii=False),\n'
    '                            ),\n'
    '                        )\n'
    '                    )\n'
    '\n            if has_bracket:'
)
if src.count(primary_anchor) != 1:
    print(f"ERROR: primary_anchor (if has_bracket:) not unique (count={src.count(primary_anchor)})")
    sys.exit(1)
src = src.replace(primary_anchor, fallback_insert, 1)

# --- CHANGE 1(b).4: extend content-stripping markers to include prefix-less form ---
# Current: for marker in ["<|tool_call>", "[Calling tool:"]: ...
# Add "call:" when it appears at line start. For simplicity and minimal risk,
# we extend the marker scan to include a byte-safe lowest index for the regex
# match against the prefix-less pattern.
# Actually easier: leave as-is. The text[:first_marker] slice will just be the
# whole text if no sentinel marker found, but that's acceptable — the parse
# returns None content only when tool_calls were recovered via prefix-less
# pattern, in which case the caller overwrites content regardless. Not a
# correctness problem; the content returned alongside prefix-less tool_calls
# will include the call:... prose, which the calling code in run_agent.py
# already handles (assistant_message.content is set from _parsed_content).
#
# To be clean anyway, extend the marker loop to also try line-anchored "call:".

marker_loop_old = (
    '            first_marker = len(text)\n'
    '            for marker in ["<|tool_call>", "[Calling tool:"]:\n'
    '                idx = text.find(marker)\n'
    '                if idx >= 0:\n'
    '                    first_marker = min(first_marker, idx)\n'
)
marker_loop_new = (
    '            first_marker = len(text)\n'
    '            for marker in ["<|tool_call>", "[Calling tool:"]:\n'
    '                idx = text.find(marker)\n'
    '                if idx >= 0:\n'
    '                    first_marker = min(first_marker, idx)\n'
    '            # r7.6-P1A inv-3 F3A\': also consider prefix-less "call:" at\n'
    '            # line-start. Uses multiline regex so "call:" inside prose\n'
    '            # (non-line-start) is not matched.\n'
    '            _prefixless_match = re.search(r"(?m)^call:\\w+\\{", text)\n'
    '            if _prefixless_match is not None:\n'
    '                first_marker = min(first_marker, _prefixless_match.start())\n'
)
if src.count(marker_loop_old) != 1:
    print(f"ERROR: marker_loop anchor not unique (count={src.count(marker_loop_old)})")
    sys.exit(1)
src = src.replace(marker_loop_old, marker_loop_new, 1)

# Final sanity
marker_count = src.count("PIPE_PATTERN_PREFIXLESS")
if marker_count < 2:
    print(f"ERROR: expected >=2 PIPE_PATTERN_PREFIXLESS hits, got {marker_count}")
    sys.exit(1)

with open(path, "w") as f:
    f.write(src)

print(f"  gemma_parser.py: applied prefix-less fallback ({marker_count} PIPE_PATTERN_PREFIXLESS hits)")
PYEOF
fi

# Sanity: syntax-check both patched files
python3 -m py_compile run_agent.py && echo "  run_agent.py: py_compile OK"
python3 -m py_compile environments/tool_call_parsers/gemma_parser.py \
  && echo "  gemma_parser.py: py_compile OK"

REMOTE_SCRIPT

  log ""
  log "STAGE COMPLETE."
  log "  run_agent.py.probe-r7.6-orig + gemma_parser.py.probe-r7.6-orig backups in place"
  log "  Change 1(a): detection gate accepts <tool_call|> closer + bare 'call:' prefix"
  log "  Change 1(b): gemma_parser.py has PIPE_PATTERN_PREFIXLESS fallback"
  log "  Change 2:    empty-follow-up fallback routes channel-marker pollution to trailer"
  log "  NOTE: variantG / variantF must be staged separately if you want β-fuse + turn-0"
  log "        restriction active. variantH patches are independent of those."
}

cmd_unstage() {
  log "Unstaging Variant H (restoring .probe-r7.6-orig backups)..."

  ssh_run "bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail
cd ~/.hermes/hermes-agent

if [[ -f run_agent.py.probe-r7.6-orig ]]; then
  cp run_agent.py.probe-r7.6-orig run_agent.py
  echo "  run_agent.py restored from .probe-r7.6-orig"
else
  echo "  run_agent.py: no r7.6 backup found — skipping (already unstaged?)"
fi

if [[ -f environments/tool_call_parsers/gemma_parser.py.probe-r7.6-orig ]]; then
  cp environments/tool_call_parsers/gemma_parser.py.probe-r7.6-orig \
     environments/tool_call_parsers/gemma_parser.py
  echo "  gemma_parser.py restored from .probe-r7.6-orig"
else
  echo "  gemma_parser.py: no r7.6 backup found — skipping"
fi

# Verify no stray r7.6 markers remain.
stray_r=$(grep -c '_r76_channel_marker_only\|_R76_EMPTY_SYNTHESIS_TRAILER' run_agent.py 2>/dev/null || true)
stray_g=$(grep -c 'PIPE_PATTERN_PREFIXLESS' environments/tool_call_parsers/gemma_parser.py 2>/dev/null || true)
if [[ "${stray_r:-0}" -ne 0 || "${stray_g:-0}" -ne 0 ]]; then
  echo "WARNING: r7.6 markers still present (run_agent=$stray_r gemma_parser=$stray_g)"
  echo "         investigate before next stage."
  exit 1
fi
echo "  verified: no stray r7.6 markers in run_agent.py or gemma_parser.py"
REMOTE_SCRIPT

  log "UNSTAGE COMPLETE."
}

cmd_status() {
  log "Current Variant H state on $REMOTE_HOST:"

  local r76_marker_hits r76_trailer_hits prefixless_hits
  local runagent_bak gemma_bak runagent_md5 gemma_md5 hermes_md5
  local r75a_hits variantf_v2_refs

  r76_marker_hits=$(ssh_run "grep -c '_r76_channel_marker_only' $REMOTE_RUNAGENT 2>/dev/null || true" | head -1)
  r76_marker_hits=${r76_marker_hits:-0}
  r76_trailer_hits=$(ssh_run "grep -c '_R76_EMPTY_SYNTHESIS_TRAILER' $REMOTE_RUNAGENT 2>/dev/null || true" | head -1)
  r76_trailer_hits=${r76_trailer_hits:-0}
  prefixless_hits=$(ssh_run "grep -c 'PIPE_PATTERN_PREFIXLESS' $REMOTE_GEMMA_PARSER 2>/dev/null || true" | head -1)
  prefixless_hits=${prefixless_hits:-0}

  runagent_bak=$(ssh_run "[[ -f ~/.hermes/hermes-agent/run_agent.py.probe-r7.6-orig ]] && echo yes || echo no")
  gemma_bak=$(ssh_run "[[ -f ~/.hermes/hermes-agent/environments/tool_call_parsers/gemma_parser.py.probe-r7.6-orig ]] && echo yes || echo no")
  runagent_md5=$(md5_remote "$REMOTE_RUNAGENT")
  gemma_md5=$(md5_remote "$REMOTE_GEMMA_PARSER")
  hermes_md5=$(md5_remote "~/.hermes/hermes-agent/HERMES.md")

  # Layer context
  r75a_hits=$(ssh_run "grep -c '_resolve_tools_for_turn_r75a' $REMOTE_RUNAGENT 2>/dev/null || true" | head -1)
  r75a_hits=${r75a_hits:-0}
  variantf_v2_refs=$(ssh_run "grep -c 'delegate_worker_v2' $REMOTE_RUNAGENT 2>/dev/null || true" | head -1)
  variantf_v2_refs=${variantf_v2_refs:-0}

  printf "  run_agent.py _r76_channel_marker_only hits:       %s (expect >=2 when staged, 0 canonical)\n" "$r76_marker_hits"
  printf "  run_agent.py _R76_EMPTY_SYNTHESIS_TRAILER hits:   %s (expect >=2 when staged, 0 canonical)\n" "$r76_trailer_hits"
  printf "  gemma_parser.py PIPE_PATTERN_PREFIXLESS hits:     %s (expect >=2 when staged, 0 canonical)\n" "$prefixless_hits"
  printf "  run_agent.py.probe-r7.6-orig backup present:      %s\n" "$runagent_bak"
  printf "  gemma_parser.py.probe-r7.6-orig backup present:   %s\n" "$gemma_bak"
  printf "  run_agent.py md5:                                 %s\n" "${runagent_md5:-<absent>}"
  printf "  gemma_parser.py md5:                              %s\n" "${gemma_md5:-<absent>}"
  printf "  layer: variantG _resolve_tools_for_turn_r75a hits: %s (3=staged, 0=unstaged)\n" "$r75a_hits"
  printf "  layer: variantF delegate_worker_v2 refs:           %s (5=F staged, 0=F unstaged)\n" "$variantf_v2_refs"
  printf "  HERMES.md md5 (canonical 0780c232a6cb52e13e432261f0d68ad9): %s\n" "${hermes_md5:-<absent>}"

  if [[ "$r76_marker_hits" -ge 2 && "$r76_trailer_hits" -ge 2 && "$prefixless_hits" -ge 2 ]]; then
    echo "  STATE: STAGED (r7.6-P1A Variant H)"
  elif [[ "$r76_marker_hits" -eq 0 && "$r76_trailer_hits" -eq 0 && "$prefixless_hits" -eq 0 ]]; then
    echo "  STATE: VARIANT-H UNSTAGED"
  else
    echo "  STATE: PARTIAL — investigate before running probe or returning control"
  fi
}

case "${1:-}" in
  stage)    cmd_stage ;;
  unstage)  cmd_unstage ;;
  status)   cmd_status ;;
  verify)   cmd_status ;;
  "")       die "usage: $0 {stage|unstage|status}" ;;
  *)        die "unknown subcommand: $1" ;;
esac
