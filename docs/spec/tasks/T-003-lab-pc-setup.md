# T-003 — Lab PC setup: WSL2, CUDA toolkit, conda, repo, Tailscale, remote coding

| Field | Value |
|---|---|
| Tier | **[H]** human |
| Depends on | – (T-001 for the clone step) |
| Requirements | NFR-1, NFR-7 |
| May edit 06-contracts.md | no |

## Goal
The lab PC's WSL2 Ubuntu can compile CUDA code, has conda, holds the repo with all submodules, is reachable over Tailscale, and is the machine where you and the coding model work (VS Code Remote-SSH + Claude Code; see `10-workflow-small-models.md` §2).

## Background
WSL2 uses the **Windows** NVIDIA driver; you install only the CUDA *toolkit* (the compiler, `nvcc`) inside Ubuntu, never a Linux driver. PyTorch 2.9.1 wheels use CUDA 12.8, so `nvcc` must be 12.8 as well to compile gsplat and SAGA's extensions. Keep all project files on the WSL filesystem (`~/nvs`), not `/mnt/c`, which is very slow.

## Read first
1. `docs/spec/04-architecture-and-env.md` §6, §8, §11

## Steps (tick each; paste the checked outputs into "Findings")
1. **Windows:**
   - [ ] NVIDIA driver recent enough for CUDA 12.8 (R570+). Update it from nvidia.com if needed.
   - [ ] `%UserProfile%\.wslconfig`:
     ```ini
     [wsl2]
     memory=24GB
     swap=16GB
     processors=12
     ```
     Then `wsl --shutdown` in PowerShell and reopen Ubuntu.
   - [ ] Power plan: sleep = Never (plugged in). Pause Windows Update during long runs.
2. **WSL Ubuntu:**
   ```bash
   lsb_release -a; gcc --version | head -1          # note the versions
   sudo apt update && sudo apt install -y build-essential git tmux curl wget unzip
   nvidia-smi                                         # must show RTX A4000 and "CUDA Version: 12.8" or higher
   ```
3. **CUDA toolkit 12.8 for WSL.** VERIFY the current keyring file name at https://developer.nvidia.com/cuda-downloads (Linux → x86_64 → WSL-Ubuntu → deb (network)).
   ```bash
   wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
   sudo dpkg -i cuda-keyring_1.1-1_all.deb && sudo apt update && sudo apt install -y cuda-toolkit-12-8
   echo 'export PATH=/usr/local/cuda-12.8/bin:$PATH' >> ~/.bashrc
   echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.8/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
   echo 'export TORCH_CUDA_ARCH_LIST="8.6"' >> ~/.bashrc
   source ~/.bashrc && nvcc --version                 # release 12.8
   ```
4. **Miniforge:**
   ```bash
   curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
   bash Miniforge3-$(uname)-$(uname -m).sh -b -p "$HOME/miniforge3" && "$HOME/miniforge3/bin/conda" init bash
   exec bash && conda --version
   ```
5. **Repo.** No GitHub login on the lab: the PC is shared, and a stored token would give anyone on it push access to all your repos. Commits are made on the lab, fetched to the laptop over SSH (`git fetch lab-pc5:nvs phase-a`) and pushed from there. The repo is public, so cloning needs no auth.
   ```bash
   git config --global user.name "Hasan Faisal"
   git config --global user.email "<your GitHub email>"
   git config --global url."https://github.com/".insteadOf git@github.com:
   git clone -b phase-a --recurse-submodules https://github.com/hasanfaesal/nvs.git ~/nvs   # current working branch
   cd ~/nvs && git submodule status
   ```
