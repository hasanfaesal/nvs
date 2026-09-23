# AGENTS.md — rules for anyone (human or model) coding PromptSplat

**Read this whole file before doing anything, then read your task card.** This file is the single source of rules. `CLAUDE.md` and `.cursor/rules/promptsplat.mdc` only point here.

## 1. What this project is
- PromptSplat turns a phone video of a static scene into a **3D Gaussian Splatting** scene (COLMAP poses → gsplat MCMC training). It is shown in a browser with **Nuxt + Spark**.
- **SAGA** then learns a 32-D affinity feature per Gaussian from 2D masks, so a user can select objects by **text** (CLIP) or by **click**.
- A controlled experiment compares three mask sources: V1 SAM per-frame, V2 SAM 2 per-frame, V3 SAM 2 tracked (AutoSeg-SAM2 fork).
- Full spec: `docs/spec/README.md`. **Interfaces:** `docs/spec/06-contracts.md` (C1–C16), which is the source of truth for paths, formats, APIs and camera math.

## 2. Repo map (details: C1)
```text
pipeline/     offline CLI: python -m pipeline <command>   (ingest, split, train3dgs, export, masks, saga, index …)
server/       FastAPI app (app.py) + query engine (query.py; GpuEngine and FakeEngine)
evaluation/   metrics, 3D eval, 2D baseline, MRC, aggregation   (NOT "eval/")
experiments/  run_matrix.py
web/          Nuxt 4 SPA (app/pages, app/components/SplatViewer.client.vue, app/utils/splatModes.ts)
configs/      pipeline.yaml, scenes.yaml, experiments.yaml   (all defaults live here)
third_party/  git submodules = our forks: SegAnyGAussians (SAGA), gsplat, AutoSeg-SAM2 (branch promptsplat)
tests/        CPU-only pytest files with synthetic data
docs/spec/    the specification + task cards (docs/spec/tasks/)
scenes/ data/ checkpoints/   big local data — gitignored, never committed
results/      small JSON results — committed
```

## 3. Where code runs
- **Laptop** (where you, the coding model, run): Arch Linux, **no GPU**, ~17 GB free disk. You edit code and run **CPU checks** only.
- **Lab PC** (WSL2 Ubuntu, RTX A4000 16 GB): the human runs the card's **lab check** there and pastes the output back to you. Never assume you can run GPU code.

## 4. Commands
```bash
# laptop
source .venv/bin/activate
pytest -q                                            # all CPU tests (must stay < 60 s)
python scripts/make_fixture_scene.py                 # tiny synthetic scene in scenes/_fixture
PS_FAKE=1 uvicorn server.app:app --reload --port 8000
cd web && npm run dev                                # http://localhost:3000 (proxies /api to :8000)
cd web && npx nuxi generate                          # build → web/.output/public (served by FastAPI)
cd web && npx vitest run                             # web unit tests (after T-B14)

# lab (the human runs these)
conda activate ps
python -m pipeline <command> --scene <id> [...]      # C16
uvicorn server.app:app --host 127.0.0.1 --port 8000
```

## 5. Hard rules
1. **One task card per session.** Read the whole card. Read **only** the files under "Read first", unless the card says otherwise.
2. **Scope:** create or modify **only** the files listed in the card. Never touch:
   - `docs/proposals/`, `docs/fyp-options/`, `docs/compute/`, `docs/title-explained.md`, `docs/figures/`, `docs/template/`;
   - `docs/spec/06-contracts.md` (unless the card says "may edit 06-contracts.md");
   - `third_party/*` (unless the card is a FORK-patch card, and then only through the submodule recipe in §7).
3. **Contracts win.** Paths, file formats, JSON keys, API shapes, config keys and camera conventions come from `06-contracts.md`. Don't invent new ones.
4. **Build on upstream.** Follow the card's provenance:
   - **COPY:** copy the upstream code and keep the `Source:` header (format in `docs/spec/05-codebase-map.md` §5);
   - **WRAP:** call the upstream script as a subprocess through `pipeline/run_stage.py`;
   - **NEW:** only where the card says so.
