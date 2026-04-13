---
name: plan
description: "Plan a task with full dependency-aware context — identifies all files to read, modify, create, and test before any work begins"
argument-hint: "[task description]"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, AskUserQuestion
model: claude-opus-4-6
context: fork
agent: general-purpose
---

# Plan Task

## Overview
Creates a comprehensive implementation plan before any code is written. Identifies all files that need to be read, modified, created, or deleted — and logs the plan as a commit-style entry in task.md.

## When to Use
- Before starting any non-trivial feature or change
- When you need to understand the full scope of a task
- Before a refactor to identify the blast radius
- When estimating effort for a task

## Instructions

### Step 1: Understand the Task
1. Parse `$ARGUMENTS` to understand what the user wants to build/change
2. Classify the task: new-feature, enhancement, bug-fix, refactor, migration, config-change

### Step 2: Load Context
1. Read `.ccs/architecture.md` to understand where this task fits
2. Read `.ccs/file-index.md` to identify relevant files by rank
3. Read `.ccs/project-map.md` to trace dependency chains
4. Read `.ccs/conventions.md` to know what patterns to follow

### Step 3: Identify Files
Using the hybrid approach (index lookup + targeted grep):

**Files to READ** (understand context):
- Direct matches from index (files with matching symbols/names)
- Dependency chain files (imports of matched files)
- Similar existing implementations (grep for similar patterns)
- Test files for affected code

**Files to MODIFY** (make changes):
- Files where the actual logic change goes
- Files that import modified files (if interface changes)
- Test files that need updating

**Files to CREATE** (new files):
- New components/modules
- New test files
- New types/interfaces

**Files to DELETE** (cleanup):
- Replaced files
- Deprecated code

### Step 4: Create Plan
Log a plan entry in `.ccs/task.md`:

```markdown
## Task #{next_number}: {task_title}

**Timestamp:** {now}
**Status:** planned
**Type:** {task_type}
**Description:** {detailed description}

### Implementation Plan
1. {step_1}
2. {step_2}
3. {step_3}

### Files to Read
| File | Rank | Reason |
|------|------|--------|
| {file} | {rank} | {reason} |

### Files to Modify
| File | Change |
|------|--------|
| {file} | {what changes} |

### Files to Create
| File | Purpose |
|------|---------|
| {file} | {purpose} |

### Files to Delete
| File | Reason |
|------|--------|
| {file} | {reason} |

### Dependencies Identified
{dependency chain}

### Test Strategy
{what tests to run/write}

### Risk Assessment
- Blast radius: {low/medium/high}
- Breaking changes: {yes/no}
- Test coverage impact: {description}
```

### Step 5: Present to User
Output the plan in a readable format and ask for confirmation before proceeding.

## Limitations
- Plan is based on static analysis — runtime behavior may differ
- Cannot predict all side effects of changes
- Large tasks may need to be broken into sub-tasks

---
*Built by [Anit Chaudhary](https://github.com/anitc98) — codebase-context-skill v1.0.0*
