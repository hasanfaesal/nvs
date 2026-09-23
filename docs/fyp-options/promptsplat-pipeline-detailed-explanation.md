# PromptSplat Pipeline: Detailed End-to-End Explanation

This document explains the six-stage pipeline from [Option 1 — PromptSplat](option-1-language-grounded-3dgs.md) in extreme detail: what each stage actually does, how data flows between them, and what evaluators will see at the end.

## Mental model

The easiest way to think about the whole system is:

You first build a photorealistic 3D scene. Then you give every tiny part of that scene an object-affinity descriptor. Finally, CLIP connects human language to groups of those 3D parts.

> object affinity descriptor: feature vector designed to quantify how likely two visual entities belong to together.

The six lines in the proposal compress several offline training jobs, data conversions, and runtime services:

```text
1. SfM & Camera Poses (COLMAP)
2. Base 3DGS Training (Inria 3DGS)
3. 2D Pseudo-labeling (SAM 2)
4. Semantic Feature Extraction (CLIP ViT)
5. Contrastive Field Optimization (SAGA)
6. Query & Interactive Inference (CLIP text encoder + Cosine matching)
```

A more technically accurate data flow is:

```text
Phone video
    │
    ├── Frames ──> COLMAP ──> camera poses + sparse geometry
    │                              │
    │                              └──> 3DGS training
    │                                    │
    │                                    └──> photorealistic RGB Gaussians
    │
    ├── Training frames ──> SAM / SAM 2 ──> object and part masks
    │                                              │
    │                                              └──> SAGA training
    │                                                    │
    │                                                    └──> 32-D affinity
    │                                                         per Gaussian
    │
    └── Masked regions ──> CLIP image encoder ──> semantic embeddings
                                                        │
Text query ──> CLIP text encoder ──> similarity/voting ──> target Gaussians
                                                        │
                                                        └──> browser highlight
```

There are really **three representations**:

1. **RGB Gaussian parameters** — what the scene looks like.
2. **SAGA affinity features** — which Gaussians belong together.
3. **CLIP mask embeddings** — what those groups might mean in language.

---

## Before the listed pipeline: capture and split

You record a static scene with a phone — for example, a desk containing a red chair, monitor, keyboard, mug, books, and lamp.

The phone video is **not** treated like normal video during reconstruction. You extract perhaps **60–120 sharp, overlapping frames**. Each frame becomes a separate camera observation of the same static world.

Good capture requires:

- no moving objects;
- slow camera motion;
- substantial overlap between consecutive frames;
- textured surfaces;
- stable lighting and exposure;
- several viewpoints around each important object.

You then divide frames into:

- **training views**, used to build the scene and train SAGA;
- **held-out views**, used only for evaluation.

For a strict experiment:

- held-out RGB frames must not be used to optimize 3DGS if you report held-out PSNR;
- held-out masks must never enter semantic training;
- SAM 2 should not propagate through held-out frames in a way that leaks their appearance back into training masks.

COLMAP may still estimate held-out camera poses as part of pose recovery, provided this is documented. But the held-out images should not contribute photometric or semantic training losses.

---

## Stage 1: COLMAP reconstructs the camera arrangement

### The problem it solves

Every phone frame is taken from a different unknown position. To combine them into one 3D scene, the system must know:

- camera focal length and other intrinsics;
- camera position;
- camera orientation;
- which pixels in different images observe the same physical point.

These are not normally stored accurately enough in the video metadata, so COLMAP estimates them.

### 1. Feature extraction

COLMAP detects distinctive local image features, such as corners, textured patches, and edges.

For example, it may detect the same corner of a book in frames 12, 13, 15, and 18.

Each detected point has a descriptor intended to remain recognizable under moderate viewpoint and lighting changes.

### 2. Feature matching

COLMAP compares descriptors between frames and proposes correspondences:

```text
Frame 12, pixel (840, 410)
        corresponds to
Frame 15, pixel (735, 398)
```

Geometric verification rejects matches that are inconsistent with epipolar geometry.

