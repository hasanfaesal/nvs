# Third-party code

Every upstream repo PromptSplat builds on, with its pin and license. Provenance types: `docs/spec/05-codebase-map.md` §1.

| Name | Upstream | Fork / branch | Pinned base SHA (date) | License | Use |
|---|---|---|---|---|---|
| SAGA | https://github.com/Jumpat/SegAnyGAussians (v2) | hasanfaesal/SegAnyGAussians @ promptsplat | `2d4c5d77c857c956d747e4775d3d72c4ec5dfe16` (2026-09-24) | Apache-2.0 (+ Inria notice on 3DGS files) | FORK |
| gsplat | https://github.com/nerfstudio-project/gsplat (main) | hasanfaesal/gsplat @ promptsplat | `512d366b67073d77ca099ede742683c165dfc23b` (2026-09-24) | Apache-2.0 | FORK |
| AutoSeg-SAM2 | https://github.com/zrporz/AutoSeg-SAM2 | hasanfaesal/AutoSeg-SAM2 @ promptsplat | `58143073acaf681ee0bbbda405d877f185ae850f` (2026-09-24) | MIT | FORK |
| SAM 2 | https://github.com/facebookresearch/sam2 | – | (SHA at T-004) | Apache-2.0 | PIP (git) |
| segment-anything | https://github.com/facebookresearch/segment-anything | – | (SHA at T-004) | Apache-2.0 | PIP (git) |
| OpenCLIP | https://github.com/mlfoundations/open_clip | – | (version at T-004) | MIT | PIP |
| LangSplat | https://github.com/minghanqin/LangSplat | – | (SHA at T-E01) | Inria/MPII Gaussian-Splatting license (non-commercial research only) | COPY (eval GT/localization) |
| Gaussian Grouping | https://github.com/lkeab/gaussian-grouping | – | (SHA at T-E02) | Apache-2.0 | COPY (eval metrics) |
| Segment-then-Splat | https://github.com/luyr/Segment-then-Splat | – | (SHA at T-B07) | MIT | COPY (mask dedup) |
| Spark | https://github.com/sparkjsdev/spark | – | npm 2.2.0 | MIT | NPM + COPY examples |
| COLMAP | https://github.com/colmap/colmap | – | 4.2.0 (conda-forge) | BSD-3 | binary |
| plyfile | https://github.com/dranjan/python-plyfile | – | (version at T-004) | GPL-3.0 | PIP |
| LERF-OVS data | LangSplat README / LERF | – | download date (T-007) | LERF: MIT; annotations: **check** (T-007) | data |
