# PromptSplat specification

These documents define the whole final-year project:
- what to build and why;
- which existing GitHub code every file comes from;
- the exact interfaces between components;
- how to test everything;
- how to build it one small task at a time, including with small coding models such as Claude Haiku.

The proposals in `docs/proposals/` are the academic framing. **This spec is what gets implemented.** Where they differ (NeRF, timelines, number of scenes), this spec wins; the decision log in `00-overview.md` §8 explains why.

## Two ways to read

### Learner path (new to the field? start here)
1. `00-overview.md`: what the project is, the research question, scope, success criteria.
2. `02-glossary.md`: the vocabulary (cameras, Gaussians, masks, CLIP, SAGA, metrics).
3. `01-reading-list.md`: 30 papers in reading order, each tied to the tasks it prepares you for.
4. `04-architecture-and-env.md`: how the pieces and machines fit together.
5. `07-phase-a.md` → `08-phase-b.md` → `09-experiments-and-evaluation.md`, as you reach each phase.

### Implementer path (for each task)
1. `/AGENTS.md`: the rules (coding models load it automatically).
2. `10-workflow-small-models.md`: the per-card loop and copy-paste prompts.
3. `tasks/README.md`: the status table; pick the next card.
4. The card itself; it lists exactly what else to read.

## Document index

| File | What it answers |
|---|---|
| `00-overview.md` | What are we building, why, what's in and out of scope, the decision log, risks |
| `01-reading-list.md` | What should I read, in which order, and what should I take from each paper |
| `02-glossary.md` | What does this term mean |
| `03-requirements.md` | What must work, how we check it, and which task delivers it |
| `04-architecture-and-env.md` | Components, data flow, machines, environments, version pins, networking, GPU budget |
| `05-codebase-map.md` | Where every file's code comes from (upstream repo/file, or new) and the fork patch registry |
| `06-contracts.md` | **Frozen interfaces:** folders, file formats, configs, camera math, API, results (C1–C16) |
| `07-phase-a.md` | Design of ingest → COLMAP → gsplat → export → server → viewer |
| `08-phase-b.md` | Design of SAGA import, the 3 mask sources, SAGA stages, query index, query engine, explorer UI |
| `09-experiments-and-evaluation.md` | Run matrix, metric definitions (incl. MRC), statistics, report tables |
| `10-workflow-small-models.md` | Roles, the per-card loop, prompts, git and submodule rules, reviewer checklist |
| `tasks/` | ~56 task cards, `_TEMPLATE.md`, and `README.md` (status + dependency graph) |

## Conventions in all docs

| Mark | Meaning |
|---|---|
| `C<n>` | Section n of `06-contracts.md` |
| `FR-…`, `NFR-…` | Requirement IDs in `03-requirements.md` |
| `T-…` | Task card IDs in `tasks/` |
| `[H]` / `[S]` / `[M]` | Human-only / small model / stronger model (or small model + review) |
| FORK / PIP / COPY / WRAP / GENERATOR / NEW | Provenance types (`05-codebase-map.md` §1) |
| `VERIFY (T-xxx)` | Checked on 2026-09-23 but must be re-confirmed at the pinned commit by task T-xxx |
| "laptop" / "lab" | Your Arch Linux laptop (no GPU) / the lab PC (WSL2 + RTX A4000) |

All paths are relative to the repo root.

## First steps

1. Read `00-overview.md` and skim the glossary.
2. Do the setup cards in order: `tasks/T-001` (forks), `T-002` (skeleton + laptop env), `T-003` (lab PC), `T-004` (lab envs), `T-007` (data).
3. Start the SAGA port spike `T-005` early. It is the biggest technical risk, and it can run in parallel with Phase A.