> epipolar geometry: intrinsic projective geometry between two pinhole camera views of the same 3D scene.

This is why blank walls, reflections, motion blur, and repeated patterns are problematic: they provide either too few reliable correspondences or too many ambiguous ones.

### 3. Structure from Motion

Using the correspondences, COLMAP jointly estimates:

- camera intrinsics \(K\);
> internal optical and digital characteristics of the camera.
- camera extrinsics \([R|t]\);
> position and orientation of the camera in the 3D world.
- sparse 3D landmark positions.
> discrete set of distinct 3D coordinates in world space that represent key physical features in the environment.

A camera projection is approximately:

\[
p \sim K[R|t]P
\]

where:

- \(P\) is a world-space 3D point;
- \(R,t\) transform it into camera space;
- \(K\) projects it onto the image plane;
- \(p\) is the resulting image pixel.

The output is a sparse point cloud plus a camera matrix for every registered frame.

### Important limitation

Monocular SfM generally recovers geometry only up to an arbitrary scale. A distance of `1.0` is not necessarily one metre unless you provide metric calibration.

Therefore, SAGA's "physical mask scale" means a scale consistent inside that reconstructed coordinate system — not automatically a real-world measurement in metres.

### What exists after Stage 1

You have:

- extracted and undistorted images;
- estimated camera intrinsics;
- camera poses;
- a sparse point cloud;
- a common 3D coordinate system.

It may look like a sparse constellation of colored points. It is **not** yet the polished scene evaluators will see.

---

## Stage 2: 3D Gaussian Splatting builds the photorealistic scene

### What is a Gaussian here?

The scene is represented by hundreds of thousands or millions of soft 3D ellipsoids.

Each Gaussian normally stores:

- a 3D centre \(\mu_i\);
- anisotropic scale;
- 3D rotation;
- opacity \(\alpha_i\);
- color or spherical-harmonic coefficients.

A Gaussian is not necessarily an object or even a physical point. Many overlapping Gaussians collectively approximate surfaces, fine details, transparency, and view-dependent color.

### Initialization

The sparse COLMAP points give 3DGS an approximate initial geometry.

Gaussians are initialized around those points. Training then moves, duplicates, resizes, rotates, recolors, and removes them.

### Differentiable rendering

For one training camera:

1. Transform the Gaussians into camera coordinates.
2. Project each 3D ellipsoid into a 2D ellipse.
3. Sort visible Gaussians approximately front-to-back.
4. Alpha-composite their colors at each pixel.

Conceptually:

\[
C(p)=\sum_i c_i w_i,
\qquad
w_i=\alpha_i\prod_{j<i}(1-\alpha_j)
\]

A Gaussian contributes strongly when:

- its projected ellipse covers the pixel;
- it has sufficient opacity;
- nearer Gaussians have not already blocked it.

### Optimization

The rendered image is compared with the real phone frame. A typical reconstruction loss combines pixel error and structural similarity.

Gradients update the Gaussian parameters so that renders from all training cameras resemble their corresponding photographs.

Adaptive density control usually:

- splits or clones Gaussians where more detail is needed;
- enlarges or moves Gaussians;
- prunes nearly invisible Gaussians.

### What Stage 2 learns

It learns **appearance and geometry**, not object identity.

At this point, the system can render a convincing new view between the original phone viewpoints, but it does not know that 20,000 particular Gaussians constitute a chair.

### Output

The important artifact is a 3DGS checkpoint or PLY-like asset containing all RGB Gaussians.

This is the visual foundation of the browser demo.

---

## Stage 3: SAM or SAM 2 creates 2D pseudo-labels

### What pseudo-label means

You are not manually drawing training masks around every object in every frame.

Instead, a pretrained segmentation model generates masks automatically. They are called **pseudo-labels** because they supervise another model but are not guaranteed to be correct.

Manual masks should still be created for held-out evaluation views. Those are ground truth, not pseudo-labels.

### SAM masks are class-agnostic

SAM can identify coherent image regions, but a mask does not inherently contain the word "chair."

It might produce overlapping masks such as:

