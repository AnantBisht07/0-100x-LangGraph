---
name: init
description: "Deep-research the codebase and generate context files (project-map, architecture, file-index, conventions) in .ccs/ directory"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion, Task
model: claude-opus-4-6
context: fork
agent: general-purpose
---

# Initialize Codebase Context

## Overview
Performs a deep analysis of the entire codebase and generates local reference files in `.ccs/` that power all other commands. This is the foundation — run it once per project, then use `/ccs:refresh` to keep it current.

## When to Use
- First time using codebase-context-skill in a project
- After major codebase restructuring
- When context files are missing or corrupted
- After cloning a new repository

## Instructions

### Step 1: Check Existing Context
1. Check if `.ccs/` directory exists with `Glob("**/.ccs/*")`
2. If exists, ask user: "Context files already exist. Rebuild from scratch or incremental update?"
3. If rebuilding, proceed. If incremental, delegate to `/ccs:refresh` logic.

### Step 2: Ask Preferences (first run only)
If `.ccs/preferences.json` does not exist, ask user:
1. **Refresh mode**: on-demand / incremental / session-based
2. Save to `.ccs/preferences.json`

### Step 3: Discovery Phase
1. Run `Glob("**/*")` excluding: `node_modules/`, `dist/`, `build/`, `.next/`, `__pycache__/`, `.git/`, `coverage/`, `.cache/`, `*.lock`, `*.min.*`, `.ccs/`
2. Count files by extension, total directories
3. Read package manager files: `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `pom.xml`, `Gemfile`, `requirements.txt`
4. Read config files: `tsconfig.json`, `.eslintrc*`, `.prettierrc*`, `jest.config*`, `vitest.config*`, `webpack.config*`, `vite.config*`, `next.config*`

### Step 4: Structural Analysis
For each source file (JS, TS, JSX, TSX, PY, GO, RS, JAVA, RB, PHP — limit to source code only):
1. Read the first 50 lines to extract imports and exports
2. Classify the file role: entry-point, component, page, util, helper, config, test, type, style, middleware, service, controller, model, hook, context, store, api, schema
3. Record import/export relationships

### Step 5: Dependency Graph
1. Build a map: `file -> [files it imports]` and `file -> [files that import it]`
2. Rank each file by import count (how many files import it)
3. Assign ranks: S (imported by 10+), A (5-9), B (2-4), C (1), D (0)

### Step 6: Pattern Recognition
1. Detect architecture pattern from directory structure and file organization
2. Detect naming conventions by sampling 10 file names and 10 variable names
3. Detect test patterns from test files
4. Detect import/export style from source files
5. Detect error handling patterns via Grep for try/catch, .catch, Result, Error

### Step 7: Generate Context Files
Using the templates in `templates/`, generate:
1. `.ccs/project-map.md` — file tree + dependency graph
2. `.ccs/architecture.md` — tech stack, patterns, data flow
3. `.ccs/file-index.md` — ranked file index with symbols
4. `.ccs/conventions.md` — all detected patterns
5. `.ccs/task.md` — empty task log (session start header only)
6. `.ccs/preferences.json` — user preferences

### Step 8: Report
Output a summary:
```
Codebase Context Initialized
├── Files indexed: {count}
├── Directories: {count}
├── Tech stack: {stack}
├── Architecture: {pattern}
├── S-rank files: {count}
├── A-rank files: {count}
├── Test files: {count}
├── Context files generated in .ccs/
└── Refresh mode: {mode}
```

## Token Efficiency Rules
- Use Glob results to decide what to read — never read blindly
- Read file headers (first 50 lines) instead of full files during indexing
- Process files in parallel batches of 5-10
- Skip binary files, images, fonts, lock files, minified files
- Total context files should be under 3000 lines combined

## Limitations
- Does not perform semantic analysis (no embeddings or vector search)
- Import detection is regex-based, not AST-based
- May miss dynamic imports or runtime dependencies
- Large monorepos (10,000+ files) may need scoped initialization

---
*Built by [Anit Chaudhary](https://github.com/anitc98) — codebase-context-skill v1.0.0*
