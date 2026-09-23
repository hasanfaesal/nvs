# T-E06 — Aggregate all results into `results/summary.json` (+ statistics)

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-E03 (the file formats), T-002 |
| Requirements | FR-E6, NFR-9 |
| May edit 06-contracts.md | no |

## Goal
`python -m evaluation.aggregate` reads every result file under `results/` and writes `results/summary.json` (C14.5):
- per-scene and overall tables with mean ± std;
- the K ablation, the 2D baseline, Phase A metrics and systems numbers;
- Wilcoxon tests with Holm correction.

## Background
The report tables and the results page both come from this single file.
- **Seeds** give training variance, reported as mean ± std per scene.
- **Scenes** give generalization, reported as the mean of the per-scene means ± std across scenes.
- **Paired tests** ask whether V3 beats V1 on the *same* queries more often than chance. The Wilcoxon signed-rank test compares per-query IoU, averaged over seeds.
- **Holm correction** adjusts the p-values because we run three planned comparisons.

## Read first
1. `docs/spec/09-experiments-and-evaluation.md` §6, §7
2. `docs/spec/06-contracts.md` §C14 (every sub-section), §C15
3. `pipeline/config.py` (`results_root`, `scenes_root`)

## Files
| Action | Path |
|---|---|
| create | `evaluation/aggregate.py` |
| create | `tests/test_aggregate.py` |

## Provenance
NEW (`scipy.stats.wilcoxon`).

## Interface
```python
CORE = ("sam", "sam2_frame", "sam2_track_k10")
PAIRS = (("sam2_track_k10", "sam"), ("sam2_track_k10", "sam2_frame"), ("sam2_frame", "sam"))
def holm(pvals: list[float]) -> list[float]: ...
def aggregate(results: Path, scenes: Path | None = None) -> dict: ...     # C14.5
def main() -> None: ...                                                   # writes results/summary.json
```

## Steps
1. Glob `results/*/*/seed*.json`, `results/*/*/mrc.json`, `results/*/baseline_2d.json`, `results/*/phase_a.json` and `results/*/latency.json`.
2. **`main`:** for each (scene, variant in CORE), the mean and std (ddof=1 if n > 1, else 0) over seeds of `miou`, `mbiou`, `loc_acc`, plus `n_seeds`, plus `mrc` from `mrc.json` (null if missing).
3. **`overall`:** per variant, the mean over scenes of the seed-means, the std across scenes, and the mean MRC.
4. **`ablation_k`:** variants matching `sam2_track_k(\d+)$`, seed 0 → `{scene, k, miou, mrc}` (K = 10 comes from the core runs).
5. **`baseline_2d`**, **`phase_a`**: copy the key fields.
6. **`systems`:**
   - if a scenes dir is available, read each `scenes/*/logs/stages.jsonl` → `{scene, stage, variant, seed, seconds, peak_vram_mb: peak−baseline}`;
   - add a `latency.json` row per scene.
7. **`wilcoxon`:**
   - per variant, build a map `(scene, frame, query) → IoU averaged over seeds`;
   - for each pair in `PAIRS`, keep the common keys and run `scipy.stats.wilcoxon(a, b, zero_method="wilcox")`, skipping it if n < 6 or every difference is zero;
   - report `{a, b, n, mean_diff, p_value, p_holm}`, with `holm()` applied over the 3 tests.
8. **`holm(p)`** (step-down, monotone): sort ascending; `adj_i = min(1, max_{j ≤ i} (m − j) · p_(j))` with j 0-based; map back to the original order.
9. Add `generated_utc`; write `indent=1`.

## Tests (synthetic result files in tmp)
- 2 scenes × `CORE` × seeds `{0,1}` with known `miou` values → the means and stds match hand-computed values; `overall` is correct.
- `holm([0.01, 0.04, 0.03]) == [0.03, 0.06, 0.06]` (approx).
- The Wilcoxon row exists for a pair with ≥ 6 common queries, and not when there are fewer.
- A missing `mrc.json` gives `mrc: null` without crashing.

## Laptop check
```bash
pytest -q tests/test_aggregate.py tests/test_imports.py
```

## Lab check
```bash
python -m evaluation.aggregate && python -c "import json; d=json.load(open('results/summary.json')); print({k: len(v) if isinstance(v, list) else v for k, v in d.items()})"
```

## Done when
- [ ] Tests pass; `summary.json` is produced on the lab

## Findings / Blockers