- entire chair;
- chair seat;
- chair backrest;
- one chair leg;
- cushion;
- larger chair-and-shadow region.

This hierarchy is useful because SAGA supports multiple segmentation granularities.

### Baseline: independent SAM masks

In the original SAGA baseline, SAM processes each image independently.

That can create inconsistencies:

```text
Frame 1: chair mask includes cushion
Frame 2: chair mask excludes cushion
Frame 3: chair and nearby table merge
Frame 4: one chair leg is missed
```

SAM has no guarantee that mask 17 in one frame corresponds to mask 9 in another frame.

### Proposed method: SAM 2 propagation

For the proposed PromptSplat variant:

1. Select key frames throughout the video.
2. Generate or correct masks on those frames.
3. Assign object-track IDs.
4. Run the SAM 2 video predictor forward and possibly backward.
5. Propagate the masks through the sequence.
6. Correct drift at additional key frames.
7. Export masks in SAGA's expected format.

SAM 2 has temporal memory, so an object can retain a persistent identity across consecutive views:

```text
chair track ID = 4
frame 001 -> mask
frame 002 -> mask
frame 003 -> partially occluded mask
frame 004 -> mask
```

It can still fail through severe occlusion, reflections, abrupt camera jumps, or similar adjacent objects.

### Why SAM 2 could improve the final 3D field

The same physical Gaussian appears in several camera views. If its projected pixels receive contradictory masks, SAGA receives contradictory gradients.

For example:

- view A says the cushion and frame belong together;
- view B says they are separate;
- view C accidentally includes the floor.

Independent SAM masks create noisy supervision. Temporally propagated SAM 2 masks should be more stable, reducing those contradictions.

That is the actual research hypothesis — not merely "SAM 2 is newer."

### Persistent IDs caveat

Original SAGA primarily learns from per-image mask co-membership. It does not require matching instance IDs across images: shared 3D Gaussians provide the cross-view connection.

Persistent SAM 2 IDs are still useful for:

- stabilizing masks;
- CLIP score aggregation;
- evaluation;
- debugging propagation;
- optionally constructing target tracks.

But if IDs are introduced directly into the loss, that becomes an additional methodological change. To isolate the experiment correctly, the principal controlled variable should remain mask source:

- independent SAM masks;
- SAM 2 propagated masks.

---

## Stage 4: estimate mask scale

SAGA needs to distinguish between parts, objects, and larger groups.

For example, the clicked area might belong to:

- a chair leg;
- the whole chair;
- all furniture near the desk.

A purely 2D mask area is unsuitable because the same chair looks large when close and small when far away.

SAGA therefore uses the trained 3DGS model to render depth for the mask's camera. Mask pixels are approximately lifted into 3D, producing a point set. The spread of that point set estimates the mask's 3D scale:

\[
s_M \approx
2\sqrt{\sigma_x^2+\sigma_y^2+\sigma_z^2}
\]

This makes the scale more consistent across viewpoints.

Small scales correspond roughly to parts; larger scales correspond to complete objects or larger structures.

---

## Stage 5: SAGA learns a grouping descriptor for every Gaussian

This is the core trainable scene-understanding stage.

### Affinity features

Suppose the RGB reconstruction contains \(N\) Gaussians.

SAGA attaches a trainable feature vector to each one:

\[
f_i \in \mathbb{R}^{32}
\]

The original paper uses 32 dimensions.

These are **not** CLIP vectors and do not directly represent words such as "chair." They represent affinity:

> At a requested scale, should these two Gaussians be grouped as the same target?

After training:

- Gaussians on the same chair should have similar features;
- chair and floor Gaussians should be dissimilar;
- seat and backrest may be similar at object scale but separable at part scale.

### Scale gate

A single feature vector must support different granularities. SAGA learns a small scale-gating function:

\[
f_i^s = S(s)\odot f_i
\]

where:

- \(s\) is the requested scale;
- \(S(s)\) outputs 32 values between zero and one;
- elementwise multiplication activates or suppresses feature channels.

