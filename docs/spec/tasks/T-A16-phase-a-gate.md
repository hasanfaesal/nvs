# T-A16 — Phase A gate: full runs, measurements, demo check

| Field | Value |
|---|---|
| Tier | **[H]** human |
| Depends on | T-A07, T-A12, T-A15 |
| Requirements | FR-A1–FR-A11, NFR-1, NFR-3, NFR-4, NFR-6, NFR-8, NFR-11 |
| May edit 06-contracts.md | no |

## Goal
All 4 LERF-OVS scenes are trained at full length, exported, measured and viewable. Phase A is tagged done.

## Read first
1. `docs/spec/07-phase-a.md` §12–§13
2. `docs/spec/04-architecture-and-env.md` §8, §11

## Steps (lab PC, inside tmux)
1. **Full training**, ~20–40 min per scene:
   ```bash
   tmux new -s ps   # or: tmux attach -t ps
   conda activate ps && cd ~/nvs && git pull --recurse-submodules
   for s in figurines ramen waldo_kitchen teatime; do
     python -m pipeline train3dgs --scene $s --force && python -m pipeline export --scene $s --force
   done
   ```
2. **VRAM and time check:**
   ```bash
   python - <<'EOF'
   import json, glob
   for f in sorted(glob.glob("scenes/*/logs/stages.jsonl")):
       for line in open(f):
           r = json.loads(line)
           if r["peak_vram_mb"] is not None:
               print(f.split("/")[1], r["stage"], round(r["seconds"]), r["peak_vram_mb"] - (r["baseline_vram_mb"] or 0))
   EOF
   ```
   Every delta must be < 14000 MB.
3. **Build and serve:**
   ```bash
   cd web && npm install && npx nuxi generate && cd ..
   uvicorn server.app:app --host 127.0.0.1 --port 8000        # leave running in a tmux window
   sudo tailscale serve --bg 8000                               # the syntax you recorded in T-003
   ```
4. **Lab-PC browser** (Windows, `http://localhost:8000`). For each scene:
   - time the load (< 15 s);
   - orbit for 10 s and read the FPS (≥ 30);
   - write the FPS into `results/<id>/phase_a.json` as `"fps_lab"`.
5. **Laptop** over the tailnet: open `https://<lab-machine>.<tailnet>.ts.net`. The list and one scene should load (the FPS may be low on the iGPU; that's fine).
6. Laptop: `pytest -q` passes.
7. Commit the results and tag:
   ```bash
   git add results && git commit -m "T-A16: Phase A results" && git push
   git tag phase-a-done && git push --tags
   ```

## Checklist
- [ ] 4 scenes: `source/`, `split.json`, `3dgs/` checkpoint + stats, `web/scene.ply` + `manifest.json`, `results/<id>/phase_a.json`
- [ ] PSNR > 20 dB on each LERF scene (record PSNR/SSIM/LPIPS in Findings)
- [ ] All VRAM deltas < 14 GB
- [ ] Lab browser: load < 15 s, FPS ≥ 30 on each scene
- [ ] Tailnet access from the laptop works
- [ ] One phone video done (T-A15)
- [ ] `pytest -q` green; tag pushed

## Laptop check
None. This is a human [H] card; nothing is coded here.

## Lab check
The Steps / Checklist above are the lab check. Record the results under Findings.

## Findings / Blockers
| Scene | PSNR | SSIM | LPIPS | #Gaussians | train min | peak VRAM | load s | FPS |
|---|---|---|---|---|---|---|---|---|
| figurines | | | | | | | | |
| ramen | | | | | | | | |
| waldo_kitchen | | | | | | | | |
| teatime | | | | | | | | |
