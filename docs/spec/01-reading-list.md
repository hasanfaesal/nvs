# 01 — Reading list (30 core papers + optional extras)

This list takes you from zero background to understanding every component you will build. Papers are in **reading order**. Each one says why it matters to this project, which sections to read, what to skip, what to take away, and which task cards it prepares you for.

All titles, venues and links were checked on 2026-09-23.

---

## How to read (start here)

**#0 — S. Keshav, *How to Read a Paper*, ACM SIGCOMM CCR 37(3), 2007.** [PDF](http://ccr.sigcomm.org/online/files/p83-keshavA.pdf)

Use its **three-pass method** for every paper below:

| Pass | Time | What you do | When it's enough |
|---|---|---|---|
| 1 | 10–15 min | title, abstract, intro, section headings, figures + captions, conclusion | "optional" papers |
| 2 | ~1 h | read everything except proofs; make sure you understand each figure; note unknown terms (look them up in `02-glossary.md`) | most core papers |
| 3 | 3–5 h | re-derive the method, open the code next to the paper, map equations to functions | **3DGS (#6), SAM 2 (#16), SAGA (#23)** |

**Beginner tips**
- Before reading, watch the project-page video if there is one; 3DGS, SAM, SAM 2, LERF and SAGA all have one.
- Keep the GitHub repo open next to the paper, and find where each equation lives in code. `05-codebase-map.md` tells you which files to look at.
- Don't get stuck on math in the first pass. Each entry below says which parts matter.

### Note template (one page per paper, e.g. in `docs/notes/<short-name>.md`)

```markdown
# <Short name> — <Venue Year>
- Problem (1 sentence):
- Key idea (2–3 sentences):
- Method in one diagram (sketch or figure number):
- Inputs → outputs:
- What we reuse (code / idea / data) and in which task:
- Numbers worth citing:
- Limitations / failure modes:
- Open questions:
```

---

## Reading schedule (tied to task cards; the proposal timelines don't apply)

| Stage | Read before | Papers |
|---|---|---|
| 0 — orientation | setup tasks T-001…T-007 | #0, #6 (pass 1), #23 (pass 1), #10 (pass 1) |
| 1 — Phase A | T-A05 (training) and T-A14 (COLMAP) | #1, #2, #3, #4 (§4 only), #5, #6 (pass 2), #7, #8, #9, #29 |
| 2 — Phase B | T-B01 onwards | #11–#22, #23 (passes 2 and 3), #25, #26, #27, #28 |
| 3 — Evaluation | T-E01 onwards | #24 (§4 in particular), #30; re-read #26–#28 for the discussion chapter |

---

## Part 1 — Cameras and Structure-from-Motion

### #1 SIFT
D. G. Lowe, *Distinctive Image Features from Scale-Invariant Keypoints*, IJCV 60(2), 2004. [PDF](https://www.cs.ubc.ca/~lowe/papers/ijcv04.pdf)
- **Why:** COLMAP's first step detects SIFT keypoints in every frame and matches them. When a capture fails, the cause is almost always too few good SIFT matches (blur, blank walls, reflections).
- **Focus:** §1; §3–§6 at the level of "what each step does" (scale-space extrema, keypoint localization, orientation, 128-D descriptor); §7.1 (ratio test).
- **Skip:** the object-recognition application sections and the Hessian-refinement math.
- **Take away:**
  - keypoints are repeatable blob-like spots, and descriptors are gradient-orientation histograms;
  - a match is accepted only if it is clearly better than the second-best;
  - **sharp, textured frames give many matches.**
- **Unlocks:** T-A13 (blur filter), T-A14 (COLMAP), T-C01 (capture protocol).

### #2 COLMAP: Structure-from-Motion Revisited
J. L. Schönberger, J.-M. Frahm, CVPR 2016. [PDF](https://openaccess.thecvf.com/content_cvpr_2016/papers/Schonberger_Structure-From-Motion_Revisited_CVPR_2016_paper.pdf)
- **Why:** COLMAP gives every frame its camera pose and intrinsics. Without poses there is no 3DGS.
- **Focus:** §2 (review of incremental SfM: correspondence search → initialization → image registration → triangulation → bundle adjustment) and Fig. 1; skim §4's contributions (next-best-view, robust triangulation).
- **Skip:** the detailed evaluation tables.
- **Take away:**
  - `feature_extractor` → `*_matcher` → `mapper` are exactly these stages;
  - sequential matching suits video, because neighbours overlap;
  - bundle adjustment jointly refines poses and 3D points.
- **Unlocks:** T-A14.

### #3 GLOMAP: Global Structure-from-Motion Revisited
L. Pan et al., ECCV 2024. [arXiv 2407.20219](https://arxiv.org/abs/2407.20219)
- **Why:** since COLMAP 4.0 this method is built in as `colmap global_mapper`. It is our fallback when the incremental mapper is slow or fails.
- **Focus:** §1 and §3 overview (rotation averaging, then *global positioning* of cameras and points together).
- **Skip:** the proofs and the long benchmark sections.
- **Take away:** global SfM solves all cameras at once and is much faster; accuracy is close to incremental SfM.
- **Unlocks:** T-A14 (fallback path).

## Part 2 — Rendering and 3D Gaussian Splatting

### #4 NeRF (background only; not implemented)
B. Mildenhall et al., *NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis*, ECCV 2020. [arXiv 2003.08934](https://arxiv.org/abs/2003.08934)
- **Why:** 3DGS reuses NeRF's **alpha-compositing** formula. You need that formula to understand 3DGS rendering, depth rendering and feature rendering.
- **Focus:** **§4 only** (volume rendering: C = Σ Tᵢ αᵢ cᵢ, Tᵢ = Π_{j<i}(1 − α_j)).
- **Skip:** everything else (MLP architecture, positional encoding, hierarchical sampling).
- **Take away:** a pixel is a front-to-back weighted sum. The same sum renders colours, depth ("expected depth") and our 32-D SAGA features.
- **Unlocks:** T-A05, T-B10.

### #5 EWA Volume Splatting
M. Zwicker, H. Pfister, J. van Baar, M. Gross, IEEE Visualization 2001. [PDF](https://www.cs.umd.edu/~zwicker/publications/EWAVolumeSplatting-VIS01.pdf)
- **Why:** this is where the "splat a 3D Gaussian onto the screen as a 2D ellipse" math comes from (3DGS eq. 5: Σ' = J W Σ Wᵀ Jᵀ).
- **Focus:** §3–§4 (Gaussian kernels, local affine approximation of the projection with the Jacobian J).
- **Skip:** the volume-data specifics and the hardware implementation.
- **Take away:** a 3D Gaussian projects to a 2D Gaussian. Its covariance comes from the camera rotation and the Jacobian of the perspective projection.
- **Unlocks:** T-A06 (camera math), T-B10 (rendering helpers).

### #6 3D Gaussian Splatting ★
B. Kerbl, G. Kopanas, T. Leimkühler, G. Drettakis, *3D Gaussian Splatting for Real-Time Radiance Field Rendering*, ACM TOG 42(4) / SIGGRAPH 2023. [arXiv 2308.04079](https://arxiv.org/abs/2308.04079)
- **Why:** the scene representation of the whole project.
- **Focus:** everything in §3–§6, and Fig. 2.
  - per-Gaussian parameters: position, scale, rotation quaternion, opacity, spherical-harmonic colour;
  - initialization from SfM points;
  - adaptive density control (clone / split / prune, opacity reset);
  - tile-based differentiable rasterizer;
  - loss: L1 + D-SSIM with λ = 0.2.
- **Skip:** nothing important. Read the evaluation section quickly.
- **Take away:**
  - every column in your PLY (`f_dc_*`, `f_rest_*`, `opacity`, `scale_*`, `rot_*`);
  - why VRAM grows during densification;
  - what "floaters" are.
- **Unlocks:** T-A05, T-A07, T-B02.

### #7 Mathematical Supplement for the gsplat Library
V. Ye, A. Kanazawa, tech report 2023. [arXiv 2312.02121](https://arxiv.org/abs/2312.02121)
- **Why:** it spells out the exact conventions of the rasterizer we call (`viewmats` = world→camera, `Ks`, the 2D covariance, the 0.3 low-pass dilation).
- **Focus:** the forward pass (projection, 2D covariance, tile rasterization, SH evaluation).
- **Skip:** the backward-pass gradients (unless curious).
- **Take away:** how to call `gsplat.rasterization` correctly, and why the camera must be in OpenCV convention.
- **Unlocks:** T-A06, T-B10.

### #8 gsplat: An Open-Source Library for Gaussian Splatting
V. Ye et al., JMLR 26(34), 2025. [arXiv 2409.06765](https://arxiv.org/abs/2409.06765)
- **Why:** it is our 3DGS trainer and renderer.
- **Focus:** the feature list (memory-efficient/packed mode, densification strategies incl. MCMC, anti-aliasing, **N-dimensional feature rendering**) and the comparison table against the original implementation.
- **Skip:** the API minutiae (our cards give the exact calls).
- **Take away:** gsplat can render any per-Gaussian vector (colour, a 32-D SAGA feature, a selection score, depth). One renderer serves the whole project.
- **Unlocks:** T-A04, T-A05, T-B10.

### #9 3D Gaussian Splatting as Markov Chain Monte Carlo
S. Kheradmand et al., NeurIPS 2024. [arXiv 2404.09591](https://arxiv.org/abs/2404.09591)
- **Why:** the densification strategy we train with (`simple_trainer.py mcmc`).
- **Focus:** §3–§4:
  - Gaussians seen as samples of a distribution (stochastic Langevin updates);
  - "relocation" of low-opacity Gaussians instead of clone/split;
  - opacity and scale regularizers;
  - a **fixed budget `cap_max`**.
- **Skip:** the derivations of the SGLD connection.
- **Take away:** `cap_max = 1,000,000` gives predictable VRAM and a predictable browser asset size (≈ 240 MB PLY), and it is robust to initialization.
- **Unlocks:** T-A05.

### #10 A Survey on 3D Gaussian Splatting
G. Chen, W. Wang, ACM Computing Surveys 58(12), 2026. [arXiv 2401.03890](https://arxiv.org/abs/2401.03890)
- **Why:** a map of the whole field for your report's related-work chapter.
- **Focus:** the taxonomy figure; the sections on **editing / segmentation / understanding** and on **compression**.
- **Skip:** the application areas unrelated to this project (avatars, SLAM, driving) on the first pass.
- **Take away:** where PromptSplat sits: "3DGS scene understanding with 2D foundation-model supervision".
- **Unlocks:** report writing; T-S02 (compression).

## Part 3 — Foundation models (frozen, never trained here)

### #11 Vision Transformer (ViT)
A. Dosovitskiy et al., *An Image is Worth 16x16 Words*, ICLR 2021. [arXiv 2010.11929](https://arxiv.org/abs/2010.11929)
- **Why:** CLIP ViT-B/16 and SAM's ViT-H encoder are ViTs.
- **Focus:** §3.1 and Fig. 1 (patches → linear embedding → transformer → [CLS]).
- **Skip:** the scaling experiments.
- **Take away:** "B/16" means the Base model with 16×16-pixel patches; "H" is Huge. Input resolution decides compute.
- **Unlocks:** T-B04, T-B05, T-B08.

### #12 SimCLR (contrastive learning)
T. Chen et al., *A Simple Framework for Contrastive Learning of Visual Representations*, ICML 2020. [arXiv 2002.05709](https://arxiv.org/abs/2002.05709)
- **Why:** SAGA's training is contrastive learning: pull features of "same object" pixels together and push others apart.
- **Focus:** §2.1, eq. (1) (NT-Xent / InfoNCE loss), the role of temperature.
- **Skip:** the augmentation ablations.
- **Take away:** positives and negatives define what the feature space learns. In SAGA, SAM masks define the positives (same mask) instead of image augmentations.
- **Unlocks:** T-B08, T-S01.

### #13 CLIP
A. Radford et al., *Learning Transferable Visual Models From Natural Language Supervision*, ICML 2021. [arXiv 2103.00020](https://arxiv.org/abs/2103.00020)
- **Why:** turns both a mask crop and a text query into comparable 512-D vectors.
- **Focus:** §2.3 (contrastive image–text training), §3.1.4 (prompt engineering and **ensembling**: "a photo of a {}").
- **Skip:** the long zero-shot benchmark tables and the robustness sections.
- **Take away:** cosine similarity between text and image embeddings. **Averaging many prompt templates** makes text embeddings more robust, which is why SAGA averages 80 templates.
- **Unlocks:** T-B08 (CLIP stage), T-B11, T-B12.

### #14 OpenCLIP: Reproducible scaling laws for contrastive language-image learning
M. Cherti et al., CVPR 2023. [arXiv 2212.07143](https://arxiv.org/abs/2212.07143)
- **Why:** the exact weights we use (`ViT-B-16`, `laion2b_s34b_b88k`) come from this open reproduction trained on LAION-2B.
- **Focus:** §1, §3 (setup), the released-model tables.
- **Skip:** the scaling-law fits.
- **Take away:** the provenance and licence of the CLIP model in your report. OpenCLIP models aren't identical to OpenAI CLIP.
- **Unlocks:** T-B12.

### #15 Segment Anything (SAM)
A. Kirillov et al., ICCV 2023. [arXiv 2304.02643](https://arxiv.org/abs/2304.02643)
- **Why:** V1's mask source, and the 2D baseline.
- **Focus:**
  - §2 (promptable segmentation task);
  - §3 (image encoder, prompt encoder, light mask decoder; **3 masks per prompt = whole / part / sub-part**);
  - the appendix section on **automatic mask generation**: a 32×32 point grid, then filtering by predicted IoU and stability score, then NMS.
- **Skip:** the data-engine and responsible-AI sections.
- **Take away:** what `points_per_side`, `pred_iou_thresh`, `stability_score_thresh` and `box_nms_thresh` do. We use the same values for SAM and SAM 2.
- **Unlocks:** T-B04, T-B05, T-E04.

### #16 SAM 2 ★
N. Ravi et al., *SAM 2: Segment Anything in Images and Videos*, ICLR 2025. [arXiv 2408.00714](https://arxiv.org/abs/2408.00714)
- **Why:** V2 and V3 both use it. V3 relies on its **video propagation**.
- **Focus:** §4 (model: **memory encoder, memory bank, memory attention**, prompts on any frame, streaming); §5 (SA-V data) quickly; §6 (video results).
- **Skip:** the detailed dataset statistics.
- **Take away:**
  - propagation carries an object's identity from frame to frame;
  - it works best with small motion between frames;
  - **LERF keyframes move 6–15° per step**, which is harder than 30 fps video. This is a real limitation to discuss.
- **Unlocks:** T-B05, T-B06, T-B07.

### #17 DEVA: Tracking Anything with Decoupled Video Segmentation
H. K. Cheng et al., ICCV 2023. [arXiv 2309.03903](https://arxiv.org/abs/2309.03903)
- **Why:** it is the "detect on keyframes + propagate + merge" design that Gaussian Grouping uses for consistent IDs. AutoSeg-SAM2 (our V3) follows the same idea with SAM 2.
- **Focus:** §3 (decoupling image segmentation from temporal propagation; in-clip consensus; merging new detections with propagated masks).
- **Skip:** the per-benchmark tables.
- **Take away:** keyframe interval, merge thresholds, and new-object insertion are the knobs that control ID consistency (our K ablation).
- **Unlocks:** T-B06, T-B07. (DEVA's code is CC BY-NC-SA: cite it, don't copy it.)

## Part 4 — Lifting 2D predictions into 3D (the core problem)

### #18 Feature field distillation
S. Kobayashi et al., *Decomposing NeRF for Editing via Feature Field Distillation*, NeurIPS 2022. [arXiv 2205.15585](https://arxiv.org/abs/2205.15585) (often called "Distilled Feature Fields")
- **Why:** the original idea of distilling 2D model features into a 3D field, which every language-3D method builds on.
- **Focus:** §3 (feature distillation alongside radiance).
- **Skip:** the editing application details.
- **Take away:** render a feature map exactly like a colour image, then compare it with the 2D teacher's features. We do the same with SAGA features.
- **Unlocks:** Phase B background.

### #19 LERF: Language Embedded Radiance Fields
J. Kerr et al., ICCV 2023. [arXiv 2303.09553](https://arxiv.org/abs/2303.09553)
- **Why:** (a) it is where your dataset's scenes come from (captured with the iPhone app Polycam); (b) it introduced the **relevancy score against canonical negatives** "object, things, stuff, texture", which SAGA's text scoring reuses.
- **Focus:** §3 (multi-scale CLIP crops, relevancy score) and the capture description.
- **Skip:** the DINO regularization details.
- **Take away:** why text scores are computed *relative to* generic negative phrases.
- **Unlocks:** T-007, T-B12.

### #20 Panoptic Lifting
Y. Siddiqui et al., *Panoptic Lifting for 3D Scene Understanding with Neural Fields*, CVPR 2023. [arXiv 2212.09802](https://arxiv.org/abs/2212.09802)
- **Why:** it states precisely the problem you study: 2D instance IDs **disagree across views**. It solves it with a linear-assignment (Hungarian) matching during training.
- **Focus:** §3 on lifting instance predictions with assignment; the robustness discussion.
- **Skip:** the semantic-class parts.
- **Take away:** one principled fix for inconsistent IDs; a baseline idea to discuss against tracking.
- **Unlocks:** T-B07 and T-S01 (discussion).

### #21 Contrastive Lift
Y. Bhalgat et al., *Contrastive Lift: 3D Object Instance Segmentation by Slow-Fast Contrastive Fusion*, NeurIPS 2023. [arXiv 2306.04633](https://arxiv.org/abs/2306.04633)
- **Why:** learning per-point embeddings with a **per-view contrastive loss** needs no cross-view ID matching. SAGA's loss works the same way, and so does our cross-view stretch.
- **Focus:** §3 (contrastive loss on per-view masks; slow-fast embeddings; clustering).
- **Skip:** the synthetic-dataset specifics.
- **Take away:** per-view contrastive learning avoids ID matching but *only indirectly* uses cross-view consistency. That gap is what T-S01 addresses.
- **Unlocks:** T-B08, T-S01.

### #22 GARField: Group Anything with Radiance Fields
C. M. Kim et al., CVPR 2024. [arXiv 2401.09419](https://arxiv.org/abs/2401.09419)
- **Why:** the **scale-conditioned affinity** idea. The same point can belong to a part (small scale) or a whole (large scale), and each mask's 3D scale is computed from depth. SAGA's `get_scale.py` and scale gate implement this.
- **Focus:** §3 (physical scale of SAM masks, scale-conditioned affinity field, hierarchical grouping).
- **Skip:** the implementation details of the hash grid.
- **Take away:** what the **granularity slider** in our click query really changes.
- **Unlocks:** T-B08, T-B12.

## Part 5 — Semantic and language Gaussian Splatting (direct related work)

### #23 SAGA: Segment Any 3D Gaussians ★★ (read three times)
J. Cen, J. Fang, C. Yang, L. Xie, X. Zhang, W. Shen, Q. Tian, AAAI 2025. [arXiv 2312.00860](https://arxiv.org/abs/2312.00860) · [AAAI page](https://ojs.aaai.org/index.php/AAAI/article/view/32193) (DOI 10.1609/aaai.v39i2.32193)
- **Why:** **the codebase you fork.** Every Phase B task touches it.
- **Focus:**
  - all of §3: mask-scale estimation, the scale-gated affinity features, the scale-aware contrastive loss (+ feature smoothing and norm regularizer), point-prompt and open-vocabulary segmentation;
  - §4: experiments on LERF / 3D-OVS / NVOS;
  - then map every term to `train_contrastive_feature.py`, and the queries to `saga_gui.py` / `prompt_segmenting.ipynb`.
- **Take away:** you must be able to explain the loss line by line, and the defaults (32-D features, 10,000 iterations, 1,000 sampled rays, cosine thresholds 0.75 / 0.85).
- **Unlocks:** T-005, T-B01–T-B12.
- **Citation warning:** `docs/proposals/proposal-extra.md` ref [5] lists the wrong authors ("Jiao, P., Chen, Z., …"). Use the author list above in your report. The proposal file itself stays unedited.

### #24 LangSplat
M. Qin et al., *LangSplat: 3D Language Gaussian Splatting*, CVPR 2024. [arXiv 2312.16084](https://arxiv.org/abs/2312.16084)
- **Why:** it created **LERF-OVS**, your ground truth (text-query masks and boxes on LERF frames), and its evaluation protocol (mIoU + localization).
- **Focus:**
  - §3.2–§3.4: SAM hierarchy (whole/part/sub-part), autoencoder for CLIP features, 3D language Gaussians;
  - §4.1: datasets and metrics.
- **Skip:** the speed comparisons.
- **Take away:** how the GT was made. LangSplat *trains on* the annotated frames; our **held-out** protocol removes them, so our numbers aren't comparable with theirs.
- **Unlocks:** T-007, T-E01–T-E03.

### #25 Gaussian Grouping
M. Ye et al., *Gaussian Grouping: Segment and Edit Anything in 3D Scenes*, ECCV 2024. [arXiv 2312.00732](https://arxiv.org/abs/2312.00732)
- **Why:** the closest earlier use of **video tracking (DEVA)** to get cross-view-consistent SAM masks for 3DGS. Your V3 must be positioned against it.
- **Focus:** §3.2 (consistent 2D masks by treating views as a video), §3.3 (identity encoding and losses), the editing results.
- **Skip:** the inpainting pipeline details.
- **Take away:**
  - GG learns *identity classes* per Gaussian;
  - SAGA learns *scale-aware affinities*;
  - you test whether tracked masks help the latter.
- **Unlocks:** T-B07, T-E02 (we copy its IoU/BIoU code).

### #26 Gaga
W. Lyu et al., *Gaga: Group Any Gaussians via 3D-aware Memory Bank*, TMLR 2026. [arXiv 2404.07977](https://arxiv.org/abs/2404.07977)
- **Why:** it associates masks across views using **3D overlap** instead of video tracking. It argues this is more robust with sparse or wide-baseline views, which is exactly the LERF keyframe situation.
- **Focus:** §3 (3D-aware memory bank, mask association).
- **Take away:** a strong alternative to tracking, and the natural explanation if V3 underperforms on wide-baseline data.
- **Unlocks:** T-B07 (discussion).

### #27 Segment then Splat
Y. Lu et al., *Segment then Splat: Unified 3D Open-Vocabulary Segmentation via Gaussian Splatting*, NeurIPS 2025. [arXiv 2503.22204](https://arxiv.org/abs/2503.22204) · code: https://github.com/luyr/Segment-then-Splat
- **Why:** the **closest prior work.** It tracks objects through multi-view sequences with SAM 2, using the same AutoSeg-SAM2 tool we fork, and then builds object-specific Gaussians.
- **Focus:** §3 (object tracking across views, assigning Gaussians to objects, CLIP for open vocabulary).
- **Take away:** state the difference clearly in the report:
  - they *segment first, then reconstruct*;
  - we keep SAGA's *feature field* and change only its supervision, in a controlled study with a per-frame SAM 2 control.
- **Unlocks:** T-B06, T-B07.

### #28 LaGa
J. Cen et al., *Tackling View-Dependent Semantics in 3D Language Gaussian Splatting*, ICML 2025 (by the SAGA authors). [arXiv 2505.24746](https://arxiv.org/abs/2505.24746)
- **Why:** it shows that the CLIP embedding of the same object **changes with viewpoint**. This affects our text-query stage and explains some failures.
- **Focus:** §1 motivation, §3 (object decomposition, view-dependent descriptor clustering and weighting).
- **Take away:** "multi-view inconsistency" affects **semantics** (CLIP) as well as masks. Use this in the discussion chapter.
- **Unlocks:** T-B11, T-B12 (discussion).

## Part 6 — Metrics

### #29 LPIPS
R. Zhang et al., *The Unreasonable Effectiveness of Deep Features as a Perceptual Metric*, CVPR 2018. [arXiv 1801.03924](https://arxiv.org/abs/1801.03924)
- **Why:** one of the three reconstruction metrics in Phase A.
- **Focus:** §3 (learned weighting of deep features) and Fig. 1.
- **Take away:** lower is better. **AlexNet and VGG variants give different numbers.** We report `lpips_net` (default alex) with every value.
- **Unlocks:** T-A05, T-A07.

### #30 Boundary IoU
B. Cheng et al., *Boundary IoU: Improving Object-Centric Image Segmentation Evaluation*, CVPR 2021. [arXiv 2103.16562](https://arxiv.org/abs/2103.16562)
- **Why:** mBIoU in our tables. It measures boundary quality, where plain IoU is dominated by the object's interior.
- **Focus:** §3–§4 (definition: IoU restricted to a band of width d around each contour; d = 2% of the image diagonal).
- **Take away:** why a method can have high IoU but low BIoU (blobby edges).
- **Unlocks:** T-E02.

---

## Optional / skim (pass 1 unless you need them)

| Paper | Venue | Link | Why you might read it |
|---|---|---|---|
| Zwicker et al., *EWA Splatting* | IEEE TVCG 2002 | [PDF](https://www.cs.umd.edu/~zwicker/publications/EWASplatting-TVCG02.pdf) | longer journal version of #5 |
| Yu et al., *Mip-Splatting* | CVPR 2024 | [2311.16493](https://arxiv.org/abs/2311.16493) | aliasing when zooming; why we keep `rasterize_mode="classic"` for SAGA compatibility |
| Fan et al., *LightGaussian* | NeurIPS 2024 | [2311.17245](https://arxiv.org/abs/2311.17245) | pruning/compression if web assets are too big (T-S02) |
| Ryali et al., *Hiera* | ICML 2023 | [2306.00989](https://arxiv.org/abs/2306.00989) | SAM 2's image encoder |
| Cheng & Schwing, *XMem* | ECCV 2022 | [2207.07115](https://arxiv.org/abs/2207.07115) | memory-based video segmentation that SAM 2's memory resembles |
| Cen et al., *Segment Anything in 3D with NeRFs* (SA3D) | NeurIPS 2023 | [2304.12308v1](https://arxiv.org/abs/2304.12308v1) | SAGA's predecessor (cite the v1 link; the newer version is an IJCV extension) |
| Zhou et al., *Feature 3DGS* | CVPR 2024 | [2312.03203](https://arxiv.org/abs/2312.03203) | distilling high-dim features into Gaussians |
| Wu et al., *OpenGaussian* | NeurIPS 2024 | [2406.02058](https://arxiv.org/abs/2406.02058) | point-level open vocabulary, 3D evaluation |
| Shen et al., *FlashSplat* | ECCV 2024 | [2409.08270](https://arxiv.org/abs/2409.08270) | optimal 2D→3D mask lifting without training |
| Choi et al., *Click-Gaussian* | ECCV 2024 | [2407.11793](https://arxiv.org/abs/2407.11793) | interactive click segmentation at two granularities |
| Ying et al., *OmniSeg3D* | CVPR 2024 | [2311.11666](https://arxiv.org/abs/2311.11666) | hierarchical contrastive 3D segmentation |
| Carion et al., *SAM 3: Segment Anything with Concepts* | ICLR 2026 | [2511.16719](https://arxiv.org/abs/2511.16719) | text-promptable video segmentation; a "future work" direction |
| Wang et al., *SSIM* | IEEE TIP 2004 | [PDF](https://ece.uwaterloo.ca/~z70wang/publications/ssim.pdf) | the SSIM metric |
| Campello et al., *HDBSCAN* | PAKDD 2013 | [DOI](https://doi.org/10.1007/978-3-642-37456-2_14) | the clustering used by SAGA's text query |
| Kim et al., *Dr. Splat* | CVPR 2025 | [2502.16652](https://arxiv.org/abs/2502.16652) | 2025 advance: register CLIP embeddings directly to Gaussians |
| Li et al., *LangSplatV2* | NeurIPS 2025 | [2507.07136](https://arxiv.org/abs/2507.07136) | 2025 advance: high-dim language Gaussians at 450+ FPS |
| Cheng et al., *Occam's LGS* | BMVC 2025 | [2412.01807](https://arxiv.org/abs/2412.01807) | 2025 advance: training-free language Gaussians |
| Zhu et al., *Unified-Lift* | CVPR 2025 | [2503.14029](https://arxiv.org/abs/2503.14029) | 2025 advance: end-to-end 2D→3D segmentation lifting |

---

## Citation corrections for your report

- **SAGA** (#23) is by **Cen, Fang, Yang, Xie, Zhang, Shen, Tian**, AAAI 2025. The author list in `proposal-extra.md` ref [5] is wrong.
- **SAM 2** was published at **ICLR 2025**; the proposals cite only the arXiv preprint.
- **Kobayashi et al.** (#18) is titled *Decomposing NeRF for Editing via Feature Field Distillation*. "Distilled Feature Fields" is only its nickname.
- **Gaga** (#26) appeared in **TMLR 2026**.
