# Codebase Context Skill

Context engineering middleware for Claude Code. Builds intelligent, token-efficient context for every user query by indexing the codebase locally and maintaining session state as MD files.

## Slash Commands

### Context Management
| Command | Purpose |
|---------|---------|
| `/ccs:init` | Deep-research the codebase, generate project-map, architecture, file-index, conventions |
| `/ccs:status` | Show what's indexed, staleness, file counts, token savings |
| `/ccs:refresh` | Rebuild index (full, incremental, or session-based per user preference) |
| `/ccs:query` | Preview which files would be selected for a given query |

### Workflow
| Command | Purpose |
|---------|---------|
| `/ccs:plan` | Plan a task with full dependency-aware context |
| `/ccs:build` | Create/implement with tracked context and commit-style logging |
| `/ccs:refactor` | Scope a refactor — identify all affected files and dependencies |
| `/ccs:fix` | Fix bugs with dependency tracking, root-cause analysis, and verification |

### Testing & Quality
| Command | Purpose |
|---------|---------|
| `/ccs:test` | Run tests, track results, suggest fixes, auto-fix failing tests |
| `/ccs:audit` | Audit code for security, performance, patterns, accessibility, dead code |
| `/ccs:review` | Code review with context — style, logic, security, performance checks |

### Research & Docs
| Command | Purpose |
|---------|---------|
| `/ccs:research` | Search official docs, resolve errors, check dependency health, find best practices |

### Operations
| Command | Purpose |
|---------|---------|
| `/ccs:deploy` | Pre-deployment checklist — tests, build, env vars, dependencies, breaking changes |
| `/ccs:track` | View/manage session task log, see all changes made this session |

## Model Strategy
- **Haiku 4.5**: File scanning, index lookup, status checks, query preview, session tracking
- **Sonnet 4.6**: Building features, fixing bugs, running tests (standard coding execution)
- **Opus 4.6**: Initialization, planning, refactoring, auditing, code review, research, deployment (deep reasoning, architecture, complex analysis)

## Context Files (generated in `.ccs/`)
- `project-map.md` — File structure + dependency graph
- `architecture.md` — Tech stack, patterns, entry points, data flow
- `file-index.md` — Files ranked by importance/centrality
- `conventions.md` — Coding style, naming, testing patterns
- `task.md` — Session task log with commit-style entries
- `preferences.json` — User preferences (refresh mode, etc.)

## Key Directories
```
codebase-context-skill/
├── skills/          # All slash command definitions
├── agents/          # Subagent definitions
├── references/      # Strategy docs and quality standards
└── templates/       # MD templates for generated files
```

## Principles
1. **Never explore unnecessarily** — index first, read only what matters
2. **Local tools first** — Glob + Grep + Read before any API calls
3. **Everything persists locally** — MD files maintain context across the session
4. **Token guardrails** — smaller models for scanning, larger for thinking
5. **Commit-style tracking** — every change logged like a git commit locally
