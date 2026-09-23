# Option 2 — DreamSplat4D: Generative 4D Gaussian Studio

## One-sentence proposal

Build a web studio that turns a foreground image or short object video into an animated 4D Gaussian asset, then lets the user orbit the object while its motion plays, scrub time, compare generation settings, and inspect quality/runtime experiments.

## Recommendation

This is the higher-wow, higher-risk option.

It is viable only if a low-memory end-to-end sample runs on the RTX A4000 during week one. Published repositories provide checkpoints and memory-reduced configurations, but their authors do not establish that the complete pipeline fits 16 GB. There are public out-of-memory reports even on larger cards.

The safe core is **video-to-4D**. Image-to-4D generation should be a stretch feature because it adds a large video diffusion model.

## Proposed title

**DreamSplat4D: Resource-Aware Generation and Interactive Web Rendering of Dynamic Gaussian Assets**

Alternative academic title:

**Evaluating Low-Memory Generative 4D Gaussian Splatting from Monocular Object Videos**

## Important terminology

This project is **not a world model**.

A world model predicts how an environment evolves, usually conditioned on actions or controls, and supports counterfactual rollouts. DreamGaussian4D and L4GM reconstruct or generate one dynamic object sequence. They do not learn a general action-conditioned transition model.

Use the accurate description:

> generative 4D reconstruction/content creation with Gaussian Splatting

This is still a strong AI project because it uses pretrained generative/reconstruction models and learns a neural deformation field over time.

## Evaluator demo

The evaluator chooses a prepared image or uploads a short object video.

The application shows a visible pipeline:

```text
foreground extraction
    -> static 3D Gaussian initialization
    -> temporal/deformation optimization
    -> 4D Gaussian frame export
    -> interactive browser playback
```

The result is not just a rendered video. The evaluator can:

- orbit around the object while it moves;
- pause and scrub time;
- change playback speed;
- compare low-memory and higher-quality configurations;
- view source, novel-view, depth, and motion panels;
- inspect temporal artifacts;
- download a video or frame sequence; and
- open the experiment report for that generation.

The homepage should load a prepared 4D result immediately. A short live job can run separately without blocking the first impression.

## Research foundation

### Primary implementation: DreamGaussian4D

