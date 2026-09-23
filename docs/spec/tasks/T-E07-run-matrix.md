# T-E07 — Experiment runner for the whole matrix (`experiments/run_matrix.py`)

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-E03, T-E04, T-E05, T-B08, T-B11 |
| Requirements | FR-E7, NFR-4, NFR-10 |
| May edit 06-contracts.md | no |

## Goal
One command runs, or resumes, every experiment in `configs/experiments.yaml`, in the order of `09-experiments-and-evaluation.md` §4. `--dry-run` prints the full command list.

## Background
The full matrix is ~55–60 GPU-hours. It must be **restartable**: every command it calls is already skip-if-done, so the runner just calls them in order and stops at the first failure. `--dry-run` lets you review the plan (and lets tests check the order) without touching the GPU.

## Read first
1. `docs/spec/09-experiments-and-evaluation.md` §3–§4
2. `docs/spec/06-contracts.md` §C6.3, §C16
3. `pipeline/cli.py` (the command names)

## Files
| Action | Path |
|---|---|
| create | `configs/experiments.yaml` (exactly C6.3) |
| create | `experiments/run_matrix.py` |
| create | `tests/test_run_matrix.py` |

## Provenance
NEW.

## Interface
```python
def plan(exp: dict) -> list[list[str]]: ...        # ordered commands, each e.g. ["python", "-m", "pipeline", "split", "--scene", "ramen"]
def main(argv: list[str] | None = None) -> int: ... # --dry-run, --only-scene ID
```

## Steps
1. `plan(exp)`. For each scene:
   1. `ingest`, `split`, `train3dgs`, `export`, `saga-import`.
   2. Then for each variant v, in order (core variants, then ablation variants):
      - `variant --variant v --seeds <seeds(v)>`, `masks`, `saga --stage scale`, `saga --stage clip`;
      - for each seed: `saga --stage train --seed k`, `index --seed k`, `python -m evaluation.eval_3d --scene s --variant v --seed k`;
      - then `python -m evaluation.mrc --scene s --variant v` (if `exp["mrc"]`).
   3. Then `python -m evaluation.baseline_2d --scene s` (if `exp["baseline_2d"]`).
   4. After all scenes: `python -m evaluation.aggregate`.
   5. Stretch entries are appended like ablations.
2. `main`:
   - load the YAML;
   - `--only-scene` filters the scenes (aggregate still runs last);
   - `--dry-run` prints one command per line and returns 0;
   - otherwise run each with `subprocess.run(cmd, check=True)` and print a `[i/N]` progress prefix. On failure, print the failing command and return 1.

## Tests
- `plan` for `{scenes: [s1], core: {variants: [sam], seeds: [0,1]}, ablations: [{variant: sam2_track_k5, seeds: [0]}], baseline_2d: true, mrc: true, stretch: []}` equals the hand-written expected list:
  - the order is exact: ingest … saga-import, `sam` block (train/index/eval for seed 0 then seed 1, then mrc), `sam2_track_k5` block (seed 0, mrc), baseline, aggregate;
  - the count is 5 + (4 + 3×2 + 1) + (4 + 3 + 1) + 1 + 1 = 26 commands.
- `main(["--dry-run"])` with a temporary YAML prints the same number of lines.

## Laptop check
```bash
pytest -q tests/test_run_matrix.py tests/test_imports.py && python -m experiments.run_matrix --dry-run | head -30
```

## Lab check
```bash
python -m experiments.run_matrix --dry-run | wc -l
python -m experiments.run_matrix --only-scene ramen   # resumes; completes whatever is missing for ramen
```

## Done when
- [ ] Tests pass; ramen completes through the runner on the lab

## Findings / Blockers
