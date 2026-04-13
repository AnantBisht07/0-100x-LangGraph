---
name: refresh
description: "Rebuild codebase index — supports full rebuild, incremental (changed files only), or session-based refresh"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
model: claude-haiku-4-5-20251001
context: fork
agent: general-purpose
---

# Refresh Context Index

## Overview
Updates the `.ccs/` context files. Supports three modes: full rebuild, incremental (only changed files), and session-based (fresh start for new sessions).

## When to Use
- Context files are stale (run `/ccs:status` to check)
- After adding/removing significant files
- At the start of a new development session (if session-based mode)
- After a major git pull or merge

## Instructions

### Step 1: Read Preferences
1. Read `.ccs/preferences.json` for refresh mode
2. If argument `$ARGUMENTS` specifies a mode (full/incremental/session), use that instead

### Step 2: Execute Refresh

#### Full Rebuild
1. Delete all existing `.ccs/*.md` files (preserve preferences.json and task.md)
2. Re-run the full `/ccs:init` process

#### Incremental Refresh
1. Read existing `.ccs/file-index.md` to get the list of previously indexed files
2. Use Glob to get the current file list
3. Identify: new files (in current but not in index), deleted files (in index but not in current), potentially modified files
4. For new files: read headers, classify, add to index
5. For deleted files: remove from all context files
6. For existing files: check if imports/exports changed (read first 50 lines, compare with index)
7. Update project-map.md, file-index.md, and architecture.md with changes
8. Update the timestamp in all context file headers

#### Session-Based
1. Run incremental refresh automatically
2. Reset task.md to a fresh session header (preserve previous session as archive)

### Step 3: Report
```
Context Refresh Complete ({mode})
├── Files added: {count}
├── Files removed: {count}
├── Files updated: {count}
├── Total indexed: {count}
└── Timestamp: {new_timestamp}
```

## Limitations
- Incremental mode may miss changes to import chains (file A changes what it exports, affecting file B's context)
- For best accuracy after major changes, use full mode

---
*Built by [Anit Chaudhary](https://github.com/anitc98) — codebase-context-skill v1.0.0*
