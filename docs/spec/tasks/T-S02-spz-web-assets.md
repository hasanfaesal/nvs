# T-S02 — Stretch: compressed SPZ web assets (only if PLY loading is too slow)

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-A16, and only if a scene takes > 10 s to load |
| Requirements | FR-S2 |
| May edit 06-contracts.md | no (C5 already allows `asset.format: "spz"`) |

## Goal
`python -m pipeline export --scene <id> --spz` also writes `web/scene.spz` and points the manifest at it, **without changing splat order** (C11).

## Background
A 1M-splat PLY is about 240 MB; SPZ (Niantic's format) is about 10× smaller, and Spark loads it natively. The risks:
- **Coordinate convention:** SPZ defaults to "RUB", while PLY files are usually "RDF". A wrong setting flips the scene.
- **Order:** Spark keeps file order for non-LoD loading. Verify it anyway, because every query score is indexed by position.

## Read first
1. `docs/spec/06-contracts.md` §C5, §C11
2. nianticlabs/spz README: the Python bindings (`spz.load_splat_from_ply`, `spz.save_spz`, `UnpackOptions` / `PackOptions` with `CoordinateSystem`); build from source with `pip install git+https://github.com/nianticlabs/spz` (VERIFY; the PyPI package `spz` is unrelated)
3. `pipeline/export_web.py`

## Files
| Action | Path |
|---|---|
| modify | `pipeline/export_web.py`: an `--spz` option |
| modify | `pipeline/cli.py` |

## Steps
1. Convert with the Python bindings, choosing the coordinate options so the result matches how Spark shows the PLY: test both options and keep the one that looks identical in the viewer.
2. Set `manifest.asset = {"file": "scene.spz", "format": "spz", "bytes": …}`.
3. **Order check** (lab, browser console or a small page): after loading, compare `packedSplats.getSplat(i).center` for i ∈ {0, 1, N/2, N−1} with the PLY positions under the viewer transform. They must match within the SPZ quantization (~1 mm).

## Laptop check
```bash
python -m py_compile pipeline/export_web.py pipeline/cli.py && pytest -q tests/test_export_web.py tests/test_imports.py
```

## Lab check
Load time before and after; visual identity; the order check passes.

## Done when
- [ ] SPZ used only if it is faster and the order check passes; otherwise abandoned, and why is recorded

## Findings / Blockers
