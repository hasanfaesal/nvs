# T-C03 — Annotate the held-out frames with labelme

| Field | Value |
|---|---|
| Tier | **[H]** human (~1–2 h per scene) |
| Depends on | T-C02 |
| Requirements | FR-E1, FR-E10 |
| May edit 06-contracts.md | no |

## Goal
Every exported frame has a labelme JSON with a polygon for every visible object from the scene's object list. The labels are placed where ingest expects them.

## Background
These are the **ground truth** for your own scenes, and they are never used for training. `evaluation/gt.py` reads labelme's format (`shapes[].label`, `points`) and unions polygons with the same label, so two mugs both labelled `mug` count as one query "mug" with two instances.

## Tool
labelme (https://github.com/wkentaro/labelme). Either:
- **Windows (lab PC):** download the standalone `Labelme.exe` from the GitHub releases page; or
- **Laptop:** `uv tool install labelme` (needs about 300 MB of disk; check `df -h` first).

Start it with `labelme <folder> --nodata --autosave`. `--nodata` keeps the image bytes out of the JSON.

## Annotation rules
1. Use the **exact label names** from T-C01's object list, lower-case (e.g. `red mug`). Same spelling in every frame.
2. **Polygon**, following the visible outline within about 2 px. Do not annotate hidden (occluded) parts.
3. **Several instances of a category:** one polygon each, same label.
4. Skip objects that are < 20×20 px or mostly out of frame. Don't label the background or the table.
5. Each JSON sits next to its image (`frame_000NN.json`). Keep the default `imagePath`.

## Steps
1. Annotate `data/raw/custom/<scene>/to_annotate/*.jpg` for both scenes.
2. Put the JSONs in `data/raw/custom/<scene>/labels/` on the lab PC (the images aren't needed there).
3. Copy them into the scene: `python -m pipeline ingest --scene <scene> --force` would redo COLMAP, so **don't**. Instead:
   `mkdir -p scenes/<scene>/source/labels && cp data/raw/custom/<scene>/labels/*.json scenes/<scene>/source/labels/`
4. Check the parse:
   `python -c "from evaluation.gt import scene_gt; g=scene_gt('desk_01'); print({k: sorted(v[1]) for k,v in g.items()})"`

## Done when
- [ ] 6 labelled frames per scene; `scene_gt` parses them all; the label names are consistent

## Laptop check
None. This is a human [H] card; nothing is coded here.

## Lab check
The Steps / Checklist above are the lab check. Record the results under Findings.

## Findings / Blockers
