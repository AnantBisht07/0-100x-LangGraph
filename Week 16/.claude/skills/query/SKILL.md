---
name: query
description: "Preview which files would be selected for a given query — shows the file selection logic without executing anything"
argument-hint: "[your question or task description]"
user-invocable: true
allowed-tools: Read, Glob, Grep
model: claude-haiku-4-5-20251001
context: fork
agent: general-purpose
---

# Query Context Preview

## Overview
Shows exactly which files would be read and why for a given query. Useful for understanding how the context engine selects files and for debugging when the wrong files are being selected.

## When to Use
- Verify the right files would be selected before a complex task
- Debug when Claude Code is reading wrong/unnecessary files
- Understand the dependency chain for a specific feature
- Check how many tokens a query would consume

## Instructions

### Step 1: Parse Query
1. Extract key terms from `$ARGUMENTS`: file names, function names, feature names, technology terms
2. Classify the query type: build, fix, refactor, test, audit, deploy, general

### Step 2: Index Lookup
1. Read `.ccs/file-index.md` — search for files matching key terms
2. Read `.ccs/project-map.md` — search for matching entries in dependency graph
3. Score each match: exact file name match (10), exact symbol match (8), partial match (5), directory match (3)

### Step 3: Live Scan
1. Use Grep to search source files for key terms from the query
2. For each grep result, note the file and matching line
3. Combine with index results, deduplicate

### Step 4: Dependency Walk
1. For each matched file, look up its imports in the project map
2. Add direct dependencies (1 hop)
3. If the query involves refactoring or debugging, add 2-hop dependencies
4. Cap at 15 files total

### Step 5: Output Preview
```
Query: "{user_query}"
Type: {query_type}

Files Selected ({count}):
┌─────┬──────────────┬────────┬─────────────────────────────┐
│ #   │ File         │ Rank   │ Reason                      │
├─────┼──────────────┼────────┼─────────────────────────────┤
│ 1   │ {file}       │ S      │ {reason}                    │
│ 2   │ {file}       │ A      │ {reason}                    │
│ ... │              │        │                             │
└─────┴──────────────┴────────┴─────────────────────────────┘

Dependency Chain:
{file_1} → imports → {file_2} → imports → {file_3}

Estimated Token Cost: ~{tokens} tokens ({count} file reads)
Without index: ~{tokens_without} tokens ({count_without} file reads)
Savings: ~{percentage}%
```

## Limitations
- Preview only — does not actually read the files
- Token estimates are approximate (based on average file sizes from index)
- Cannot predict runtime/dynamic dependencies

---
*Built by [Anit Chaudhary](https://github.com/anitc98) — codebase-context-skill v1.0.0*