At a fine scale, more detailed channels can distinguish chair legs. At a coarse scale, other channels can represent the whole chair.

The gate is just a small linear layer followed by sigmoid, so changing scale is cheap.

### Rendering affinity features

The RGB Gaussian renderer already knows which Gaussians contribute to each pixel.

SAGA reuses the same compositing weights but renders feature vectors instead of colors:

\[
F(p)=\sum_i f_i w_i
\]

Therefore, the feature rendered at one pixel is a weighted blend of the affinity features of the visible Gaussians along that ray.

This is the mechanism that connects 2D masks to 3D Gaussians.

### Contrastive supervision

For a training image, SAGA samples pixels and asks whether pairs belong to a common mask at the selected scale.

A positive pair might be:

```text
pixel on chair seat <-> pixel on chair back
```

A negative pair might be:

```text
pixel on chair <-> pixel on floor
```

For positive pairs, training raises cosine similarity between rendered features. For negative pairs, it lowers similarity.

Because rendered features depend on the underlying Gaussian features, backpropagation transfers the SAM mask relationships into the 3D representation.

### Why this becomes multi-view 3D knowledge

Suppose one chair Gaussian contributes to pixels in 30 training frames.

Every one of those pixels backpropagates into the same underlying Gaussian feature. Consequently, information from multiple cameras is fused into one persistent 3D descriptor.

This is why a selection can remain attached to the chair as the evaluator rotates the camera.

### Additional stabilizers

SAGA includes:

- **feature-norm regularization**, which encourages blended features along a camera ray to agree;
- **local K-nearest-neighbour smoothing**, which reduces isolated false-positive Gaussians;
- **balanced pair sampling**, because arbitrary pixel pairs are overwhelmingly negative;
- **extra weighting for small masks**, so large surfaces do not dominate training.

The published configuration uses approximately:

- 32-dimensional features;
- 16 neighbours for smoothing;
- 10,000 optimization iterations;
- eight sampled scales per iteration;
- 1,000 sampled pixels per iteration.

### What is frozen and what is trained

Normally:

- RGB Gaussian geometry and appearance are loaded from Stage 2 and kept fixed;
- SAM/SAM 2 is frozen;
- CLIP is frozen;
- per-Gaussian SAGA affinity features are trained;
- the scale gate is trained.

If RGB Gaussians are genuinely frozen, semantic training cannot degrade reconstruction PSNR. Reconstruction metrics then describe the base scene quality rather than testing a semantic/RGB tradeoff.

### Output

After SAGA training, each Gaussian has:

```text
position + shape + opacity + RGB/SH + 32-D affinity vector
```

The scene can now answer grouping questions but still does not directly understand arbitrary words.

---

## Stage 6: CLIP adds language

There is an important simplification in the six-line pipeline: original SAGA does **not** normally compare a CLIP text vector directly with the 32-dimensional Gaussian affinity vector.

Those spaces were trained for different purposes and usually have different dimensions.

The accurate original SAGA open-vocabulary process is closer to this:

### Offline CLIP image extraction

For every useful SAM mask:

1. Apply the mask to its source image.
2. Form a masked region or crop.
3. Pass it through the frozen CLIP image encoder.
4. Normalize and store the visual embedding.

A masked chair observed from ten viewpoints now has several CLIP image embeddings.

### Build candidate 3D targets

SAGA uses affinity features to determine whether masks from different views correspond to approximately the same 3D Gaussian subset.

Masks can be grouped by the overlap of their selected 3D anchor Gaussians. This creates a "vote graph" or candidate-target clusters.

A cluster may represent:

- chair;
- chair seat;
- monitor;
- desk;
- book stack.

### Online text query

When the user types `red chair`:

1. Tokenize the phrase.
2. Run the frozen CLIP text encoder.
3. Normalize the text vector.
4. Compute cosine similarity or CLIP relevance against stored mask-image vectors.
5. Aggregate scores across masks belonging to the same 3D target.
6. Select or rank target clusters.
7. Convert the chosen target into per-Gaussian confidence values.

