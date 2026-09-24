# T-A04 — gsplat fork patch: train/test split from `split.json` (P-GS-1)

| Field | Value |
|---|---|
| Tier | [S] (FORK-patch card: use the submodule recipe) |
| Depends on | T-001 |
| Requirements | FR-A5 |
| May edit 06-contracts.md | no |

## Goal
gsplat's `simple_trainer.py` accepts `--split_file scenes/<id>/split.json` and uses exactly its `train` and `test` lists. Without the flag, behaviour is unchanged.

## Background
Upstream gsplat always holds out every 8th image (`test_every`). We need its test set to also contain the annotated LERF-OVS frames and to skip outlier cameras, so the split must come from our `split.json` (C4). The change is ~10 lines in the **fork** only.

## Read first
1. `docs/spec/07-phase-a.md` §5.1
2. `docs/spec/06-contracts.md` §C4
3. Fork: `third_party/gsplat/examples/datasets/colmap.py`: class `Dataset.__init__` (the `indices % self.parser.test_every` lines, ≈ L458–462 on main)
4. Fork: `third_party/gsplat/examples/simple_trainer.py`: the `Config` dataclass, and where `Dataset(...)` is constructed (train and val)

## Files
| Action | Path |
|---|---|
| modify | `third_party/gsplat/examples/datasets/colmap.py` |
| modify | `third_party/gsplat/examples/simple_trainer.py` |
| modify | `third_party/gsplat` submodule pointer (main repo) |

## Provenance
FORK patch **P-GS-1** (`05-codebase-map.md` §4.2).

## Steps
1. `git -C third_party/gsplat checkout promptsplat`.
2. In `Dataset.__init__`, add a keyword parameter `split_file: Optional[str] = None` and replace the index selection:
   ```python
   if split_file is not None:
       import json
       key = "train" if split == "train" else "test"          # gsplat calls the eval split "val"
       names = json.load(open(split_file))[key]
       pos = {n: i for i, n in enumerate(self.parser.image_names)}
       missing = [n for n in names if n not in pos]
       assert not missing, f"split_file names not in COLMAP model: {missing[:5]}"
       self.indices = np.array([pos[n] for n in names])
       print(f"[split_file] {split}: {len(self.indices)} images")
   else:
       ...  # the original test_every code, unchanged
   ```
3. In `simple_trainer.py`:
   - add `split_file: Optional[str] = None` to `Config`, with a one-line docstring comment like its neighbours;
   - pass `split_file=cfg.split_file` to **both** `Dataset(...)` calls;
   - if `Optional` isn't imported yet, import it.
4. Commit and push in the fork, then bump the submodule in the main repo (AGENTS.md §7): `[ENH]: Add split_file option to the COLMAP parser`.

## Gotchas
- `parser.image_names` holds file names **with** extensions, the same strings as `split.json`. If the lab check shows a mismatch (e.g. subfolders), report it in Findings; don't hack around it.
- Keep the diff minimal. Don't reformat the files.

## Laptop check
```bash
python -m py_compile third_party/gsplat/examples/datasets/colmap.py third_party/gsplat/examples/simple_trainer.py && \
git -C third_party/gsplat diff --stat HEAD~1 && git submodule status third_party/gsplat
```

## Lab check
```bash
cd ~/nvs && git pull --recurse-submodules && conda activate ps && cd third_party/gsplat/examples
python simple_trainer.py mcmc --data_dir ~/nvs/scenes/ramen/source --data_factor 1 --result_dir /tmp/gs_split_smoke \
  --split_file ~/nvs/scenes/ramen/split.json --max_steps 100 --disable_viewer 2>&1 | grep -E "split_file|Error" | head
```
Expected: `[split_file] train: <len(train)> images` and `[split_file] val: <len(test)> images`, matching `split.json`.
- VERIFY the flag spelling of `--max_steps` / `--disable_viewer` with `--help`; tyro may use dashes.

## Done when
- [ ] Fork commit pushed; submodule bumped; the lab check counts match

## Findings / Blockers
- Fork commit `297addc8` on `promptsplat` (pushed); submodule bumped. Diff: colmap.py +12/−1, simple_trainer.py +4/−1.
- `json` is already imported at the top of `colmap.py`, so the card's inner `import json` was dropped; the original `if split == "train"` became `elif` behind the new branch (otherwise unchanged).
- Laptop logic check (stubbed GPU/image imports, not committed): train `[2,3]`, val `[1,9]` from a toy split.json; no flag → `[0,8]` (upstream `test_every`); unknown name → `AssertionError: split_file names not in COLMAP model: ['nope.jpg']`.
- `Parser.image_names` = `pycolmap` `image.name` sorted (colmap.py ≈L195–200), i.e. names relative to the COLMAP image root. Flat `images/` → plain file names, same as split.json. VERIFY on lab: the `[split_file]` counts print without an assertion.
- Only the COLMAP `Dataset` is patched; the NCore branch of `simple_trainer.py` ignores `--split_file` (not used by PromptSplat).
- VERIFY on lab: flag spelling. The fork pins `tyro>=0.8.8`, which accepts both `--max_steps` and `--max-steps`; confirm with `python simple_trainer.py mcmc --help | grep -E "split.file|max.steps|disable.viewer"`.
