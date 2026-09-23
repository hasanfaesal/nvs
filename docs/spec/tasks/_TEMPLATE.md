# T-XXX — <Title>

| Field | Value |
|---|---|
| Tier | [S] small model / [M] stronger model or reviewed / [H] human |
| Depends on | T-…, T-… (must be `done` in `tasks/README.md`) |
| Requirements | FR-…, NFR-… (`docs/spec/03-requirements.md`) |
| May edit 06-contracts.md | no |

## Goal
One or two sentences: what exists after this card that didn't exist before.

## Background (plain language)
3–8 sentences explaining the concept, why it's needed, and what usually goes wrong. Link glossary terms (`docs/spec/02-glossary.md`).

## Read first (max 5)
1. `docs/spec/06-contracts.md` §C…
2. `docs/spec/0X-….md` §…
3. Upstream: `<repo>` @ pinned SHA (`THIRD_PARTY.md`): `<path>` :: `<symbol>`

## Files
| Action | Path |
|---|---|
| create | `pipeline/example.py` |
| create | `tests/test_example.py` |
| modify | `pipeline/cli.py`: add subcommand `example` |

## Provenance
- `pipeline/example.py`: NEW / COPY from `<repo>:<path>::<symbol>` / WRAP `<script>` (see `05-codebase-map.md`).

## Interface
```python
def example(scene_id: str, force: bool = False) -> Path: ...
```
CLI: `python -m pipeline example --scene <id> [--force]`

## Steps
1. …
2. …

## Gotchas
- …

## Laptop check (the model runs this; must pass before committing)
```bash
source .venv/bin/activate && pytest -q tests/test_example.py
```
Expected: all tests pass.

## Lab check (you run on the lab PC; paste the output back if it fails)
```bash
cd ~/nvs && git pull --recurse-submodules && conda activate ps
python -m pipeline example --scene figurines
```
Expected: …

## Done when
- [ ] Laptop check passes
- [ ] Lab check output matches "Expected"
- [ ] Commit `T-XXX: …` pushed; status set to `done` in `tasks/README.md`

## Findings / Blockers
<!-- The implementer writes here: VERIFY results, surprises, anything that blocks. -->
