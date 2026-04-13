---
name: fix
description: "Fix bugs with dependency tracking, root-cause analysis, and verification — traces from symptom to source with full context"
argument-hint: "[bug description or error message]"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch, AskUserQuestion
model: claude-sonnet-4-6
context: fork
agent: general-purpose
---

# Fix with Root-Cause Analysis

## Overview
Diagnoses and fixes bugs by tracing from the symptom (error message, incorrect behavior) to the root cause. Tracks the entire investigation in task.md and verifies the fix.

## When to Use
- Fixing a specific bug or error
- Investigating unexpected behavior
- Resolving test failures
- Fixing build/compilation errors
- Resolving dependency conflicts

## Instructions

### Step 1: Understand the Symptom
1. Parse `$ARGUMENTS` for: error message, affected feature, stack trace, reproduction steps
2. If error message provided, use Grep to find it in the codebase
3. If stack trace provided, identify the file and line where the error originates

### Step 2: Trace to Root Cause
1. Read `.ccs/file-index.md` to understand the file's importance and role
2. Read the file where the error occurs
3. Trace the call chain backward:
   - What function threw the error?
   - What called that function?
   - What data was passed in?
4. Check `.ccs/project-map.md` for the dependency chain
5. Read each file in the chain until the root cause is found

### Step 3: Research if Needed
If the error is from a library or framework:
1. Use WebSearch to search for the exact error message + library name
2. Use WebFetch to read official documentation for the relevant API
3. Check for known issues, breaking changes, or version mismatches
4. Look for community solutions (Stack Overflow, GitHub issues)

### Step 4: Develop Fix
1. Identify the minimal change that fixes the root cause
2. Check if similar patterns exist elsewhere (grep for the same anti-pattern)
3. Verify the fix doesn't break the interface contract (check imports/dependents)
4. Follow conventions from `.ccs/conventions.md`

### Step 5: Verify
1. If tests exist for the affected code, run them via Bash
2. If no tests exist, suggest writing one
3. Check that the fix doesn't introduce new issues (grep for side effects)

### Step 6: Track
Log in `.ccs/task.md`:

```markdown
## Task #{number}: Fix — {bug title}

**Status:** done
**Type:** fix

### Symptom
{error message or behavior description}

### Root Cause
{what was actually wrong and why}

### Investigation Trail
| Step | File | Finding |
|------|------|---------|
| 1 | {file} | {what you found} |
| 2 | {file} | {what you found} |

### Fix Applied
| File | Change |
|------|--------|
| {file} | {what was changed} |

### Web Research (if any)
- {search_query}: {finding}
- {doc_url}: {relevant info}

### Verification
- [ ] Fix applied
- [ ] Tests pass
- [ ] No side effects
- [ ] Similar patterns checked
```

## Limitations
- Cannot debug runtime state (no debugger access)
- Cannot reproduce timing-dependent bugs
- Web search results may include outdated solutions — always verify against current docs

---
*Built by [Anit Chaudhary](https://github.com/anitc98) — codebase-context-skill v1.0.0*
