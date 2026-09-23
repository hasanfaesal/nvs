# T-001 — Fork upstream repos, add them as submodules, record pins

| Field | Value |
|---|---|
| Tier | **[H]** human (needs your GitHub account) |
| Depends on | – |
| Requirements | NFR-4, NFR-5 |
| May edit 06-contracts.md | no |

## Goal
Three forks exist under `github.com/hasanfaesal/`, each with a `promptsplat` branch. They are git submodules in `third_party/`, and `THIRD_PARTY.md` records every upstream repo with its pinned SHA and license.

## Background
We build on existing code (`docs/spec/05-codebase-map.md`). Repos we **modify** are forked: SAGA, gsplat, AutoSeg-SAM2. Our changes live on a `promptsplat` branch in each fork. The main repo stores only the commit each submodule points to, so every checkout reproduces the exact same upstream code.

SAGA has its own nested submodules with **SSH** URLs (`third_party/segment-anything`, `kmeans_pytorch`). Tell git to use HTTPS instead, on the laptop and on the lab PC, or recursive clones will fail without SSH keys.

## Read first
1. `docs/spec/05-codebase-map.md` §1–§2 and §4
2. `docs/spec/10-workflow-small-models.md` §7 (submodule recipe)

## Files
| Action | Path |
|---|---|
| create | `.gitmodules` (created by `git submodule add`) |
| create | `third_party/SegAnyGAussians`, `third_party/gsplat`, `third_party/AutoSeg-SAM2` (submodules) |
| create | `THIRD_PARTY.md` |

## Steps
1. **HTTPS rewrite for nested submodules** (run once on the laptop now, and on the lab PC in T-003):
   ```bash
   git config --global url."https://github.com/".insteadOf git@github.com:
   ```
2. **Fork** (default: all branches are copied):
   ```bash
   gh repo fork Jumpat/SegAnyGAussians --clone=false
   gh repo fork nerfstudio-project/gsplat --clone=false
   gh repo fork zrporz/AutoSeg-SAM2 --clone=false
   ```
3. **Choose pins** (the upstream commit each `promptsplat` branch starts from). Note each SHA and today's date:
   ```bash
   git ls-remote https://github.com/Jumpat/SegAnyGAussians refs/heads/v2
   git ls-remote https://github.com/nerfstudio-project/gsplat refs/heads/main
   git ls-remote https://github.com/zrporz/AutoSeg-SAM2 HEAD
   ```
4. **Add the submodules and create the branches** (repeat for each repo; the example is SAGA):
   ```bash
   cd ~/code3/gsp
   git submodule add https://github.com/hasanfaesal/SegAnyGAussians.git third_party/SegAnyGAussians
   cd third_party/SegAnyGAussians
   git checkout -b promptsplat <PINNED_SHA>
   git push -u origin promptsplat
   cd ../..
   git config -f .gitmodules submodule.third_party/SegAnyGAussians.branch promptsplat
   ```
   Do the same for `gsplat` (from its `main` SHA) and `AutoSeg-SAM2` (from its default-branch SHA).
   - **Laptop disk is tight (17 GB free).** Don't run `--recursive` on the laptop; SAGA's nested submodules are only needed on the lab PC.
