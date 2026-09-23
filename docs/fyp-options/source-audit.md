# Source and feasibility audit

Checked on 4 September 2026. Repository counts and activity change over time; the durable facts below are links, released functionality, documented hardware, and known limitations.

## Option 1 sources

### SAGA

- Official repository: [Jumpat/SegAnyGAussians](https://github.com/Jumpat/SegAnyGAussians)
- Paper: [Segment Any 3D Gaussians](https://arxiv.org/abs/2312.00860)
- Repository branch checked: `v2`
- Repository license: Apache-2.0
- Released functionality relevant to the project:
  - 3DGS training;
  - SAM mask extraction;
  - mask-scale extraction;
  - CLIP feature extraction;
  - contrastive Gaussian feature training;
  - point and multi-point prompts;
  - open-vocabulary notebook;
  - GUI and mask rendering.
- Documented low-memory control: mask extraction supports downsampling, and the README states that downsampling can be essential with limited GPU memory.
- Important limitation: open-vocabulary interaction is supplied in a notebook rather than a polished web/API layer. This is an appropriate student integration task.

### LangSplat

- Official repository: [minghanqin/LangSplat](https://github.com/minghanqin/LangSplat)
- Paper: [LangSplat](https://arxiv.org/abs/2312.16084), CVPR 2024 Highlight
- Released pretrained models, preprocessed datasets, autoencoder, optimizer, and evaluation code.
- Documented hardware: the repository states 24 GB VRAM for training to paper-evaluation quality.
- Decision: use as related work and an optional public-checkpoint comparison, not as the mandatory A4000 training base.

### Gaussian Grouping

- Official repository: [lkeab/gaussian-grouping](https://github.com/lkeab/gaussian-grouping)
- Paper: [Gaussian Grouping](https://arxiv.org/abs/2312.00732), ECCV 2024
- Repository license: Apache-2.0
- Released SAM/DEVA pseudo-label preparation, identity-feature training, segmentation, object removal, inpainting, and style-transfer workflows.
- Public issue reports include memory growth and out-of-memory behavior on large scenes, including a report involving a 24 GB RTX 4090.
- Decision: use its editing and evaluation ideas; do not make it the primary implementation.

### FlashSplat

- Official repository: [florinshen/FlashSplat](https://github.com/florinshen/FlashSplat)
- Paper: [FlashSplat](https://arxiv.org/abs/2409.08270), ECCV 2024
- Claimed method property: closed-form/linear optimization for 3D Gaussian labels, with optimization reported within approximately 30 seconds in the project description.
- Repository limitations when checked:
  - detailed installation/tutorial section remained incomplete;
  - SAM 2 multi-view mask association was listed but not implemented; and
  - a public issue reported insufficient memory on a 3080 Ti.
- Decision: optional speed baseline only after the SAGA core is complete.

### OpenGaussian

- Official repository: [yanmin-wu/OpenGaussian](https://github.com/yanmin-wu/OpenGaussian)
- Paper: [OpenGaussian](https://arxiv.org/abs/2406.02058), NeurIPS 2024
- Released custom-video guidance, ScanNet/LERF training, text selection, evaluation, and click-selection code.
- Repository caveat: click-selection is marked as not tested with the current code version.
- Public issue evidence includes stage-three OOM on a 24 GB 4090 for a larger LERF scene.
- Decision: reference for point-level open-vocabulary understanding, not the primary 16 GB implementation.

## Option 2 sources

### DreamGaussian4D

- Official repository: [jiawei-ren/dreamgaussian4d](https://github.com/jiawei-ren/dreamgaussian4d)
- Paper: [DreamGaussian4D](https://arxiv.org/abs/2312.17142)
- Repository license: MIT
- Released functionality:
  - image-to-4D;
  - video-to-4D;
  - LGM and DreamGaussian static initialization;
  - Stable Video Diffusion driving-video generation;
  - temporal Gaussian optimization;
  - Consistent4D evaluation;
  - low/demo configuration files;
  - mesh-frame export; and
  - a Gradio application.
- Relevant supplied configurations include `4d_low.yaml`, `4d_demo.yaml`, and `4d_c4d_low.yaml`.
- Important evidence against overconfidence: a public unresolved issue reports out-of-memory behavior on an RTX A5000.
- Decision: primary codebase, conditional on the week-one A4000 test.

### L4GM

- Official repository: [nv-tlabs/L4GM-official](https://github.com/nv-tlabs/L4GM-official)
- Paper: [L4GM](https://arxiv.org/abs/2406.10324), NeurIPS 2024
- Repository license: Apache-2.0
- Released reconstruction/interpolation checkpoints and 3D/4D inference code.
- The documented standard example uses 16 output frames.
- The model repository reported approximately 3.73 GB total stored files when checked.
- The public hosted demo requested an A10G Large GPU rather than a 16 GB class.
- A public issue reports OOM for roughly 90-frame videos on a 48 GB GPU. The author’s suggested mitigations are:
  - split long clips;
  - run reconstruction and interpolation separately; and
  - replace xFormers attention with FlashAttention.
- Published training uses an eight-GPU accelerator configuration and up to 500 epochs for the released checkpoint.
- Decision: optional inference baseline; training is explicitly out of scope.

### LGM

- Official repository: [3DTopia/LGM](https://github.com/3DTopia/LGM)
- Paper: [LGM](https://arxiv.org/abs/2402.05054), ECCV 2024 Oral
- Repository claim: inference uses approximately 10 GB GPU memory while loading LGM and the referenced image/multi-view components.
- Decision: preferred static initializer, tested as an isolated process.

### 4DGaussians

- Official repository: [hustvl/4DGaussians](https://github.com/hustvl/4DGaussians)
- Paper: [4D Gaussian Splatting for Real-Time Dynamic Scene Rendering](https://arxiv.org/abs/2310.08528), CVPR 2024
- Repository license: Apache-2.0
- Repository reports approximately:
  - 8 minutes for D-NeRF scenes;
  - 30 minutes for HyperNeRF scenes; and
  - real-time rendering in its tested environment.
- It includes `export_perframe_3DGS.py`, which is the design reference for the proposed browser frame exporter.
- Decision: representation/export reference rather than a second mandatory ML codebase.

## Browser foundations

### GaussianSplats3D

- Repository: [mkkellogg/GaussianSplats3D](https://github.com/mkkellogg/GaussianSplats3D)
- License: MIT
- Supports PLY, SPLAT, and compressed KSPLAT assets.
- Integrates with Three.js through a drop-in viewer.
- Best fit when the application needs custom selection or time controls.

### SuperSplat

- Repository: [playcanvas/supersplat](https://github.com/playcanvas/supersplat)
- License: MIT
- Mature browser-based Gaussian editor.
- Best used as an offline inspection, cleanup, cropping, and conversion tool.

### SuperSplat Viewer

- Repository: [playcanvas/supersplat-viewer](https://github.com/playcanvas/supersplat-viewer)
- License: MIT
- Embeddable WebGPU/WebGL viewer with PLY, SOG, and compressed PLY support.
- Its documented animation tracks concern viewer/camera experiences; direct support for the selected project’s learned 4D deformation should not be assumed.

## Claims that must be measured locally

Neither dossier treats these as established facts:

- exact peak VRAM on the RTX A4000;
- training time on the university machines;
- browser FPS for the final assets;
- custom-scene reconstruction quality;
- SAM 2’s improvement over the SAGA baseline;
- whether L4GM 16-frame inference fits 16 GB; and
- whether DreamGaussian4D’s complete low-memory video path fits 16 GB.

These values belong in the week-one smoke-test report and final experiment logs.

## Reproducibility record

For every retained repository, save:

- exact Git commit;
- environment lockfile;
- CUDA and compiler versions;
- downloaded checkpoint name and hash;
- dataset version;
- command and configuration;
- start/end time;
- peak VRAM;
- output artifact hashes; and
- local patches.

This turns an unstable research-code integration into a defensible final-year engineering and experimental contribution.
