"""`python -m pipeline <command>` argument parser (NEW). See C16."""
import argparse
import shutil
from pathlib import Path

from pipeline.config import load_config, repo_root, scenes_root
from pipeline.ingest import ingest_colmap, ingest_from_config
from pipeline.run_stage import git_sha
from pipeline.split import build_split
from pipeline.train_3dgs import train


def cmd_info(args: argparse.Namespace) -> int:
    cfg = load_config()
    print(f"repo root:   {repo_root()}")
    print(f"scenes root: {scenes_root(cfg)}")
    print(f"scenes:      {', '.join(cfg['scenes'])}")
    print(f"nvidia-smi:  {'found' if shutil.which('nvidia-smi') else 'missing'}")
    print(f"git sha:     {git_sha()}")
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    if args.colmap:
        ingest_colmap(args.scene, args.colmap.resolve(), args.labels and args.labels.resolve(), args.force)
    else:
        ingest_from_config(args.scene, args.force)
    return 0


def cmd_split(args: argparse.Namespace) -> int:
    build_split(args.scene, args.force)
    return 0


def cmd_train3dgs(args: argparse.Namespace) -> int:
    train(args.scene, args.max_steps, args.force)
    return 0


def build_parser()-> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("info", help="print paths, scenes, GPU and git info").set_defaults(func=cmd_info)
    # Stage cards add their subcommands below.
    p = sub.add_parser("ingest", help="copy a posed dataset into scenes/<id>/source/ (C3)")
    p.add_argument("--scene", required=True)
    p.add_argument("--colmap", type=Path, help="dir with images/ and sparse/[0]; default: configs/scenes.yaml")
    p.add_argument("--labels", type=Path, help="dir of GT *.json (with --colmap)")
    p.add_argument("--force", action="store_true", help="delete source/ and re-copy")
    p.set_defaults(func=cmd_ingest)
    p = sub.add_parser("split", help="write scenes/<id>/split.json (C4)")
    p.add_argument("--scene", required=True)
    p.add_argument("--force", action="store_true", help="overwrite an existing split.json")
    p.set_defaults(func=cmd_split)
    p = sub.add_parser("train3dgs", help="gsplat MCMC training into scenes/<id>/3dgs/ (C3)")
    p.add_argument("--scene", required=True)
    p.add_argument("--max-steps", type=int, help="smoke run; default: gsplat.max_steps in configs/pipeline.yaml")
    p.add_argument("--force", action="store_true", help="delete 3dgs/ and retrain")
    p.set_defaults(func=cmd_train3dgs)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args) or 0
