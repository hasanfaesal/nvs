# T-B16 — Pseudo-label viewer page (`/labels/<id>`)

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-B13, T-A10 |
| Requirements | FR-B15 |
| May edit 06-contracts.md | no |

## Goal
A page that shows, for any training frame, the source image and the V1 / V2 / V3 masks side by side, with a frame slider and playback. Viewers can *see* whether masks stay consistent over time.

## Background
This page makes the research question visible. V3's masks carry **persistent track IDs**, so the same object keeps the same colour frame after frame. V1/V2 colours are just per-frame mask indices, so they flicker even when the masks are good.
The page also serves as a report figure (Fig. 2 in `09-experiments-and-evaluation.md` §7).

## Read first
1. `docs/spec/08-phase-b.md` §9
2. `docs/spec/06-contracts.md` §C12 (frames and labels endpoints)
3. `web/app/composables/useApi.ts`, `web/app/pages/index.vue`

## Files
| Action | Path |
|---|---|
| create | `web/app/pages/labels/[id].vue` |
| modify | `web/app/pages/index.vue`: a "Pseudo-labels" button on each card that has variants |
| modify | `web/app/composables/useApi.ts`: `getFrames(id)`, `frameImageUrl(id, stem)`, `labelUrl(id, stem, variant)` |

## Provenance
NEW.

## Steps
1. Load the scene (for its variants) and `getFrames(id)`.
2. **Columns:** "Image", plus up to three variant columns. Pick `sam`, `sam2_frame`, and the first `sam2_track_k*` (prefer `k10`), using only the variants that exist.
3. **Controls:** a `USlider` over frame indices; prev/next buttons; play/pause (advance every 500 ms, loop); keyboard ←/→ (a `keydown` listener added on mount and removed on unmount).
4. Each column shows an `<img :src="…">`; the browser caches them. Show the frame stem and index.
5. A caption below explains what to look at (the text in `08-phase-b.md` §9).

## Laptop check
```bash
cd web && npx nuxi generate
```
Manual (laptop fixture): `/labels/_fixture` shows 5 frames × 4 columns; the arrows and play work.

## Lab check
`/labels/figurines`: the V3 colours stay stable across neighbouring frames. Take the screenshots for Fig. 2.

## Done when
- [ ] Manual checks OK on both machines

## Findings / Blockers
