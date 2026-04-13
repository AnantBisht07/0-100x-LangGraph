# Quality Bar for Context Files

Standards for validating the quality of generated context files (.ccs/ directory).

## 5-Checkpoint Validation

### 1. Completeness
- All 4 core files generated (project-map, architecture, file-index, conventions)
- No placeholder content remaining
- All directories in the project represented
- Import/export relationships captured

### 2. Accuracy
- File paths match actual filesystem
- Import chains are correct (verified by grep)
- Tech stack identification is correct
- No hallucinated files or dependencies

### 3. Recency
- File modification times tracked
- Stale entries flagged (files deleted or moved)
- Index timestamp recorded
- Incremental updates preserve accuracy

### 4. Token Efficiency
- project-map.md is under 2000 lines for typical projects
- file-index.md uses compact ranking format
- architecture.md is a concise summary (under 500 lines)
- conventions.md captures patterns, not exhaustive examples

### 5. Actionability
- File roles are clearly labeled (component, util, config, test, etc.)
- Dependency chains show direction (A imports B)
- Entry points are marked
- High-importance files are at the top of rankings

## Scoring

| Score | Label | Meaning |
|-------|-------|---------|
| 5/5 | Verified | All checkpoints pass |
| 4/5 | Good | Minor gaps, still usable |
| 3/5 | Draft | Needs improvement before relying on it |
| <3 | Incomplete | Re-run /ccs:init |

## Task Entry Quality

Each entry in task.md must have:
- [ ] Clear task description
- [ ] Timestamp
- [ ] Status (pending/in-progress/done/failed)
- [ ] Files read (with line counts)
- [ ] Files modified (with change summary)
- [ ] Files created (with purpose)
- [ ] Files deleted (with reason)
- [ ] Dependencies identified
- [ ] Verification step (test run, manual check, etc.)
