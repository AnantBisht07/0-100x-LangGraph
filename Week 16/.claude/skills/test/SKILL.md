---
name: test
description: "Run tests, track results locally, diagnose failures, suggest fixes, and auto-fix failing tests with full context tracking"
argument-hint: "[scope: all | file path | test name | --fix]"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch, AskUserQuestion, Task
model: claude-sonnet-4-6
context: fork
agent: general-purpose
---

# Test Runner with Diagnostics

## Overview
Runs tests, captures results, diagnoses every failure, suggests fixes, and optionally auto-fixes failing tests. All results are tracked in `.ccs/task.md` as commit-style entries so context persists across the session.

## When to Use
- After building a new feature (`/ccs:build`)
- After fixing a bug (`/ccs:fix`)
- After refactoring (`/ccs:refactor`)
- Before deploying (`/ccs:deploy`)
- When investigating test failures
- When writing new tests for existing code

## Instructions

### Step 1: Discover Test Setup
1. Read `.ccs/conventions.md` for test framework and patterns
2. If conventions file doesn't have test info, auto-detect:
   - Check `package.json` scripts for test commands
   - Look for config files: `jest.config.*`, `vitest.config.*`, `pytest.ini`, `.pytest.ini`, `setup.cfg`, `pyproject.toml [tool.pytest]`
   - Use Glob to find test files: `**/*.test.*`, `**/*.spec.*`, `**/*_test.*`, `**/test_*.*`, `**/tests/**/*`
3. Identify the test runner command

### Step 2: Determine Scope
Parse `$ARGUMENTS`:
- **No argument or "all"** — run full test suite
- **File path** — run tests only for that file
- **Test name** — run specific test by name/pattern
- **"--fix"** — run tests AND auto-fix failures
- **"--write [file]"** — write new tests for the specified file
- **"--coverage"** — run with coverage reporting

### Step 3: Run Tests
Execute via Bash with appropriate flags:

```bash
# JavaScript/TypeScript
npx jest --verbose --no-coverage  # or npx vitest run --reporter=verbose
npm test -- --verbose
bun test --verbose

# Python
pytest -v --tb=short
python -m pytest -v --tb=short

# Go
go test ./... -v

# Rust
cargo test -- --nocapture
```

Always use:
- Verbose output for detailed results
- Non-interactive mode (no watch mode)
- Short tracebacks (expand only for failures)

### Step 4: Parse Results
Extract from test output:
- Total tests, passed, failed, skipped
- Duration
- For each failure:
  - Test name and file location
  - Error message
  - Expected vs actual values
  - Stack trace (first 10 lines)

### Step 5: Diagnose Failures
For each failing test:

1. **Read the test file** to understand what it's testing
2. **Read the source file** being tested
3. **Classify the failure**:
   - **Assertion failure** — expected value doesn't match actual
   - **Runtime error** — null reference, type error, import error
   - **Missing mock** — external dependency not mocked
   - **Environment issue** — missing env var, file, or service
   - **Outdated snapshot** — snapshot needs updating
   - **Timeout** — async operation not resolving
   - **Dependency error** — version mismatch, missing package

4. **Determine root cause**:
   - Is the test wrong or the code wrong?
   - Did a recent change break this?
   - Is it a flaky test?

5. **Search for solutions if needed**:
   - WebSearch for the exact error message + framework name
   - WebFetch official docs for the relevant API
   - Check for known issues in the test framework

### Step 6: Generate Fix Suggestions
For each failure, produce:

```markdown
### Failure: {test_name}
**File:** {test_file}:{line}
**Error:** {error_message}
**Root Cause:** {explanation}
**Confidence:** {high/medium/low}

**Suggested Fix:**
```{language}
// Before
{old_code}

// After
{new_code}
```

**Side Effects:** {what else might be affected}
```

### Step 7: Auto-Fix (if --fix flag)
If `$ARGUMENTS` contains `--fix`:
1. Apply each suggested fix with high confidence
2. Re-run the test suite to verify
3. If new failures appear, rollback and report
4. For medium/low confidence fixes, ask user before applying

### Step 8: Write New Tests (if --write flag)
If `$ARGUMENTS` contains `--write`:
1. Read the target source file
2. Read `.ccs/conventions.md` for test patterns
3. Identify untested code paths (branches, error cases, edge cases)
4. Generate test file following existing conventions
5. Run the new tests to verify they pass

### Step 9: Track Results
Update `.ccs/task.md`:

```markdown
## Task #{number}: Test Run

**Timestamp:** {now}
**Status:** {pass/fail}
**Type:** test
**Command:** {command_used}

### Results Summary
| Metric | Count |
|--------|-------|
| Total | {total} |
| Passed | {passed} |
| Failed | {failed} |
| Skipped | {skipped} |
| Duration | {duration} |

### Failures
| Test | File | Root Cause | Fix Applied |
|------|------|-----------|-------------|
| {test} | {file} | {cause} | {yes/no/suggested} |

### Fixes Applied
| File | Change |
|------|--------|
| {file} | {change_description} |

### Tests Written
| File | Tests Added | Covering |
|------|------------|----------|
| {file} | {count} | {source_file} |

### Web Research
| Query | Finding | Source |
|-------|---------|--------|
| {query} | {finding} | {url} |

### Verification
- [ ] All fixes applied
- [ ] Re-run passed
- [ ] No regressions
```

## Examples

```bash
/ccs:test                       # Run all tests
/ccs:test src/auth/login.ts     # Run tests for specific file
/ccs:test --fix                 # Run tests and auto-fix failures
/ccs:test --write src/utils.ts  # Write tests for utils.ts
/ccs:test --coverage            # Run with coverage report
/ccs:test "user login"          # Run tests matching pattern
```

## Best Practices
- Run `/ccs:test` after every `/ccs:build` or `/ccs:fix`
- Use `--fix` cautiously — review suggestions before accepting
- Use `--write` to improve coverage for critical files (S-rank and A-rank)
- Always check that fixes don't introduce new failures

## Limitations
- Cannot run tests that require external services (databases, APIs) unless already configured
- Snapshot updates need manual confirmation
- Flaky test detection requires multiple runs
- Cannot debug async timing issues

---
*Built by [Anit Chaudhary](https://github.com/anitc98) — codebase-context-skill v1.0.0*
