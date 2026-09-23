# T-007 — Download LERF-OVS and check its layout

| Field | Value |
|---|---|
| Tier | [S] writes the script; **[H]** runs and inspects it on the lab |
| Depends on | T-002 (script in the repo), T-003 (lab) |
| Requirements | FR-A1, FR-E1 |
| May edit 06-contracts.md | no (report layout differences in Findings; `configs/scenes.yaml` paths are fixed in T-A02) |

## Goal
`data/raw/lerf_ovs/` on the lab PC contains the 4 scenes (figurines, ramen, waldo_kitchen, teatime), each with `images/` and `sparse/0`, plus the `label/` folder. The actual layout and counts are recorded.

## Background
LERF-OVS is LangSplat's release of 4 LERF scenes plus text-query annotations (polygons and boxes on a few frames per scene). The official copy is one ~746 MB zip on Google Drive, and Drive sometimes blocks downloads (quota). An unofficial Hugging Face mirror, `Qmh/lerf_ovs`, exists as a fallback.

Expected, from inspecting the zip on 2026-09-23:
- frames ≈ 986×728, undistorted, PINHOLE cameras, named `frame_%05d.jpg`;
- labels are `label/<scene>/frame_XXXXX.json` (+ `.jpg`).

## Read first
1. `docs/spec/09-experiments-and-evaluation.md` §2
2. `docs/spec/07-phase-a.md` §1.1

## Files
| Action | Path |
|---|---|
| create | `scripts/download_lerf_ovs.sh` |

## Provenance
NEW. The Drive file id comes from the LangSplat README (`1QF1Po5p5DwTjFHu6tnTeYs_G0egMVmHt`).

## Steps
1. Script:
   ```bash
   #!/usr/bin/env bash
   set -euo pipefail
   cd "$(dirname "$0")/.."
   mkdir -p data/raw && cd data/raw
   if [ ! -d lerf_ovs ]; then
     if gdown 1QF1Po5p5DwTjFHu6tnTeYs_G0egMVmHt -O lerf_ovs.zip; then
       unzip -q lerf_ovs.zip && rm lerf_ovs.zip
     else
       echo "Google Drive download failed; using the Hugging Face mirror (unofficial)"
       huggingface-cli download --repo-type dataset Qmh/lerf_ovs --local-dir lerf_ovs
     fi
   fi
   find lerf_ovs -maxdepth 2 -type d | sort
   ```
2. **You, on the lab:** run it, then inspect:
   ```bash
   conda activate ps && bash scripts/download_lerf_ovs.sh
   for s in figurines ramen waldo_kitchen teatime; do
     echo "== $s"; ls data/raw/lerf_ovs/$s | head
     ls data/raw/lerf_ovs/$s/images | wc -l
     ls data/raw/lerf_ovs/label/$s/*.json 2>/dev/null | wc -l
     python -c "import pycolmap; r=pycolmap.Reconstruction('data/raw/lerf_ovs/$s/sparse/0'); print(r.summary())"
   done
   python -c "import json,glob; f=sorted(glob.glob('data/raw/lerf_ovs/label/figurines/*.json'))[0]; d=json.load(open(f)); print(f, list(d.keys())); print(d['objects'][0].keys() if 'objects' in d else d)"
   ```
3. Record in Findings:
   - the actual folder names;
   - image counts, label counts and camera model per scene;
   - the top-level JSON keys (expected: `info`, `objects`, each object with `category`, `segmentation`, `bbox`);
   - any README or license text in the zip about the annotations, to copy into `THIRD_PARTY.md`.

## Laptop check
```bash
bash -n scripts/download_lerf_ovs.sh && echo syntax-ok
```

## Lab check
Step 2. Expected: about 299 / 131 / 187 / 177 images and 4 / 7 / 5 / 6 label JSONs (figurines / ramen / waldo_kitchen / teatime), PINHOLE cameras.

## Done when
- [ ] Data present on the lab; Findings filled in; `THIRD_PARTY.md` has the data licence line

## Findings / Blockers
