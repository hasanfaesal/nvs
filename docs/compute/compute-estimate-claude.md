# Compute & Storage Feasibility Analysis: PromptSplat on NVIDIA RTX A4000 (16 GB VRAM)

**Target Project:** Option 1 — PromptSplat: Language-Grounded 3DGS Explorer  
**Evaluated Hardware:** 
- **Lab PC (Compute Server):** Intel Core i9, 1 TB NVMe SSD, single NVIDIA RTX A4000 (16 GB GDDR6 ECC VRAM, Ampere GA104, Compute Capability 8.6)
- **Local Machine (Client):** Intel Core i5 (6th Gen), 256 GB SSD (used strictly via SSH / Web Client)
- **Analysis Date:** September 2026

---

## Executive Summary & Final Verdict

### **Verdict: FEASIBLE with disciplined memory configuration**

The project is technically and computationally viable on a single 16 GB RTX A4000. Because the entire pipeline (COLMAP $\rightarrow$ 3DGS $\rightarrow$ SAM/SAM 2 $\rightarrow$ CLIP $\rightarrow$ SAGA Feature Training) runs in **sequential stages**, you never need to load multiple large models into VRAM simultaneously.

The primary constraint is peak VRAM during:
1. Base 3DGS Gaussian densification (cloning/splitting).
2. SAGA contrastive affinity feature training.

Both fit comfortably within 16 GB when using **downsample factor 8** (or factor 4 on small scenes) with **60–80 training images**. Storage requirements across models, environments, and multi-scene runs are estimated at **~50–80 GB**, consuming less than **10%** of the 1 TB SSD.

---

## 1. Hardware Profile: NVIDIA RTX A4000

| Specification | Parameter | Project Impact |
|:---|:---|:---|
| **GPU Architecture** | Ampere (GA104) | Full native support for PyTorch 2.x, CUDA 11.8/12.x, and custom CUDA rasterizers |
| **Compute Capability** | 8.6 | Fully compatible with `diff-gaussian-rasterization`, `simple-knn`, and `gsplat` |
| **CUDA Cores** | 6,144 | Fast rasterization and feature backpropagation |
| **Tensor Cores** | 192 (3rd Gen) | FP16/BF16 accelerated matrix multiplications for ViT backbones |
| **VRAM** | 16 GB GDDR6 with ECC | Safe ceiling for downsampled scenes; requires avoiding full uncompressed 4K runs |
| **Memory Bandwidth** | 448 GB/s | Fast splat sorting and gradient accumulation |
| **TDP** | 140 W | Single-slot workstation card, thermally stable under sustained training |

---

## 2. Component-by-Component VRAM & Compute Analysis

Because each stage is run independently, peak memory is non-additive across stages.

```
[ Stage 1: COLMAP ] ──> [ Stage 2: Base 3DGS ] ──> [ Stage 3: Masking (SAM/SAM2) ] ──> [ Stage 4: SAGA Features ] ──> [ Stage 5: Inference / API ]
    (~2-4 GB VRAM)          (~8-12 GB VRAM)              (~4-8 GB VRAM)                     (~8-12 GB VRAM)               (~3-5 GB VRAM)
```

### 2.1 Stage 1 — Structure from Motion (COLMAP)
- **Workload:** Feature extraction (SIFT), feature matching, incremental mapping / bundle adjustment.
- **GPU Role:** SIFT feature extraction and matching are GPU-accelerated. Bundle adjustment uses CPU (Ceres Solver).
- **VRAM Footprint:** **2–4 GB**.
- **CPU/RAM Usage:** Core i9 easily handles 60–120 images in 10–30 minutes. System RAM usage stays under 16 GB.
- **Feasibility:** 100% safe.

### 2.2 Stage 2 — Base 3D Gaussian Splatting Training (30,000 iterations)
- **Workload:** Differentiable tile-based rasterization, gradient-guided densification (splitting & cloning), opacity resets.
- **VRAM Profile:**
  - *Warmup (0–1,000 iters):* ~3–5 GB.
  - *Densification Phase (1,000–15,000 iters):* Peaks as Gaussian count reaches 1.0M–2.5M primitives.
  - *Downsample factor 8 (e.g., ~480x270 to ~540x360):* **6–9 GB peak VRAM**.
  - *Downsample factor 4 (e.g., ~960x540):* **10–13.5 GB peak VRAM**.
  - *Full resolution (1080p, no downsampling):* Can exceed 16 GB during densification spikes.
- **Mitigation Levers for 16 GB:**
  - Set `--densify_grad_threshold 0.0003` to `0.0004` (slightly higher threshold prevents runaway primitive generation).
  - Cap densification iterations via `--densify_until_iter 15000`.
  - Pass `--test_iterations -1` to avoid memory spikes caused by evaluation renders mid-training.
  - If necessary, switch to the `gsplat` backend (reduces rasterizer footprint by 25–30%).