6. **CPU `.venv` and coding tools:**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh && exec bash     # uv
   cd ~/nvs && bash scripts/setup_laptop.sh && source .venv/bin/activate && pytest   # CPU checks
   curl -fsSL https://claude.ai/install.sh | bash                   # Claude Code; VERIFY the installer URL at docs.claude.com
   ```
   Node for the web cards comes from the conda `ps` env (T-004).
7. **Tailscale + Remote-SSH.** Already installed in WSL (you use `tailscale ssh`).
   ```bash
   tailscale status
   tailscale serve --help | head -40                 # VERIFY the syntax; expected: sudo tailscale serve --bg 8000
   ```
   Don't enable `serve` yet; T-A16 does it once the server exists.
   - On the laptop: add `Host lab` to `~/.ssh/config` (doc 10 §2); VS Code → *Remote-SSH: Connect to Host… → lab* → open `~/nvs`; run `claude` in its terminal. It must load `AGENTS.md` (ask it "what is rule 8?").
   - The laptop clone `~/code3/gsp` is retired once this works: make sure it has nothing unpushed first (`git status -sb`).
8. **Space:** `df -h ~` shows ≥ 200 GB free; `free -h` shows the `.wslconfig` memory.

## Laptop check
None.

## Lab check
Everything in the steps above. Paste into "Findings": Ubuntu version, GCC version, `nvidia-smi` header line, `nvcc --version` last line, `conda --version`, `git submodule status`, the `tailscale serve` syntax, and the `pytest` summary line from `~/nvs`.

## Done when
- [x] `nvidia-smi` and `nvcc` 12.8 work in WSL
- [x] conda works; the repo is cloned with all submodules (including SAGA's nested ones)
- [x] `.venv` + `pytest` pass on the lab; commits reach GitHub via the laptop (step 5)
- [x] Findings filled in (the other cards rely on the GCC and Ubuntu versions)

## Findings / Blockers
- Lab PC = `DESKTOP-9PFE671`, reached from the laptop with `ssh lab-pc5`; WSL user `hasanfaesal`, repo at `~/nvs`.
- Ubuntu 22.04.5 LTS (jammy); `gcc (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0`.
- `NVIDIA-SMI 580.105.07  Driver Version: 581.80  CUDA Version: 13.0`; RTX A4000 16376 MiB. `nvidia-smi` is at `/usr/lib/wsl/lib/` and is not on the PATH of non-interactive SSH shells.
- `nvcc`: `Build cuda_12.8.r12.8/compiler.35583870_0` (release 12.8, V12.8.93). `developer.download.nvidia.com` ran at ~2–40 kB/s from the lab network (PyTorch's server ran at ~5.7 MB/s); a retry of the apt install went through.
- `conda 26.7.2` (Miniforge at `~/miniforge3`); `uv 0.12.20`.
- The `.bashrc` CUDA exports only apply to interactive shells (Ubuntu's `.bashrc` returns early otherwise), so scripts run over SSH export `PATH`/`TORCH_CUDA_ARCH_LIST` themselves.
- `.wslconfig` (in `C:\Users\IMRAN`) has `memory=56GB` and no CPU cap: WSL sees 54 GiB and 32 cores, more than step 1 asks for. Left unchanged. The WSL distro belongs to the Windows account IMRAN, so anyone on that account can read `~`; hence no GitHub credentials on the lab (step 5).
- `git submodule status --recursive`: AutoSeg-SAM2 `5814307` (+ segment-anything-1 `1ded132`, segment-anything-2 `c98aa6b`), SegAnyGAussians `2e1927a` (+ kmeans_pytorch `f7f36bd`, segment-anything `6fdee8f`), gsplat `297addc8` (+ glm `2d4c4b4d`, googletest `d72f9c8a`). SAGA's 4 rasterizer/simple-knn dirs are vendored in `submodules/`, not git submodules.
- `pytest` on the lab: `49 passed, 1 skipped in 0.93s`.
- `tailscale serve` syntax: `tailscale serve --bg 8000` (add `sudo` if it asks for operator rights). Not enabled yet.
- Skipped: Claude Code install and VS Code Remote-SSH on the lab. The model runs on the laptop and drives the lab over `ssh lab-pc5`, which also keeps credentials off the lab.

