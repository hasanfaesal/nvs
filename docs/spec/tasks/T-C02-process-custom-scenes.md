# T-C02 — Ingest the custom scenes and pick the frames to annotate

| Field | Value |
|---|---|
| Tier | **[H]** human |
| Depends on | T-C01, T-A15 |
| Requirements | FR-A2, FR-E10 |
| May edit 06-contracts.md | no |

## Goal
Both custom scenes are ingested (frames + COLMAP). For each, 6 evenly spaced frames are chosen and exported for annotation. **Nothing is trained yet**: the annotated frames must be held out, so the split happens after annotation (T-C04).

## Steps
1. Add both scenes to `configs/scenes.yaml`:
   ```yaml
   desk_01:  {title: Desk (custom), dataset: custom, input_type: video, input: data/raw/custom/desk_01/video.mp4, labels: data/raw/custom/desk_01/labels, demo_queries: []}
   shelf_01: {title: Shelf (custom), dataset: custom, input_type: video, input: data/raw/custom/shelf_01/video.mp4, labels: data/raw/custom/shelf_01/labels, demo_queries: []}
   ```
2. Ingest: `for s in desk_01 shelf_01; do python -m pipeline ingest --scene $s; done`.
   - If fewer than 80% of frames register, try the second take (`video_b.mp4`), or recapture following `07-phase-a.md` §8.
3. Pick the frames to annotate: 6 evenly spaced registered frames, avoiding the first and last 5%.
   ```bash
   python - <<'EOF'
   import shutil
   from pipeline.colmap_io import load_cameras
   from pipeline.config import scene_dir
   for s in ["desk_01", "shelf_01"]:
       names = sorted(load_cameras(scene_dir(s)/"source/sparse/0"))
       lo, hi = int(0.05*len(names)), int(0.95*len(names))
       pick = [names[lo + round(i*(hi-lo-1)/5)] for i in range(6)]
       out = scene_dir(s).parent.parent/"data/raw/custom"/s/"to_annotate"; out.mkdir(parents=True, exist_ok=True)
       for n in pick: shutil.copy2(scene_dir(s)/"source/images"/n, out/n)
       print(s, pick)
   EOF
   ```
4. Record the picked names in Findings. Copy the `to_annotate/` folders to wherever you'll annotate (T-C03).

## Done when
- [ ] Both scenes ingested (≥ 80% registered); 6 frames per scene exported for annotation

## Laptop check
None. This is a human [H] card; nothing is coded here.

## Lab check
The Steps / Checklist above are the lab check. Record the results under Findings.

## Findings / Blockers
