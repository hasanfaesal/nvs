# 02 — Glossary

Short, precise definitions of every term used in the spec and the task cards. Coding models: if a card uses a term you are unsure about, look it up here **before** guessing.

## A. Cameras and geometry

| Term | Meaning |
|---|---|
| **Intrinsics (K)** | 3×3 matrix `[[fx,0,cx],[0,fy,cy],[0,0,1]]`. fx, fy are focal lengths in pixels; (cx, cy) is the principal point. They change when you resize an image: multiply all four by the scale factor. |
| **Extrinsics (R, t)** | The camera pose, as the rotation R (3×3) and translation t (3) that map a world point into camera coordinates: `X_cam = R·X_world + t`. |
| **World→camera / camera→world** | World→camera is `[[R,t],[0,0,0,1]]`; its inverse is camera→world. gsplat's `viewmats` are world→camera. three.js `camera.matrixWorld` is camera→world. |
| **Camera center** | Where the camera sits in world coordinates: `C = −Rᵀt`. |
| **OpenCV convention** | Camera axes: x right, **y down, z forward**. Used by COLMAP, gsplat and SAGA. |
| **OpenGL convention** | Camera axes: x right, **y up, looks along −z**. Used by three.js. Converting between the two flips y and z (C10). |
| **Camera model (COLMAP)** | `PINHOLE` = fx, fy, cx, cy only. `OPENCV` adds lens distortion. We estimate `OPENCV`, then **undistort** the images so the rest of the pipeline sees `PINHOLE`. |
| **Undistortion** | Resampling images so straight lines are straight (distortion removed). COLMAP's `image_undistorter` does it. |
| **Structure-from-Motion (SfM)** | Estimating every camera pose plus a sparse 3D point cloud from overlapping photos. COLMAP is the SfM tool. |
| **Keypoint / descriptor** | A distinctive image spot and the vector describing it (SIFT, 128-D). Matching descriptors across frames produces correspondences. |
| **Sequential / exhaustive matching** | Sequential matches each frame with its neighbours (fast; right for video). Exhaustive matches every pair (slow; right for unordered photos). |
| **Registered image** | A frame for which SfM found a pose. Few registered frames = failed capture. |
| **Bundle adjustment (BA)** | Joint optimization of all camera poses and 3D points so that reprojection error is minimal. |
| **Sparse point cloud** | COLMAP's `points3D`: triangulated keypoints. It initializes 3DGS. |
| **Homogeneous coordinates** | Appending a 1 to a point (`[x,y,z,1]`) so rotation and translation become a single 4×4 matrix multiply. |
| **Column-major** | How three.js stores `Matrix4.elements`: the first 4 numbers are the first *column*. Reshape to 4×4, then **transpose**, to get the usual row-major matrix. |

## B. 3D Gaussian Splatting

| Term | Meaning |
|---|---|
| **Gaussian / splat / primitive** | One 3D ellipsoid "blob". A scene has ~0.3–3 million of them. |
| **Mean (position)** | Its center xyz. PLY fields `x,y,z`. |
| **Scale** | Its size along 3 axes. Stored as **log** values (`scale_0..2`); the real size is `exp(scale)`. |
| **Rotation** | Unit quaternion (w,x,y,z), PLY fields `rot_0..3`, stored as w first. It may be unnormalized, so normalize before use. |
| **Covariance** | Shape matrix `Σ = R S Sᵀ Rᵀ` built from rotation and scale. |
| **Opacity** | How solid the Gaussian is. Stored as a **logit**; the real value is `sigmoid(opacity)` ∈ (0,1). |
| **Spherical harmonics (SH)** | View-dependent colour coefficients. Degree 3 = 16 coefficients per colour channel. `f_dc_0..2` = degree-0 ("DC") term; `f_rest_0..44` = the other 15 × 3 values, stored channel-major. RGB of the DC term = `0.5 + 0.28209479 · f_dc`. |
| **Alpha compositing** | A pixel's colour = front-to-back weighted sum `Σ Tᵢ αᵢ cᵢ`, with `Tᵢ = Π_{j<i}(1−α_j)`. The same sum renders depth or any feature vector. |
| **Rasterization** | Projecting all Gaussians to 2D ellipses, sorting them by depth per 16×16 tile, and compositing. gsplat's `rasterization()` does it on the GPU. |
| **Expected depth (ED)** | `Σ wᵢ zᵢ / Σ wᵢ`: the average depth of the Gaussians hit by a pixel. gsplat `render_mode="RGB+ED"`. |
| **Densification** | Adding Gaussians where the image isn't explained well (clone/split) and removing useless ones (prune). This is what grows VRAM. |
| **MCMC strategy** | gsplat densification from the 3DGS-MCMC paper: keeps a **fixed budget** (`cap_max`) and *relocates* dead Gaussians instead of cloning or splitting. |
| **Floaters** | Stray blobs in empty space, usually from poorly covered regions. |
| **PLY** | The file format for Gaussians: a header plus one binary row per Gaussian. Row order matters to us (C11). |
| **SPZ** | Niantic's compressed splat format (~10× smaller). A stretch item (T-S02). |
| **LoD (level of detail)** | Spark can merge splats into a hierarchy. **We disable it**, because it breaks the "splat i = Gaussian i" mapping. |
| **Held-out / test view** | A frame never used for training; used only to measure quality. |
| **`data_factor`** | gsplat's image downscale factor. We use 1 and pre-resize phone frames to ≤ 1600 px instead. |
| **`normalize_world_space`** | A gsplat option that re-centers and rotates the scene. **Must be `False`**, or the PLY no longer lines up with COLMAP cameras and SAGA. |

