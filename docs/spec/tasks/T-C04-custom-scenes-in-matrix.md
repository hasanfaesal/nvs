# T-C04 — Split, train and evaluate the custom scenes; add them to the results

| Field | Value |
|---|---|
| Tier | **[H]** human |
| Depends on | T-C03, T-E08 |
| Requirements | FR-E10, NFR-9 |
| May edit 06-contracts.md | no |

## Goal
`desk_01` and `shelf_01` go through the same matrix as the LERF scenes, with their annotated frames held out. `results/summary.json` includes them.

## Steps
1. **Split** (the annotated frames go to test, because their labels exist now): `for s in desk_01 shelf_01; do python -m pipeline split --scene $s --force; done`. Check that `annotated` has 6 entries.
2. Add both scenes to `configs/experiments.yaml` → `scenes`.
3. Run `python -m experiments.run_matrix --only-scene desk_01`, then `--only-scene shelf_01`, in tmux (~20–25 GPU-h). `run_matrix` re-runs `evaluation.aggregate` at the end.
4. **Demo queries:** pick 3 good queries per scene, put them in `scenes.yaml`, and re-run `export --force`.
5. Commit: `git add results configs && git commit -m "T-C04: custom scenes results" && git push`.

## Done when
- [ ] Both custom scenes in `summary.json` (core variants × 3 seeds, the ablation, the baseline, MRC)

## Laptop check
None. This is a human [H] card; nothing is coded here.

## Lab check
The Steps / Checklist above are the lab check. Record the results under Findings.

## Findings / Blockers
