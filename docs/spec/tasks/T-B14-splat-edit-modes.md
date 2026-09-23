# T-B14 — Splat edit modes: pure mode maths + applying it to Spark

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-A11 |
| Requirements | FR-B13 |
| May edit 06-contracts.md | no |

## Goal
- `app/utils/splatModes.ts`: a **pure** function that turns (original colours/opacities, scores, threshold, mode, colour) into new colours/opacities. Unit-tested with vitest.
- `app/composables/useSplatEdits.ts`: applies the result to the Spark `SplatMesh` fast enough for 1M splats (< 200 ms).

## Background
The server sends one score per Gaussian (C13). The browser decides what "selected" means (score ≥ threshold) and how to show it:
- **highlight:** tint the selection yellow, dim the rest;
- **isolate:** hide everything else;
- **hide:** remove the selection;
- **transparent:** fade everything else;
- **recolor:** paint the selection;
- **heatmap:** colour every splat by its score.

Keeping the maths pure (plain typed arrays in and out) makes it testable without WebGL. The Spark-specific part (reading and writing per-splat colour and alpha) is copied from Spark's examples.

## Read first
1. `docs/spec/08-phase-b.md` §8.3–§8.4
2. `docs/spec/06-contracts.md` §C13
3. `web/app/components/SplatViewer.client.vue` (`getSplatMesh`)
4. Spark @ 2.2.0: `examples/splat-painter/` (per-splat RGBA editing) and `docs/splat-mesh.md` / `PackedSplats` (`forEachSplat`, `setSplat`, `needsUpdate`)

## Files
| Action | Path |
|---|---|
| create | `web/app/utils/splatModes.ts` |
| create | `web/tests/splatModes.test.ts` |
| create | `web/app/composables/useSplatEdits.ts` |
| modify | `web/package.json`: devDependency `vitest`, script `"test": "vitest run"` |

## Provenance
- `splatModes.ts`: NEW.
- `useSplatEdits.ts`: COPY + adapt from Spark `examples/splat-painter` (MIT; header as in `05-codebase-map.md` §5), with the fallback from Spark's `PackedSplats` docs.

## Interface
```ts
export type Mode = 'none' | 'highlight' | 'isolate' | 'hide' | 'transparent' | 'recolor' | 'heatmap'
export type RGB = [number, number, number]            // 0..1
export function turbo(x: number): RGB                 // Turbo colormap polynomial approximation, clamped
export function applyMode(origRgb: Float32Array, origAlpha: Float32Array, scores: Uint8Array | null,
                          t: number, mode: Mode, color: RGB, outRgb: Float32Array, outAlpha: Float32Array): number
                          // returns the number of selected splats; writes into outRgb/outAlpha (no allocation)
export function useSplatEdits(getMesh: () => any): { capture(): void; apply(scores: Uint8Array | null, t: number, mode: Mode, color: RGB): number; reset(): void }
```

## Steps
1. `turbo(x)` (x clamped to [0,1]), with each channel clamped to [0,1] (the published polynomial approximation):
   ```ts
   r = 0.13572138 + x*(4.61539260 + x*(-42.66032258 + x*(132.13108234 + x*(-152.94239396 + x*59.28637943))))
   g = 0.09140261 + x*(2.19418839 + x*(4.84296658 + x*(-14.18503333 + x*(4.27729857 + x*2.82956604))))
   b = 0.10667330 + x*(12.64194608 + x*(-60.58204836 + x*(110.36276771 + x*(-89.90310912 + x*27.34824973))))
   ```
2. `applyMode`: `thr = Math.round(t*255)`; `sel = scores !== null && scores[i] >= thr`. Apply the table in `08-phase-b.md` §8.3 exactly:
   - highlight colour `(1.0, 0.8, 0.0)`, mix 0.4·orig + 0.6·yellow; dim factor 0.5;
   - transparent alpha factor 0.15;
   - `scores === null` or mode `'none'` → copy the originals.
3. `useSplatEdits`:
   - `capture()` reads the original per-splat colour (0–1) and opacity once:
     - **primary:** the splat-painter approach (`mesh.splatRgba` / `updateGenerator()`);
     - **fallback:** `mesh.packedSplats.forEachSplat((i, center, scales, quaternion, opacity, color) => …)`, also caching center/scales/quaternion (needed to call `setSplat`).
   - `apply()` runs `applyMode` into preallocated output arrays, then writes back:
     - primary: through the RGBA array + `mesh.updateGenerator()`;
     - fallback: `setSplat(i, center, scales, quaternion, alpha, color)` for all i, then `mesh.packedSplats.needsUpdate = true`.
   - VERIFY which path works in 2.2.0 (read the example first). Record it and the measured apply time for 1M splats in Findings.
4. Tests (`web/tests/splatModes.test.ts`, vitest), with 4 splats, scores `[0, 100, 200, 255]` and t = 0.7 (thr 179 → splats 2 and 3 selected):
   - `isolate`: alpha of 0 and 1 is 0; 2 and 3 keep the original; returns 2;
   - `hide`: the inverse;
   - `recolor`: 2 and 3 get the colour exactly, alpha unchanged;
   - `transparent`: alpha of 0 and 1 is 0.15·orig;
   - `highlight`: splat 3's rgb = 0.4·orig + 0.6·(1, 0.8, 0), splat 0's rgb = 0.5·orig;
   - `heatmap`: every rgb is in [0,1] and splat 3's differs from splat 0's;
   - `turbo(0)` and `turbo(1)` are within [0,1]; `scores = null` → a copy of the originals, returns 0.

## Laptop check
```bash
cd web && npm install -D vitest && npx vitest run && npx nuxi generate
```

## Lab check
In T-B15 (the modes are visible in the UI). Measure the apply time on a 1M-splat scene there.

## Done when
- [ ] Vitest passes; the Findings record the Spark API path used

## Findings / Blockers
