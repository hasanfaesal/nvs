# T-F01 — Demo preparation, backup video, reproducibility dry run

| Field | Value |
|---|---|
| Tier | **[H]** human |
| Depends on | T-E09, T-C04 |
| Requirements | success criteria S1–S8 (`00-overview.md` §7) |
| May edit 06-contracts.md | no |

## Goal
A rehearsed, reliable demo on the lab PC, a backup screen recording, and proof that someone else can reproduce one scene from the docs.

## Steps
1. **Demo content:**
   - for each scene, 3 strong `demo_queries` (in `scenes.yaml`, then `export --force`);
   - one "wow" click object per scene;
   - a note on one honest failure case to show.
2. **Warm-up script** (run after every server start, so the first queries are fast):
   ```bash
   for s in figurines ramen waldo_kitchen teatime desk_01 shelf_01; do
     python -c "import json,httpx; m=httpx.get('http://127.0.0.1:8000/api/scenes/$s').json(); [httpx.post('http://127.0.0.1:8000/api/scenes/$s/query/text', json={'text': q, 'variant': 'sam2_track_k10', 'seed': 0}, timeout=120) for q in m.get('demo_queries', [])]"
   done
   ```
3. **Demo script** (5–7 min):
   1. landing: the scene list;
   2. figurines explorer: orbit;
   3. text query → highlight → isolate → recolor;
   4. click mode + the granularity slider;
   5. mask-source switch V1 → V3 on the same query;
   6. the pseudo-label viewer (V1 flicker vs V3 stable);
   7. the results page: main table, MRC, one failure case;
   8. a custom scene.
4. **Backup video:** record the whole script with OBS on Windows (1080p) and keep it on the laptop **and** a USB drive.
5. **Reproducibility dry run (S8):** a classmate, or you on a fresh clone in a new folder, follows `docs/spec/README.md` → `07-phase-a.md` to process **one** scene end to end, without help. Write down every point where they got stuck, and fix the docs.
6. **Presentation-day checklist:**
   - lab PC awake, no pending Windows Update;
   - tmux: server running; warm-up done;
   - `tailscale serve` active;
   - browser full-screen at `localhost:8000`;
   - backup video ready;
   - `nvidia-smi` clean.
7. Final tag: `git tag v1.0 && git push --tags`.

## Done when
- [ ] Demo rehearsed twice within the time; backup video saved; dry-run notes addressed; `v1.0` tagged

## Laptop check
None. This is a human [H] card; nothing is coded here.

## Lab check
The Steps / Checklist above are the lab check. Record the results under Findings.

## Findings / Blockers
