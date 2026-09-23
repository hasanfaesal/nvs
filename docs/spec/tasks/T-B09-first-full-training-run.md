# T-B09 — First full Phase B run: figurines × {V1, V2, V3} × seed 0

| Field | Value |
|---|---|
| Tier | **[H]** human (long GPU runs) |
| Depends on | T-B07, T-B08 |
| Requirements | FR-B4–FR-B7, NFR-1 |
| May edit 06-contracts.md | no |

## Goal
Real SAGA features for one scene and all three mask sources exist, so the query index, the query engine and the UI (T-B10–T-B16) can be built against real data. The times, VRAM and mask statistics are recorded.

## Read first
1. `docs/spec/08-phase-b.md` (intro + §3–§4)
2. `docs/spec/04-architecture-and-env.md` §9, §11

## Steps (lab, tmux; stop the demo server first)
```bash
tmux attach -t ps || tmux new -s ps
conda activate ps && cd ~/nvs && git pull --recurse-submodules
for v in sam sam2_frame sam2_track_k10; do
  python -m pipeline all --scene figurines --variant $v --seeds 0 || break
  python -m pipeline masks --scene figurines --variant $v --check
done
```
Then run the T-005 sanity query on each variant's `contrastive_feature_point_cloud.ply`. Take the feature of a Gaussian near the scene center, and count the Gaussians with cos > 0.75. The count should be between 0.1% and 30% of N.

## Checklist
- [ ] 3 variants: masks, scales, CLIP features, `seed0` training outputs
- [ ] Every stage's VRAM delta < 14 GB (see the T-B08 lab snippet)
- [ ] Sanity query plausible for each variant

## Laptop check
None. This is a human [H] card; nothing is coded here.

## Lab check
The Steps / Checklist above are the lab check. Record the results under Findings.

## Findings / Blockers
| Variant | masks/frame (mean) | tracks (V3) | mask time | scale+clip time | train time | peak VRAM | sanity count |
|---|---|---|---|---|---|---|---|
| sam | | – | | | | | |
| sam2_frame | | – | | | | | |
| sam2_track_k10 | | | | | | | |
