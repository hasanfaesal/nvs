# 00 — Project overview

## 1. One paragraph

**PromptSplat** turns a phone video of a static indoor scene into a photorealistic 3D scene made of Gaussians (**3D Gaussian Splatting, 3DGS**).
- It then teaches every Gaussian a small "affinity" feature, so Gaussians belonging to the same object can be found together (**SAGA**).
- Supervision comes from 2D object masks (**SAM / SAM 2**) and 2D language features (**CLIP**).
- In a browser, a user types *"the rubber duck"* or clicks an object. The matching Gaussians light up from every viewpoint and can be isolated, hidden, made transparent or recolored.

The research question is whether masks **tracked through the video with SAM 2** give more consistent 3D segmentation than masks computed **independently per frame**.

## 2. What the evaluator sees (demo story)

1. On the lab PC's browser, the **explorer** opens a prepared scene (e.g. LERF *figurines*). The evaluator orbits it at ≥ 30 FPS.
2. They type a phrase. The selected Gaussians are highlighted from every angle. Buttons switch between **highlight / isolate / hide / transparent / recolor / heatmap**, and a slider changes the confidence threshold.
3. They switch on **click mode** and click an object. A granularity slider moves the selection between a part and the whole object.
4. The **mask-source switcher** changes between V1 (SAM per-frame), V2 (SAM 2 per-frame) and V3 (SAM 2 tracked). The same query visibly changes.
5. The **pseudo-label viewer** shows the training frames with each source's masks side by side. V3 keeps the same color (same object ID) across frames; V1/V2 flicker.
6. The **results page** shows the held-out mIoU / mBIoU / localization accuracy, the mask-consistency metric (MRC), the reconstruction metrics and the systems numbers, including failure cases.

## 3. Phases

### Phase A — reconstruction + viewer (the non-NeRF part of `proposal-initial.md`)
- **Input:** a posed public dataset (LERF-OVS), a phone video, or a folder of photos.
- **Pipeline:** frames + blur filter → COLMAP poses → gsplat 3DGS (MCMC strategy, capped at 1M Gaussians) → web asset + manifest.
- **App:** FastAPI serves the scenes; the Nuxt + Spark web app lists them and renders them in the browser.
- **Metrics:** PSNR / SSIM / LPIPS on held-out views, training time, peak VRAM, FPS, asset size.
- **Exit gate (T-A16):**
  - all 4 LERF-OVS scenes are processed and viewable at ≥ 30 FPS on the lab PC, and load over Tailscale on the laptop;
  - one phone video goes through the video path end to end;
  - every stage peaks below 14 GB of VRAM.

### Phase B — semantics + queries + evaluation (`proposal-extra.md`)
- **SAGA** on top of the gsplat scene, trained three times with different mask sources (V1/V2/V3) and 3 seeds each.
- **Query engine:**
  - text: CLIP + SAGA clusters;
  - click: rendered SAGA feature + scale gate.
- **Explorer:** query panel, modes, mask-source switcher, pseudo-label viewer, results page.
- **Evaluation:** held-out mIoU / mBIoU / localization, MRC, a 2D-only baseline, the K ablation, systems measurements.
- **Custom data:** 2 phone scenes, annotated with labelme.
- **Exit gate (T-B17):**
  - text and click queries work in the browser on all LERF-OVS scenes for all variants;
  - median latency is < 2 s;
  - the camera-alignment debug overlay matches.

## 4. Research question, hypotheses, variables

**Question** (from `docs/fyp-options/option-1-language-grounded-3dgs.md`): *Does temporally propagated SAM 2 supervision improve 3D Gaussian segmentation consistency over independently generated masks when camera views and GPU memory are limited?*

**Variants** (the only thing that changes between them is the mask source):

| ID | Mask source | Role |
|---|---|---|
| V1 `sam` | SAM v1 ViT-H automatic masks, each frame independently | SAGA's original method (baseline) |
| V2 `sam2_frame` | SAM 2.1 automatic masks, each frame independently | control: isolates the effect of the newer model |
| V3 `sam2_track_k10` | SAM 2.1 masks detected on keyframes and **tracked** forward and backward through the frame sequence (AutoSeg-SAM2 fork, K=10) | **our method** |
| (stretch) V3x `sam2_track_k10_xview` | V3 + a cross-view contrastive term that uses the track IDs | stretch |

