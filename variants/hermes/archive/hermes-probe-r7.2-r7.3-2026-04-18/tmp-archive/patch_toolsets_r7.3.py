#!/usr/bin/env python3
"""Idempotently add `file_readonly` toolset to toolsets.py."""
import sys

PATH = "/home/parallels/.hermes/hermes-agent/toolsets.py"

src = open(PATH).read()
if '"file_readonly"' in src:
    print("ALREADY_PRESENT")
    sys.exit(0)

needle = (
    '    "file": {\n'
    '        "description": "File manipulation tools: read, write, patch (with fuzzy matching), and search (content + files)",\n'
    '        "tools": ["read_file", "write_file", "patch", "search_files"],\n'
    '        "includes": []\n'
    '    },\n'
    '    \n'
    '    "tts": {'
)

new_block = (
    '    "file": {\n'
    '        "description": "File manipulation tools: read, write, patch (with fuzzy matching), and search (content + files)",\n'
    '        "tools": ["read_file", "write_file", "patch", "search_files"],\n'
    '        "includes": []\n'
    '    },\n'
    '    \n'
    '    "file_readonly": {\n'
    '        "description": "Read-only file tools: read_file and search_files only (no write_file, no patch). Use to mechanically prevent role-collapse mutation in untrusted/orientation-only agents.",\n'
    '        "tools": ["read_file", "search_files"],\n'
    '        "includes": []\n'
    '    },\n'
    '    \n'
    '    "tts": {'
)

if needle not in src:
    print("ANCHOR_NOT_FOUND")
    sys.exit(1)

src = src.replace(needle, new_block, 1)
open(PATH, "w").write(src)
print("INSERTED")
