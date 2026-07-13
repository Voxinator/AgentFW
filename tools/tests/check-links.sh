#!/usr/bin/env bash
# tools/tests/check-links.sh — verify that relative markdown links and backticked
# repo-relative file references in policy/, adapters/, and profiles/ resolve to
# real files. Directories that don't exist yet are skipped silently.
#
# Checked:
#   1. Markdown links [text](path)
#   2. Backticked references `path/to/file.ext` ending in .md/.sh/.yaml/.json/.toml
#      (must contain a '/' — bare filenames are prose, not repo references)
# A reference resolves if it exists relative to the containing file's directory
# OR relative to the repo root.
#
# Ignored (false-positive control): http(s)://, mailto:, anchor-only (#...),
# absolute paths, ~ home-dir and hidden-dotdir (.claude/, .codex/) install-target
# paths (explicit ./x relative links stay checkable), and anything containing
# $ < > { } * , or whitespace
# (templates, brace-expansion shorthand, globs). A trailing #anchor is stripped
# before resolution.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

checked=0
failures=()

skip_candidate() {
  # exit 0 = deliberately ignored
  local cand="$1"
  case "$cand" in
    http://*|https://*|mailto:*) return 0 ;;
    '#'*)                        return 0 ;;  # anchor-only
    /*)                          return 0 ;;  # absolute path — out of scope
    '~'*)                        return 0 ;;  # home-dir install-target path — out of scope
    '.'[!/]*)                    return 0 ;;  # hidden dotdir/dotfile (.claude/, .codex/ install targets) — out of scope; ./x stays checkable
    *'$'*|*'<'*|*'>'*)           return 0 ;;  # templated placeholder
    *'{'*|*'}'*|*'*'*|*','*)     return 0 ;;  # brace-expansion / glob shorthand
    *' '*|*"$(printf '\t')"*)    return 0 ;;  # whitespace — not a path
    '')                          return 0 ;;
  esac
  return 1
}

check_candidate() {
  local file="$1" cand="$2"
  cand="${cand%%#*}"                          # strip trailing anchor
  [ -n "$cand" ] || return 0
  checked=$((checked + 1))
  local dir
  dir="$(dirname "$file")"
  if [ -e "$dir/$cand" ] || [ -e "$ROOT/$cand" ]; then
    return 0
  fi
  failures+=("$file -> $cand")
}

for scan_dir in policy adapters profiles; do
  [ -d "$scan_dir" ] || continue
  while IFS= read -r -d '' file; do
    # 1) markdown links: [text](target)
    while IFS= read -r target; do
      skip_candidate "$target" && continue
      check_candidate "$file" "$target"
    done < <(grep -oE '\]\([^)]+\)' "$file" 2>/dev/null | sed -E 's/^\]\(//; s/\)$//' || true)

    # 2) backticked repo-relative paths ending in a known file extension
    while IFS= read -r target; do
      skip_candidate "$target" && continue
      case "$target" in */*) ;; *) continue ;; esac
      check_candidate "$file" "$target"
    done < <(grep -oE '`[^`]+`' "$file" 2>/dev/null | sed -E 's/^`//; s/`$//' | grep -E '\.(md|sh|yaml|json|toml)(#[^ ]*)?$' || true)
  done < <(find "$scan_dir" -type f -name '*.md' -print0)
done

if [ "${#failures[@]}" -gt 0 ]; then
  echo "FAIL: ${#failures[@]} unresolved reference(s) out of $checked checked:" >&2
  for f in "${failures[@]}"; do
    echo "  $f" >&2
  done
  exit 1
fi

echo "PASS: $checked links checked"