**Hypotheses**
- **H1 (labels):** V3's pseudo-labels are more consistent across views than V1's and V2's (higher MRC).
- **H2 (3D, tracking effect):** V3 has higher held-out mIoU than V2.
- **H3 (3D, overall):** V3 has higher held-out mIoU than V1.
- **H4 (3D vs 2D):** the 3D variants beat the 2D-only baseline in localization accuracy and consistency.

**Held fixed:** scene, split, the RGB 3DGS model (one per scene, shared by all variants), mask resolution (÷4), automatic-mask thresholds, SAGA hyper-parameters, query thresholds, seeds {0,1,2}.

**Reported honestly even if they fail.** Issue #138 in the SAGA repo reports that V2-style SAM 2 masks made SAGA *worse*. A negative or mixed result is a valid finding.

## 5. Scope

### In scope
- Phase A and Phase B as above.
- 4 public scenes: LERF-OVS figurines, ramen, waldo_kitchen, teatime.
- 2 custom phone scenes (tabletop; cluttered desk or shelf).
- CLI-only processing on the lab PC.
- Local demo on the lab PC browser, plus private access over the Tailscale tailnet.

### Stretch (only after the Phase B gate)
- V3x cross-view loss (T-S01).
- SPZ compressed web assets (T-S02), only if PLY load time > 10 s.

### Out of scope (decided during planning)
- Anything NeRF: no NeRF training and no NeRF-vs-3DGS comparison.
- Uploading videos through the web app, background job runners, databases.
- Authentication, multi-user use, public internet deployment.
- Dynamic scenes, relighting, generative inpainting (hidden objects just reveal empty space).
- Training or fine-tuning SAM, SAM 2 or CLIP (always frozen).
- LLM query rewriting and relational queries ("the mug left of the laptop").
- Real-time SLAM, WebXR, voice queries, FlashSplat comparison.
- Running LangSplat or comparing with published paper numbers (different protocol).
- Downsample-factor and view-count ablations.

## 6. What is pretrained, what is optimized, what is ours

| Kind | Components |
|---|---|
| **Pretrained, frozen** | SAM v1 ViT-H, SAM 2.1 Hiera-L, OpenCLIP ViT-B/16 (LAION-2B) |
| **Optimized per scene** | RGB Gaussians (gsplat MCMC); SAGA affinity features + scale gate (per variant, per seed) |
| **Our contribution** | SAM 2 tracked supervision for SAGA (AutoSeg-SAM2 fork with a SAM 2 detector), the controlled 3-variant study, the MRC consistency metric, the held-out evaluation, the browser query system (FastAPI + Nuxt + Spark), the 2 custom scenes with annotations |

## 7. Success criteria (targets, not claims)

| # | Criterion | Measured by |
|---|---|---|
| S1 | 4 public + 2 custom scenes reproducible from the CLI | T-A16, T-C02 |
| S2 | Text and click queries select objects in the browser for every variant | T-B17 |
| S3 | Median text-query and click-query latency < 2 s (warm server) | T-B17, C15 logs |
| S4 | ≥ 30 FPS orbit on the lab-PC browser | T-A16 |
| S5 | No out-of-memory crash; every stage peaks < 14 GB | C15 logs |
| S6 | V1/V2/V3 compared under matched settings, 3 seeds, with held-out metrics, MRC, and a statistical test | T-E08 |
| S7 | Failure cases and low-confidence queries shown in the results page | T-E09 |
| S8 | Another student can reproduce one scene from the docs | T-F01 dry run |

## 8. Decision log

