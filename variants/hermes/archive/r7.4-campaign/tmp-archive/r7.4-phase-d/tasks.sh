#!/usr/bin/env bash
# Task text bank — verbatim from probe-tasks.md
# Used by runner.sh to feed the wrapper via stdin.

task_text() {
  case "$1" in
    T1) cat <<'EOF'
What's the capital of France?
EOF
      ;;
    T2) cat <<'EOF'
In /home/parallels/scratch/scratch.py there is a variable named `foo`. Rename it to `bar`. There is only one occurrence. Return the diff.
EOF
      ;;
    T4) cat <<'EOF'
Refactor the auth module to use the new session store. Three files need changes: src/auth/session.ts, src/auth/middleware.ts, and tests/auth.test.ts. All existing tests must still pass after the refactor.
EOF
      ;;
    T5) cat <<'EOF'
The dashboard sometimes shows stale data after a user hits Save. It's intermittent — reproduces maybe 1 in 5 times. Find the root cause and fix it.
EOF
      ;;
    T6) cat <<'EOF'
Build a new export feature for our product. Users should be able to export their data as CSV, JSON, or PDF. It needs to respect permissions (users can only export data they own), include test coverage, and update the API docs. Ship it end-to-end.
EOF
      ;;
    T8) cat <<'EOF'
Write a one-off script to count files larger than 10MB in ~/Downloads and print the total. Python is fine.
EOF
      ;;
    T10) cat <<'EOF'
Migrate our Postgres 12 database to Postgres 16 with zero downtime. Production DB is ~80GB, active 24/7, and has three dependent services.
EOF
      ;;
    *) echo "UNKNOWN_TASK: $1" >&2; return 1 ;;
  esac
}

task_text "$@"
