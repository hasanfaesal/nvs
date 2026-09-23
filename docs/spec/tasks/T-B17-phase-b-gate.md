# T-B17 — Phase B gate: all LERF scenes queryable, latency measured, UI verified

| Field | Value |
|---|---|
| Tier | **[H]** human |
| Depends on | T-B15, T-B16 (and T-B09–T-B13) |
| Requirements | FR-B1–FR-B15, NFR-1, NFR-2, NFR-5, NFR-7 |
| May edit 06-contracts.md | no |

## Goal
Text and click queries work in the browser for every LERF-OVS scene and every core variant (seed 0), latency is measured, and Phase B is tagged done.

## Read first
1. `docs/spec/08-phase-b.md` §12–§13

## Steps
1. **Train and index** the remaining scenes. Run it in tmux, and stop the server first; this takes hours.
   ```bash
   for s in ramen waldo_kitchen teatime figurines; do for v in sam sam2_frame sam2_track_k10; do
     python -m pipeline all --scene $s --variant $v --seeds 0 || break 2; done; done
   ```
2. **Demo queries:** for each scene, pick 3–5 label categories and put them in `configs/scenes.yaml` → `demo_queries`. Re-run `python -m pipeline export --scene <id> --force` so the manifest picks them up (the web PLY is unchanged).
3. **Rebuild the web app and start the server:** `cd web && npx nuxi generate && cd .. && uvicorn server.app:app --host 127.0.0.1 --port 8000`.
4. **UI checks** (lab browser), for each scene × variant:
   - 3 text queries; screenshot to `docs/figures/phaseb/<scene>_<variant>_<query>.png`;
   - note in Findings whether the right object was selected.
   Also:
   - click queries on 2 objects, with the granularity slider showing part vs whole;
   - every mode, recolor, history and the variant/seed switch;
   - the alignment overlay on each scene.
5. **Latency benchmark** (server warm; writes C14.6), for each scene:
   ```bash
   python - <<'EOF'
   import httpx, json, time, glob, statistics, numpy as np, subprocess
   BASE = "http://127.0.0.1:8000"; V = "sam2_track_k10"
   sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
   def look_at(p, t, up):
       p, t, up = map(np.asarray, (p, t, up)); z = p - t; z /= np.linalg.norm(z); x = np.cross(up, z); x /= np.linalg.norm(x); y = np.cross(z, x)
       return [*x, 0, *y, 0, *z, 0, *p, 1]                        # three.js column-major camera->world
   MESH = [1, 0, 0, 0, 0, -1, 0, 0, 0, 0, -1, 0, 0, 0, 0, 1]
   for scene in ["figurines", "ramen", "waldo_kitchen", "teatime"]:
       m = httpx.get(f"{BASE}/api/scenes/{scene}").json(); iv = m["initial_view"]
       cats = sorted({o["category"] for f in glob.glob(f"scenes/{scene}/source/labels/*.json") for o in json.load(open(f))["objects"]})
       texts = [f"{pre}{c}" for pre in ["", "a ", "the "] for c in cats][:21]
       httpx.post(f"{BASE}/api/scenes/{scene}/query/text", json={"text": "warm up", "variant": V, "seed": 0}, timeout=120)
       tm = []
       for t in texts[:20]:
           t0 = time.time(); httpx.post(f"{BASE}/api/scenes/{scene}/query/text", json={"text": t, "variant": V, "seed": 0}, timeout=120); tm.append((time.time()-t0)*1000)
       cam = {"matrix_world": look_at(iv["position"], iv["target"], iv["up"]), "fov_y_deg": iv["fov_y_deg"], "width": 1280, "height": 720}
       cm, rng = [], np.random.default_rng(0)
       while len(cm) < 20:
           px = [float(rng.uniform(320, 960)), float(rng.uniform(180, 540))]
           t0 = time.time(); r = httpx.post(f"{BASE}/api/scenes/{scene}/query/click", json={"variant": V, "seed": 0, "camera": cam, "mesh_matrix_world": MESH, "pixel": px, "scale": 0.5}, timeout=120)
           if r.status_code == 200: cm.append((time.time()-t0)*1000)
       out = {"scene_id": scene, "variant": V, "seed": 0, "n_text": len(tm), "text_median_ms": statistics.median(tm), "text_p90_ms": float(np.percentile(tm, 90)),
              "n_click": len(cm), "click_median_ms": statistics.median(cm), "click_p90_ms": float(np.percentile(cm, 90)), "warm": True, "git_sha": sha}
       json.dump(out, open(f"results/{scene}/latency.json", "w"), indent=1); print(out)
   EOF
   ```
6. **VRAM:** re-run the T-A16 VRAM snippet. Every Phase B stage must be < 14 GB.
7. **Commit and tag:** `git add results configs/scenes.yaml docs/figures/phaseb && git commit -m "[ENH]: Add Phase B gate results" && git push && git tag phase-b-done && git push --tags`.

## Checklist
- [ ] 4 scenes × 3 variants × seed 0 have `query_index.pt`
- [ ] Text queries checked, screenshots saved, correctness noted
- [ ] Click and granularity OK; modes, history, switching OK; overlay aligned
- [ ] `latency.json` medians < 2000 ms for text and click on every scene
- [ ] VRAM deltas < 14 GB; tag pushed

## Laptop check
None. This is a human [H] card; nothing is coded here.

## Lab check
The Steps / Checklist above are the lab check. Record the results under Findings.

## Findings / Blockers
