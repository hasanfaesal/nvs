# T-B15 — Explorer query panel: text, click, threshold, modes, variants, history, alignment overlay

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-B13, T-B14, T-A12 |
| Requirements | FR-B10–FR-B14 |
| May edit 06-contracts.md | no |

## Goal
The explorer page (`/scene/<id>`) gets a working query panel. Every behaviour in `08-phase-b.md` §8 works on the laptop (fixture + fake engine) and on the lab (real scenes).

## Background
This is what the evaluator uses:
- type a phrase, or click an object;
- slide the threshold;
- switch display modes;
- switch the mask source (V1/V2/V3) to see the research effect;
- replay earlier queries.

The **alignment overlay** shows the server's own render of the current camera over the Spark view. If they don't line up, click queries hit the wrong object, so it's the tool for debugging the camera path.

## Read first
1. `docs/spec/08-phase-b.md` §8
2. `docs/spec/06-contracts.md` §C12, §C13
3. `web/app/pages/scene/[id].vue`, `web/app/composables/useApi.ts`
4. `web/app/composables/useSplatEdits.ts`

## Files
| Action | Path |
|---|---|
| create | `web/app/components/QueryPanel.vue` |
| modify | `web/app/pages/scene/[id].vue`: mount `QueryPanel`, wire the viewer events, and add the overlay `<img>` |
| modify | `web/app/composables/useApi.ts`: `textQuery`, `clickQuery`, `debugRenderUrl`/`debugRender`, `b64ToBytes` |

## Provenance
NEW (Nuxt UI components: `USelect`, `UInput`, `UButton`, `UBadge`, `USwitch`, `USlider`, `UCard`).

## Steps
1. **`useApi` additions:**
   - `textQuery(id, {text, variant, seed})`;
   - `clickQuery(id, {variant, seed, camera, mesh_matrix_world, pixel, scale})`;
   - `debugRender(id, {camera, mesh_matrix_world}) → Blob`;
   - `b64ToBytes(s) → Uint8Array` (`atob` + a loop, or `Uint8Array.from(atob(s), c => c.charCodeAt(0))`).
2. **`QueryPanel.vue` sections, in this order** (`08-phase-b.md` §8.1):
   1. Mask source + seed selects. Label the variants "V1 SAM (per-frame)", "V2 SAM 2 (per-frame)", "V3 SAM 2 (tracked)", falling back to the raw id.
   2. Text input + Search + demo chips.
   3. Click-mode switch + granularity slider.
   4. Threshold slider.
   5. Mode buttons + colour input + Reset.
   6. Info.
   7. History (last 10).
   8. Alignment-overlay switch + refresh.
3. **State:** `scores: Uint8Array | null`, `threshold`, `mode` (default `'highlight'`), `color`, `lastQuery` (`{kind: 'text', text}` or `{kind: 'click', camera, mesh, pixel, scale}`), `history[]`.
4. **Behaviour:**
   - **New query:** set `scores`, set `threshold = default_threshold`, then `edits.apply(...)`. Push to history (keep 10).
   - **Threshold / mode / colour changes:** re-apply, throttled with `requestAnimationFrame`.
   - **Variant or seed change:** re-run `lastQuery`.
   - **Click mode:** handle the viewer `pick` → `clickQuery` with `viewer.getCameraState()` and `viewer.getMeshMatrixWorld()`. On 409, show a `useToast()` message "Clicked background, try on an object".
   - **History click:** re-apply the stored scores, threshold and mode without calling the server.
   - **Reset:** `edits.reset()`, `mode = 'none'`.
   - **Overlay on:** fetch `debugRender`, show it as an absolutely positioned `<img>` over the viewer with `opacity: 0.5`, `pointer-events: none` and `width/height` = the canvas CSS size. Refresh on the button or when toggled on.
5. **Info:** the selected count (the return value of `apply`), `latency_ms`, `cached`, and kept clusters as badges.

## Laptop check
```bash
cd web && npx vitest run && npx nuxi generate
```
Manual (you, laptop): fixture + `PS_FAKE=1` server + `npm run dev`, then `/scene/_fixture`:
- a text query highlights a blob, and the threshold slider grows and shrinks it;
- click mode on the red sphere selects the red sphere; clicking the sky gives the toast;
- all modes work; recolor changes the colour;
- history replays;
- the overlay shows the fake render roughly aligned with the view.

## Lab check
The real scene in the lab browser: repeat the manual checks with figurines' label categories. Check the overlay alignment (edges within ~2 px) and the mode-apply time (< 200 ms).

## Done when
- [ ] Laptop manual check OK; lab manual check OK

## Findings / Blockers
