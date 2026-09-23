# T-B10 — Shared gsplat rendering helpers (`pipeline/render.py`)

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-A06, T-004 |
| Requirements | FR-B8 |
| May edit 06-contracts.md | no |

## Goal
One module loads Gaussians from a PLY and renders, with gsplat:
- RGB images;
- N-dimensional features (SAGA's 32-D);
- per-Gaussian scalars (selection or score);
- expected depth + alpha.

The query index, the server and the evaluation all use it.

## Background
`gsplat.rasterization` alpha-composites **any** per-Gaussian vector (glossary: *alpha compositing*):
- `sh_degree=3` with SH coefficients gives colour;
- `sh_degree=None` with an `[N, D]` tensor gives a D-channel image (features, a 0/1 selection, scores);
- `render_mode="RGB+ED"` appends the expected depth as the last channel.

Inputs must be **activated**: `scales = exp(log_scales)`, `opacities = sigmoid(logits)`. Cameras are world→camera `viewmats` plus pixel `Ks` (C10.2).

## Read first
1. `docs/spec/06-contracts.md` §C10.2, §C11
2. `docs/spec/02-glossary.md` §B
3. `pipeline/plyio.py`
4. gsplat: `gsplat/rendering.py::rasterization` docstring (signature in `05-codebase-map.md` notes: `rasterization(means, quats, scales, opacities, colors, viewmats, Ks, width, height, ..., sh_degree=None, render_mode="RGB", ...) -> (colors [C,H,W,X], alphas [C,H,W,1], meta)`)

## Files
| Action | Path |
|---|---|
| create | `pipeline/render.py` |
| create | `tests/test_render_load.py` |

## Provenance
NEW, using **gsplat** (PIP from the fork).

## Interface
```python
@dataclass
class Gaussians:
    means: "torch.Tensor"      # [N,3]
    quats: "torch.Tensor"      # [N,4] wxyz
    scales: "torch.Tensor"     # [N,3] ACTIVATED (exp)
    opacities: "torch.Tensor"  # [N]   ACTIVATED (sigmoid)
    sh: "torch.Tensor"         # [N,16,3]

def load_gaussians(ply: Path, device: str = "cuda") -> Gaussians: ...
def render_rgb(g: Gaussians, viewmat: np.ndarray, K: np.ndarray, w: int, h: int) -> np.ndarray: ...          # uint8 [h,w,3]
def render_features(g: Gaussians, feats: "torch.Tensor", viewmat, K, w, h) -> tuple["torch.Tensor", "torch.Tensor"]: ...  # [h,w,D], alpha [h,w]
def render_scalar(g: Gaussians, values: "torch.Tensor", viewmat, K, w, h) -> np.ndarray: ...                # float [h,w]
def render_depth(g: Gaussians, viewmat, K, w, h) -> tuple[np.ndarray, np.ndarray]: ...                     # depth [h,w], alpha [h,w]
```

## Steps
1. `load_gaussians`:
   - `d = plyio.read_vertex(ply)`;
   - `means` = stack of x, y, z; `quats` = `rot_0..3`;
   - `scales = exp(scale_0..2)`; `opacities = sigmoid(opacity)`;
   - `f_dc [N,1,3]`; `f_rest [N,45] → reshape [N,3,15] → transpose(1,2) → [N,15,3]`; `sh = cat → [N,16,3]`;
   - all float32 on `device`.
2. A private `_raster(g, colors, viewmat, K, w, h, sh_degree, mode)`:
   - `from gsplat import rasterization` inside;
   - `viewmats = torch.as_tensor(viewmat, dtype=torch.float32, device=dev)[None]`, same for `Ks`;
   - call `rasterization(g.means, g.quats, g.scales, g.opacities, colors, viewmats, Ks, w, h, sh_degree=sh_degree, render_mode=mode)`;
   - return `out[0], alpha[0, ..., 0]`.
3. The public functions:
   - `render_rgb` → `(out.clamp(0,1)*255).round().byte().cpu().numpy()`;
   - `render_features` → `_raster(g, feats, …, None, "RGB")`;
   - `render_scalar` → `_raster(g, values[:, None].float(), …, None, "RGB")[0][..., 0]`;
   - `render_depth` → `_raster(g, g.sh, …, 3, "RGB+ED")`, then `out[..., 3]` and the alpha.
4. Wrap the calls in `torch.no_grad()`.

## Tests (CPU, `load_gaussians(device="cpu")` only; rasterization is lab-only)
- Write 4 Gaussians with `plyio.write_gaussians_ply` (log scales `log(0.1)`, logit opacity `0.0`, random `shN`), then load them:
  - `scales ≈ 0.1`, `opacities ≈ 0.5`;
  - `sh.shape == (4,16,3)`, `sh[:, 1+k, c] == shN[:, k, c]`.

## Laptop check
```bash
pytest -q tests/test_render_load.py tests/test_imports.py
```

## Lab check
```bash
python - <<'EOF'
import json, time, numpy as np, cv2
from pipeline.config import scene_dir
from pipeline import colmap_io, render
from pipeline.camera import colmap_viewmat
s = scene_dir("ramen"); split = json.load(open(s/"split.json")); cams = colmap_io.load_cameras(s/"source/sparse/0")
g = render.load_gaussians(s/"web/scene.ply")
ps = []
for n in split["test"][:5]:
    c = cams[n]; t0 = time.time(); img = render.render_rgb(g, colmap_viewmat(c.R, c.t), c.K, c.width, c.height)
    gt = cv2.cvtColor(cv2.imread(str(s/"source/images"/n)), cv2.COLOR_BGR2RGB)
    mse = ((img.astype(float) - gt.astype(float))**2).mean(); ps.append(10*np.log10(255**2/mse)); print(n, round(ps[-1],2), f"{(time.time()-t0)*1000:.0f} ms")
print("mean PSNR", np.mean(ps), "manifest PSNR", json.load(open(s/"web/manifest.json"))["metrics_3dgs"]["psnr"])
c = cams[split["train"][0]]; d, a = render.render_depth(g, colmap_viewmat(c.R, c.t), c.K, c.width // 4, c.height // 4)
print("depth>0 where alpha>0.5:", bool((d[a > 0.5] > 0).all()))
import torch; f, a = render.render_features(g, torch.randn(len(g.means), 32, device="cuda"), colmap_viewmat(c.R, c.t), c.K / 4 * [[1],[1],[4]], c.width // 4, c.height // 4)
print("feature map", tuple(f.shape))
EOF
```
Expected:
- the mean PSNR is within ~1 dB of the manifest PSNR;
- depth is positive under alpha;
- the feature map shape is `(h, w, 32)`;
- each render takes tens of ms.

Note: `K/4` must scale fx, fy, cx and cy **but not** the bottom row. The snippet does it inline; in real code use `camera.intrinsics(..., scale=0.25)`.

## Done when
- [ ] Tests pass; the lab PSNR check passes

## Findings / Blockers
