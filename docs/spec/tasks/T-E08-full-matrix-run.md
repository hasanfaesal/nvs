# T-E08 — Run the full experiment matrix (LERF-OVS scenes)

| Field | Value |
|---|---|
| Tier | **[H]** human (~2.5 days of unattended GPU time) |
| Depends on | T-E07, T-B17 |
| Requirements | FR-E8, NFR-1, NFR-4, NFR-9 |
| May edit 06-contracts.md | no |

## Goal
Every run in `configs/experiments.yaml` completes for the 4 LERF-OVS scenes; `results/summary.json` is generated and committed. The custom scenes follow later (T-C04).

## Steps
1. Stop the demo server. `tmux new -s matrix`.
2. `conda activate ps && cd ~/nvs && git pull --recurse-submodules && python -m experiments.run_matrix --dry-run | wc -l`
3. `python -m experiments.run_matrix 2>&1 | tee -a logs_matrix.txt`
   - If it stops: read the failing command, fix the cause (a card, via Prompt B if it's a code bug), and re-run the same command; the runner resumes.
   - Check daily: `tail logs_matrix.txt`, `nvidia-smi`, `df -h ~`.
4. When it finishes:
   - check `results/summary.json`: every scene × core variant × 3 seeds is present, plus the K ablation, the baseline and the MRC rows;
   - look at 10 failure renders per variant (`results/*/*/renders_seed0/`) and write 3–5 sentences in Findings on the typical failures.
5. Commit and tag:
   ```bash
   git add results && git commit -m "[ENH]: Add full matrix results on LERF-OVS" && git push && git tag eval-done && git push --tags
   ```

## Checklist
- [ ] 4 scenes × 3 core variants × 3 seeds evaluated
- [ ] K ablation (5, 20) + baseline + MRC present
- [ ] `summary.json` has `wilcoxon` rows
- [ ] All VRAM deltas < 14 GB
- [ ] Failure analysis notes written

## Laptop check
None. This is a human [H] card; nothing is coded here.

## Lab check
The Steps / Checklist above are the lab check. Record the results under Findings.

## Findings / Blockers
