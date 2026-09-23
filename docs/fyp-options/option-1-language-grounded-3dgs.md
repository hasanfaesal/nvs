# Option 1 — PromptSplat: Language-Grounded 3DGS Explorer

## One-sentence proposal

Build a web application that reconstructs a static real-world scene as a 3D Gaussian Splat, learns object-aware 3D features from SAM/SAM 2 and CLIP supervision, and lets a user find, select, isolate, recolor, or remove objects using text or clicks.

## Recommendation

This is the recommended option. It has the best balance of:

- a clear Bachelor of AI contribution;
- established papers and official repositories;
- phone-based data collection;
- quantitative experiments;
- manageable 16 GB GPU scope; and
- an evaluator-friendly live web demonstration.

The project must be presented as **open-vocabulary 3D scene understanding**, not as “a Gaussian Splat viewer.”

## Proposed title

**PromptSplat: Language-Grounded Understanding and Interactive Editing of 3D Gaussian Scenes**

Alternative academic title:

**Improving Multi-View Semantic Consistency in Language-Embedded 3D Gaussian Splatting with Video Mask Propagation**

## Evaluator demo

The evaluator opens a photorealistic room in the browser and can orbit it immediately.

They type:

> the red chair beside the desk

The relevant 3D Gaussians become highlighted from every viewpoint. The evaluator can then:

- isolate the chair;
- make everything else transparent;
- recolor it;
- hide it;
- inspect the confidence heatmap; or
- click another object to select it in 3D.

A second panel shows:

- the original phone frames;
- SAM/SAM 2 pseudo-labels;
- the learned 3D selection;
- held-out ground truth; and
- the method’s IoU, query latency, FPS, and peak VRAM.

This combination makes the AI contribution visible instead of leaving it hidden behind the viewer.

## Research foundation

### Primary implementation: SAGA