CLIP gives language semantics; SAGA gives stable 3D grouping.

This is why the system is **open-vocabulary**: query labels do not need to be manually predefined. But performance remains limited by what CLIP can recognize in masked image regions.

### Relational-language limitation

A query such as `red chair` is realistic.

A query such as `the red chair beside the desk` is not guaranteed to use the relation "beside" compositionally. CLIP may retrieve the correct chair because the phrase globally resembles its images, but there is no explicit spatial-relation parser.

The final demo should use relational prompts only after empirical testing. The project explicitly excludes general relational reasoning.

---

## Exact runtime flow for an evaluator's text query

By demo time, all expensive reconstruction and semantic training should already be complete.

When the evaluator submits a query:

1. Browser sends the scene ID, text, and threshold to FastAPI.
2. Backend checks the query cache.
3. On a cache miss, CLIP encodes the text.
4. Backend compares it with stored mask embeddings.
5. Scores are aggregated by candidate 3D target.
6. Target scores are converted into Gaussian-level confidences.
7. Backend returns:
   - Gaussian IDs or a bitset;
   - confidence values;
   - query latency;
   - target metadata.
8. Browser applies those values to the loaded scene.
9. Selected Gaussians change color or opacity.
10. Rotating the camera requires no new segmentation — the selected entity is already a 3D Gaussian set.

With stable per-Gaussian indexing, a threshold slider can often operate entirely in the browser after confidences have been downloaded.

---

## Exact runtime flow for a click

For click selection:

1. The browser records the clicked pixel.
2. It sends the camera matrix, viewport dimensions, pixel, and desired scale.
3. SAGA renders or retrieves the affinity feature at that pixel.
4. That feature becomes the query vector.
5. Cosine similarity is calculated against all scale-gated Gaussian features.
6. Gaussians above the threshold are selected.
7. The resulting confidence array is returned to the browser.

Positive and negative clicks can refine the query by combining several prompted feature vectors.

Unlike text querying, click querying does not need CLIP.

---

## What the browser actually renders

The viewer receives the RGB splat asset and a stable index for every Gaussian.

There are two implementation options.

### Direct shader/index update

The server returns a confidence byte for every Gaussian. A custom viewer shader changes its appearance:

- **highlight**: blend its color with an accent color;
- **isolate**: set unselected opacity to zero;
- **hide**: set selected opacity to zero;
- **confidence mode**: map confidence to a heatmap;
- **recolor**: override selected color coefficients.

This is the polished option.

### Two-layer fallback

The backend exports a second splat asset containing only selected Gaussians.

The browser renders:

- original scene as one layer;
- selected object as another layer.

This is less efficient but easier and acceptable for the FYP.

### "Remove" does not mean inpainting

Hiding chair Gaussians reveals empty or poorly reconstructed space behind them. The system does not generate the wall or floor that was originally occluded.

Therefore:

- hide/remove = suppress selected Gaussians;
- not = photorealistic object removal and 3D inpainting.

Likewise, recoloring is a visual override, not a physically correct material edit.

---

## What evaluators should see

The demonstration should begin with a prepared scene already loaded. They should **not** wait for COLMAP, SAM 2, or SAGA training.

A strong presentation flow is:

1. **Photorealistic exploration**  
   The evaluator orbits a custom room or desk scene at interactive frame rate.

2. **Text selection**  
   They enter `red chair`. The chair is highlighted.

3. **View consistency**  
   They rotate around the scene. The selection remains attached to the 3D chair rather than becoming a single frozen 2D mask.

4. **Object operation**  
   They isolate, hide, make transparent, or recolor the chair.

5. **Confidence visualization**  
   A heatmap reveals highly confident seat Gaussians and uncertain boundary Gaussians.

6. **Click selection**  
   They click a mug or monitor and see the corresponding 3D object selected.

7. **Method comparison**  
   The interface switches between:
   - independent SAM supervision;
   - SAM 2 propagated supervision.

8. **Evidence panel**  
   The evaluator sees the source image, generated pseudo-mask, rendered 3D mask, manual held-out mask, errors, and numerical metrics.