5. **GPU libraries are imported inside functions** (`gsplat`, `sam2`, `segment_anything`, `open_clip`, `hdbscan`, and anything that needs CUDA), never at module top level. Every module must import on the laptop.
6. **`torch.load(path, map_location="cpu")`** always (SAGA writes CUDA tensors).
7. **No new dependencies and no new config keys** unless the card allows them. Defaults live in `configs/pipeline.yaml`; read them through `pipeline/config.py`.
8. **Never reorder, filter or drop Gaussians** (index invariant, C11). Row i is the same Gaussian everywhere.
9. **Camera math only through `pipeline/camera.py`** (C10). Never re-derive it inline.
10. **Tests:** one `tests/test_<module>.py` per non-trivial module. Plain `assert`s, synthetic data, no GPU, no network, < 10 s. A test must fail if the logic is wrong.
11. **Minimal code:** no speculative options, abstractions or "for later" code. Mark deliberate shortcuts with a `ponytail:` comment that names the limit.
12. **Never commit large files:** `data/`, `scenes/`, `checkpoints/`, `*.pt`, `*.pth`, `*.ply`, `.venv/`, `node_modules/`, `web/.output/`.
13. **Stop and ask.** If the card is ambiguous, contradicts the contracts, needs an unlisted file, or a check fails twice for the same reason:
    - write the problem under **"Blockers"** in the card;
    - stop, and tell the human.
    Guessing is worse than stopping.

## 6. Style
- **Python 3.10:**
  - type hints on public functions; `pathlib.Path`; `argparse` (no click/typer); f-strings;
  - `print` for progress; small functions;
  - first line of each module: a docstring saying what it does and its provenance type (e.g. `"""Split builder (NEW). See C4."""`).
- **Subprocesses:** always through `pipeline.run_stage.run_stage(...)` for GPU or long stages. Absolute paths as arguments. `cwd` set explicitly.
- **TypeScript / Vue:**
  - `<script setup lang="ts">`, strict types;
  - Nuxt UI components (`UButton`, `UCard`, `USelect`, `USlider`, `USwitch`, `UInput`, `UBadge`, `UTable`);
  - fetch only through `app/composables/useApi.ts`.
- **Errors:** raise with a message that says what to check (e.g. `"split.json names not found in COLMAP model: frame_00012.jpg — re-run split"`).

## 7. Git
- Never force-push. Never rewrite pushed history.
- **Commit messages:**
  - Subject: `[TAG]: <Imperative summary>`. Capitalized imperative verb (`Add`, `Implement`, `Fix`, `Wire`, `Update`), no trailing period, under 72 characters. No card id (`T-XXX`) anywhere in the message.
  - Tags: `[ENH]` features/capabilities · `[FIX]` bug fixes · `[DOCS]` docs, runbooks, specs, task cards · `[DB]` schemas/store layer · `[CFG]` config files, loaders, env parsing · `[DEP]` dependencies, forks, submodule bumps · `[BLD]` build system, toolchain, project skeleton.
  - Body (multi-file or non-trivial changes): blank line, then `- ` bullets with imperative verbs: what was added/changed, why edge cases are guarded, which tests were added.
  - Example: `[ENH]: Add split builder for train/test frame lists`, body `- Add pipeline/split.py …` / `- Add tests/test_split.py covering hold-out spacing`.
- No "Co-Authored-By" or "Generated with …" trailers in commits or PRs.
- **Submodule recipe** (FORK-patch cards only):
  ```bash
  cd third_party/<repo>
  git checkout promptsplat                     # never commit on a detached HEAD
  git add <files> && git commit -m "[ENH]: <Summary>"
  git push origin promptsplat
  cd ../..
  git add third_party/<repo> && git commit -m "[DEP]: Bump <repo> fork"
  ```

## 8. Facts you must not re-derive
- **Coordinates (C10):**
  - COLMAP / gsplat / SAGA use OpenCV axes (x right, y down, z forward); `viewmat` = world→camera.
  - three.js uses OpenGL axes. The Spark `SplatMesh` quaternion is `(1,0,0,0)`.
- **Scores (C13):** uint8 = `round(clip((cos+1)/2, 0, 1) * 255)`. Default thresholds: text 0.925, click 0.875.
- **Masks (C7):** `torch.bool [M, H//4, W//4]` per train frame; M may be 0.
- **Variant ids (C2):** `sam`, `sam2_frame`, `sam2_track_k{K}` (+ `_xview`).
- **SAGA scripts:** run with `cwd=third_party/SegAnyGAussians` and absolute paths. Use `conda run -n saga` only when `envs.saga == "saga"`.
- **Frames:** sorted image names = capture order. Train/test lists come from `scenes/<id>/split.json` (C4).