Build on the official [SAGA: Segment Any 3D Gaussians](https://github.com/Jumpat/SegAnyGAussians) repository.

A Gaussian affinity feature is a learned vector attached to each 3D Gaussian that represents what that Gaussian is likely to belong with semantically or instance-wise.

SAGA already provides:

- 3DGS scene training;
- SAM mask extraction;
- mask-scale estimation;
- CLIP feature extraction for open-vocabulary queries;
- training of a contrastive 3D Gaussian affinity feature field;
- point-prompt and multi-point 3D segmentation;
- open-vocabulary segmentation logic;
- mask rendering;
- an interactive desktop GUI; and
- pretrained/public dataset workflows.

The repository identifies the work as AAAI 2025 and uses an Apache-2.0 repository license. Its current `v2` branch was active when checked on 4 September 2026. Transitive dependencies and pretrained weights still retain their own licenses.

### Supporting papers and implementations

- Qin et al., [LangSplat: 3D Language Gaussian Splatting](https://arxiv.org/abs/2312.16084), CVPR 2024 Highlight. It distills CLIP language features into 3D Gaussians and uses hierarchical SAM supervision.
- Ye et al., [Gaussian Grouping: Segment and Edit Anything in 3D Scenes](https://arxiv.org/abs/2312.00732), ECCV 2024. It learns compact identity encodings from SAM/DEVA masks and supports local scene editing.
- Shen et al., [FlashSplat: 2D to 3D Gaussian Splatting Segmentation Solved Optimally](https://arxiv.org/abs/2409.08270), ECCV 2024. It provides a fast optimization-based alternative for lifting 2D masks to 3D.
- Wu et al., [OpenGaussian: Towards Point-Level 3D Gaussian-based Open Vocabulary Understanding](https://arxiv.org/abs/2406.02058), NeurIPS 2024.
- Kerbl et al., [3D Gaussian Splatting for Real-Time Radiance Field Rendering](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/), ACM TOG/SIGGRAPH 2023.
- Kirillov et al., [Segment Anything](https://arxiv.org/abs/2304.02643), ICCV 2023.
- Ravi et al., [SAM 2: Segment Anything in Images and Videos](https://arxiv.org/abs/2408.00714), 2024.
- Radford et al., [Learning Transferable Visual Models From Natural Language Supervision](https://arxiv.org/abs/2103.00020), ICML 2021.

Do not attempt to reimplement LangSplat, OpenGaussian, and SAGA together. SAGA should be the codebase. The other papers provide baselines, design justification, and related work.

## Why this is an AI project

The project has three learned components:

1. A vision foundation model predicts object masks from the scene images.
2. CLIP maps image regions and arbitrary text into a shared semantic embedding space.
3. SAGA optimizes a contrastive feature vector for each 3D Gaussian so that Gaussians belonging to the same object are close in feature space and different objects are separated.

The 3DGS color/geometry model provides the photorealistic scene representation. The learned affinity/language field provides the AI scene-understanding capability.

The report should distinguish these components explicitly:

- **Pretrained:** SAM or SAM 2 and CLIP.
- **Optimized per scene:** RGB Gaussians and SAGA affinity features.
- **Student contribution:** consistent pseudo-label pipeline, controlled experiments, browser query/visualization system, custom dataset, and analysis.

## Research question

Recommended primary question:

> Does temporally propagated SAM 2 supervision improve open-vocabulary 3D Gaussian segmentation consistency over independently generated SAM masks when camera views and GPU memory are limited?

Recommended hypothesis:

> Propagating stable object identities through a phone video will reduce cross-view mask disagreement and improve held-out 3D segmentation IoU, particularly when only 25–50 reconstruction views are available.

This is a defensible extension rather than a new model invented from scratch. SAM 2 supplies the video mask propagation, while SAGA supplies the 3D feature-learning method.

## Exact project scope

### Required core

- Reproduce SAGA on one provided public scene.
- Capture and reconstruct at least three custom static scenes.
- Support text and click queries.
- Render selected objects consistently from arbitrary camera views.
- Compare original SAGA mask supervision with SAM 2 propagated supervision.
- Build the complete interactive web application.
- Report segmentation, reconstruction, speed, and memory results.

### Optional stretch features

- Object removal by hiding selected Gaussians.
- Basic recoloring or scene recomposition.
- Voice-to-text queries using the browser speech API.
- A WebXR viewing mode.
- A FlashSplat runtime comparison.

### Explicitly out of scope

- Training SAM, SAM 2, or CLIP from scratch.
- General relational reasoning such as “the item owned by the person near the door.”
- Dynamic-scene reconstruction.
- Generative 3D inpainting.
- Real-time phone SLAM.
- A general-purpose LLM agent.
- Supporting unlimited user uploads during the final presentation.

## Pipeline
1. SfM & Camera Poses (COLMAP)
2. Base 3DGS Training (Inria 3DGS)
3. 2D Pseudo-labeling (SAM 2)
4. Semantic Feature Extraciton (CLIP ViT)
5. Contrastive Field Optimization (SAGA)
6. Query & Interactive Inference (CLIP text encoder + Cosine matching)

## End-to-end ML pipeline

### Stage 1 — Capture a static scene

Use a phone to record a slow orbit or walkthrough.

Capture rules:

- The scene must remain static.
- Use diffuse, stable lighting.
- Avoid mirrors, blank walls, motion blur, and rapid exposure changes.
- Maintain large overlap between consecutive frames.
- Walk a loop when possible.
- Record at 1080p, then downsample for training.
- Extract approximately 60–120 useful frames rather than using every video frame.

Good first scenes:

- a desk with toys, books, a mug, and stationery;
- a small lab corner;
- a shelf with visually distinct objects.

Do not start with a full building or a large outdoor environment.

### Stage 2 — Camera poses and base 3DGS

Use the data conversion already expected by SAGA/3DGS:

1. Extract frames with FFmpeg.
2. Estimate camera intrinsics and poses with COLMAP.
3. Train the base RGB 3D Gaussian model.
4. hold out approximately 10–20% of camera views for evaluation.

Nerfstudio’s `ns-process-data` may be used as a convenient COLMAP frontend, but the final files must match the selected SAGA pipeline.

### Stage 3A — Original SAGA pseudo-label baseline

Follow the official SAGA pipeline:

1. Run SAM over the training images.
2. Estimate physical mask scales using the trained 3DGS.
3. Extract CLIP features.
4. Train SAGA’s contrastive Gaussian affinity features for the documented 10,000 iterations.
5. Save the per-Gaussian feature tensor and scene checkpoint.

This is the main reproducible baseline.

### Stage 3B — Proposed SAM 2 supervision

Create an adapter, not a new segmentation model:

1. Choose several key frames distributed through the phone video.
2. Obtain masks on those frames using points, boxes, or automatic proposals.
3. Use the official SAM 2 video predictor to propagate stable object masks through the frame sequence.
4. Assign persistent instance IDs across frames.
5. Convert masks and metadata into the format expected by SAGA.
6. Reuse SAGA’s mask-scale extraction and contrastive feature training unchanged.

The important controlled variable is the pseudo-label source:

- independent SAM masks; versus
- temporally propagated SAM 2 masks.

All remaining training settings should be held fixed.

### Stage 4 — Text and click query service

For text queries:

1. Encode the text with the same CLIP text encoder used by the pipeline.
2. Compare the text embedding with learned object/region embeddings.
3. calculate a similarity score or binary selection for each Gaussian.
4. Return the selected Gaussian IDs, confidence values, and timing.

For click queries:

1. Send the camera matrix, viewport size, and clicked pixel to the backend.
2. Reuse SAGA’s point-prompt selection logic.
3. Return the selected Gaussian mask.

Cache query results by scene ID, model version, and normalized query.

### Stage 5 — Browser visualization

Recommended viewer:

- Use [GaussianSplats3D](https://github.com/mkkellogg/GaussianSplats3D) inside a React/Three.js page because it is easier to extend with application-specific controls.
- Use [SuperSplat](https://github.com/playcanvas/supersplat) offline to inspect, crop, and compress scene assets.

Start with a low-risk visualization path:

1. The backend exports the selected subset as a small temporary splat asset.
2. The browser renders the original scene and selected overlay as two scenes.
3. Highlight, isolate, and hide operations toggle those layers.

After that works, add the polished path:

1. Preserve a stable per-Gaussian index during export.
2. Return a compact bitset or byte confidence array from the query API.
3. Add one small viewer/shader extension that updates per-splat color and opacity.

The overlay approach is an acceptable fallback if the shader extension becomes unreliable.

## Web application

### Recommended stack

- Frontend: Next.js or React with TypeScript.
- 3D rendering: Three.js plus GaussianSplats3D.
- API: FastAPI.
- GPU worker: the pinned SAGA Python environment.
- Job/metadata storage: SQLite.
- Artifact storage: local filesystem for development; optional S3-compatible storage for deployment.
- Progress: Server-Sent Events or WebSocket.

Do not run the CUDA environment inside the web frontend process.

### Main pages

#### 1. Demo landing page

- Open directly into a polished prepared scene.
- Show three example queries.
- Include a concise “how it works” strip.
- Provide a clear button to enter the full explorer.

#### 2. Scene explorer

- Full-screen orbit viewer.
- Search box with example prompts.
- Click-selection mode.
- RGB, identity, similarity, and binary-mask views.
- Highlight, isolate, hide, transparency, and recolor actions.
- Confidence threshold slider.
- Saved-query/history panel.

#### 3. Experiment lab

- Choose method: SAM baseline or SAM 2 propagation.
- Choose view count and downsampling setting.
- Display held-out masks and errors.
- Plot IoU, localization accuracy, runtime, FPS, and VRAM.
- Link each result to its exact configuration and checkpoint.

#### 4. Method page

- Architecture diagram.
- Explanation of pretrained versus trained components.
- Dataset and annotation procedure.
- Limitations and failure cases.
- Paper and repository links.

### Suggested API

```text
GET  /api/scenes
GET  /api/scenes/{scene_id}
POST /api/scenes/{scene_id}/query/text
POST /api/scenes/{scene_id}/query/click
GET  /api/queries/{query_id}
GET  /api/artifacts/{artifact_id}
GET  /api/experiments
GET  /api/experiments/{experiment_id}
POST /api/jobs
GET  /api/jobs/{job_id}
```

Keep training endpoints disabled in the public presentation deployment unless authentication and resource limits are added.

## Dataset and annotation plan

### Public data

Use a small subset rather than every available dataset:

- one or two LERF scenes for reproducibility;
- LERF-Mask annotations from Gaussian Grouping where useful; and
- one SAGA-provided preprocessed scene for the first smoke test.

### Custom data

Capture three scenes with increasing difficulty:

1. Distinct tabletop objects.
2. A cluttered shelf or desk.
3. A room corner with repeated categories and partial occlusion.

Annotate:

- 8–12 named objects per scene;
- 8–12 held-out views per scene; and
- synonyms/query phrases for each object.

Use CVAT, Label Studio, or Roboflow for held-out 2D masks. These manually checked held-out masks are evaluation labels, not training labels.

Store a manifest containing:

- scene ID;
- frame IDs;
- train/validation/test split;
- camera files;
- query phrases;
- object IDs;
- annotation version; and
- license/source information.

## Experimental design

### Required methods

1. **2D-only baseline:** Grounded SAM or CLIP-guided SAM on each held-out image independently.
2. **SAGA baseline:** official independent SAM pseudo-label pipeline.
3. **PromptSplat:** the same SAGA training with SAM 2 propagated masks.

### Required ablations

Keep the experiment matrix small:

- Pseudo-label source: SAM versus SAM 2 propagation.
- Number of training views: approximately 25, 50, and 100.
- Input downsample factor: 8 and 4, if both fit.

Do not add multiple CLIP backbones unless the main experiments finish early.

### Metrics

#### Semantic quality

- Mean Intersection over Union on held-out rendered masks.
- Mean pixel accuracy.
- Text-query localization accuracy.
- Boundary F-score if boundary quality is a visible issue.
- Cross-view consistency: agreement of the same selected 3D Gaussians when rendered from different held-out views.

#### Reconstruction quality

- PSNR.
- SSIM.
- LPIPS.

These ensure that adding semantic features does not silently destroy the RGB reconstruction.

#### Systems measurements

- Training time per stage.
- Peak GPU VRAM.
- Text-query latency.
- Click-query latency.
- Browser FPS.
- Scene download size.

Report mean and standard deviation across scenes where meaningful. Do not report only the best scene.

### Statistical treatment

- Fix random seeds for comparable runs.
- Run at least three seeds for the most important small experiment if time permits.
- Report per-scene results as well as the overall mean.
- Include failure cases and low-confidence queries.
- Keep all experiment configurations in version-controlled YAML or JSON files.

## 16 GB GPU plan

SAGA’s documentation explicitly notes that image downsampling can be essential when GPU memory is limited. Start conservatively.

Initial target:

- downsample factor 8;
- 60–80 training images;
- a small tabletop scene;
- a lower-memory SAM/SAM 2 checkpoint where compatible;
- sequential preprocessing and feature training; and
- only one active CUDA process.

Promotion rule:

- Move from downsample 8 to 4 only if measured peak usage remains below approximately 14 GB.
- Increase image count only after the full pipeline completes twice without memory errors.
- Keep at least 1–2 GB free for CUDA fragmentation and viewer/process overhead.

If 3DGS densification causes memory growth:

- lower the training resolution;
- reduce input views;
- prune low-opacity Gaussians;
- stop densification earlier; or
- use a memory-efficient gsplat-based reconstruction and export into the SAGA-compatible format, but only after the official baseline works.

Do not assume two A4000 cards provide a 32 GB memory pool. Use extra cards to run different scene experiments in parallel.

## Week-one feasibility gate

The option is accepted if all of the following work on the A4000:

1. The official SAGA environment builds.
2. One provided scene trains or loads successfully.
3. A point prompt produces a 3D object mask.
4. A text query works through the notebook or script.
5. Peak VRAM is recorded.
6. The resulting PLY loads in a browser viewer.

If only the custom-data preprocessing fails, keep the option and fix capture/COLMAP. If the official provided scene cannot run within 16 GB after documented downsampling, reassess before committing the semester.

## Implementation phases

### Phase 0 — Reproduction and risk removal

- Pin the SAGA environment.
- Reproduce a provided example.
- Record commands, versions, runtime, and VRAM.
- Load the result in GaussianSplats3D.

Exit criterion: a reproducible text/click-selected object.

### Phase 1 — Minimal web explorer

- Create scene manifest format.
- Embed the Gaussian viewer.
- Add camera controls and scene loading.
- Connect one hard-coded query result as an overlay.

Exit criterion: the selected object can be isolated in the browser.

### Phase 2 — Query API

- Wrap CLIP text encoding and SAGA selection.
- Add text and click endpoints.
- Cache results.
- Add threshold and view-mode controls.

Exit criterion: arbitrary supported text queries update the 3D view.

### Phase 3 — Custom data

- Define a capture checklist.
- Process three static scenes.
- Create train/held-out splits.
- Annotate evaluation views.

Exit criterion: at least two custom scenes have usable reconstruction and labels.

### Phase 4 — SAM 2 experiment

- Produce propagated masks.
- Convert them into SAGA input.
- Train paired baseline/proposed runs.
- Verify that only the mask source changed.

Exit criterion: complete metrics for one public and two custom scenes.

### Phase 5 — Evaluation and presentation

- Run the final experiment matrix.
- Add plots and failure cases to the web app.
- Optimize scene loading.
- Prepare three cached examples and one short live query.
- Record a backup video.

## Example 14-week schedule

- Week 1: reproduce SAGA and measure VRAM.
- Week 2: base 3DGS export and browser viewer.
- Week 3: text/click query adapter.
- Week 4: minimal FastAPI and React integration.
- Week 5: first custom scene and capture guide.
- Week 6: remaining custom scenes.
- Week 7: SAM 2 mask propagation adapter.
- Week 8: baseline/proposed paired runs.
- Week 9: view-count ablation.
- Week 10: downsampling ablation and systems measurements.
- Week 11: final evaluation and failure analysis.
- Week 12: web-app research pages and visual polish.
- Week 13: report, citations, reproducibility package.
- Week 14: demo rehearsal, cache, and backup recording.

## Risks and fallbacks

### COLMAP fails on a custom scene

Fallback:

- recapture with slower motion and more texture;
- remove blurred frames;
- use a smaller scene; and
- retain public/preprocessed scenes for the final demo.

### SAM masks change identity between views

This is the main research problem. Use SAM 2 propagation, key-frame correction, and persistent IDs. Show remaining failures rather than hiding them.

### Training exceeds 16 GB

Use downsample 8, fewer views, smaller scenes, sequential stages, and a smaller segmentation checkpoint. Preserve the same settings for paired comparisons.

### Open-vocabulary queries are unreliable

- Show similarity confidence.
- Include positive and negative prompt phrases.
- Evaluate a fixed query set.
- Do not insert an LLM that silently rewrites failed queries.

### Browser highlighting requires too much renderer work

Use the two-layer selected-subset overlay. It is less elegant but preserves the core interaction without writing a renderer from scratch.

### Live preprocessing is too slow

Precompute all scenes. The evaluator’s live action should be query and 3D interaction, not COLMAP or model training.

## Success criteria

The project is successful when:

- at least one public and three custom scenes are reproducible;
- text and click queries select objects in browser-rendered 3D;
- the SAM and SAM 2 variants are compared under matched settings;
- held-out segmentation metrics and systems measurements are reported;
- the app maintains an acceptable interactive frame rate on the presentation machine;
- all examples expose confidence and failure cases; and
- another student can reproduce one complete scene from the instructions.

Suggested quantitative targets are project goals, not claims:

- median text-query response below two seconds for a loaded scene;
- browser interaction above 30 FPS on the presentation machine;
- no out-of-memory run in the final fixed configuration; and
- a measurable held-out consistency or IoU improvement from SAM 2 supervision.

The last target must be reported honestly even if the hypothesis is not supported.

## Deliverables

- SAGA environment/container and setup guide.
- Capture and preprocessing scripts.
- SAM baseline and SAM 2 mask adapters.
- Scene manifests and custom evaluation annotations.
- Paired experiment configurations.
- Metrics and result artifacts.
- FastAPI query service.
- React/Next.js 3D explorer.
- Three prepared demo scenes.
- Technical report and presentation.
- License and attribution file.

## Attribution and license cautions

- SAGA’s repository is Apache-2.0, but verify the license of each included submodule.
- The original Inria 3DGS implementation has its own research-oriented license; do not assume it is Apache-2.0.
- SAM, SAM 2, CLIP/OpenCLIP checkpoints, datasets, and browser viewers each have separate terms.
- Academic demonstration is usually compatible with these research assets, but public commercial deployment must be reviewed independently.

## Reference links

### Main code

- [SAGA official repository](https://github.com/Jumpat/SegAnyGAussians)
- [Original 3DGS repository](https://github.com/graphdeco-inria/gaussian-splatting)
- [SAM 2 repository](https://github.com/facebookresearch/sam2)
- [GaussianSplats3D](https://github.com/mkkellogg/GaussianSplats3D)
- [SuperSplat](https://github.com/playcanvas/supersplat)

### Related code

- [LangSplat](https://github.com/minghanqin/LangSplat)
- [Gaussian Grouping](https://github.com/lkeab/gaussian-grouping)
- [FlashSplat](https://github.com/florinshen/FlashSplat)
- [OpenGaussian](https://github.com/yanmin-wu/OpenGaussian)

### Papers

- [SAGA: Segment Any 3D Gaussians](https://arxiv.org/abs/2312.00860)
- [LangSplat](https://arxiv.org/abs/2312.16084)
- [Gaussian Grouping](https://arxiv.org/abs/2312.00732)
- [FlashSplat](https://arxiv.org/abs/2409.08270)
- [OpenGaussian](https://arxiv.org/abs/2406.02058)
- [3D Gaussian Splatting](https://arxiv.org/abs/2308.04079)
- [Segment Anything](https://arxiv.org/abs/2304.02643)
- [SAM 2](https://arxiv.org/abs/2408.00714)
- [CLIP](https://arxiv.org/abs/2103.00020)