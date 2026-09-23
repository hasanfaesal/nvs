# T-E09 — Results page (`/results`) + results-file endpoint

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-E06, T-B13 |
| Requirements | FR-E9, NFR-7, NFR-9 |
| May edit 06-contracts.md | no |

## Goal
- `/results` shows every table from `results/summary.json`, with simple bar charts and a gallery of failure renders.
- The server exposes the files under `results/` safely.

## Background
The evaluator should see the numbers, including failures, inside the same app. All the data is already in `summary.json` (C14.5), so the page only displays it.
- **Security:** the new endpoint serves files by relative path, so it must resolve the path and refuse anything outside `results/` (path traversal).
- **Charts:** plain inline SVG bars are enough; no chart library.

## Read first
1. `docs/spec/06-contracts.md` §C12 (the `/api/results` and `/api/results/file/...` rows), §C14.5
2. `docs/spec/09-experiments-and-evaluation.md` §7
3. `server/app.py`, `web/app/composables/useApi.ts`

## Files
| Action | Path |
|---|---|
| modify | `server/app.py`: add `GET /api/results/file/{rel_path:path}` |
| modify | `tests/test_app.py`: traversal test |
| create | `web/app/pages/results.vue` |
| modify | `web/app/composables/useApi.ts`: `getResults()`, `resultFileUrl(rel)` |

## Provenance
NEW.

## Steps
1. **Endpoint:**
   - `root = results_root().resolve()`; `p = (root / rel_path).resolve()`;
   - if `root not in p.parents` or `not p.is_file()`: 404;
   - else `FileResponse(p)`.
2. **Page sections:**
   1. Overall table (variant × mIoU/mBIoU/loc ± std, MRC).
   2. Per-scene table (`UTable` or a plain `<table>`), best value in bold.
   3. A bar chart of mIoU per scene, grouped by variant, as inline SVG with error bars for std. Use a colourblind-safe palette and label the axes.
   4. MRC table.
   5. K ablation table.
   6. 2D baseline vs the best 3D variant.
   7. Phase A table.
   8. Systems table (stage times, VRAM, latency).
   9. Wilcoxon table.
   10. **Failure gallery:**
       - from the per-seed files, the 12 lowest-IoU queries for the selected variant (a `USelect`);
       - images via `resultFileUrl(scene/variant/renders_seed0/<stem>__<query>.jpg)`;
       - caption: scene, frame, query, IoU.
   - Fetch the per-query data with `resultFileUrl('<scene>/<variant>/seed0.json')`.
3. An empty state when there is no `summary.json` yet.

## Tests
`tests/test_app.py`:
- `/api/results/file/../pyproject.toml` → 404;
- `/api/results/file/%2e%2e/pyproject.toml` → 404;
- a real file under tmp `PS_RESULTS_DIR` → 200.

## Laptop check
```bash
pytest -q tests/test_app.py && cd web && npx nuxi generate
```
Manual: copy a small fake `summary.json` into a tmp results dir, set `PS_RESULTS_DIR`, run the fake server, and open `/results`.

## Lab check
Open `/results` in the lab browser after T-E08, and compare 3 numbers with `summary.json`.

## Done when
- [ ] Tests pass; the page shows the real results

## Findings / Blockers