## C. Segmentation and tracking

| Term | Meaning |
|---|---|
| **Mask** | A per-pixel true/false image marking one region. We store stacks `[M, h, w]` per frame. |
| **SAM** | Segment Anything (v1). Given a point/box prompt, predicts masks. |
| **SAM 2 / 2.1** | Successor to SAM that also works on video: it keeps a **memory** of previous frames to follow an object over time. |
| **AMG (automatic mask generator)** | "Segment everything": prompt SAM with a grid of points, keep masks with high predicted IoU and stability, remove duplicates with NMS. |
| **`points_per_side`** | Grid density of the AMG (32 → 32×32 = 1,024 prompts). |
| **Predicted IoU / stability score** | SAM's confidence in a mask / how little the mask changes when the threshold wiggles. Low values are filtered out. |
| **NMS (non-maximum suppression)** | Drop a mask if it overlaps a better one too much (`box_nms_thresh`). |
| **Granularity / level** | The same point can mean a part or a whole. SAM outputs 3 masks per prompt (whole / part / sub-part). AutoSeg-SAM2 calls these "levels" (large, middle, small). |
| **Prompt** | What you give SAM: points, a box, or an existing mask. |
| **Propagation** | SAM 2 carrying a mask from one frame to the next using its memory. It can go forward or **reverse**. |
| **Keyframe** | A frame where new objects are detected (AMG) before being propagated. |
| **Track / track ID** | One object followed through many frames under one ID. |
| **K / `--detect_stride`** | How often (in frames) AutoSeg-SAM2 checks for new objects. Our ablation uses K ∈ {5, 10, 20}. |
| **Drift** | A tracked mask slowly sliding onto the wrong object. Worse with large motion between frames. |
| **Pseudo-label** | An automatically generated label (e.g. a SAM mask) used as training supervision. Not ground truth. |

## D. Language (CLIP)

| Term | Meaning |
|---|---|
| **CLIP** | A model that maps images and text into the same 512-D space, where matching pairs have high cosine similarity. We use OpenCLIP ViT-B/16 (LAION-2B). |
| **Embedding** | The vector a model outputs for an input. |
| **Cosine similarity** | `a·b / (‖a‖‖b‖)` ∈ [−1, 1]. |
| **Prompt template / ensembling** | Embedding "a photo of a {query}", "a close-up photo of a {query}", … (80 templates) and averaging. It is more robust than the bare word. |
| **Canonical negatives** | Generic phrases ("object", "things", "stuff", "texture"). A mask's text score is how much it prefers the query over each of them (softmax with temperature 10, minimum over negatives). |
| **Open-vocabulary** | Querying with any text, not a fixed list of classes. |

## E. SAGA

| Term | Meaning |
|---|---|
| **Affinity feature** | A learned 32-D vector per Gaussian. Gaussians of the same object at the same scale end up with similar features. |
| **Contrastive loss** | Pull features of pixel pairs inside the same mask together (positives) and push others apart (negatives). |
| **Mask scale** | The 3D physical size of a mask: the std of its back-projected pixels using rendered depth (`get_scale.py`). |
| **Scale gate** | A tiny network `Sigmoid(Linear(1→32))` that turns a scale into 32 weights. Multiplying a feature by the gate focuses it on that granularity. |
| **Quantile transform (`q_trans`)** | Maps raw 3D scales to [0,1] by their rank among all training masks. The gate takes this value. The click slider sets it directly. |
| **Feature smoothing** | SAGA saves each Gaussian's feature as the average over its 16 nearest neighbours (KNN), which reduces noise. |
| **Anchors** | A random 1% of Gaussians, used to build each mask's "identifier". |
| **Mask identifier** | A true/false vector over anchors: which anchors agree with this mask's feature. Masks with similar identifiers are the same object. |
| **HDBSCAN** | Density-based clustering. It groups all training masks (across all frames) into objects. Label −1 = noise. |
| **Query feature** | The 32-D feature and scale used to score every Gaussian (from a clicked pixel, or from the best mask of a text-matched cluster). |
| **Threshold** | Score cut-off for "selected" (C13). |