### 2.3 Stage 3A — Original SAGA SAM Extraction (2D Baseline)
- **Workload:** `extract_segment_everything_masks.py` running ViT-H / ViT-L automatic mask generator across training images.
- **VRAM Footprint:**
  - `sam_vit_h` (Huge, 636M params): **4–6 GB peak** (FP16 inference).
  - `sam_vit_b` (Base, 91M params): **1.5–2.5 GB peak**.
- **Mitigation Levers:**
  - Use SAGA's built-in `--downsample` argument.
  - Reduce `points_per_batch` from 64 to 32 or 16 if processing crowded scenes.

### 2.4 Stage 3B — Proposed SAM 2 Video Propagation (PromptSplat Core)
- **Workload:** SAM 2 video predictor keeping past frame embeddings and memory conditioning in a streaming memory bank.
- **VRAM Footprint (for 60–120 frames):**
  - `sam2_hiera_large` (~224M params): **6–9 GB peak VRAM** in `bfloat16`/`float16`.
  - `sam2_hiera_base_plus` (~80M params): **3.5–5 GB peak VRAM** (recommended default).
  - `sam2_hiera_small` (~46M params): **~2.5 GB peak VRAM**.
- **Assessment:** For short sequences (60–120 frames downsampled), SAM 2 video memory stays within 6–8 GB. It does not threaten the 16 GB ceiling.

### 2.5 Stage 4 — CLIP Feature Extraction
- **Workload:** Pre-extracting region/mask CLIP embeddings for text matching.
- **VRAM Footprint:**
  - `ViT-L/14`: **1.5–2.5 GB**.
  - `ViT-B/32`: **< 1.0 GB**.
- **Assessment:** Negligible load.

### 2.6 Stage 5 — SAGA Contrastive Feature Training (10,000 iterations)
- **Workload:** Optimizing 3D Gaussian affinity vectors with contrastive loss over sampled rays and 2D pseudo-labels.
- **VRAM Footprint:** **8–12 GB peak** at downsample factor 8.
- **Mitigation Levers:**
  - Lower `num_sampled_rays` if memory approaches 14 GB.
  - Clear PyTorch memory cache before running (`torch.cuda.empty_cache()`).

### 2.7 Stage 6 — Runtime Query Service & Browser Viewer
- **Backend (FastAPI):** Holds CLIP text encoder in VRAM (~1.5 GB) and queries precomputed feature tensors.
- **Rendering:** Rendering a pre-trained splat of 1M–2M Gaussians takes **< 4 GB VRAM**.
- **Browser:** The evaluator's client machine renders the `.ply` or compressed `.spz` splat using WebGL / WebGPU via `GaussianSplats3D`.

---

## 3. Storage Footprint & 1 TB SSD Budget

Detailed projection for software, model checkpoints, raw datasets, intermediate representations, and checkpoints on the Lab PC's 1 TB SSD:

### 3.1 Static Components (Downloaded / Installed Once)

| Item | Description | Size |
|:---|:---|:---|
| **Conda / Python Environments** | PyTorch 2.x + CUDA 11.8/12.1 + SAGA + SAM2 dependencies | 8–12 GB |
| **SAM Checkpoints** | `sam_vit_h.pth` (~2.5 GB) + `sam_vit_b.pth` (~375 MB) | ~2.9 GB |
| **SAM 2 Checkpoints** | `sam2_hiera_large.pt` (~898 MB) + `sam2_hiera_b+.pt` (~323 MB) | ~1.3 GB |
| **CLIP Models** | OpenAI / OpenCLIP ViT-B/32 & ViT-L/14 cached weights | ~1.5 GB |
| **Frontend / Web Stack** | Node.js, `node_modules` for Next.js/React + Three.js | ~1.0 GB |
| **Subtotal (Static Infrastructure)** | | **~15–19 GB** |

### 3.2 Per-Scene Storage Breakdown

For each scene captured (1080p video, 60–120 extracted frames):

| Component | Format / Content | Size per Scene |
|:---|:---|:---|
| **Raw Input Video** | MP4 (1080p, 1–2 minutes) | 0.3–0.8 GB |
| **Extracted Frames** | PNG / JPG (original + downsampled x4, x8) | 0.2–0.5 GB |
| **COLMAP Project** | Database, sparse points3D, images.bin, cameras.bin | 0.05–0.1 GB |
| **Base 3DGS Model** | Checkpoint iterations (7k, 30k) + final uncompressed `.ply` | 0.4–1.2 GB |
| **2D Masks (SAM Baseline)** | Per-frame binary masks & metadata | 0.2–0.5 GB |
| **2D Masks (SAM 2 Propagated)** | Per-frame tracked masks & instance ID manifests | 0.2–0.5 GB |
| **CLIP Embeddings Cache** | Feature tensors per mask/region | 0.1–0.3 GB |
| **SAGA Feature Checkpoint** | Per-Gaussian affinity feature vectors (`.pt`) | 0.2–0.6 GB |
| **Web-Optimized Assets** | Quantized / pruned `.ply` or `.spz` for Three.js viewer | 0.02–0.1 GB |
| **Subtotal (Per Scene)** | | **~1.5–4.5 GB** |

