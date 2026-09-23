"""`python -m pipeline <command>` argument parser (NEW). See C16."""
import argparse
import shutil

from pipeline.config import load_config, repo_root, scenes_root
from pipeline.run_stage import git_sha


def cmd_info(args: argparse.Namespace) -> int:
    cfg = load_config()
    print(f"repo root:   {repo_root()}")
    print(f"scenes root: {scenes_root(cfg)}")
    print(f"scenes:      {', '.join(cfg['scenes'])}")
    print(f"nvidia-smi:  {'found' if shutil.which('nvidia-smi') else 'missing'}")
    print(f"git sha:     {git_sha()}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("info", help="print paths, scenes, GPU and git info").set_defaults(func=cmd_info)
    # Stage cards add their subcommands below.
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args) or 0
