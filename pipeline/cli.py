"""`python -m pipeline <command>` argument parser (NEW). See C16."""
import argparse
import shutil
from pathlib import Path

from pipeline.config import load_config, repo_root, scenes_root
from pipeline.export_web import export
from pipeline.ingest import ingest_colmap, ingest_from_config, ingest_images, ingest_video
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
    labels = args.labels and args.labels.resolve()
    if args.colmap:
        ingest_colmap(args.scene, args.colmap.resolve(), labels, args.force)
    elif args.video:
        ingest_video(args.scene, args.video.resolve(), labels, args.force)
    elif args.images:
        ingest_images(args.scene, args.images.resolve(), labels, args.matcher, args.force)
    else:
        ingest_from_config(args.scene, args.force)
    return 0


def cmd_split(args: argparse.Namespace) -> int:
    build_split(args.scene, args.force)
    return 0


def cmd_train3dgs(args: argparse.Namespace) -> int:
    train(args.scene, args.max_steps, args.force)
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    export(args.scene, args.force)
    return 0


def build_parser()-> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("info", help="print paths, scenes, GPU and git info").set_defaults(func=cmd_info)
    # Stage cards add their subcommands below.
    p = sub.add_parser("ingest", help="build scenes/<id>/source/ from a posed dataset, a video or photos (C3)")
    p.add_argument("--scene", required=True)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--colmap", type=Path, help="dir with images/ and sparse/[0]; default: configs/scenes.yaml")
    g.add_argument("--video", type=Path, help="phone video; frames + COLMAP with the sequential matcher")
    g.add_argument("--images", type=Path, help="photo folder; resized copies + COLMAP")
    p.add_argument("--matcher", choices=("sequential", "exhaustive"), default="exhaustive",
                   help="COLMAP matcher for --images (video always uses sequential)")
    p.add_argument("--labels", type=Path, help="dir of GT *.json (with --colmap, --video or --images)")
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
    p = sub.add_parser("export", help="write web/scene.ply, web/manifest.json and results/<id>/phase_a.json (C5, C14.1)")
    p.add_argument("--scene", required=True)
    p.add_argument("--force", action="store_true", help="overwrite an existing export")
    p.set_defaults(func=cmd_export)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args) or 0
