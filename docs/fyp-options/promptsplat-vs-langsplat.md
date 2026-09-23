# PromptSplat vs LangSplat

Comparison of the Option 1 proposal ([PromptSplat](./option-1-language-grounded-3dgs.md)) against [LangSplat: 3D Language Gaussian Splatting](https://arxiv.org/abs/2312.16084) (CVPR 2024 Highlight).

**References**

- Paper: [arXiv:2312.16084](https://arxiv.org/abs/2312.16084)
- Project page: [langsplat.github.io](https://langsplat.github.io)
- Code: [github.com/minghanqin/LangSplat](https://github.com/minghanqin/LangSplat)

---

## Short answer

PromptSplat overlaps strongly with LangSplat in goal and inputs, but it is **not the same method**.

| | LangSplat | PromptSplat (proposed) |
|---|---|---|
| Core representation | Per-Gaussian **language features** (compressed CLIP) | Per-Gaussian **affinity/grouping features** (SAGA) |
| Main training signal | Regress rendered features toward CLIP mask embeddings | Contrastive co-membership from SAM masks |
| Text query path | Render language field → decode to CLIP → text relevance | CLIP on masked regions → 3D target voting |
| Primary research contribution | Direct 3D language field with SAM hierarchy + autoencoder | SAM 2 temporal supervision + interactive web system |
| Primary codebase | LangSplat | SAGA |

PromptSplat should be described as:

> A SAGA-based interactive 3D segmentation system that evaluates whether SAM 2 temporal mask propagation improves multi-view consistency under sparse-view reconstruction.

It should **not** be presented as a new version of LangSplat.

---

## Shared surface area

Both projects:

- reconstruct a static scene with 3D Gaussian Splatting;
- use SAM for 2D pseudo-labels;
- use CLIP for open-vocabulary text queries;
- support text-driven 3D object selection from arbitrary viewpoints;
- target open-vocabulary 3D scene understanding rather than a plain splat viewer.

From an evaluator's perspective, a text query such as "red chair" can look similar in both demos. The difference is **how** the 3D selection is learned and retrieved internally.

---

## Central technical difference

### LangSplat: direct language features on Gaussians

LangSplat augments each 3D Gaussian with **three compressed language embeddings** at SAM's hierarchical levels (subpart, part, whole):

\[
\{f_i^{subpart}, f_i^{part}, f_i^{whole}\}, \quad f_i^l \in \mathbb{R}^3
\]

Pipeline:

```text
SAM masks
    ↓
masked image regions
    ↓
512-D CLIP image embeddings
    ↓
scene-specific autoencoder (512 → 3)
    ↓
3-D language features stored on each Gaussian
    ↓
render language features → decode back to 512-D CLIP
    ↓
text query via CLIP text encoder + relevancy score
```

Key properties:

- Each Gaussian carries a **semantic/language descriptor** distilled from CLIP.
- Training minimizes reconstruction error between rendered language features and compressed CLIP targets.
- Querying is **dense text-to-language-field relevance** over rendered feature maps.
- Granularity is handled by **three discrete SAM levels**, stored as separate feature sets per Gaussian.
- Original LangSplat uses **independent per-image SAM** masks, not SAM 2 video propagation.

### PromptSplat / SAGA: grouping first, language second

SAGA attaches a **32-dimensional affinity feature** to each Gaussian:

\[
f_i \in \mathbb{R}^{32}
\]

This vector does not mean "chair" or "table." It answers:

> At a given physical scale, should these two Gaussians belong to the same target?

Pipeline:

```text
SAM / SAM 2 masks
    ↓
pixel-pair co-membership (contrastive supervision)
    ↓
32-D affinity feature per Gaussian (+ scale gate)
    ↓
CLIP image embeddings on masked regions (separate branch)
    ↓
mask clustering into 3D targets → vote-based text retrieval
```

Key properties:

- Each Gaussian carries an **instance/grouping descriptor**, not a word embedding.
- Training uses **contrastive pixel-pair supervision** from mask co-membership.
- Text queries go through **CLIP mask retrieval + 3D target voting**, not direct text-to-affinity cosine matching.
- Granularity uses a **continuous physical-scale gate**, not three fixed SAM levels.
- **Click prompting** is native: the clicked pixel's affinity feature becomes the query vector.

See [promptsplat-pipeline-detailed-explanation.md](./promptsplat-pipeline-detailed-explanation.md) Stage 6 for the accurate SAGA query path.

---

## Side-by-side comparison

| Aspect | LangSplat | PromptSplat (SAGA-based) |
|---|---|---|
| Per-Gaussian feature | 3-D compressed CLIP (×3 levels) | 32-D affinity + scale gate |
| Feature meaning | Semantic / language | Object grouping / co-membership |
| SAM usage | Independent masks per image; 3 hierarchy levels | Independent SAM baseline vs SAM 2 propagation (proposed) |
| CLIP role | Supervision target + query space | Mask-image embedding + query voting |
| Click queries | Not a first-class design | Native (point-prompt segmentation) |
| Multi-granularity | Three discrete SAM levels | Continuous scale-gated affinity |
| Main eval focus | Localization + semantic segmentation IoU | SAM vs SAM 2 supervision + cross-view consistency |
| System deliverable | Research pipeline + eval scripts | Full web app + experiment lab + custom datasets |
| Interactive editing | Not the official focus | Highlight, isolate, hide, recolor in browser |

---

## What PromptSplat adds beyond LangSplat

### 1. Research experiment (main novelty)

The controlled comparison:

```text
Everything fixed:
- same scene, training frames, 3DGS checkpoint
- same SAGA settings, seeds, query set, held-out annotations

Only changed:
- independent SAM masks  vs  SAM 2 propagated masks
```

Research question (from the proposal):

> Does temporally propagated SAM 2 supervision improve open-vocabulary 3D Gaussian segmentation consistency over independently generated SAM masks when camera views and GPU memory are limited?

LangSplat does not include this experiment. Note: **Gaussian Grouping** already used video mask tracking for cross-view identity; PromptSplat's defensible angle is the **controlled SAGA + SAM 2 + sparse-view** evaluation, not being first to use video propagation with 3DGS.

### 2. System and UX contribution

PromptSplat adds:

- FastAPI query service (text + click);
- React/Three.js browser explorer;
- experiment lab with baseline/ablation views;
- custom phone-captured scenes and held-out annotations;
- confidence heatmaps, isolate/hide/recolor controls;
- systems metrics (latency, FPS, VRAM) in the demo UI.

LangSplat's official repo is a research training/rendering/eval pipeline, not an interactive web application.

### 3. Click-based 3D segmentation

SAGA supports millisecond-scale point-prompt segmentation in 3D. LangSplat is optimized for text-query relevancy maps over language features.

---

## What LangSplat does that PromptSplat does not

- Learns a **true per-Gaussian language field** (features are directly CLIP-derived).
- Uses a **scene-specific autoencoder** to compress 512-D CLIP into 3-D latent features per Gaussian.
- Stores **three explicit semantic levels** (subpart / part / whole) as separate language features.
- Reports strong benchmarks on LERF localization and 3D-OVS semantic segmentation against LERF and related NeRF methods.
- Achieves very fast language-feature rendering (paper reports up to **199×** speedup over LERF at 1440×1080).

---

## Can you use the entire LangSplat codebase?

**Technically possible, but it would no longer be the current PromptSplat proposal.**

If LangSplat were the base, the project would become:

> LangSplat + SAM 2-derived masks + web frontend + extra evaluation

That is a valid alternative FYP, but it requires rewriting the methodology, research question, and implementation plan around LangSplat's direct language-field regression—not SAGA's contrastive affinity training.

### What LangSplat provides

- RGB 3DGS training (Inria fork);
- SAM + CLIP preprocessing (`preprocess.py`);
- scene-specific CLIP autoencoder;
- language-feature optimization on frozen RGB Gaussians;
- language-feature rendering;
- LERF / 3D-OVS evaluation scripts.

### What LangSplat does not provide

- SAGA's 32-D affinity field and contrastive training;
- scale-gated multi-granularity affinity features;
- SAGA-style click prompting;
- SAGA's mask-clustering / vote-based open-vocabulary retrieval;
- SAM 2 propagation adapter;
- paired SAM vs SAM 2 experiment infrastructure;
- browser viewer, query API, or editing UI;
- custom held-out annotation workflow.

### Integration cost

LangSplat and SAGA use **different modified Gaussian models and CUDA rasterizers** (LangSplat uses `langsplat-rasterization`; SAGA uses its own fork). Combining both full codebases is not drop-in and would create unnecessary CUDA/checkpoint compatibility work.

---

## Recommended approach

**Keep SAGA as the primary codebase**, as stated in the proposal:

> Do not attempt to reimplement LangSplat, OpenGaussian, and SAGA together. SAGA should be the codebase. The other papers provide baselines, design justification, and related work.

Use LangSplat as:

- a major **related-work** comparison (alternative design: direct language field vs affinity + CLIP voting);
- optional **baseline numbers** on public scenes (LERF, 3D-OVS) if time permits;
- justification for the CLIP + SAM language-grounding design space.

Do **not** switch the entire project to LangSplat unless the research question and contribution are rewritten accordingly.

---

## Wording correction for the proposal

The proposal says the system learns features "from SAM/SAM 2 and CLIP supervision." For SAGA, that wording is slightly misleading.

More accurate:

- **SAM / SAM 2** supervises the per-Gaussian **affinity field** (grouping).
- **CLIP** independently assigns open-vocabulary semantics to **masked regions / 3D targets** at query time.

Making this distinction explicit helps evaluators understand that PromptSplat is not a LangSplat reproduction.

---

## License note

The [LangSplat repository](https://github.com/minghanqin/LangSplat) inherits the **Inria Gaussian-Splatting research license** (non-commercial research/evaluation use). If LangSplat code, checkpoints, or preprocessed data are reused—even as a baseline—cite the paper, retain license terms, and document modifications. SAGA's repository is Apache-2.0, but transitive dependencies and weights retain their own terms.

---

## Related documents

- [Option 1 — PromptSplat proposal](./option-1-language-grounded-3dgs.md)
- [PromptSplat pipeline (detailed)](./promptsplat-pipeline-detailed-explanation.md)
- [Source audit](./source-audit.md)
