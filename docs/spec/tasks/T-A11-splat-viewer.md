# T-A11 — `SplatViewer.client.vue`: Spark + three.js viewer component

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-A10 |
| Requirements | FR-A10, NFR-3, NFR-11 |
| May edit 06-contracts.md | no |

## Goal
A reusable Vue component that:
- loads a scene PLY with **Spark**;
- applies the manifest's mesh rotation and initial view;
- orbits with three.js `OrbitControls` and shows FPS;
- emits clicks (not drags) with canvas coordinates;
- exposes the camera state that the click and debug-render APIs need.

## Background
Spark renders Gaussian splats inside a normal three.js scene: add a `SparkRenderer`, then add `SplatMesh` objects.
- Two things matter for the rest of the project:
  - **LoD must be off.** Level-of-detail merges splats, and then splat *i* would no longer be Gaussian *i* (C11).
  - **The mesh must be rotated with the quaternion (1,0,0,0).** COLMAP scenes are "y down"; three.js is "y up" (C10.3).
- We **copy** Spark's own example code instead of inventing the setup.

## Read first
1. `docs/spec/07-phase-a.md` §11.3
2. `docs/spec/06-contracts.md` §C5, §C10.3, §C10.5
3. Spark @ 2.2.0: `examples/hello-world/index.html` (setup), `examples/nonlod/` (LoD options), `examples/interactivity/` (OrbitControls). Read them on GitHub: https://github.com/sparkjsdev/spark/tree/v2.2.0/examples (VERIFY the tag name)
4. `web/app/composables/useApi.ts` (the `InitialView` type)

## Files
| Action | Path |
|---|---|
| create | `web/app/components/SplatViewer.client.vue` |

## Provenance
COPY + adapt of Spark examples (MIT). Put this header at the top of `<script setup>`:
```ts
// Source: https://github.com/sparkjsdev/spark @ v2.2.0, examples/hello-world/index.html (+ examples/nonlod, examples/interactivity)
// License: MIT. Changes: Vue component; LoD disabled; initial view from manifest; FPS; click events; camera state.
```

## Interface
```ts
props: { assetUrl: string; initialView: InitialView; meshQuaternion: [number, number, number, number] }
emits: ready({ numSplats }), pick({ u, v, width, height }), error(message: string)
defineExpose({ getCameraState, getMeshMatrixWorld, getSplatMesh, fps })
// getCameraState(): { matrix_world: number[16], fov_y_deg: number, width: number, height: number }   (C10.5; CSS pixels)
// getMeshMatrixWorld(): number[16]
```

## Steps
1. `onMounted`:
   1. `new THREE.WebGLRenderer({ canvas, antialias: false })` and `renderer.setPixelRatio(devicePixelRatio)`.
   2. A `THREE.PerspectiveCamera(initialView.fov_y_deg, 1, 0.01, 1000)`; `position` and `up` from `initialView`.
   3. `scene.add(new SparkRenderer({ renderer, enableLod: false }))`.
   4. `mesh = new SplatMesh({ url: assetUrl, enableLod: false })`, then `mesh.quaternion.set(...meshQuaternion)`, then `scene.add(mesh)`.
   5. `OrbitControls` (`three/addons/controls/OrbitControls.js`) with `controls.target.fromArray(initialView.target)`.
   6. A `ResizeObserver` on the container calls `resize()`: `renderer.setSize(w, h, false)`, `camera.aspect = w/h`, `camera.updateProjectionMatrix()`.
   7. `renderer.setAnimationLoop(...)`:
      - `controls.update()`, then `renderer.render(scene, camera)`;
      - FPS = the number of frames in the last ≥ 500 ms window ÷ that window, written to a `ref<number>`.
   8. `await mesh.initialized`, then emit `ready({ numSplats: mesh.packedSplats?.numSplats ?? 0 })`. On an exception, emit `error`.
   - VERIFY the LoD option names and `initialized` / `packedSplats` against the 2.2.0 examples, and record the real names in Findings.
2. **Click vs drag:** on `pointerdown`, store `offsetX/offsetY/time`. On `pointerup`, if the movement is < 4 px and the time < 300 ms, emit `pick({ u: offsetX, v: offsetY, width: canvas.clientWidth, height: canvas.clientHeight })`.
3. **Exposed functions:**
   - `getCameraState`: call `camera.updateMatrixWorld()` first, then return `Array.from(camera.matrixWorld.elements)` (column-major, as C10.5 expects).
   - `getMeshMatrixWorld`: `mesh.updateMatrixWorld()` first, then the same.
4. `onBeforeUnmount`: `setAnimationLoop(null)`, disconnect the observer, `controls.dispose()`, `mesh.dispose?.()`, `renderer.dispose()`.
5. **Template:** a relative full-size `div` containing a full-size `canvas`.

## Gotchas
- `width` / `height` sent to the API are **CSS pixels** (`clientWidth`), not the drawing-buffer size.
- Don't set `renderer.setSize(w, h)` with CSS updates (the third argument is `false`); the CSS classes size the canvas.

## Laptop check
```bash
cd web && npx nuxi generate
```
Manual (you, laptop, fixture): used by the explorer page in T-A12. Look at it there.

## Lab check
Done in T-A12 and T-A16 (real scene in the lab browser).

## Done when
- [x] The build passes; the Findings record the verified Spark option names

## Findings / Blockers
- Tag `v2.2.0` exists on sparkjsdev/spark (checked with `gh api`); examples read at that tag. `web/node_modules/@sparkjsdev/spark` is 2.2.0.
- VERIFIED LoD option names (2.2.0 `dist/types` + `spark.module.js`):
  - `SparkRendererOptions.enableLod?: boolean` (defaults to `true` in the source, so `false` must be passed).
  - `SplatMeshOptions.enableLod?: boolean`: when `false`, `SplatMesh.update()` forces `context.enableLod = false` (the renderer never swaps in `lodSplats`).
  - `SplatMeshOptions.lod?: boolean | "quality"` (+ `nonLod`, `lodAbove`, `lodScale`): `examples/nonlod` uses `lod: false` for the plain mesh. The component passes `lod: false` too, so no LoD tree is built.
- VERIFIED `SplatMesh.initialized: Promise<SplatMesh>` and `SplatMesh.packedSplats?: PackedSplats` with `PackedSplats.numSplats: number`; `SplatMesh.dispose()` exists.
- The upstream examples use `SparkControls` (nonlod) or `OrbitControls` from `three/addons/controls/OrbitControls.js` (interactivity); the component uses the latter, as the card says.
- ASSUMPTION: FPS follows the card (frames in the last ≥ 500 ms window ÷ window), not 07-phase-a §11.3 (rolling mean of 60 intervals). Same purpose, card wins.
- ASSUMPTION: `progress` emit (07 §11.3, optional) skipped; not in the card's interface.
- `setup` errors (WebGL context, load failure) are caught and emitted as `error(message)`.
- Laptop check: `npx nuxi generate` passes; `npx nuxi typecheck` and `npx eslint app/components/SplatViewer.client.vue` are clean; `pytest -q` green.
- VERIFY on lab: the scene renders upright, orbits, and `ready.numSplats` equals the manifest's `num_gaussians` (T-A12/T-A16).