Build on [DreamGaussian4D](https://github.com/jiawei-ren/dreamgaussian4d).

The official repository already provides:

- image-to-4D generation;
- video-to-4D reconstruction;
- LGM-based static initialization;
- optional DreamGaussian static initialization;
- Stable Video Diffusion-based driving-video generation;
- a deformable Gaussian model;
- `4d_low`, `4d_demo`, and `4d_c4d_low` configurations;
- Consistent4D evaluation scripts;
- per-frame mesh export;
- a Gradio demo; and
- an MIT repository license.

Its low/demo configurations reduce views, batch size, temporal-grid size, or input sampling. These are useful starting points, not proof of 16 GB compatibility.

The associated paper is:

- Ren et al., [DreamGaussian4D: Generative 4D Gaussian Splatting](https://arxiv.org/abs/2312.17142), arXiv 2023.

Be transparent that this paper is an arXiv work rather than presenting it as a CVPR/ICLR publication.

### Strong feed-forward comparator: L4GM

[L4GM](https://github.com/nv-tlabs/L4GM-official) is a NeurIPS 2024 large 4D reconstruction model. It takes a single-view video and produces animated 3D Gaussians in a feed-forward pass.

The official release provides:

- Apache-2.0 code;
- reconstruction and interpolation checkpoints;
- 3D and 4D inference scripts;
- 16-frame example inference;
- a Gradio demo; and
- a total model-repository size of approximately 3.73 GB for the released files when checked.

L4GM is attractive as a baseline, but it is not safe to make it mandatory:

- its published training command uses an eight-GPU accelerator configuration;
- the public Hugging Face demo requests an A10G Large GPU, which has more VRAM than an A4000;
- a public issue reports out-of-memory behavior for long videos on a 48 GB card; and
- the authors recommend shorter clips, running reconstruction/interpolation separately, and memory-efficient attention.

Use L4GM quantitatively only if its 16-frame inference passes the local feasibility test.

### Static initialization: LGM

[LGM: Large Multi-View Gaussian Model](https://github.com/3DTopia/LGM) is an ECCV 2024 Oral paper and official implementation.

Its repository reports approximately 10 GB of inference memory when LGM and its image/multi-view dependencies are loaded. This makes it a plausible static initializer on the A4000 when stages are executed sequentially.

Paper:

- Tang et al., [LGM: Large Multi-View Gaussian Model for High-Resolution 3D Content Creation](https://arxiv.org/abs/2402.05054), ECCV 2024 Oral.

### Dynamic representation references

- Wu et al., [4D Gaussian Splatting for Real-Time Dynamic Scene Rendering](https://arxiv.org/abs/2310.08528), CVPR 2024.
- Yang et al., [Real-time Photorealistic Dynamic Scene Representation and Rendering with 4D Gaussian Splatting](https://arxiv.org/abs/2310.10642), ICLR 2024.
- Jiang et al., [Consistent4D: Consistent 360° Dynamic Object Generation from Monocular Video](https://arxiv.org/abs/2311.02848), ICLR 2024.
- Blattmann et al., [Stable Video Diffusion: Scaling Latent Video Diffusion Models to Large Datasets](https://arxiv.org/abs/2311.15127), 2023.

## Why this is an AI project

Depending on the chosen path, the system contains:

1. A foreground segmentation/background-removal model.
2. LGM, a learned feed-forward model that predicts a 3D Gaussian object from images.
3. Stable Video Diffusion, which creates a driving motion sequence from a static image.
4. A learned HexPlane/K-Planes-style temporal feature grid and deformation MLP that changes Gaussian position, scale, rotation, and opacity over time.
5. Optional L4GM inference, which directly predicts animated Gaussian representations from video.

DreamGaussian4D performs per-input optimization. That is a legitimate learned component: the system fits temporal/deformation parameters using neural and generative priors. It is not merely playing a mesh animation.

The report should label:

- **Pretrained:** LGM, Stable Video Diffusion, optional L4GM, and foreground segmentation.
- **Optimized per asset:** canonical Gaussians and temporal deformation field.
- **Student contribution:** resource-aware pipeline, experiment design, 4D export format, browser renderer/player, custom data, and evaluation.

## Recommended research question

Primary question:

> What speed, memory, and novel-view/temporal quality trade-offs arise when generative 4D Gaussian Splatting is constrained to a 16 GB workstation GPU?

Secondary question:

> How does motion supervision from a real monocular video compare with Stable Video Diffusion-generated motion when both are optimized into the same 4D Gaussian representation?

Recommended hypotheses:

- Lower temporal/spatial settings will substantially reduce peak VRAM and runtime while preserving enough visual quality for interactive web use.
- Real object videos will produce more faithful motion than generated driving videos, while image-to-4D will offer greater creative accessibility.

The first question is mandatory. The second is included only if the image-to-video stage fits.

## Exact project scope

### Required core

- Reproduce DreamGaussian4D on at least one provided sample.
- Implement video-to-4D using the low-memory configuration.
- Evaluate on a small Consistent4D subset.
- Process a custom set of short foreground object videos.
- Export the learned dynamic Gaussians at fixed timestamps.
- Play the 4D asset interactively in a browser.
- Compare at least two memory/quality configurations.
- Report novel-view quality, temporal quality, runtime, and peak VRAM.

### Conditional feature

Use L4GM as a feed-forward baseline only if 16-frame inference fits on the A4000 without changing the scientific task.

### Stretch features

- Image-to-4D with Stable Video Diffusion.
- Text-to-image followed by image-to-4D.
- Motion transfer between objects.
- Mesh/GLB export.
- WebXR viewing.

### Explicitly out of scope

- Training LGM, L4GM, or Stable Video Diffusion from scratch.
- Reproducing the full Objaverse training setup.
- Long videos.
- Full human avatars with hands and faces.
- Large dynamic rooms.
- Physically correct interaction.
- Action-conditioned future prediction.
- An unrestricted public generation service.

## Choose the right core input

### Core: short video-to-4D

Use:

- an isolated object;
- a simple or removed background;
- 16–24 sampled frames;
- approximately one short motion cycle;
- limited occlusion; and
- a mostly fixed camera for custom clips.

This skips the largest optional component—video diffusion—and makes the observed motion the optimization target.

Good custom subjects:

- a toy rotating or nodding;
- a flower opening in a controlled clip;
- a small articulated figure;
- a plush toy with simple motion;
- a hand moving a rigid object, if the hand is cropped or masked out.

Avoid transparent objects, fast topology changes, hair, loose fabric, and large self-occlusions.

### Stretch: image-to-4D

The repository’s image path:

1. removes the background;
2. uses Stable Video Diffusion to produce a driving video;
3. initializes static geometry with LGM or DreamGaussian;
4. optimizes temporal deformation; and
5. exports an animation.

Run these stages as separate processes and release GPU memory between them. Do not load SVD, LGM, and the 4D optimizer simultaneously on a 16 GB card.

## End-to-end pipeline

### Stage 1 — Input validation

For images:

- require one centered object;
- show the foreground mask;
- allow crop and mask correction; and
- reject extremely small or heavily occluded subjects.

For videos:

- trim to a short interval;
- sample a fixed number of frames;
- crop to a square;
- remove or mask the background;
- show a contact sheet before starting; and
- store the exact sampled frames in the job artifacts.

### Stage 2 — Static 3D initialization

Preferred path:

- run LGM on the first/representative frame;
- write the static Gaussian checkpoint;
- render an orbit preview; and
- stop if the static geometry is unusable.

Fallback:

- use DreamGaussian’s slower per-object optimization for a small curated case.

LGM and DreamGaussian should not both be mandatory experiments.

### Stage 3 — Motion source

For video-to-4D:

- use sampled frames from the real input clip.

For image-to-4D:

- run the repository’s Stable Video Diffusion generation script;
- expose seed and motion bucket controls only if they are stable;
- select one driving clip; and
- preserve it as an experiment artifact.

### Stage 4 — 4D Gaussian optimization

Start from DreamGaussian4D’s provided configuration rather than rewriting the model.

The optimizer learns:

- canonical Gaussian parameters;
- temporal feature planes;
- an MLP-based deformation;
- time-varying position;
- scale and rotation changes; and
- optional opacity changes.

Start with:

- `configs/4d_demo.yaml` for the smallest image-to-4D smoke test; or
- `configs/4d_c4d_low.yaml` for the low-memory video-to-4D path.

The final report must record every changed parameter instead of referring vaguely to a “low setting.”

### Stage 5 — Export time-indexed Gaussians

4D Gaussian browser formats are less standardized than static 3DGS formats. Keep the export deliberately simple.

Implement a small exporter based on the same idea as `export_perframe_3DGS.py` in the official 4DGaussians repository:

1. Load the canonical Gaussians and deformation checkpoint.
2. Evaluate the deformation at 16 fixed normalized timestamps.
3. Write one PLY/SPLAT-compatible Gaussian frame per timestamp.
4. Normalize all frames into one shared coordinate system and bounding box.
5. Write a manifest.

Suggested manifest:

```json
{
  "version": 1,
  "frameCount": 16,
  "fps": 8,
  "loop": true,
  "bounds": {
    "min": [-1, -1, -1],
    "max": [1, 1, 1]
  },
  "frames": [
    {"time": 0.0, "url": "frame-000.ksplat"},
    {"time": 0.0667, "url": "frame-001.ksplat"}
  ]
}
```

DreamGaussian4D’s provided configurations use a small number of Gaussians compared with room-scale captures, so preloading a short frame sequence is plausible.

### Stage 6 — Browser 4D player

Recommended implementation:

- Three.js plus [GaussianSplats3D](https://github.com/mkkellogg/GaussianSplats3D);
- convert each frame into compressed KSPLAT;
- preload the next frames;
- keep camera position independent from animation time;
- swap or update the active splat buffer on the animation clock; and
- pause buffer updates while the user is dragging the timeline.

Lowest-risk prototype:

1. Preload all 16 low-point-count frames as separate scenes.
2. Show one and hide the others.
3. Advance with discrete frame timing.
4. Confirm orbiting remains interactive.

Optimization after correctness:

- reuse one GPU buffer;
- update only changed attributes;
- interpolate timestamps if the representation supports it; and
- add progressive asset loading.

Fallback:

- export per-frame meshes and use a Three.js mesh-sequence player.

The fallback preserves interactivity but should be labelled as a mesh visualization of a Gaussian-generated result, not as direct Gaussian rendering.

## Web application

### Recommended stack

- Frontend: Next.js or React with TypeScript.
- 3D/4D player: Three.js and GaussianSplats3D.
- API: FastAPI.
- GPU jobs: one isolated Python worker process.
- Job records: SQLite.
- Artifacts: local disk initially.
- Progress: Server-Sent Events or WebSocket.

### Main pages

#### 1. Gallery landing page

- Autoplay a lightweight prepared 4D asset.
- Present image-to-4D and video-to-4D examples.
- Show generation time and hardware honestly.
- Link directly to the interactive player.

#### 2. Creation studio

- Image/video upload.
- Crop, trim, frame sample, and mask preview.
- Choose “fast/demo” or “quality” preset.
- Show the individual pipeline stages.
- Stream logs/progress without exposing raw terminal output.
- Save all generation parameters.

#### 3. 4D player

- Orbit, pan, and zoom.
- Play, pause, scrub, loop, and speed controls.
- Source-video overlay.
- Time and camera reset.
- Novel-view presets.
- Optional depth/motion view.
- Download rendered MP4, manifest, or frame assets.

#### 4. Comparison lab

- Synchronize two results to the same camera and time.
- Compare demo/low settings.
- Show PSNR, SSIM, LPIPS, temporal error, runtime, VRAM, and asset size.
- Expose visible failure cases such as duplicated limbs or melting back views.

#### 5. Method and limitations

- Separate pretrained and optimized components.
- Explain why this is not a world model.
- Link every paper and repository.
- Show the 16 GB feasibility evidence.

### Suggested API

```text
POST /api/assets/validate
POST /api/jobs/video-to-4d
POST /api/jobs/image-to-4d
GET  /api/jobs/{job_id}
GET  /api/jobs/{job_id}/events
POST /api/jobs/{job_id}/cancel
GET  /api/results
GET  /api/results/{result_id}
GET  /api/results/{result_id}/manifest
GET  /api/experiments
GET  /api/experiments/{experiment_id}
```

Only enable image-to-4D after its feasibility gate passes.

## Dataset plan

### Public benchmark

Use a manageable subset of [Consistent4D](https://consistent4d.github.io/):

- select approximately 5–10 objects;
- include slow and moderate motion;
- include at least one difficult case;
- use the repository’s existing conversion/evaluation path; and
- preserve the official split/protocol where available.

The public subset provides views that custom monocular phone clips cannot provide for quantitative novel-view evaluation.

### Custom data

Collect approximately 8–12 short object clips:

- 2–4 seconds before sampling;
- simple background or clean foreground mask;
- 16–24 final frames;
- diverse rigid and mildly non-rigid motion; and
- consent/ownership documented.

For image-to-4D, use 8–12 foreground images from the same object categories so the presentation can compare real and generated motion.

Do not claim quantitative novel-view accuracy on a custom single-camera clip without novel-view ground truth. Use public multiview data for that claim and a user study/failure analysis for custom examples.

## Experimental design

### Required methods

1. **Static baseline:** LGM output repeated through time. This establishes what motion modeling contributes.
2. **DreamGaussian4D fast/demo configuration.**
3. **DreamGaussian4D low/quality configuration that fits 16 GB.**
4. **L4GM 16-frame inference**, only if the local feasibility test passes.

Do not report L4GM numbers produced on different data/settings as if they were a direct local comparison.

### Required ablations

Keep the matrix controlled:

- fast/demo versus selected higher-quality configuration;
- 8 versus 16 temporal samples;
- real-video motion versus SVD-generated motion, only if image-to-4D fits.

Optional:

- LGM versus DreamGaussian static initialization on three examples.

### Visual-quality metrics

- PSNR on held-out novel views.
- SSIM on held-out novel views.
- LPIPS on held-out novel views.
- CLIP image similarity when no pixel-aligned reference exists.

### Temporal metrics

- Temporal LPIPS between adjacent rendered frames.
- Optical-flow warping error where a reliable flow estimate is available.
- Cycle endpoint error for looping motions.
- Flicker score measured on a fixed novel camera trajectory.

State exactly how each temporal metric is calculated. “Temporal consistency” without a definition is not a result.

### Systems metrics

- Peak VRAM for every stage.
- Static initialization time.
- Motion-generation time.
- 4D optimization time.
- Export time.
- Browser load time.
- Browser FPS while animation and camera movement occur together.
- Compressed asset size.

### Human evaluation

For custom clips, a small blinded study can ask participants to rate:

- motion plausibility;
- identity preservation;
- multiview consistency; and
- overall preference.

Randomize method order. Do not use the user study as a substitute for public-dataset metrics.

## 16 GB feasibility evidence and cautions

### Positive evidence

- DreamGaussian4D ships memory-reduced `4d_low`, `4d_demo`, and `4d_c4d_low` configurations.
- The demo configuration lowers training batch size and input sampling relative to larger settings.
- LGM’s repository reports an approximately 10 GB inference footprint for its combined inference stack.
- Video-to-4D can skip Stable Video Diffusion entirely.
- The stages can run sequentially in separate processes.

### Negative evidence

- DreamGaussian4D has a public unresolved report of out-of-memory behavior on an RTX A5000.
- L4GM’s hosted demo requests a GPU class with more than 16 GB.
- L4GM has a public long-video out-of-memory report even on 48 GB.
- L4GM training is designed for eight GPUs and is not an A4000 training target.
- Research repositories depend on pinned CUDA/PyTorch versions and custom rasterizers.

Conclusion:

> The project is plausible on 16 GB only with a short video, low-memory settings, sequential stages, and measured confirmation. It is not guaranteed.

## Mandatory week-one feasibility gate

Run these tests in order.

### Test 1 — Environment

- Build the exact pinned DreamGaussian4D environment.
- Compile its Gaussian rasterizer and `simple-knn`.
- Record driver, CUDA, PyTorch, xFormers, and compiler versions.

Pass condition: the official import/smoke test completes after a fresh environment activation.

### Test 2 — Static LGM

Run the provided sample through:

```bash
python lgm/infer.py big --test_path <sample-image>
```

Pass condition:

- valid Gaussian output;
- no OOM;
- measured peak usage leaves enough margin to run later stages separately.

### Test 3 — Low-memory video-to-4D

Run the shortest official Consistent4D sample with:

```bash
python main_4d.py \
  --config configs/4d_c4d_low.yaml \
  input=<sample-video-directory>
```

Pass condition:

- all optimization iterations finish;
- peak VRAM stays below the card limit;
- a moving result renders from a novel view; and
- runtime is practical for repeated experiments.

### Test 4 — Export and browser

- Export 16 Gaussian timestamps.
- Load them in the prototype web player.
- Orbit while playing.

Pass condition: stable playback without a browser crash or multi-minute load.

### Optional Test 5 — Image-to-4D

Run SVD, LGM, and deformation as separate processes.

Pass condition: all stages fit individually. Failure does not invalidate the video-to-4D core.

### Optional Test 6 — L4GM

Run the official 16-frame example with reconstruction and interpolation separated.

Pass condition: it fits without changing the task or reducing the model to an unreported configuration.

If Tests 1–4 fail after the documented low-memory settings, discard Option 2 and select Option 1. Do not spend the semester creating a new 4D model or custom CUDA renderer to rescue it.

## Memory-reduction rules

- Run SVD, LGM, and 4D optimization in separate OS processes.
- Delete the prior process before starting the next stage.
- Use mixed precision exactly as supported by the repository.
- Enable xFormers or another documented memory-efficient attention path.
- Use 16 or fewer final frames initially.
- Use the provided low/demo config before changing architecture code.
- Lower batch/views and resolution one variable at a time.
- Record changes in experiment configuration files.
- Avoid concurrent display processes on the training GPU.
- Use additional A4000 cards for separate experiments, not as an assumed shared-memory pool.

## Implementation phases

### Phase 0 — Reproduction and hard gate

- Complete Tests 1–4.
- Pin the environment.
- Record peak VRAM and runtime.
- Commit one known-good sample manifest.

Exit criterion: an official sample plays as a time-varying asset in the browser.

### Phase 1 — Video preprocessing

- Implement trim, sample, crop, and background-mask stages.
- Create a contact-sheet approval screen.
- Save deterministic preprocessing parameters.

Exit criterion: a custom clip matches the research repository’s expected format.

### Phase 2 — Job orchestration

- Wrap LGM and 4D optimization as separate worker commands.
- Parse progress into structured events.
- Add cancellation and failure states.
- Save logs and configuration with each result.

Exit criterion: one API request produces a result manifest.

### Phase 3 — 4D web player

- Implement preload, play, pause, scrub, orbit, and speed.
- Add source-video synchronization.
- Measure load time and FPS.
- Add mesh fallback only if needed.

Exit criterion: the presentation machine can orbit while motion plays.

### Phase 4 — Data and baseline runs

- Select Consistent4D subset.
- Capture custom clips.
- Run static and dynamic baselines.
- Verify output and metric scripts.

Exit criterion: complete artifacts for at least five public and five custom cases.

### Phase 5 — Experiments

- Run fast/quality comparisons.
- Run temporal-sample ablation.
- Run image-to-4D comparison only if feasible.
- Analyze failures.

Exit criterion: fixed result set with no cherry-picked omissions.

### Phase 6 — Presentation

- Build gallery and comparison lab.
- Add methodology and limitations.
- Cache polished examples.
- Rehearse one short live generation or preprocessing action.
- Record a backup video.

## Example 14-week schedule

- Week 1: hard feasibility gate and environment pinning.
- Week 2: timestamp exporter and basic browser player.
- Week 3: input preprocessing.
- Week 4: FastAPI job worker and progress events.
- Week 5: player controls and source synchronization.
- Week 6: Consistent4D subset and baseline metrics.
- Week 7: custom video collection.
- Week 8: fast/quality experiment runs.
- Week 9: temporal-sample ablation.
- Week 10: optional SVD or L4GM experiment.
- Week 11: final metrics, user study, and failure analysis.
- Week 12: gallery, comparison lab, and visual polish.
- Week 13: report and reproducibility package.
- Week 14: demo optimization, rehearsal, and backup recording.

## Risks and fallbacks

### The full model does not fit 16 GB

Fallback sequence:

1. Use video-to-4D and skip SVD.
2. Use the repository’s low/demo config.
3. Reduce temporal frames.
4. Run every stage in a fresh process.
5. Restrict the data to centered objects.

If the official low path still fails, reject this project and use Option 1.

### Back views melt or duplicate geometry

- Constrain inputs to objects represented by LGM’s training distribution.
- Reject severe self-occlusion.
- Show the first orbit preview before dynamic optimization.
- Include failures in the analysis.

### Motion flickers

- Compare temporal resolutions.
- Evaluate fixed-camera flicker.
- Avoid aggressive motions.
- Use the real-video core rather than SVD-generated motion.

### Dynamic splat web rendering is unstable

- Limit output to 16 small Gaussian frames.
- Use discrete frame switching first.
- Fall back to the exported mesh sequence.
- Keep pre-rendered orbit videos as presentation backup.

### A live job is too slow

- Open with prepared interactive assets.
- Run only a short demo-quality job live.
- Show honest measured runtime.
- Never fake a cached result as live inference.

### Dependency installation consumes the schedule

- Freeze a successful Conda lockfile or container immediately.
- Keep the research environment isolated from the web environment.
- Do not upgrade CUDA/PyTorch after reproduction without a specific reason.

## Success criteria

The project is successful when:

- the video-to-4D core runs repeatedly on the A4000;
- at least five public and eight custom objects are processed;
- two resource settings are compared under matched inputs;
- novel-view and temporal metrics are reported;
- peak VRAM and stage runtime are measured;
- 4D results are interactive in the browser rather than only MP4 files;
- limitations are visible and documented; and
- one complete example can be reproduced from the instructions.

Suggested engineering targets, to be validated rather than assumed:

- no final-stage OOM;
- 16 timestamp frames per result;
- interactive camera control during playback;
- prepared-result load time suitable for a live presentation; and
- one short demo setting that completes within the presentation window.

## Deliverables

- Pinned DreamGaussian4D environment/container.
- Video/image preprocessing pipeline.
- LGM static-initialization adapter.
- Low-memory 4D optimization configurations.
- Per-timestamp Gaussian exporter and manifest specification.
- Interactive browser 4D player.
- FastAPI job orchestration.
- Consistent4D subset manifest.
- Custom object clips and consent/source records.
- Metric scripts and experiment configurations.
- Prepared gallery and comparison lab.
- Technical report, presentation, and fallback recording.
- License and attribution file.

## Attribution and license cautions

- DreamGaussian4D’s repository is MIT-licensed, but its model dependencies and weights have separate terms.
- L4GM code/model release is Apache-2.0 according to its repository/model card.
- LGM, Stable Video Diffusion, Zero123, ImageDream/MVDream, Objaverse, and Consistent4D must each be reviewed separately.
- The original 3DGS implementation has a research-oriented license.
- A university demo is not equivalent to permission for a public commercial generation service.

## Reference links

### Main code

- [DreamGaussian4D](https://github.com/jiawei-ren/dreamgaussian4d)
- [L4GM](https://github.com/nv-tlabs/L4GM-official)
- [LGM](https://github.com/3DTopia/LGM)
- [4DGaussians](https://github.com/hustvl/4DGaussians)
- [GaussianSplats3D](https://github.com/mkkellogg/GaussianSplats3D)
- [SuperSplat](https://github.com/playcanvas/supersplat)

### Papers

- [DreamGaussian4D](https://arxiv.org/abs/2312.17142)
- [L4GM](https://arxiv.org/abs/2406.10324)
- [LGM](https://arxiv.org/abs/2402.05054)
- [4D Gaussian Splatting for Real-Time Dynamic Scene Rendering](https://arxiv.org/abs/2310.08528)
- [Real-time Photorealistic Dynamic Scene Representation and Rendering with 4D Gaussian Splatting](https://arxiv.org/abs/2310.10642)
- [Consistent4D](https://arxiv.org/abs/2311.02848)
- [Stable Video Diffusion](https://arxiv.org/abs/2311.15127)
- [3D Gaussian Splatting](https://arxiv.org/abs/2308.04079)
