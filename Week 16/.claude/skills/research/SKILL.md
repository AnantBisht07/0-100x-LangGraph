---
name: research
description: "Search official docs, resolve dependency issues, find error fixes, lookup best practices — web-powered research with local tracking"
argument-hint: "[error message | library name | topic | 'deps' for dependency check]"
user-invocable: true
allowed-tools: Read, Write, Glob, Grep, Bash, WebSearch, WebFetch, AskUserQuestion
model: claude-opus-4-6
context: fork
agent: general-purpose
---

# Research & Documentation Lookup

## Overview
Web-powered research engine that searches official documentation, finds error solutions, checks dependency compatibility, and looks up best practices. Results are cached locally in `.ccs/task.md` so the same research never needs to happen twice.

## When to Use
- Looking up official docs for a library or framework being used
- Investigating an error message that persists after retry
- Checking for dependency version mismatches or breaking changes
- Finding best practices for a specific pattern or approach
- Getting community solutions for a known issue
- Checking if a package is deprecated or has vulnerabilities

## Instructions

### Step 1: Determine Research Type
Parse `$ARGUMENTS`:
- **Error message in quotes** → Error research mode
- **Library/package name** → Documentation lookup mode
- **"deps"** → Dependency compatibility check mode
- **"best-practices [topic]"** → Best practices research mode
- **"breaking-changes [package]"** → Migration/upgrade research mode
- **General topic** → General research mode

### Step 2: Gather Local Context
1. Read `.ccs/architecture.md` for tech stack (know which versions are in use)
2. Read `package.json` / `requirements.txt` / `go.mod` for exact dependency versions
3. Read `.ccs/task.md` to check if this topic was already researched this session
4. If already researched → return cached findings instead of re-searching

### Step 3: Error Research Mode
When the user has a persistent error:

1. **Extract error details**:
   - Error message (exact text)
   - Stack trace (if available)
   - What was tried already (from task.md)

2. **Search strategy** (in order):
   - WebSearch: `"{exact error message}" {framework} {language}`
   - WebSearch: `{error type} {framework} {version} fix`
   - WebSearch: `{error message} site:github.com/issues`
   - WebSearch: `{error message} site:stackoverflow.com`

3. **Fetch and analyze**:
   - WebFetch the top 3 results
   - Extract: root cause, fix steps, version requirements
   - Cross-reference with the user's actual versions

4. **Verify fix applicability**:
   - Does the fix match the user's version?
   - Does the fix apply to the user's configuration?
   - Are there side effects?

5. **Output**:
   ```markdown
   ## Error Research: {error_message}

   ### Root Cause
   {explanation}

   ### Fix
   {step-by-step fix}

   ### Sources
   - {url_1}: {what it said}
   - {url_2}: {what it said}

   ### Version Compatibility
   - Your version: {version}
   - Fix applies to: {version_range}
   - Compatible: {yes/no}
   ```

### Step 4: Documentation Lookup Mode
When looking up a library's official docs:

1. **Identify the library** from the query or from `package.json`
2. **Find official docs URL**:
   - WebSearch: `{library_name} official documentation`
   - Common patterns: docs.{lib}.com, {lib}.readthedocs.io, github.com/{org}/{lib}#readme
3. **Fetch relevant pages**:
   - WebFetch the API reference for the specific feature mentioned
   - WebFetch the getting started / configuration page if needed
4. **Extract**:
   - Relevant API signatures
   - Configuration options
   - Usage examples
   - Common gotchas/notes
5. **Save findings** in task.md for session-long reference

### Step 5: Dependency Check Mode
When `$ARGUMENTS` is "deps":

1. Read package manager files for all dependencies
2. For each dependency (or flagged ones):
   - WebSearch: `{package} latest version {year}`
   - WebSearch: `{package} breaking changes {current_version} to latest`
   - Check for deprecation notices
3. Run native audit commands:
   - `npm audit` / `yarn audit` / `pnpm audit`
   - `pip-audit` / `safety check`
   - `go mod verify`
4. **Output dependency report**:
   ```markdown
   ## Dependency Health Report

   | Package | Current | Latest | Status | Action |
   |---------|---------|--------|--------|--------|
   | {pkg} | {ver} | {latest} | {ok/outdated/vulnerable/deprecated} | {action} |

   ### Vulnerabilities Found
   {details}

   ### Breaking Changes to Watch
   {details}

   ### Recommended Updates
   {prioritized list}
   ```

### Step 6: Best Practices Mode
When `$ARGUMENTS` starts with "best-practices":

1. Extract the topic (e.g., "best-practices React error boundaries")
2. WebSearch: `{topic} best practices {year}`
3. WebSearch: `{topic} recommended approach {framework}`
4. WebFetch top 2-3 authoritative sources
5. Compile actionable recommendations with code examples
6. Cross-reference with the project's current approach (from conventions.md)

### Step 7: Breaking Changes Mode
When `$ARGUMENTS` starts with "breaking-changes":

1. Extract package name and current version
2. WebSearch: `{package} migration guide {current_version} to {latest}`
3. WebSearch: `{package} changelog breaking changes`
4. WebFetch the official migration guide
5. **Output**:
   ```markdown
   ## Breaking Changes: {package} {current} → {target}

   ### Changes Required
   | Change | Affected Files | Migration Step |
   |--------|---------------|---------------|
   | {change} | {files} | {step} |

   ### Code Changes
   ```{language}
   // Before ({current_version})
   {old_code}

   // After ({target_version})
   {new_code}
   ```
   ```

### Step 8: Track All Research
Every research result is logged in `.ccs/task.md`:

```markdown
## Task #{number}: Research — {topic}

**Timestamp:** {now}
**Status:** done
**Type:** research

### Query
{what was searched}

### Findings
{compiled results}

### Sources
| URL | Relevance |
|-----|-----------|
| {url} | {what was found} |

### Action Items
- {recommended action from findings}
```

## Token Efficiency
- ALWAYS check task.md first — if the same topic was already researched, return cached results
- Search with specific terms (include version numbers, exact error text)
- Fetch only the relevant page, not entire documentation sites
- Extract just the actionable information, not the full page content

## Examples
```bash
/ccs:research "Cannot read properties of undefined (reading 'map')"
/ccs:research react-query
/ccs:research deps
/ccs:research best-practices "React error handling"
/ccs:research breaking-changes next.js
/ccs:research "CORS policy blocked" express
```

## Limitations
- Web search results may include outdated information — always check version compatibility
- Cannot access private documentation or internal wikis
- Rate limits on web fetching may slow down large dependency audits
- Community solutions should be verified against official docs

---
*Built by [Anit Chaudhary](https://github.com/anitc98) — codebase-context-skill v1.0.0*
