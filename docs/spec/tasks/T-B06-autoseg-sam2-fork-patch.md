# T-B06 — AutoSeg-SAM2 fork: SAM 2 detector option + document the output format (P-AS-1)

| Field | Value |
|---|---|
| Tier | **[M]** (third-party internals; judgement call on the decision rule) |
| Depends on | T-001, T-004 |
| Requirements | FR-B6 |
| May edit 06-contracts.md | no |

## Goal
1. The AutoSeg-SAM2 fork runs on our frame folders, and its output format is **documented precisely** in Findings (T-B07 depends on it).
2. It gets a `--detector {sam1,sam2}` option. `sam2` detects objects on keyframes with SAM 2.1's automatic mask generator (C6.1 thresholds) instead of SAM v1, keeping AutoSeg's level, NMS and new-object logic.

## Background
AutoSeg-SAM2 (MIT; the tool used by Segment-then-Splat for 3DGS) does "automatic segmentation + tracking". What it does is described in `08-phase-b.md` §3.4:
- detects objects on keyframes;
- tracks them forward and backward with the SAM 2 video predictor;
- keeps each object's ID.

Upstream detects with **SAM v1**. For a clean experiment, V3 should detect with **SAM 2.1**, like V2, so that V3 vs V2 differs only by tracking.

**Decision rule:** if porting the detection (especially its "level" selection of whole / part / sub-part masks) takes more than **1 working day**, keep `sam1` and record this in `docs/spec/port-report.md` (section "AutoSeg detector"). The analysis then compares V3 with V1 for the tracking effect, with V2 reported alongside.

## Read first
1. `docs/spec/08-phase-b.md` §3.4
2. Fork: `third_party/AutoSeg-SAM2/README.md` and `auto-mask-batch.py` (the whole file), plus the helper module it imports to build the SAM v1 generator and to pick levels (find it from the imports)
3. Segment-then-Splat: `third_party/AutoSeg-SAM2/autoseg.sh` in https://github.com/luyr/Segment-then-Splat (the exact flags they used: levels large and middle, `--detect_stride 10 --batch_size 40`)
4. sam2: `sam2/automatic_mask_generator.py` (its constructor arguments and the `multimask_output` handling)

## Files (inside the fork)
| Action | Path |
|---|---|
| modify | `third_party/AutoSeg-SAM2/auto-mask-batch.py` |
| modify | the helper file that builds the SAM v1 AMG (name found in step 1) |
| modify | submodule pointer in the main repo |
| modify | `docs/spec/port-report.md` (main repo): add an "AutoSeg detector" section |

## Provenance
FORK patch **P-AS-1** (`05-codebase-map.md` §4.3).

## Steps
1. **Read and document, before changing anything.** Write in Findings:
   - the CLI flags of `auto-mask-batch.py` (video path, output dir, level, detect stride, batch size, checkpoint paths);
   - how "level" is implemented (which SAM multimask output, or which filtering);
   - where the SAM v1 generator is built;
   - the **output layout**: file names, per-frame array shapes, dtype, and whether the array index equals the object ID, persistent across frames;
   - whether a reverse pass runs by default.
2. **Run upstream unchanged** on the lab (30 train frames of ramen, level `large`, stride 10) to confirm it works and to see real output files. Record the time and VRAM.
3. **Add `--detector {sam1,sam2}`** (default `sam1`, i.e. upstream behaviour). With `sam2`:
   - build `SAM2AutomaticMaskGenerator(build_sam2(cfg, ckpt, apply_postprocessing=False), points_per_side=32, pred_iou_thresh=0.88, stability_score_thresh=0.95, box_nms_thresh=0.7, crop_n_layers=0, min_mask_region_area=100)`;
   - reproduce the level selection the same way upstream does it for SAM v1. If upstream selects one of the 3 multimask outputs per point, do the same with SAM 2's per-point outputs.
   - Keep `mask_nms` / `masks_update` / `search_new_obj` unchanged.
4. **Run the patched version** with `--detector sam2` on the same 30 frames. Compare the object counts with step 2.
5. Commit in the fork (`[ENH]: Add --detector sam2 option`, AGENTS.md §7), push, and bump the submodule.
6. Write the port-report section: the detector used for V3 (sam2, or sam1 per the decision rule), time spent, and differences observed.

## Laptop check
```bash
python -m py_compile third_party/AutoSeg-SAM2/auto-mask-batch.py && git -C third_party/AutoSeg-SAM2 log --oneline -1
```

## Lab check
```bash
cd ~/nvs && conda activate ps && mkdir -p /tmp/autoseg_test/frames
ls scenes/ramen/variants/sam/images | head -30 | nl -v0 -nrz -w5 | while read i n; do ln -sfn "$PWD/scenes/ramen/variants/sam/images/$n" /tmp/autoseg_test/frames/$i.jpg; done
cd third_party/AutoSeg-SAM2
python auto-mask-batch.py <flags recorded in step 1> --detector sam2   # video path /tmp/autoseg_test/frames, level large, stride 10
```
Expected: it completes; the per-frame outputs exist; the object counts are non-zero; VRAM < 14 GB. Paste the output listing.

## Done when
- [ ] Findings document the output format precisely
- [ ] The `--detector sam2` patch is pushed (or the decision rule is applied and documented)

## Findings / Blockers
