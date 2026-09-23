# T-B12 — Query engine: text, click, debug render (GPU) + fake engine (laptop)

| Field | Value |
|---|---|
| Tier | **[M]** (it copies SAGA's scoring exactly; the camera maths must be right) |
| Depends on | T-B11, T-A06 |
| Requirements | FR-B10, FR-B11, FR-A11 |
| May edit 06-contracts.md | no |

## Goal
`server/query.py` provides `GpuEngine` (real SAGA queries) and `FakeEngine` (the laptop stand-in), with the same methods. Both return one uint8 score per Gaussian (C13).

## Background
- **Text query:**
  1. CLIP scores every training mask against the query, relative to generic negatives: "object", "things", "stuff", "texture".
  2. Clusters (objects) are scored by the average of their masks.
  3. For each well-scoring cluster, its best mask's SAGA feature and scale become a *query feature*.
  4. Every Gaussian is scored by cosine similarity after scale gating.
- **Click query:**
  1. Render SAGA's feature map from the user's current camera.
  2. Take the clicked pixel's feature.
  3. Score every Gaussian the same way; the "granularity" slider picks the scale.
- The maths is **copied from SAGA** (`clip_utils`, `saga_gui.py`, the notebook). Our one deliberate change: use **all** kept clusters. The notebook accidentally used only cluster index 0.
- **FakeEngine** exists so the whole UI works on the laptop without a GPU.

## Read first
1. `docs/spec/08-phase-b.md` §6
2. `docs/spec/06-contracts.md` §C9, §C10.5, §C11, §C13
3. Fork: `third_party/SegAnyGAussians/clip_utils/__init__.py` (`default_template` list, `get_scores_with_template`), and `clip_utils/clip_utils.py` (`OpenCLIPNetwork`)
4. Fork: `third_party/SegAnyGAussians/saga_gui.py` → `fetch_data` (≈ L572–688), and `prompt_segmenting.ipynb` cells 47–53
5. `pipeline/render.py`, `pipeline/camera.py`, `pipeline/query_index.py` (`load_saga_outputs`)

## Files
| Action | Path |
|---|---|
| create | `server/query.py` |
| create | `tests/test_query.py` |

## Provenance
NEW, with COPY blocks from SAGA (Apache-2.0): the 80 `default_template` strings, the `get_scores_with_template` logic, and the `fetch_data` similarity formula. Each block gets a `# Source:` header.

## Interface
```python
@dataclass
class QueryResult:
    scores_u8: np.ndarray       # uint8 [N]
    default_threshold: float
    info: dict
    latency_ms: float

def to_u8(sim: "torch.Tensor | np.ndarray") -> np.ndarray: ...     # round(clip((sim+1)/2, 0, 1)*255)
def text_mask_scores(mask_clip, pos, negs) -> "torch.Tensor": ...    # [T]: min_j softmax(10*[e·pos, e·neg_j])[0]
def select_clusters(scores, clusters, keep: float) -> list[tuple[int, float, int]]: ...  # (cluster, score, best_mask_index)
def gated_similarity(pf, g, q) -> "torch.Tensor": ...                # normalize(pf*g) @ q, shape [N]

class GpuEngine:
    clip_model: object; clip_preprocess: object; tokenizer: object          # public: reused by evaluation/baseline_2d.py (T-E04)
    def text_embeddings(self, text: str) -> tuple["torch.Tensor", "torch.Tensor"]: ...   # (pos [512], negs [4,512]), unit-norm, cached
    def text_query(self, scene_id: str, variant: str, seed: int, text: str) -> QueryResult: ...
    def click_query(self, scene_id: str, variant: str, seed: int, cam: dict, mesh_matrix_world: list[float],
                    pixel: tuple[float, float], scale: float) -> QueryResult: ...
    def render_rgb(self, scene_id: str, cam: dict, mesh_matrix_world: list[float]) -> np.ndarray: ...
class FakeEngine: ...                                                  # same three methods, numpy only
class Background(Exception): ...                                       # click on empty space -> HTTP 409
def get_engine() -> "GpuEngine | FakeEngine": ...                      # Fake if PS_FAKE=1 or no CUDA; cached singleton
```

## Steps
1. **Pure functions** (CPU-testable): `to_u8`, `text_mask_scores`, `select_clusters`, `gated_similarity`.
   - `select_clusters`:
     - cluster score = the mean of its masks' scores, clusters ≥ 0 only;
     - keep the clusters with score > `keep`, or the single best one if none pass;
     - for each kept cluster, the best mask is the argmax of the mask scores within it.
2. **Text embeddings** (GpuEngine):
   - `open_clip.create_model_and_transforms("ViT-B-16", pretrained="laion2b_s34b_b88k")`, fp16, on the GPU; tokenizer `open_clip.get_tokenizer("ViT-B-16")`;
   - positive: the templated mean of the normalized embeddings, then normalized;
   - negatives: exactly as `get_scores_with_template` does. COPY; don't redesign;
   - `functools.lru_cache(maxsize=512)` on the stripped, lower-cased text.
3. **Scene cache:** an `OrderedDict` LRU of 2 entries keyed by (scene, variant, seed). Each entry holds:
   - `render.load_gaussians(web/scene.ply)`;
   - `pf`, gate and `q_trans` from `query_index.load_saga_outputs`;
   - `query_index.pt` (moved to the GPU).
   Assert the C11 invariant on load (same count, same `xyz_hash` as the manifest).
4. **`text_query`:**
   - `scores = text_mask_scores(mask_clip, pos, negs)`;
   - `kept = select_clusters(scores, mask_cluster, cfg.query.cluster_keep_thresh)`;
   - for each kept cluster: `g = gate(q_trans([[mask_scale[m*]]]))`, `q = mask_feat[m*]`, `sim_c = gated_similarity(pf, g, q)`;
   - `sim = max over c`;
   - return a `QueryResult` with `to_u8(sim)`, `default_threshold = cfg.query.text_threshold`, `info = {"kept_clusters": [...]}`.
   - Cache whole results by (scene, variant, seed, text).
5. **`click_query`** (C10.5):
   - `viewmat = camera.threejs_to_viewmat(cam["matrix_world"], mesh_matrix_world)`;
   - `(w, h, s) = camera.fit_render_size(cam["width"], cam["height"], cfg.query.render_max_side)`;
   - `K = camera.fov_intrinsics(cam["fov_y_deg"], w, h)`; `(px, py) = camera.pixel_to_render(u, v, s, w, h)`;
   - `F, alpha = render.render_features(g, normalize(pf), viewmat, K, w, h)`;
   - `if alpha[py, px] < 0.5: raise Background`;
   - `gv = gate(torch.tensor([[scale]]))[0]` (the slider value **is** the quantile, as in the GUI);
   - `f = normalize(normalize(F[py, px]) * gv)`; `sim = gated_similarity(pf, gv, f)`;
   - `info = {"pixel_alpha": float(alpha[py, px])}`, `default_threshold = cfg.query.click_threshold`.
6. **`render_rgb`:** the same camera path, returning `render.render_rgb(...)`.
7. **`FakeEngine`** (numpy + `pipeline.camera` + `plyio`), loading `web/scene.ply` of any scene (the fixture on the laptop):
   - text: `rng = default_rng(int(sha1(text)) % 2**32)`; the center is a random Gaussian; `sim = 1 − 2·clip(dist / (0.25·extent), 0, 1)`;
   - click: build the ray with `camera.ray_through_pixel`. The center is the **first hit**: among Gaussians in front of the camera whose distance to the ray is < `0.02·extent`, the one with the smallest depth along the ray. If there are none, `raise Background`. Radius `r = (0.1 + 0.9·scale)·0.5·extent`; `sim = 1 − 2·clip(dist/r, 0, 1)`;
   - render: project the Gaussian centers (`camera.project`), paint them far to near with their DC colour (`0.5 + 0.2821·f_dc`) into an `h × w` image; empty = black;
   - `extent = max(xyz.max(0) − xyz.min(0))`.

## Tests (`tests/test_query.py`, CPU)
- `to_u8`: `[-1, 0, 1]` → `[0, 128, 255]` (0 → 127.5 → rounds to 128; state the rounding used).
- `text_mask_scores`: `pos = e1`, `negs = [e2, e3, e4, e5]`; a mask embedding `e1` scores > 0.99; a mask embedding `e2` scores < 0.01.
- `select_clusters`: masks with clusters `[0,0,1,−1]` and scores `[0.9,0.5,0.2,0.99]` → cluster 0 is kept (mean 0.7) with best mask 0, cluster 1 is not kept, noise is ignored.
- `gated_similarity` is 1 for `pf == q` along the gated direction.
- **FakeEngine click on the fixture** (`make_fixture` into a tmp dir, `PS_SCENES_DIR`):
  - the three.js camera at (−1, 0, 5) looking down −z (`matrix_world` = translation, column-major) with `mesh_matrix_world` = diag(1,−1,−1,1), 200×200, fov 50, clicking the center pixel;
  - the highest-scoring Gaussian lies within 0.55 of (−1, 0, 0), i.e. on the red sphere;
  - at least 90% of the Gaussians with `scores_u8 ≥ 230` are within 0.5 of (−1, 0, 0);
  - a click at a pixel that sees only empty space (the top-left corner of a camera aimed away from the scene, e.g. at three.js (0, 0, 5) looking along +z) raises `Background`.
- FakeEngine text: the same text gives the same scores twice; a different text gives different scores.

## Laptop check
```bash
pytest -q tests/test_query.py tests/test_imports.py
```

## Lab check
```bash
python - <<'EOF'
import json, numpy as np
from server.query import get_engine
e = get_engine(); print(type(e).__name__)
cats = [o["category"] for o in json.load(open(sorted(__import__("glob").glob("scenes/figurines/source/labels/*.json"))[0]))["objects"]][:3]
for v in ["sam", "sam2_frame", "sam2_track_k10"]:
    for c in cats:
        r = e.text_query("figurines", v, 0, c)
        print(v, c, "selected", int((r.scores_u8 >= round(r.default_threshold*255)).sum()), f"{r.latency_ms:.0f} ms", r.info["kept_clusters"][:2])
EOF
```
Expected:
- the engine is `GpuEngine`;
- each query selects between 0.01% and 30% of the Gaussians;
- the first query takes ~1–3 s (loading), later ones < 300 ms.
- Visual correctness is checked in the UI at T-B17.

## Done when
- [ ] Tests pass; the lab text queries return plausible selections

## Findings / Blockers
