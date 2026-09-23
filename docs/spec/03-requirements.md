# 03 — Requirements

Every requirement has an **ID**, an **acceptance test** (how we know it's met) and the **task cards** that implement it. Task cards cite these IDs, and the phase gates (T-A16, T-B17, T-E08) re-run the acceptance tests.

Notation: `C<n>` = section of `06-contracts.md`.

---

## Phase A — reconstruction and viewer

| ID | Requirement | Acceptance test | Tasks |
|---|---|---|---|
| FR-A1 | Ingest a **posed COLMAP dataset** (LERF-OVS) into `scenes/<id>/source/` (C3), copying GT labels to `source/labels/`. | `python -m pipeline ingest --scene figurines --colmap … --labels …` exits 0. The number of images in `source/images/` equals the number of registered images in `sparse/0`. The camera model is PINHOLE or SIMPLE_PINHOLE. Label JSONs are copied. | T-A02 |
| FR-A2 | Ingest a **phone video**: extract frames, drop blurred ones, run COLMAP, undistort, produce the same canonical layout. | On a 30–60 s phone video: ≥ 80% of the kept frames are registered, and `source/images` + `sparse/0` exist. The kept/dropped frame counts are printed. | T-A13, T-A14, T-A15 |
| FR-A3 | Ingest a **folder of photos** with exhaustive matching. | Same as FR-A2 on a folder of ≥ 30 photos. | T-A14, T-A15 |
| FR-A4 | Create a **deterministic split** (C4): test = every 8th sorted image ∪ annotated frames; outlier cameras excluded. | Running `split` twice gives an identical file. `annotated ⊆ test`, train ∩ test = ∅. The unit tests in `tests/test_split.py` pass. | T-A03 |
| FR-A5 | **Train 3DGS** with gsplat MCMC using exactly the split's train images, and report PSNR / SSIM / LPIPS on the split's test images. | The checkpoint and `stats/val_step*.json` exist. The number of test images in the stats equals `len(split.test)`. The PSNR is plausible (LERF-OVS: > 20 dB). | T-A04, T-A05 |
| FR-A6 | **Export** the web asset + manifest (C5) + `phase_a.json` (C14.1), preserving Gaussian order (C11). | The PLY row count equals the checkpoint's N. `xyz_hash` recomputed from the PLY equals the manifest's. No row is dropped even when NaNs are injected (unit test). | T-A06, T-A07 |
| FR-A7 | **Log every subprocess stage** with wall time and peak VRAM (C15). | Each GPU stage adds one line to `logs/stages.jsonl` with non-null `peak_vram_mb` on the lab. | T-A01 |
| FR-A8 | The **server** lists scenes, returns a scene's manifest, streams its asset and hosts the built web app with SPA fallback (C12). | The `tests/test_app.py` endpoint tests pass on the laptop with the fixture scene. `curl /api/scenes` works on the lab. | T-A08 |
| FR-A9 | A **scene list page** shows each scene's title, Gaussian count and PSNR, and links to the explorer. | Manual check on the laptop with the fixture scene and on the lab with real scenes. | T-A10 |
| FR-A10 | A **3D viewer** loads a scene, supports orbit/pan/zoom, starts at the manifest's initial view, and shows FPS. | The scene appears upright and centered. Dragging orbits around the target. The FPS readout updates. | T-A11, T-A12 |
| FR-A11 | **Laptop development without a GPU**: a fixture scene plus a fake query engine. | `PS_FAKE=1 uvicorn server.app:app` plus `npm run dev` show the fixture scene. Queries return selections (T-B12). | T-A09, T-B12 |

## Phase B — semantics, queries, explorer

| ID | Requirement | Acceptance test | Tasks |
|---|---|---|---|
| FR-B1 | SAGA scripts run from our CLI in env `ps` (port), or in env `saga` (fallback) chosen **only** by `envs.saga` in `configs/pipeline.yaml`. | SAGA's own pipeline runs end to end on one LERF-OVS scene (T-005 report). Changing the one config key switches envs without code changes. | T-005, T-006, T-B08 |
| FR-B2 | SAGA consumes the **gsplat scene** (no SAGA RGB training). | `saga-import` creates C8. SAGA's own `GaussianModel.load_ply` loads the file with 45 `f_rest` fields, and its xyz equals `web/scene.ply` row for row. SAGA's `get_scale.py` and `train_contrastive_feature.py` then run on it (T-B08). | T-B02, T-B08 |
| FR-B3 | **Variant dirs** give SAGA only the train images (C3). | SAGA prints "skipped N cameras" with N = number of test + excluded images. No file in a variant's `sam_masks/` has a test stem. | T-B01, T-B03 |
| FR-B4 | **V1** masks: SAGA's SAM v1 ViT-H automatic masks, per frame. | One `sam_masks/<stem>.pt` per train image, shape C7. | T-B04 |
| FR-B5 | **V2** masks: SAM 2.1 automatic masks per frame, with the **same** thresholds and resolution as V1. | Same file checks as V1. The config values used are printed and equal C6.1 `masks.amg`. | T-B05 |
| FR-B6 | **V3** masks: SAM 2.1 detection on keyframes + forward/backward tracking (AutoSeg-SAM2 fork), K configurable, track IDs saved. | Same file checks, plus `track_ids/<stem>.json` lengths equal the mask counts. In the pseudo-label viewer, IDs persist across neighbouring frames. | T-B06, T-B07 |
| FR-B7 | SAGA **scale, CLIP and contrastive training** per (variant, seed). Seeds are reproducible; `q_trans.joblib` is saved. | Two runs with the same seed give nearly identical `scale_gate.pt`: the max abs diff is far smaller than between different seeds (GPU nondeterminism is tolerated). `q_trans.joblib` exists next to it. | T-B01, T-B08 |
| FR-B8 | **Shared rendering helpers** (RGB, N-D features, scalar, depth) with gsplat. | Lab check: our RGB renders of 5 test views, compared with the GT images, give a mean PSNR within 1 dB of gsplat's reported test PSNR. The depth render is positive where alpha > 0.5. A 32-D feature render has shape `[h,w,32]`. | T-B10 |
| FR-B9 | **Query index** per (variant, seed) (C9). | The file exists. The hash matches the manifest. The cluster count is between 5 and 500. The fraction of masks in clusters is > 50%. | T-B11 |
| FR-B10 | **Text query** returns per-Gaussian scores (C12, C13). | A known object name from the labels highlights that object (manual, lab). Warm median latency < 2 s. | T-B12, T-B13 |
| FR-B11 | **Click query** with granularity (scale) returns per-Gaussian scores. A background click returns 409. | Clicking an object highlights it; moving the scale from 0.1 to 0.9 grows the selection from part to whole (manual, lab). The camera test vectors (C10.6) pass. | T-A06, T-B12, T-B13 |
| FR-B12 | **Debug render overlay** to verify camera alignment. | A semi-transparent server render overlaid on the Spark view lines up (edges within ~2 px at the default view). | T-B13, T-B15 |
| FR-B13 | Explorer **modes**: highlight, isolate, hide, transparent, recolor (colour picker), heatmap; threshold slider; reset. | The `tests/splatModes.test.ts` vitest tests pass. Every mode is visibly correct on the fixture (laptop) and on a real scene (lab). Applying a mode to 1M splats takes < 200 ms. | T-B14, T-B15 |
| FR-B14 | **Variant switcher**, seed selector, query history (last 10), demo query chips from the manifest. | Switching variants re-runs the current query. Clicking a history item re-applies it without a server call. | T-B15 |
| FR-B15 | **Pseudo-label viewer**: the same train frame with V1 / V2 / V3 masks side by side, plus a frame slider. | V3 colours stay stable across consecutive frames; V1/V2 colours don't (expected). | T-B13, T-B16 |

## Evaluation

| ID | Requirement | Acceptance test | Tasks |
|---|---|---|---|
| FR-E1 | Parse GT from the **LERF-OVS JSON** and **labelme JSON** into `{category: (mask, boxes)}`. | Unit tests with tiny synthetic JSONs of both formats. Same-label polygons are unioned. | T-E01 |
| FR-E2 | Metrics: **IoU, Boundary IoU (0.02), localization hit**. | Unit tests: identical masks give IoU = 1; disjoint masks give 0; a known square pair gives the hand-computed value. The localization hit/miss cases are correct. | T-E02 |
| FR-E3 | **3D evaluation** per (scene, variant, seed) on annotated held-out frames (C14.2). | The JSON exists, with one entry per (frame, category). The summary equals the mean of the entries. | T-E03 |
| FR-E4 | **2D-only baseline** on the same frames and queries (C14.3). | Same checks as FR-E3. | T-E04 |
| FR-E5 | **MRC** per (scene, variant) (C14.4). | Unit test on a synthetic planar scene: identical masks warped between two cameras give MRC ≈ 1; random masks give MRC < 0.3. | T-E05 |
| FR-E6 | **Aggregate** into `results/summary.json` (C14.5), with mean ± std and Wilcoxon tests. | Unit test on synthetic result files. | T-E06 |
| FR-E7 | **Experiment runner** executes the C6.3 matrix with skip-if-done; `--dry-run` prints the command list. | The dry-run output lists every stage for every (scene, variant, seed) in order. A second run skips everything. | T-E07 |
| FR-E8 | The full matrix is executed and results are committed. | `results/summary.json` covers 4 scenes × 3 variants × 3 seeds + ablations + baseline + MRC. | T-E08 |
| FR-E9 | **Results page** shows the main table, MRC, K ablation, baseline, Phase A metrics, systems numbers and the worst-query list. | Manual check against `summary.json`. | T-E09 |
| FR-E10 | **2 custom scenes** captured, processed, annotated (labelme) and included in the matrix. | Both scenes appear in `summary.json`. | T-C01–T-C04 |

## Stretch

| ID | Requirement | Acceptance test | Tasks |
|---|---|---|---|
| FR-S1 | V3x: optional cross-view contrastive term using track IDs. `--xview_weight 0` must reproduce upstream behaviour. | With weight 0, the loss curve is identical to V3 for the same seed. V3x results appear in the summary. | T-S01 |
| FR-S2 | SPZ web assets, used only if PLY load time > 10 s. | Splat count and order are unchanged; the load time drops. | T-S02 |

---

## Non-functional requirements

| ID | Requirement | How it's checked |
|---|---|---|
| NFR-1 | Every GPU stage peaks **< 14 GB VRAM** (A4000 has 16 GB; keep 2 GB headroom). | `peak_vram_mb − baseline_vram_mb` in C15 logs, reviewed at T-A16 / T-B17 / T-E08 |
| NFR-2 | Warm server: **median text-query and click-query latency < 2 s** (measured over 20 queries). | T-B17 |
| NFR-3 | **≥ 30 FPS** orbit in the lab-PC browser for all demo scenes. | T-A16 (FPS readout) |
| NFR-4 | **Reproducible:** every run driven by `configs/*.yaml`, seeds fixed, `git_sha` in every result file, upstream SHAs in `THIRD_PARTY.md`. | review at gates |
| NFR-5 | **Provenance:** every COPY file has the header from `05-codebase-map.md` §5; every fork change is in the patch registry. | review at each card |
| NFR-6 | **Laptop tests:** `pytest -q` finishes in < 60 s, with no GPU, network or datasets. | every card's laptop check |
| NFR-7 | **Security (private demo):** bind `127.0.0.1`; tailnet access only through `tailscale serve`; validate inputs as in C12; never build a file path from raw request strings. | T-A08, T-B13 code review |
| NFR-8 | **No large files in git:** `data/`, `scenes/`, `checkpoints/`, `*.pt`, `*.ply`, `*.pth`, `node_modules/`, `.venv/` are gitignored. | T-002, `git count-objects -vH` stays small |
| NFR-9 | **Honest reporting:** all scenes and seeds reported, failures shown, no per-variant threshold tuning. | T-E06, T-E09 |
| NFR-10 | **Idempotent CLI:** each command skips existing outputs unless `--force`, and exits non-zero on failure. | per-card checks |
| NFR-11 | A 1M-splat scene loads in the lab-PC browser in **< 15 s** from localhost. | T-A16 |
| NFR-12 | **Minimal code:** no new dependency unless the card allows it; no speculative options; one test file per non-trivial module. | review |

---

## Traceability: gates re-check requirements

| Gate | Re-checks |
|---|---|
| T-A16 Phase A gate | FR-A1–FR-A11, NFR-1, NFR-3, NFR-4, NFR-6, NFR-8, NFR-11 |
| T-B17 Phase B gate | FR-B1–FR-B15, NFR-1, NFR-2, NFR-5, NFR-7 |
| T-E08 full matrix | FR-E1–FR-E8, NFR-1, NFR-4, NFR-9 |
| T-F01 demo | everything visible to the evaluator; the S8 reproducibility dry run |
