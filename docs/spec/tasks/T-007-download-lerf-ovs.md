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
Inspected on the laptop on 2026-09-24 (the lab PC still needs its own download). The Google Drive download worked first time (746 MB zip, 948 MB unpacked). The HF fallback was not needed.

**Folder names** (`data/raw/lerf_ovs/`): `figurines/`, `ramen/`, `waldo_kitchen/`, `teatime/`, `label/`. There is no extra wrapper folder.
- Each scene has `images/`, `sparse/0/` (`cameras.bin`, `images.bin`, `points3D.bin`, `points3D.ply`), plus the COLMAP leftovers `distorted/` (`database.db`, `sparse/0` with **OPENCV** cameras, the raw pre-undistortion model) and `stereo/`. Use `images/` + `sparse/0` only.
- Labels: `label/<scene>/frame_XXXXX.json` + `frame_XXXXX.jpg`.

| Scene | images (= registered) | label JSONs | camera (`sparse/0`) | W×H | labelled frames | objects | distinct categories (strip+lower) |
|---|---|---|---|---|---|---|---|
| figurines | 299 | 4 | PINHOLE, 1 camera | 986×728 | 41, 105, 152, 195 | 57 | 21 |
| ramen | 131 | 7 | PINHOLE, 1 camera | 988×731 | 6, 24, 60, 65, 81, 119, 128 | 80 | 14 |
| waldo_kitchen | 187 | 5 | PINHOLE, 1 camera | 985×725 | 53, 66, 89, 140, 154 | 29 | 18 |
| teatime | 177 | 6 | PINHOLE, 1 camera | 988×730 | 2, 25, 43, 107, 129, 140 | 62 | 14 |

- Every registered image name exists in `images/` and vice versa. Every labelled frame exists in `images/`.
- **Frame numbers have gaps** (the frames were dropped before COLMAP): figurines is missing 293 and 295 (last frame 00301), waldo_kitchen 155–157 (last 00190), teatime 148, 155 and 156 (last 00180). ramen has no gaps. Sorted names are still capture order, but frame number ≠ index. The split (T-A03) must work on the sorted list, not on `int(name)`.
- Image sizes differ per scene (not all 986×728). `info.width/height` in each label JSON matches its scene's camera.
- **Category counts differ from `09-experiments-and-evaluation.md` §2** (17/14/17/16): the real counts are 21/14/18/14. Raw and normalised counts are the same (no case or whitespace duplicates). Update that table when it is next allowed to be edited.

**Label JSON:** top-level keys `info`, `objects`.
- `info` = `{name, width, height, depth, note}`.
- Each object = `{category, group, segmentation, area, layer, bbox, iscrowd, note}`.
- `segmentation` is **one polygon**, a list of `[x, y]` points. This is not COCO's flat list-of-lists.
- `bbox` is `[x1, y1, x2, y2]` in pixels (x2 > x1 and y2 > y1 for every object). This is not COCO's xywh.
- Sample: figurines `frame_00041.json` → `{'category': 'old camera', 'group': 3, 'area': 12124.0, 'layer': 1.0, 'bbox': [434.0, 109.0, 607.0, 231.0], 'iscrowd': 0, 'note': ''}`.

**README / licence:** the zip contains **no** README, LICENSE or `.txt`/`.md` files, so there is no annotation licence text to copy. `THIRD_PARTY.md` row "LERF-OVS data" should read: download date 2026-09-24, Drive id `1QF1Po5p5DwTjFHu6tnTeYs_G0egMVmHt`; licence: "LERF scenes: MIT (LERF repo); LangSplat annotations: no licence stated in the zip, research use, cite LangSplat". I did not edit `THIRD_PARTY.md` because it is not in this card's Files, so the human still needs to make that edit.

**Script change vs. the card:** the HF fallback uses `hf download` instead of `huggingface-cli download`. huggingface_hub ≥ 1.0 (1.32.0 installed; `setup_lab.sh` installs it unpinned) prints "`huggingface-cli` is deprecated and no longer works". The mirror path itself was not exercised.

**Lab:** still to do: run the script and Step 2 on the lab PC. Expect exactly the counts above.
