---
name: audit
description: "Audit code for security vulnerabilities, performance issues, pattern inconsistencies, accessibility gaps, dead code, and dependency problems"
argument-hint: "[scope: security | performance | patterns | accessibility | dead-code | deps | all] [file or directory]"
user-invocable: true
allowed-tools: Read, Write, Glob, Grep, Bash, WebSearch, WebFetch, Task
model: claude-opus-4-6
context: fork
agent: general-purpose
---

# Code Audit

## Overview
Performs a systematic audit of the codebase across multiple dimensions: security, performance, patterns, accessibility, dead code, and dependency health. Produces an actionable report with severity-ranked findings tracked in task.md.

## When to Use
- Before a major release or deployment
- When onboarding to a new codebase
- Periodic code health checks
- After major dependency updates
- When investigating performance or security concerns
- Before a code review

## Instructions

### Step 1: Determine Scope
Parse `$ARGUMENTS`:
- **"security"** — security-focused audit only
- **"performance"** — performance audit only
- **"patterns"** — code consistency and pattern audit
- **"accessibility"** or **"a11y"** — accessibility audit (UI codebases)
- **"dead-code"** — unused exports, unreachable code
- **"deps"** — dependency health, version mismatches, vulnerabilities
- **"all"** or no argument — full audit across all dimensions
- Optional file/directory path to scope the audit

### Step 2: Load Context
1. Read `.ccs/architecture.md` for system overview
2. Read `.ccs/file-index.md` to prioritize (S-rank and A-rank first)
3. Read `.ccs/conventions.md` to understand expected patterns

### Step 3: Security Audit
Grep for known vulnerability patterns:

| Pattern | Risk | Grep Query |
|---------|------|-----------|
| SQL Injection | Critical | `query\(.*\$\|.*\+.*\)`, raw SQL with string concat |
| Command Injection | Critical | `exec\(`, `spawn\(`, `system\(`, `eval\(` |
| XSS | High | `innerHTML`, `dangerouslySetInnerHTML`, `document.write` |
| Hardcoded Secrets | High | `password\s*=\s*["']`, `secret\s*=\s*["']`, `api_key\s*=` |
| Path Traversal | High | `\.\.\/`, `path.join.*req\.(params\|query\|body)` |
| Insecure Auth | Medium | Missing auth middleware on route handlers |
| CORS Issues | Medium | `origin: ['*']`, `Access-Control-Allow-Origin: *` |
| Unvalidated Input | Medium | Request params used directly without validation |

For each finding, read the file to confirm it's a real issue (not a false positive).

### Step 4: Performance Audit
Grep for performance anti-patterns:

| Pattern | Impact | What to Look For |
|---------|--------|-----------------|
| N+1 Queries | High | DB calls inside loops, `.map(async` with DB queries |
| Blocking I/O | High | `readFileSync`, `writeFileSync` in request handlers |
| Memory Leaks | High | Event listeners without cleanup, intervals without clear |
| Large Bundle | Medium | Whole-library imports (`import _ from 'lodash'`) |
| Re-renders | Medium | Missing React.memo, inline object/function props |
| Missing Cache | Medium | Repeated expensive computations without memoization |
| Unoptimized Queries | Medium | `SELECT *`, missing WHERE clauses, no LIMIT |

### Step 5: Pattern Audit
Check for consistency:
- Mixed naming conventions (camelCase + snake_case)
- Different error handling styles in similar code
- Inconsistent import styles (default vs named, relative vs absolute)
- Mixed async patterns (callbacks + promises + async/await)
- Code duplication (similar 10+ line blocks in multiple files)

### Step 6: Accessibility Audit (UI codebases only)
Grep for a11y issues:
- `<img` without `alt` attribute
- `<button` or `<a` without accessible text
- Click handlers without keyboard equivalents (`onClick` without `onKeyDown`)
- Missing form labels
- Hardcoded color values without contrast consideration
- Missing `role` attributes on custom interactive elements

### Step 7: Dead Code Detection
1. For each exported symbol in file-index, grep for its usage
2. If an export is never imported elsewhere → flag as potentially dead
3. Check for unreachable code (return statements before code)
4. Check for unused variables/imports
5. Check for commented-out code blocks

### Step 8: Dependency Audit
1. Read `package.json` / `requirements.txt` / `go.mod` etc.
2. Check for:
   - Outdated major versions (WebSearch for latest versions)
   - Known vulnerabilities (run `npm audit` / `pip-audit` / etc.)
   - Duplicate dependencies (same thing from different packages)
   - Missing peer dependencies
   - Unused dependencies (installed but never imported)
3. Use WebSearch to check for deprecation notices

### Step 9: Generate Audit Report
```markdown
# Audit Report

**Scope:** {dimensions audited}
**Files scanned:** {count}
**Timestamp:** {now}

## Summary
| Severity | Count |
|----------|-------|
| Critical | {count} |
| High | {count} |
| Medium | {count} |
| Low | {count} |
| Info | {count} |

## Critical Findings
### {finding_title}
- **File:** {file}:{line}
- **Severity:** Critical
- **Category:** {security/performance/etc}
- **Description:** {description}
- **Fix:** {suggested fix}

## High Findings
...

## Recommendations
1. {prioritized action item}
2. {prioritized action item}
```

### Step 10: Track in Task Log
Log the full audit in `.ccs/task.md` with findings count and top action items.

## Examples
```bash
/ccs:audit                      # Full audit
/ccs:audit security             # Security only
/ccs:audit performance src/api  # Performance audit on API directory
/ccs:audit deps                 # Dependency health check
/ccs:audit dead-code            # Find unused code
/ccs:audit a11y                 # Accessibility audit
```

## Limitations
- Cannot detect runtime-only vulnerabilities
- Dead code detection may have false positives (dynamically referenced code)
- Dependency vulnerability data depends on web search accuracy
- Accessibility audit covers common patterns, not WCAG 2.1 AA compliance

---
*Built by [Anit Chaudhary](https://github.com/anitc98) — codebase-context-skill v1.0.0*
