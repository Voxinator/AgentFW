# Fixture and Evaluation-Artifact Hygiene

Fixtures and evaluation artifacts sometimes need to contain a behavior without revealing the
behavior, the evaluation target, or the expected fix to the subject being evaluated. Treat the
entire artifact as observable. Scanning source contents alone is not a contamination check.

Use this discipline for seeded repositories, benchmark inputs, challenge fixtures, and any artifact
whose validity depends on keeping its construction intent hidden.

## Leak-channel inventory

Before release, inspect every channel below from the subject's point of view:

- **Contents:** source, tests, configuration, documentation, generated files, binary strings,
  metadata, and ignored or untracked files included with the artifact. Search both natural-language
  hints and exact target terms.
- **Names:** file and directory names, executable names, test names, archive names, worktree paths,
  and other labels visible in a recursive listing. Use neutral identifiers that do not name the
  planted behavior or expected repair.
- **Messages:** commit subjects and bodies, annotated-tag messages, release notes, changelogs, and
  tool-generated messages preserved in the artifact.
- **Refs:** branch, tag, remote-tracking, stash, note, and other ref names and annotations. All refs
  must be neutral from their first creation; deleting or renaming a revealing ref later is not
  sufficient.
- **Reflog and object history:** reflog entries, unreachable commits and blobs, alternate object
  databases, and shared-worktree history. A worktree shares its repository's object store, so build
  a distributable fixture in a fresh standalone repository rather than assuming a new worktree is
  isolated.
- **Comments:** code comments, docstrings, TODOs, disabled code, test descriptions, and
  natural-reading observations. A comment can reveal the missing behavior without using a banned
  keyword.
- **Committed tooling:** guards, reproducers, seed scripts, validators, snapshots, and tests that
  encode what was planted. A checker that searches for the hidden payload is itself a leak when it
  is committed with the artifact.

Also inspect the artifact as an archive and after a clean checkout. Packaging can restore generated
or ignored material that a working-tree-only scan missed.

## One-source pattern discipline

Maintain exactly one canonical, machine-readable source for forbidden words and patterns. Keep that
source outside the artifact under test. Both of these consumers must be generated from or read that
same source:

1. the banned-word/pattern rule delivered to the construction worker; and
2. the external contamination guard that scans the finished artifact.

Do not copy and maintain two pattern lists. The dispatch/validation harness must assert their
identity mechanically, for example by recording the canonical source digest in both rendered
inputs and failing when either digest differs. Normalization, escaping, or regex compilation must
be deterministic and tested so a worker term cannot silently disappear from the guard. Any
one-off exception belongs in the canonical source with an explicit reason; it must not be patched
into only one consumer.

The canonical list is a minimum, not the whole review: natural-language hints and neutral-looking
metadata still require human or independent semantic inspection.

## Construction and validation boundary

- Keep the canonical pattern source, renderer, guard, reproducers, mutation scripts, expected
  payloads, and validation logs outside the artifact and outside its Git object database.
- Give construction workers only the generated constraint they need. Do not include the hidden
  expected fix, evaluation rationale, or a reproducer whose shape discloses the target.
- Create neutral paths and refs from the outset. Use append-only history: do not rely on amend,
  rebase, reset, ref deletion, or later cleanup to erase an earlier leak.
- Run validation from an external harness against a disposable checkout or archive. Do not copy the
  harness into the artifact merely to make its checks reproducible.
- Preserve validation evidence separately from the deliverable. Evidence names and logs can be as
  revealing as the checker itself.

## Release gate

Release only when an external guard and an independent inspection cover all seven channels above,
the worker rule and guard patterns resolve to the same canonical source identity, validation
tooling is absent from the deliverable and its object database, history is append-only, and every
visible ref/path name is neutral. A failure in any channel invalidates the artifact; sanitizing only
the working-tree contents is not enough.