## F. Metrics and statistics

| Term | Meaning |
|---|---|
| **PSNR** | Peak signal-to-noise ratio between rendered and real test images (dB, higher = better). |
| **SSIM** | Structural similarity (0–1, higher = better). |
| **LPIPS** | Learned perceptual distance (lower = better). AlexNet and VGG versions differ, so we always report which one. |
| **IoU** | Intersection-over-union of predicted and GT masks: `|P∩G| / |P∪G|`. |
| **mIoU** | Mean IoU over all (test frame, query) pairs of a scene. |
| **BIoU / mBIoU** | Boundary IoU: IoU computed only in a thin band around contours (2% of the image diagonal). Measures edge quality. |
| **Localization accuracy** | Fraction of queries where the highest-scoring pixel (after a 30×30 mean filter) lies inside a GT box of that object. |
| **MRC (mask reprojection consistency)** | Our consistency metric. Warp each mask from frame i into frame j using rendered depth and camera poses, and IoU it with the best-matching mask in j. Average over masks and frame pairs. Higher = labels agree across views. Definition in `09` §5.4. |
| **Seed** | A random-number starting point. Different seeds show training variance. We run 3. |
| **mean ± std** | Average and standard deviation across seeds (or across scenes). |
| **Wilcoxon signed-rank test** | A paired, non-parametric test: is variant A's per-query IoU consistently higher than B's? p < 0.05 means "unlikely by chance". |

## G. Project terms

| Term | Meaning |
|---|---|
| **Scene** | One captured place, e.g. `figurines`. Folder `scenes/<scene_id>/` (C3). |
| **Variant** | One mask source trained into SAGA: `sam` (V1), `sam2_frame` (V2), `sam2_track_k10` (V3), plus the ablation and stretch ids (C2). |
| **Variant dir** | `scenes/<id>/variants/<variant>/`: a SAGA-style source folder holding only the **train** images (symlinks) plus that variant's masks. |
| **`split.json`** | The train/test lists (C4). |
| **Manifest** | `scenes/<id>/web/manifest.json`: what the web app needs to show a scene (C5). |
| **Index invariant** | Row i means the same Gaussian in every file and in every API score array (C11). |
| **`xyz_hash`** | sha1 of the first 1,000 positions, used to detect order mismatches (C11). |
| **Fixture scene** | `scenes/_fixture`: a tiny synthetic scene so the web app and server run on the laptop without a GPU. |
| **Fake engine** | The server's CPU stand-in for GPU queries (`PS_FAKE=1`). It returns plausible selections for UI development. |
| **Task card** | One unit of work in `docs/spec/tasks/`. One session = one card. |
| **Tier [H] / [S] / [M]** | Who does a card: [H] you (human), [S] small model (e.g. Claude Haiku), [M] stronger model (Sonnet/Opus) or small model plus review. |
| **Laptop check / lab check** | The two verification steps in a card: CPU tests the model runs on the laptop / GPU commands you run on the lab PC and paste back. |
| **`run_stage`** | Our helper that runs a subprocess and logs time + peak VRAM (C15). |
| **FORK / PIP / COPY / WRAP / GENERATOR / NEW** | Where a file's code comes from (`05-codebase-map.md` §1). |
| **`promptsplat` branch** | The branch in each fork where our patches live. |

## H. Infrastructure

| Term | Meaning |
|---|---|
| **WSL2** | Windows Subsystem for Linux: a real Ubuntu VM on the lab PC, with GPU access through the Windows NVIDIA driver. |
| **`.wslconfig`** | File in the Windows user folder that sets WSL2's RAM/CPU/swap limits. |
| **conda env** | An isolated Python + packages installation (lab uses miniforge). Ours: `ps` (main), `colmap`, optionally `saga`. |
| **uv** | A fast Python package manager. The laptop uses it for the CPU-only `.venv`. |
| **Tailscale / `tailscale serve`** | Private network between your devices. `tailscale serve` exposes the lab server (port 8000) only to your tailnet, over HTTPS. |
| **tmux** | Keeps long jobs running after SSH disconnects. **Always run GPU jobs inside tmux.** |
| **git submodule** | A pinned git repo inside our repo (`third_party/*`). The parent repo stores only its commit SHA. |
| **SPA** | Single-page application: all pages are rendered in the browser; the server only serves files and JSON. |
| **Nuxt / Nuxt UI** | Vue framework (file-based pages) / its component library (`UButton`, `UCard`, `USlider`, …). |
| **Spark** | Three.js library that renders Gaussian splats (`SparkRenderer`, `SplatMesh`). |
| **FastAPI** | Python web framework for the JSON API and static files. |
