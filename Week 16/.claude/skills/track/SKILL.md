---
name: track
description: "View and manage the session task log — see all changes, research, tests, and audits performed this session with commit-style history"
argument-hint: "[summary | detail | clear | export]"
user-invocable: true
allowed-tools: Read, Write, Glob, Grep
model: claude-haiku-4-5-20251001
context: fork
agent: general-purpose
---

# Session Tracker

## Overview
Displays the session task log (`.ccs/task.md`) in various formats. Shows every action taken this session — builds, fixes, tests, audits, research — with full commit-style details.

## When to Use
- Check what's been done this session
- Get a summary before ending work
- Export session history for documentation
- Clear the task log for a fresh start
- Understand context that's been built up during the session

## Instructions

### Parse Arguments
Parse `$ARGUMENTS`:
- **No argument or "summary"** → Compact summary view
- **"detail"** → Full task log with all entries
- **"clear"** → Archive current log and start fresh
- **"export"** → Export as a standalone markdown file
- **"files"** → List only files touched this session
- **"stats"** → Session statistics

### Summary View (default)
Read `.ccs/task.md` and output:

```
Session Summary
├── Started: {timestamp}
├── Tasks completed: {count}
│   ├── Builds: {count}
│   ├── Fixes: {count}
│   ├── Tests: {count}
│   ├── Audits: {count}
│   ├── Reviews: {count}
│   ├── Research: {count}
│   └── Other: {count}
│
├── Files touched: {count}
│   ├── Read: {count}
│   ├── Modified: {count}
│   ├── Created: {count}
│   └── Deleted: {count}
│
├── Test results: {passed}/{total} ({last_run_time})
├── Audit findings: {critical}/{high}/{medium}/{low}
│
└── Context savings: ~{estimate}% fewer tokens vs no indexing
```

### Detail View
Output the full `.ccs/task.md` content.

### Clear
1. Copy current `.ccs/task.md` to `.ccs/task-archive-{timestamp}.md`
2. Create fresh `.ccs/task.md` with new session header
3. Report: "Session archived. Fresh task log started."

### Export
1. Read full `.ccs/task.md`
2. Write to `session-report-{timestamp}.md` in project root
3. Report: "Session exported to {filename}"

### Files View
Extract all unique file paths from task.md entries:
```
Files Touched This Session
├── Modified:
│   ├── src/auth/login.ts
│   └── src/api/users.ts
├── Created:
│   └── src/utils/validator.ts
├── Deleted:
│   └── src/old/deprecated.ts
└── Read Only:
    ├── src/config/db.ts
    └── src/types/user.ts
```

### Stats View
```
Session Statistics
├── Duration: {time since session start}
├── Total tasks: {count}
├── Files read: {count} (estimated {tokens} tokens)
├── Files modified: {count}
├── Lines changed: ~{estimate}
├── Test runs: {count}
├── Research queries: {count}
├── Web fetches: {count}
└── Context file refreshes: {count}
```

## Limitations
- Token savings estimate is approximate
- Line change count is estimated from diff summaries in task.md
- Stats depend on task.md entries being complete

---
*Built by [Anit Chaudhary](https://github.com/anitc98) — codebase-context-skill v1.0.0*