9. **Failure case**  
   You deliberately show a difficult small, reflective, or partially occluded object and explain why it fails.

That last step makes the project look scientifically evaluated rather than selectively demonstrated.

---

## How the quantitative evaluation works

The proposed evaluation has three methods:

1. **2D-only baseline:** Grounded SAM or CLIP-guided SAM on each held-out image independently.
2. **SAGA baseline:** official independent SAM pseudo-label pipeline.
3. **PromptSplat:** the same SAGA training with SAM 2 propagated masks.

### Held-out mask IoU

For a named object:

1. Query the trained 3D representation.
2. Select Gaussians.
3. Render those selected Gaussians from a held-out camera.
4. Produce a binary 2D mask.
5. Compare it with the manually annotated held-out mask.

\[
IoU = \frac{|prediction\cap ground\ truth|}
{|prediction\cup ground\ truth|}
\]

This tests whether the learned 3D selection projects correctly into a camera view never used for semantic training.

### Mean pixel accuracy

Count the percentage of correctly classified foreground and background pixels, preferably reporting class-balanced variants because backgrounds dominate images.

### Text-query localization accuracy

Create a fixed query list with synonyms:

```text
chair
red chair
seat
the office chair
```

Define success before running experiments — for example, the highest-scoring target overlaps the correct object above a specified IoU.

### Cross-view consistency

Do not define this as "the same Gaussian IDs are selected in every view"; that is automatically true once a 3D subset has been selected.

A meaningful metric should compare:

- rendered masks across overlapping held-out viewpoints after geometric reprojection; or
- held-out IoU variance for the same object; or
- consistency of independently issued per-view clicks after lifting their selections into 3D.

### Reconstruction metrics

Use held-out RGB rendering to report:

- PSNR;
- SSIM;
- LPIPS.

These indicate whether the underlying 3D scene is visually credible.

### Systems metrics

Show:

- preprocessing time;
- 3DGS training time;
- SAGA training time;
- peak VRAM;
- text-query latency;
- click-query latency;
- scene download size;
- browser FPS.

The paper's millisecond SAGA segmentation figure refers to core feature matching, not necessarily the complete browser/API/CLIP request. End-to-end latency must be measured locally.

---

## The central experiment

The cleanest scientific comparison is:

```text
Everything fixed:
- same scene
- same training frames
- same 3DGS checkpoint
- same SAGA settings
- same random seed policy
- same query set
- same held-out annotations

Only changed:
- independent SAM masks
  versus
- SAM 2 propagated masks
```

You then repeat this with approximately 25, 50, and 100 training views.

The expected result is that SAM 2 helps most when views are limited or objects are partially occluded. But this remains a hypothesis. If it does not improve IoU, that is still a valid result if you analyze propagation drift and mask errors honestly.

---

## Final deliverable

The final product is not merely a Gaussian viewer. It is a reproducible per-scene open-vocabulary 3D understanding system containing:

- phone-captured scene datasets;
- COLMAP camera reconstructions;
- trained photorealistic 3DGS assets;
- independent SAM and propagated SAM 2 mask sets;
- per-Gaussian SAGA affinity tensors;
- CLIP mask-embedding databases;
- manually annotated held-out masks;
- paired experiment configurations and results;
- FastAPI text/click query service;
- React/Three.js interactive viewer;
- prepared evaluator scenes;
- report, setup guide, and failure analysis.

The one-sentence evaluator experience is:

> "I can freely explore a photorealistic reconstruction, describe or click an object, and the system identifies the corresponding 3D Gaussian subset consistently from every viewpoint — while also showing measured evidence that SAM 2 supervision did or did not improve that consistency."

---

## Important correction to the six-line pipeline

CLIP image embeddings and SAGA affinity training are **separate branches**, and original SAGA's language query is a **mask/target voting process** — not simply direct cosine matching between text and per-Gaussian affinity vectors.

See the main proposal: [option-1-language-grounded-3dgs.md](option-1-language-grounded-3dgs.md)