| Decision | Choice | Why |
|---|---|---|
| Order | Phase A, then Phase B. The timelines in the proposals are ignored. | The user wants a working 3DGS app before semantics |
| NeRF | Dropped entirely | The user only uses Gaussian splatting |
| 3DGS trainer | gsplat + MCMC, `normalize_world_space=False`, classic rasterizer, SH degree 3 | Best maintained quality/memory; hard Gaussian cap (1M) fits 16 GB and the browser; modern env shared with SAM 2 |
| Public data | LangSplat LERF-OVS, 4 scenes, **held-out protocol only** | Phone-captured, ordered frames, COLMAP poses, text-query GT. Held-out means honest numbers; published numbers use a different protocol, so no paper comparison. |
| Custom data | 2 phone scenes, labelme annotation | enough for mean ± std across scenes |
| Processing | CLI only; the web app only views and queries processed scenes | A pipeline run takes 1–2.5 h, so it can't be shown live. Simplest. |
| Web stack | Nuxt 4 (SPA, `ssr:false`) + Nuxt UI + Spark; FastAPI serves everything | User preference (Vue/Nuxt). GaussianSplats3D is unmaintained and points to Spark, which supports per-splat edits. |
| Demo host | Browser on the lab PC (A4000); tailnet access through `tailscale serve`; no auth | The laptop iGPU is too weak; Tailscale already restricts access |
| Mask sources | V1 SAM, V2 SAM 2 per-frame, V3 SAM 2 tracked (AutoSeg-SAM2 fork) | V2 separates "better model" from "tracking". AutoSeg-SAM2 is an existing MIT repo already used for 3DGS (Segment-then-Splat). |
| SAGA loss | Unchanged for V1–V3; cross-view term only as a stretch | Clean controlled variable |
| Baseline | 2D-only: SAM masks + best CLIP score on the test photo | Uses already-installed models |
| Ablations | 3 seeds on core runs; AutoSeg `--detect_stride` K ∈ {5,10,20} | Variance plus the one knob specific to our method |
| Consistency metric | mIoU + **mask reprojection consistency (MRC)** | Directly measures the "multi-view consistency" in the title |
| Envs | Try one modern env with SAGA ported; fall back to a legacy `saga` env | Fewer envs if the port works; a safe fallback if not |
| Upstream code | Forks as git submodules (SAGA, gsplat, AutoSeg-SAM2); everything else pinned pip/npm; small COPY snippets with attribution | The user asked to build on existing repos |
| Coding workflow | Tool-agnostic (`AGENTS.md`); coding on the laptop; GPU checks on the lab PC by the user | The user uses Claude Code and Cursor; the laptop has no GPU |

## 9. Risks and fallbacks

| Risk | Signal | Fallback |
|---|---|---|
| SAGA won't build or run on Python 3.10 / PyTorch 2.9 | T-005 spike fails within its 3-day timebox | T-006: legacy env `saga` (Py 3.7 / torch 1.12 / CUDA 11.6) via `conda run -n saga`; switch `envs.saga` in `configs/pipeline.yaml` |
| COLMAP 4.2 output unreadable by SAGA's loader | T-A14 lab check | pin `colmap=3.11` in the `colmap` env |
| COLMAP fails on a phone video | few registered images | recapture (slower, more texture, locked exposure); remove blurred frames; smaller scene; `global_mapper` |
| Out of memory | stage peak ≥ 14 GB in C15 | lower `cap_max` (e.g. 700k); mask downsample stays 4; `num_sampled_rays` 1000 → 750; `offload_state_to_cpu` for SAM 2; fewer AutoSeg objects per batch |
| SAM 2 tracking drifts on LERF keyframes (6–15° per step, not 30 fps video) | many short tracks, low MRC | smaller K; report it as a finding (tracking needs dense video). The custom scenes use real video. |
| AutoSeg `--detector sam2` port too hard | T-B06 > 1 day | keep SAM v1 detection; argue the tracking effect from V3 vs V1 with V2 reported; note it in `port-report.md` |
| Open-vocabulary query unreliable | wrong clusters | show the confidence heatmap and threshold; fixed query set for evaluation; **no** LLM rewriting |
| Spark per-splat API differs from the docs | T-B14 check fails | fall back from `splatRgba` to `PackedSplats.setSplat` + `needsUpdate`; last resort: overlay a second `SplatMesh` built from the selected subset |
| Clicks select the wrong object | debug overlay misaligned | fix `pipeline/camera.py` against the C10.6 test vectors; never patch around it in the UI |
| HDBSCAN too slow or memory-hungry | > 20k masks | `query_index.max_masks` (use every 2nd frame) |
| LERF-OVS Google Drive quota | download fails | Hugging Face mirror `Qmh/lerf_ovs` (T-007) |
| Laptop disk (17 GB free) | `uv`/npm fill the disk | no datasets or checkpoints on the laptop; CPU torch only; fixture scene ≤ 20 MB |
| Hypothesis not supported | V3 ≤ V1/V2 | Report it with analysis (MRC, failure cases). Honesty is a success criterion. |