5. **Write `THIRD_PARTY.md`** with this table. Fill in the SHAs, and open each repo's LICENSE to confirm the license:

   | Name | Upstream | Fork / branch | Pinned base SHA (date) | License | Use |
   |---|---|---|---|---|---|
   | SAGA | https://github.com/Jumpat/SegAnyGAussians (v2) | hasanfaesal/SegAnyGAussians @ promptsplat | … | Apache-2.0 (+ Inria notice on 3DGS files) | FORK |
   | gsplat | https://github.com/nerfstudio-project/gsplat (main) | hasanfaesal/gsplat @ promptsplat | … | Apache-2.0 | FORK |
   | AutoSeg-SAM2 | https://github.com/zrporz/AutoSeg-SAM2 | hasanfaesal/AutoSeg-SAM2 @ promptsplat | … | MIT | FORK |
   | SAM 2 | https://github.com/facebookresearch/sam2 | – | (SHA at T-004) | Apache-2.0 | PIP (git) |
   | segment-anything | https://github.com/facebookresearch/segment-anything | – | (SHA at T-004) | Apache-2.0 | PIP (git) |
   | OpenCLIP | https://github.com/mlfoundations/open_clip | – | (version at T-004) | MIT | PIP |
   | LangSplat | https://github.com/minghanqin/LangSplat | – | (SHA at T-E01) | **check** | COPY (eval GT/localization) |
   | Gaussian Grouping | https://github.com/lkeab/gaussian-grouping | – | (SHA at T-E02) | Apache-2.0 | COPY (eval metrics) |
   | Segment-then-Splat | https://github.com/luyr/Segment-then-Splat | – | (SHA at T-B07) | MIT | COPY (mask dedup) |
   | Spark | https://github.com/sparkjsdev/spark | – | npm 2.2.0 | MIT | NPM + COPY examples |
   | COLMAP | https://github.com/colmap/colmap | – | 4.2.0 (conda-forge) | BSD-3 | binary |
   | plyfile | https://github.com/dranjan/python-plyfile | – | (version at T-004) | GPL-3.0 | PIP |
   | LERF-OVS data | LangSplat README / LERF | – | download date (T-007) | LERF: MIT; annotations: **check** | data |

6. Commit and push:
   ```bash
   git add .gitmodules third_party THIRD_PARTY.md
   git commit -m "T-001: add SAGA, gsplat, AutoSeg-SAM2 forks as submodules; THIRD_PARTY.md"
   git push
   ```

## Laptop check
```bash
git submodule status                         # 3 lines, each with a SHA and a path under third_party/
git -C third_party/SegAnyGAussians branch --show-current   # promptsplat
git -C third_party/gsplat branch --show-current            # promptsplat
git -C third_party/AutoSeg-SAM2 branch --show-current      # promptsplat
```

## Lab check
Done in T-003: `git clone --recurse-submodules https://github.com/hasanfaesal/nvs.git ~/nvs` succeeds, including SAGA's nested submodules.

## Done when
- [ ] 3 forks, each with a `promptsplat` branch on GitHub
- [ ] `git submodule status` lists all 3
- [ ] `THIRD_PARTY.md` committed with the SHAs and licenses

## Findings / Blockers
- Done 2026-09-24 with `gh` (account hasanfaesal). Global `url."https://github.com/".insteadOf git@github.com:` set on the laptop; the lab PC still needs it (T-003).
- Pins: SAGA `v2` = `2d4c5d7`, gsplat `main` = `512d366` (describes as `v1.5.3-674-g512d366b`), AutoSeg-SAM2 default branch `main` = `5814307`. Full SHAs in `THIRD_PARTY.md`.
- Licenses confirmed from the LICENSE files: SAGA Apache-2.0 (its `submodules/diff-gaussian-rasterization/LICENSE.md` carries the Inria notice), gsplat Apache-2.0, AutoSeg-SAM2 MIT. OpenCLIP and COLMAP read via the GitHub API (MIT-style and BSD-3).
- **LangSplat's LICENSE.md is the Inria/MPII Gaussian-Splatting license (non-commercial research only).** Copying ~30 lines is fine for an FYP. If that is a problem, re-implement them instead (as `05-codebase-map.md` §2 says). Final call at T-E01.
- SAGA's nested submodules (`kmeans_pytorch`, `segment-anything`) still use SSH URLs in the fork's `.gitmodules`. The insteadOf rewrite handles this; P-SAGA-1 (T-005) switches them to HTTPS.
- No `--recursive` on the laptop. `.git/modules` is about 227 MB.
- Not run: `git push` of the main repo (the runner does it). VERIFY on lab (T-003): `git clone --recurse-submodules` succeeds.
