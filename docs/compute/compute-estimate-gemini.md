# Compute and Storage Feasibility Assessment: PromptSplat (Option 1)

**Target Hardware:**
- **Lab PC (Compute Server):** Intel Core i9, NVIDIA RTX A4000 (16 GB VRAM GDDR6 with ECC), 1 TB NVMe SSD.
- **Client Laptop (Access Machine):** Intel Core i5 6th Gen, 256 GB SSD (connected via SSH).

**Project Reference:** `docs/fyp-options/option-1-language-grounded-3dgs.md`

---

## 1. Executive Summary

- **Feasibility Verdict:** **100% Computationally Feasible.**
- **GPU VRAM Fit:** The 16 GB VRAM on the NVIDIA RTX A4000 is an ideal match for the proposed pipeline, provided the sequential execution and downsampling guardrails specified in the proposal are adhered to.
- **Storage Footprint:** Total disk space across 4 scenes (1 public baseline + 3 custom datasets), checkpoints, foundation model weights, and environments will occupy **~60–100 GB** on the Lab PC's 1 TB SSD (<10% total capacity).
- **Client Laptop Load:** Minimal. All preprocessing, training, and API query inference occur on the Lab PC; the laptop only handles SSH, code editing, and browser-based WebGL/WebGPU viewing.

---

## 2. VRAM Breakdown Across Pipeline Stages

The pipeline runs sequentially stage-by-stage. Each stage saves its outputs to disk and clears GPU memory before the next stage starts.

| Stage | Component / Task | Framework / Model | Expected Peak VRAM | Feasibility on 16 GB A4000 | Notes & Mitigations |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Stage 1** | Structure from Motion (SfM) | COLMAP | ~2–6 GB | **Safe** | Primary load is on CPU and system RAM. CUDA is only used for SIFT feature matching. |
| **Stage 2** | Base 3DGS Scene Training | Inria 3DGS / `diff-gaussian-rasterization` | 8–12 GB | **Safe** | Standard 3DGS training on 60–120 frames at 720p/1080p produces ~1–2.5M Gaussians. Peaks under 12 GB. |
| **Stage 3A** | 2D Baseline Pseudo-labeling | SAM (`vit_h` or `vit_b`) | 6–10 GB | **Safe** | Batch size = 1 inference. Can reduce `points_per_batch` if using automatic mask generation. |
| **Stage 3B** | Video Mask Propagation | SAM 2 (`sam2_hiera_l` / `b+`) | 6–10 GB | **Safe** | Sequential video predictor tracking over 60–120 frames. Set `video_storage_device="cpu"` to prevent frame-cache creep. |
| **Stage 4** | Semantic Feature Extraction | CLIP (ViT-B/32 or ViT-L/14) | 4–6 GB | **Safe** | Forward-pass encoding on cropped mask proposals. Fits easily. |
| **Stage 5** | 3D Affinity Field Optimization | SAGA (`train_contrastive_feature.py`) | **10–14 GB** | **Safe (with tuning)** | **Critical Bottleneck Stage.** Requires downsampling (`--downsample 8` to start, then `4`). Limit `--num_sampled_rays 1000` to cap VRAM to ~12 GB. |
| **Stage 6** | Interactive Query Service | FastAPI + SAGA Query + CLIP text | 2–4 GB | **Safe** | CLIP text encoding + dot-product selection over precomputed Gaussian features runs in <200 ms. |

---

## 3. Storage and Disk Budget Analysis

All training artifacts, raw videos, and environment packages remain on the **Lab PC (1 TB SSD)**.

