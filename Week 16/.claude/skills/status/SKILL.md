---
name: status
description: "Show what's indexed in .ccs/, staleness of context files, file counts, and estimated token savings"
user-invocable: true
allowed-tools: Read, Glob, Grep
model: claude-haiku-4-5-20251001
context: fork
agent: general-purpose
---

# Context Status

## Overview
Shows the current state of the codebase context — what's indexed, how fresh it is, and estimated token savings from using the index.

## When to Use
- Check if context is initialized before starting work
- Verify context files are up-to-date
- See how many files would be explored without the index

## Instructions

### Step 1: Check Context Exists
1. Use Glob to check for `.ccs/` directory
2. If missing, output: "No context found. Run `/ccs:init` to initialize."
3. If exists, proceed.

### Step 2: Read Context Files
1. Read `.ccs/project-map.md` — extract file count, directory count
2. Read `.ccs/file-index.md` — extract rank distribution (S/A/B/C/D counts)
3. Read `.ccs/architecture.md` — extract tech stack summary
4. Read `.ccs/conventions.md` — extract test framework
5. Read `.ccs/preferences.json` — extract refresh mode
6. Read `.ccs/task.md` — count task entries this session

### Step 3: Check Staleness
1. Get the timestamp from the context file headers
2. Use Glob to count current source files
3. Compare counts — if current files differ from indexed, flag as stale
4. Check if any source files have been modified since the index timestamp

### Step 4: Output Report
```
Codebase Context Status
├── Initialized: {timestamp}
├── Refresh mode: {mode}
├── Staleness: {fresh/stale/very-stale}
│
├── Files indexed: {count}
│   ├── S-rank: {count}
│   ├── A-rank: {count}
│   ├── B-rank: {count}
│   ├── C-rank: {count}
│   └── D-rank: {count}
│
├── Tech stack: {stack}
├── Architecture: {pattern}
├── Test framework: {framework}
│
├── Session tasks logged: {count}
│
└── Estimated token savings: ~{percentage}%
    (Index lookup replaces {count} file reads per query)
```

## Limitations
- Staleness check is based on file count comparison, not content hashing
- Token savings estimate is approximate

---
*Built by [Anit Chaudhary](https://github.com/anitc98) — codebase-context-skill v1.0.0*
