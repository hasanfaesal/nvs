# T-A12 — Explorer page, Phase A (viewer + info panel)

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-A11 |
| Requirements | FR-A10 |
| May edit 06-contracts.md | no |

## Goal
`/scene/<id>` shows the scene full-height with `SplatViewer` and a 320 px side panel: title, Gaussian count, PSNR/SSIM/LPIPS, live FPS, asset size, load progress or errors, and a controls hint.

## Background
This page becomes the main explorer in Phase B, where T-B15 adds the query panel. Keep the side panel a vertical stack of `UCard` sections, so later cards can append sections without restructuring.

## Read first
1. `docs/spec/07-phase-a.md` §11.2
2. `web/app/components/SplatViewer.client.vue`
3. `web/app/composables/useApi.ts`

## Files
| Action | Path |
|---|---|
| create | `web/app/pages/scene/[id].vue` |

## Provenance
NEW.

## Steps
1. `const id = useRoute().params.id as string`; load `getScene(id)` on mount. On error, show "Scene not found" and a link back to `/`.
2. Layout: `div.flex` with the viewer area (`flex-1 relative`), and `aside.w-80 border-l overflow-y-auto p-4 space-y-4` for the panel. The height fills the window below the header.
3. `<SplatViewer ref="viewer" :asset-url="scene.asset_url" :initial-view="scene.initial_view" :mesh-quaternion="scene.mesh_quaternion_xyzw" @ready=… @error=…>`.
4. An overlay (absolute, centered) while loading: "Loading scene (NNN MB)…", from `scene.asset.bytes`. It is hidden on `ready`.
5. The **Scene** `UCard`: title, `num_gaussians` (formatted), metrics (PSNR 2 dp, SSIM 3 dp, LPIPS 3 dp with its `lpips_net`), `FPS {{ viewer?.fps }}`, asset MB, and the hint "Drag: orbit · Right-drag: pan · Wheel: zoom".
6. Leave a comment `<!-- Phase B sections (T-B15) go below -->` at the end of the panel.

## Laptop check
```bash
cd web && npx nuxi generate
```
Manual (you, laptop): fixture + fake server + `npm run dev`. Open `/scene/_fixture`: the red sphere is on the left, the green cube on the right, the grey floor **below** them (not above), and the FPS readout updates.

## Lab check
Build and serve as in T-A10, then open `http://localhost:8000/scene/ramen` in the lab browser. The scene appears upright, and the FPS is ≥ 30 while orbiting.

## Done when
- [ ] The fixture looks right on the laptop; a real scene looks right on the lab PC

## Findings / Blockers
