# Final-year project shortlist: AI with Gaussian Splatting

Research checked on 4 September 2026.

This folder deliberately keeps only the two selected options:

1. [Language-Grounded 3DGS Explorer](./option-1-language-grounded-3dgs.md)
2. [Generative 4D Gaussian Studio](./option-2-generative-4d-gaussian-studio.md)

## Is 3D Gaussian Splatting AI?

Plain 3D Gaussian Splatting (3DGS) is best described as a computer-graphics and inverse-rendering method. It optimizes millions of explicit Gaussian primitives so that their rendered views match photographs. It uses differentiable optimization, but the original method does not contain a conventional learned neural network or a reusable pretrained model. A project that only captures a scene, trains 3DGS, and opens the result in a viewer may therefore be judged as a graphics project rather than a strong AI project.

The distinction is less clear for 4D Gaussian Splatting. Several 4DGS systems learn neural deformation fields, feature grids, or temporal models that move canonical Gaussians over time. Those components are machine learning. Nevertheless, the safest presentation is to identify the exact learned task and evaluate it, rather than relying on the name “4DGS” to establish the AI contribution.

Both shortlisted projects make the AI contribution explicit:

- Option 1 distills predictions from vision-language foundation models into a learned 3D Gaussian feature field. It performs open-vocabulary 3D retrieval and segmentation.
- Option 2 uses pretrained reconstruction/video models and learns a time-dependent deformation of Gaussian primitives to create a dynamic 4D asset.

## Recommendation

### Choose Option 1 for the best overall balance

Option 1 is the recommended FYP. Its core AI task—language-guided 3D segmentation—is easy to explain and evaluate. The live demonstration is interactive, the data can be captured with a phone, and memory can be controlled through image downsampling and small scenes. It also has several mature foundations: SAGA, LangSplat, Gaussian Grouping, SAM, and CLIP.

### Choose Option 2 if demo spectacle is the highest priority

Option 2 has a stronger immediate “wow” moment: a photograph or short video becomes an animated object that the evaluator can orbit while time is playing. Its main risk is GPU memory and research-code fragility. The full pipeline must pass the week-one feasibility test in its low-memory configuration before this option is accepted as the final project.

## Scope rule

Do not combine the two projects into one FYP. Each is already a complete project with:

- a research question;
- a reproducible paper implementation;
- custom data;
- quantitative experiments;
- a backend GPU pipeline; and
- a substantial interactive web application.

Combining semantic scene understanding, generative editing, and 4D generation would create integration work without producing a clearer research claim.

## Shared implementation strategy

Use the original research repository as the ML core. Put a small adapter around it instead of rewriting its training code.

Recommended system boundary:

```text
Browser application
    |
    | HTTP / WebSocket
    v
FastAPI orchestration service
    |
    | starts one pinned research pipeline at a time
    v
Python/CUDA worker
    |
    | writes manifests, metrics, previews, and splat assets
    v
Artifact directory or object storage
```

For a university demonstration, a single GPU worker and SQLite job database are sufficient. Redis, Kubernetes, microservices, and multi-user scheduling are unnecessary.

## Shared web-presentation principles

The web app should communicate the research, not merely expose a model:

- Open on a prepared result so the first impression never depends on a long GPU job.
- Keep one short live job for authenticity.
- Show the input, intermediate AI output, final 3D/4D result, and quantitative metrics.
- Provide a “method” view that labels which components are pretrained, optimized per scene, and implemented by the student.
- Include baseline and ablation results inside the app.
- Cache at least three polished examples and record a fallback video.
- Never claim an action is real-time if it is a precomputed result.

## GPU note

The RTX A4000 has 16 GB of VRAM. Multiple A4000 cards do not automatically combine their memory. NVLink is not required for ordinary distributed data-parallel training, but data parallelism still gives every GPU its own model copy. For these projects, multiple cards are most useful for running independent scenes or experiments concurrently.

The detailed dossiers distinguish:

- claims reported by repository authors;
- estimates that must be measured locally; and
- hard feasibility gates where 16 GB compatibility is not established.

## Core references

- Kerbl et al., [3D Gaussian Splatting for Real-Time Radiance Field Rendering](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/) (ACM TOG/SIGGRAPH 2023).
- [Nerfstudio](https://github.com/nerfstudio-project/nerfstudio), an established neural rendering toolkit.
- [gsplat](https://github.com/nerfstudio-project/gsplat), a CUDA-accelerated Gaussian-splatting library.
- [GaussianSplats3D](https://github.com/mkkellogg/GaussianSplats3D), a Three.js Gaussian viewer with PLY, SPLAT, and compressed KSPLAT support.
- [SuperSplat](https://github.com/playcanvas/supersplat), an MIT-licensed browser editor for Gaussian splats.
- [SuperSplat Viewer](https://github.com/playcanvas/supersplat-viewer), an embeddable MIT-licensed WebGPU/WebGL viewer.

## What “complete” should mean

The final submission should contain:

- a reproducible environment or container;
- scripts for one public example and one custom example;
- fixed train/validation/test definitions;
- logged peak VRAM and runtime;
- baseline and ablation results;
- the web application;
- at least three prepared demo cases;
- a short technical report; and
- clear attribution and license notes for every model, dataset, and repository.
