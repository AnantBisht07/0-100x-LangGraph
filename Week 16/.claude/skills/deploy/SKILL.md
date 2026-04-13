---
name: deploy
description: "Pre-deployment checklist — verifies tests pass, build succeeds, env vars set, no breaking changes, dependencies locked, and generates deploy report"
user-invocable: true
allowed-tools: Read, Write, Glob, Grep, Bash, WebSearch, AskUserQuestion
model: claude-opus-4-6
context: fork
agent: general-purpose
---

# Deploy Checklist

## Overview
Runs a comprehensive pre-deployment checklist to catch issues before they reach production. Verifies tests, build, environment variables, dependencies, breaking changes, and generates a deploy-ready report.

## When to Use
- Before deploying to staging or production
- Before creating a release PR
- As a final check after a series of changes
- Before merging a feature branch

## Instructions

### Step 1: Load Context
1. Read `.ccs/architecture.md` for build/deploy commands and deploy target
2. Read `.ccs/task.md` for all changes made this session
3. Read `.ccs/conventions.md` for git/CI conventions

### Step 2: Run Checklist

#### 2.1 Tests
- [ ] Run full test suite (`npm test` / `pytest` / `go test` / etc.)
- [ ] All tests pass (0 failures)
- [ ] No skipped tests that should be running
- Report: `{passed}/{total} tests pass`

#### 2.2 Build
- [ ] Run build command (`npm run build` / `go build` / etc.)
- [ ] Build succeeds without errors
- [ ] Build succeeds without warnings (or warnings are acceptable)
- [ ] Build output is reasonable size
- Report: `Build {success/failed} ({size} output)`

#### 2.3 Linting
- [ ] Run linter (`npx eslint .` / `flake8` / `golangci-lint run` / etc.)
- [ ] No errors (warnings may be acceptable)
- Report: `{errors} errors, {warnings} warnings`

#### 2.4 Type Checking (if applicable)
- [ ] Run type checker (`npx tsc --noEmit` / `mypy .` / etc.)
- [ ] No type errors
- Report: `{errors} type errors`

#### 2.5 Environment Variables
1. Grep for `process.env.`, `os.environ`, `os.Getenv`, `env::var` in source
2. Grep for `.env.example`, `.env.sample`, `.env.template`
3. Compare: are all referenced env vars documented?
4. Check for hardcoded secrets (should be env vars)
- [ ] All env vars documented in .env.example or equivalent
- [ ] No secrets hardcoded in source

#### 2.6 Dependencies
- [ ] Lock file exists and is up-to-date (package-lock.json, yarn.lock, etc.)
- [ ] No audit vulnerabilities above medium severity
- [ ] All peer dependencies satisfied
- Report: `{vulns} vulnerabilities`

#### 2.7 Breaking Changes
1. Read `.ccs/task.md` for all changes this session
2. Check if any modified files are:
   - Public API endpoints
   - Exported interfaces/types
   - Database schema
   - Configuration format
3. Flag any potential breaking changes
- [ ] No unintended breaking changes
- Report: `{count} potential breaking changes`

#### 2.8 Git Status
- [ ] All changes committed (clean working tree)
- [ ] Branch is up-to-date with base branch
- [ ] No merge conflicts
- Report: `{status}`

### Step 3: Generate Deploy Report
```markdown
# Deploy Checklist Report

**Timestamp:** {now}
**Branch:** {branch}
**Changes this session:** {count} tasks

## Results
| Check | Status | Details |
|-------|--------|---------|
| Tests | {pass/fail} | {passed}/{total} |
| Build | {pass/fail} | {details} |
| Lint | {pass/fail} | {errors} errors |
| Types | {pass/fail/n/a} | {errors} errors |
| Env Vars | {pass/fail} | {missing count} missing |
| Dependencies | {pass/fail} | {vuln count} vulnerabilities |
| Breaking Changes | {pass/warn} | {count} flagged |
| Git Status | {clean/dirty} | {details} |

## Verdict: {READY / NOT READY / READY WITH WARNINGS}

## Action Items (if not ready)
1. {action}
2. {action}
```

### Step 4: Track
Log deploy check in `.ccs/task.md`.

## Limitations
- Cannot run actual deployment
- Cannot verify external services (DB connections, API endpoints)
- Breaking change detection is based on file analysis, not API contract testing

---
*Built by [Anit Chaudhary](https://github.com/anitc98) — codebase-context-skill v1.0.0*
