---
name: review
description: "Code review with full codebase context — checks style, logic, security, performance, test coverage, and convention adherence"
argument-hint: "[file path or directory or git diff scope]"
user-invocable: true
allowed-tools: Read, Write, Glob, Grep, Bash, AskUserQuestion
model: claude-opus-4-6
context: fork
agent: general-purpose
---

# Code Review

## Overview
Performs a comprehensive code review with full codebase context. Unlike a standalone review, this leverages the project's conventions, architecture, and dependency graph to provide relevant, specific feedback.

## When to Use
- Before committing changes
- After a build or refactor session
- Reviewing someone else's code in your project
- Self-review before creating a PR
- After `/ccs:fix` to verify fix quality

## Instructions

### Step 1: Determine Review Scope
Parse `$ARGUMENTS`:
- **File path** — review a specific file
- **Directory** — review all source files in a directory
- **"staged"** — review `git diff --staged` (staged changes only)
- **"changes"** — review `git diff` (all uncommitted changes)
- **"session"** — review all files modified this session (from task.md)
- No argument — review files modified this session

### Step 2: Load Context
1. Read `.ccs/conventions.md` — coding standards to review against
2. Read `.ccs/architecture.md` — understand where the code fits
3. Read `.ccs/file-index.md` — know the file's role and importance
4. If reviewing changes, read the original file + the diff

### Step 3: Review Checklist
For each file under review, check:

**Correctness**
- [ ] Logic is sound — no off-by-one, null refs, race conditions
- [ ] Edge cases handled — empty arrays, null values, boundary conditions
- [ ] Error handling present — errors caught, logged, surfaced appropriately
- [ ] Types are correct — no type mismatches, proper generics

**Security**
- [ ] No injection vulnerabilities (SQL, XSS, command)
- [ ] Input validation present at boundaries
- [ ] No secrets hardcoded
- [ ] Auth/authz checks in place

**Performance**
- [ ] No unnecessary re-renders or re-computations
- [ ] No N+1 queries or blocking operations
- [ ] Proper cleanup of resources/listeners

**Convention Adherence**
- [ ] Naming follows project conventions
- [ ] Import style matches existing patterns
- [ ] Error handling matches project patterns
- [ ] File location is appropriate for its role

**Maintainability**
- [ ] Functions are reasonably sized (under 50 lines)
- [ ] No deep nesting (max 3-4 levels)
- [ ] No code duplication with existing code
- [ ] Clear variable names (no single-letter except iterators)

**Tests**
- [ ] Tests exist for new/changed logic
- [ ] Tests cover the happy path and key edge cases
- [ ] Test naming is clear and descriptive

### Step 4: Generate Review
```markdown
# Code Review: {scope}

**Reviewer:** codebase-context-skill
**Timestamp:** {now}
**Files reviewed:** {count}

## Summary
- Approvals: {count}
- Suggestions: {count}
- Issues: {count}
- Blockers: {count}

## {file_name}

### Line {line}: {issue_type}
**Severity:** {blocker/issue/suggestion/nitpick}
```{language}
// Current
{current_code}

// Suggested
{suggested_code}
```
**Reason:** {explanation}

---

## Overall Assessment
{summary — approve / approve with suggestions / request changes}
```

### Step 5: Track
Log review in `.ccs/task.md` with findings count and outcome.

## Limitations
- Cannot review runtime behavior or test execution
- Convention checks depend on `.ccs/conventions.md` quality
- Does not replace human review for business logic validation

---
*Built by [Anit Chaudhary](https://github.com/anitc98) — codebase-context-skill v1.0.0*
