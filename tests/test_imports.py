"""Every module must import on the laptop without pulling GPU libraries (AGENTS.md rule 5)."""
import importlib
import pkgutil
import sys

GPU_MODULES = ("gsplat", "sam2", "segment_anything", "open_clip", "hdbscan")
PACKAGES = ("pipeline", "server", "evaluation", "experiments")


def test_all_modules_import_without_gpu_libs():
    for name in PACKAGES:
        pkg = importlib.import_module(name)
        for info in pkgutil.walk_packages(pkg.__path__, name + "."):
            if info.name.endswith("__main__"):
                continue  # importing __main__ would run the CLI
            importlib.import_module(info.name)
    loaded = [m for m in GPU_MODULES if m in sys.modules]
    assert not loaded, f"GPU libraries imported at module level: {loaded}"