### 3.3 Full Project Total (Semester Lifecycle)

| Category | Calculation | Estimated Size |
|:---|:---|:---|
| Static Infrastructure | Environments, repos, foundation checkpoints | ~18 GB |
| Public Benchmark Scenes | 2 LERF / 3D-OVS scenes for validation | ~8 GB |
| Custom Real-World Scenes | 3 custom scenes (tabletop, shelf, room corner) | ~12 GB |
| Ablation Checkpoints | View counts (25, 50, 100) & Downsampling (4, 8) variants | ~20 GB |
| Evaluation Data & Logs | Ground-truth annotations, CSV metrics, test renders | ~2 GB |
| Miscellaneous / Caches | Pip cache, Conda package tarballs, temp files | ~10 GB |
| **TOTAL PROJECT FOOTPRINT** | | **~70 GB** |
| **Worst-Case Ceiling (no pruning of temp files)** | | **~100 GB** |
| **Available Space Remaining on 1 TB SSD** | | **~900 GB (90% free)** |

---

## 4. Compute Time Estimates (A4000 Workstation)

Estimated wall-clock time per scene pipeline:

| Step | Operation | Duration (60–100 frames) |
|:---|:---|:---|
| 1 | Frame Extraction & Preprocessing | 1–3 minutes |
| 2 | COLMAP Feature Matching & Sparse Reconstruction | 15–35 minutes |
| 3 | Base 3DGS Training (30k iterations) | 25–45 minutes |
| 4 | SAM / SAM 2 Mask Generation & Propagation | 10–20 minutes |
| 5 | Mask Scale Estimation & CLIP Feature Extraction | 5–10 minutes |
| 6 | SAGA Contrastive Feature Training (10k iterations) | 15–30 minutes |
| **Total Pipeline per Scene** | | **~1.2 – 2.5 hours** |

*Semester Experiment Budget:*
Running 4 primary scenes $\times$ 2 methods (SAM vs. SAM 2) + 6 ablation runs $\approx$ 14 complete runs $\approx$ **25–40 total GPU-hours**. This is well within semester boundaries and leaves ample room for failed attempts or hyperparameter sweeps.

---

## 5. Workflow Architecture: Laptop vs. Lab PC

```
┌─────────────────────────────────────────────────────────┐
│                    STUDENT LAPTOP                       │
│           (Core i5 6th Gen, 256 GB SSD, No GPU)         │
│                                                         │
│  - Code editing (VS Code via Remote - SSH)              │
│  - Git version control                                  │
│  - Terminal commands (tmux session management)          │
│  - Browser preview (via SSH port forwarding: localhost) │
│  - Report writing & documentation                       │
└───────────────────────────┬─────────────────────────────┘
                            │ SSH (Port 22)
                            │ Port Forwarding (8000 / 3000)
┌───────────────────────────▼─────────────────────────────┐
│                    LAB WORKSTATION                      │
│        (Core i9, 1 TB NVMe SSD, NVIDIA RTX A4000 16GB)  │
│                                                         │
│  - COLMAP SfM                                           │
│  - 3DGS & SAGA Feature Training (CUDA)                  │
│  - SAM / SAM 2 Mask Propagation                         │
│  - FastAPI Query Server                                 │
│  - Node / Next.js Web Server                            │
└─────────────────────────────────────────────────────────┘
```

### Essential Operational Practices for Remote SSH:
1. **Always use `tmux` or `screen`:** Deep learning jobs will terminate if the SSH connection drops. Run all training inside detached `tmux` sessions.
2. **Never attempt local ML execution on the laptop:** The 6th Gen i5 lacks CUDA and cannot run 3DGS or SAM training.
3. **Port forwarding for demo & web testing:**
   ```bash
   ssh -L 3000:localhost:3000 -L 8000:localhost:8000 user@lab-pc-ip
   ```
   This allows viewing the Next.js UI (`:3000`) and FastAPI endpoints (`:8000`) in the laptop's browser while all compute and rendering backend runs on the lab workstation.

---

## 6. Summary Checklist for Week 1 Feasibility Gate

To validate the hardware safely during Week 1:

- [ ] Verify NVIDIA drivers and CUDA compatibility: `nvidia-smi` reports CUDA $\ge$ 11.8 on A4000.
- [ ] Set up dedicated Conda environment with PyTorch $\ge$ 2.0 with CUDA toolkit.
- [ ] Clone `SegAnyGAussians` and install submodules (`diff-gaussian-rasterization`, `simple-knn`).
- [ ] Run base 3DGS training on a downsampled public dataset (downsample 8) while monitoring VRAM via `watch -n 1 nvidia-smi`.
- [ ] Confirm peak memory stays $< 12$ GB.
- [ ] Run `sam2_hiera_base_plus` mask propagation on a 60-frame sample video to verify memory bank stability.
- [ ] Export a test `.ply` file and load it in `GaussianSplats3D` in the browser.
