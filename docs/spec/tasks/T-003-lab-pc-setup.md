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
5. **Repo** (the lab now commits and pushes, including fork branches, so `gh` auth is always needed):
   ```bash
   sudo apt install -y gh && gh auth login && gh auth setup-git
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
- [ ] `nvidia-smi` and `nvcc` 12.8 work in WSL
- [ ] conda works; the repo is cloned with all submodules (including SAGA's nested ones)
- [ ] `.venv` + `pytest` pass on the lab; VS Code Remote-SSH + Claude Code open `~/nvs`; `git push` works from the lab
- [ ] Findings filled in (the other cards rely on the GCC and Ubuntu versions)

## Findings / Blockers