| Category | Components & Checkpoints | Estimated Size (4 Scenes Total) |
| :--- | :--- | :--- |
| **Foundation Model Weights** | SAM 2 (`sam2_hiera_large.pt` ~900 MB), SAM ViT-H (~2.5 GB), CLIP ViT-B/32 & L/14 (~1.5 GB) | ~5 – 8 GB (one-off) |
| **Environments & Dependencies** | PyTorch, CUDA toolkits, rasterizer extensions, Node.js, Python venvs | ~15 – 25 GB |
| **Raw Footage & COLMAP Data** | 1080p MP4s, extracted PNGs (60–120 per scene), sparse point clouds, database files | ~10 – 15 GB (~2.5–4 GB / scene) |
| **Base 3DGS Models** | Trained PLY files (1–3M Gaussians), checkpoints at 7k and 30k iterations | ~5 – 8 GB (~1.5–2 GB / scene) |
| **2D Masks & Feature Tensors** | Extracted SAM/SAM 2 binary masks, precomputed CLIP feature vectors | ~15 – 30 GB (~4–7 GB / scene) |
| **SAGA Affinity Checkpoints** | Optimized per-Gaussian low-dimensional affinity vectors | ~3 – 5 GB (~0.8–1.2 GB / scene) |
| **Evaluation Data & Annotations** | Held-out 2D ground truth masks, metric logs, cache | < 1 GB |
| **Total Estimated Disk Usage** | | **~60 – 100 GB** |
| **Available Free Buffer** | (On 1 TB SSD) | **> 850 GB** |

---

## 4. SSH & Dual-Machine Workflow Architecture

```
┌────────────────────────────────────────────────────────┐
│                   Lab PC (Workstation)                 │
│  - Intel Core i9, 1 TB SSD, RTX A4000 (16 GB VRAM)     │
│  - Runs COLMAP, 3DGS training, SAM 2, SAGA, and CLIP   │
│  - Hosts FastAPI backend (port 8000)                   │
│  - Serves Next.js / static web viewer assets           │
└───────────────────────────▲────────────────────────────┘
                            │ SSH Remote Forwarding
                            │ ssh -L 3000:localhost:3000 -L 8000:localhost:8000 ...
┌───────────────────────────▼────────────────────────────┘
│                   Client Laptop                        │
│  - Intel Core i5 6th Gen, 256 GB SSD                   │
│  - VS Code Remote - SSH (code editing & terminal)      │
│  - Chrome / Firefox: Three.js / GaussianSplats3D viewer│
│    (Renders client-side WebGL at 30+ FPS)              │
└────────────────────────────────────────────────────────┘
```

### Laptop Considerations (Core i5 6th Gen, 256 GB SSD)
1. **Zero Deep Learning Workload:** The laptop acts strictly as a thin client. No PyTorch, CUDA, or COLMAP builds touch the laptop's internal disk.
2. **WebGL / 3D Rendering Feasibility:** Rendering 3D Gaussian Splats in the browser using `GaussianSplats3D` is bound by client GPU/iGPU fill rate. A 6th Gen Intel HD Graphics iGPU can render ~500k to 1M splats at 30+ FPS. Using `SuperSplat` to prune background/unnecessary Gaussians prior to web export guarantees smooth interactive orbit and selection.

---

## 5. Technical Safeguards for 16 GB VRAM Execution

To eliminate Out-of-Memory (OOM) risks during development:

1. **Downsample Initial Inputs:**
   - Execute SAGA mask extraction and feature training with `--downsample 8` first.
   - Only promote to `--downsample 4` once memory profiling with `nvidia-smi` confirms peak usage remains $\le 13.5\text{ GB}$.
2. **Cap SAGA Sampled Rays:**
   - In `train_contrastive_feature.py`, pass `--num_sampled_rays 1000` (or lower) to prevent batch expansion from overflowing memory.
3. **SAM 2 Memory Guard:**
   - When calling SAM 2's `build_sam2_video_predictor`, specify `video_storage_device="cpu"` to keep uncompressed video frame buffers in system RAM rather than VRAM.
4. **Enforce Sequential Execution:**
   - Never run multiple training scripts concurrently on the single A4000.
   - Separate data generation, 3DGS training, mask propagation, and feature training into distinct bash pipeline steps.
