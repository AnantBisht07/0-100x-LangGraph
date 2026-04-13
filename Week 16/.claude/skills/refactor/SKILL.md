---
name: refactor
description: "Scope a refactor — identify all affected files, dependencies, blast radius, and create a tracked refactoring plan"
argument-hint: "[what to refactor and target approach]"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, AskUserQuestion
model: claude-opus-4-6
context: fork
agent: general-purpose
---

# Refactor with Scope Analysis

## Overview
Analyzes the full blast radius of a refactor before making any changes. Identifies every file that imports, references, or depends on the target code, then creates a tracked refactoring plan.

## When to Use
- Renaming a function, class, or module
- Extracting shared logic into a utility
- Changing an interface or API contract
- Restructuring directory layout
- Migrating from one pattern to another (e.g., class to hooks)

## Instructions

### Step 1: Identify the Target
1. Parse `$ARGUMENTS` to understand what's being refactored
2. Use Grep to find all occurrences of the target symbol/pattern
3. Read `.ccs/project-map.md` to find the target's dependency chain

### Step 2: Map the Blast Radius
1. **Direct references** — Grep for the symbol name across all source files
2. **Import chain** — Files that import the target file
3. **Re-exports** — Files that re-export the target (index files, barrel exports)
4. **Test files** — Tests that test the target code
5. **Config files** — Configs that reference the target (routes, middleware, etc.)
6. **Type files** — Type definitions that depend on the target interface

### Step 3: Classify Impact
For each affected file:
- **Must change** — directly references the target symbol
- **May need update** — imports from the target file but may not use the changed symbol
- **Should verify** — indirectly depends (2+ hops in dependency chain)

### Step 4: Create Refactoring Plan
Log in `.ccs/task.md`:

```markdown
## Task #{number}: Refactor — {description}

**Status:** planned
**Type:** refactor
**Blast radius:** {low/medium/high} ({count} files affected)

### Target
- **Symbol:** {symbol_name}
- **Location:** {file:line}
- **Change:** {what's changing}

### Affected Files
| File | Impact | Change Required |
|------|--------|----------------|
| {file} | must-change | {description} |
| {file} | may-update | {description} |
| {file} | verify | {description} |

### Refactoring Steps (order matters)
1. {step — usually update the source first}
2. {step — then update direct importers}
3. {step — then update re-exports}
4. {step — then update tests}
5. {step — then verify indirect deps}

### Breaking Changes
{list of interface changes that affect external consumers}

### Rollback Strategy
{how to undo if something goes wrong}
```

### Step 5: Execute (with confirmation)
1. Ask user: "Ready to execute? This affects {count} files."
2. If confirmed, make changes in the order specified
3. Log each change in task.md as it happens
4. After all changes, suggest running `/ccs:test` to verify

## Limitations
- Cannot detect dynamic references (e.g., `obj[variableName]`)
- String-based references (e.g., API route names) may be missed
- Cross-repository dependencies are not tracked

---
*Built by [Anit Chaudhary](https://github.com/anitc98) — codebase-context-skill v1.0.0*
