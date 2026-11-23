#!/usr/bin/env python3
"""Build one upload-ready zip per skill.

A skill is any top-level folder that has a SKILL.md. Each zip is written to
dist/<skill>.zip and holds exactly one top-level folder named after the skill,
with SKILL.md directly inside it, which is the layout the Claude apps expect
under Settings -> Capabilities -> Skills.

Only files tracked by git go in, so local venvs, caches, renders and voice
samples (all in .gitignore) never leak into a release. Outside a git checkout
it falls back to walking the folder and skipping common junk.

Usage:
    python tools/build_skill_zips.py            # all skills
    python tools/build_skill_zips.py own-voice-dub
    python tools/build_skill_zips.py --out build
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", "venv", ".venv", "hf-cache", "out", "work", "samples", "node_modules"}
SKIP_FILES = {".DS_Store", "Thumbs.db"}
SKIP_SUFFIXES = {".pyc", ".zip"}
# Fixed timestamp so rebuilding the same commit gives byte-identical zips.
EPOCH = (2020, 1, 1, 0, 0, 0)


def find_skills() -> list[str]:
    return sorted(p.parent.name for p in ROOT.glob("*/SKILL.md") if not p.parent.name.startswith("."))


def skill_files(skill: str) -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z", "--", skill],
            cwd=ROOT, check=True, capture_output=True,
        ).stdout.decode()
        files = [ROOT / f for f in out.split("\0") if f]
        if files:
            return sorted(f for f in files if f.is_file())
    except (OSError, subprocess.CalledProcessError):
        pass
    files = []
    for dirpath, dirnames, filenames in os.walk(ROOT / skill):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            p = Path(dirpath) / name
            if name not in SKIP_FILES and p.suffix not in SKIP_SUFFIXES:
                files.append(p)
    return sorted(files)


def build(skill: str, out_dir: Path) -> Path:
    files = skill_files(skill)
    if not any(f.relative_to(ROOT).as_posix() == f"{skill}/SKILL.md" for f in files):
        sys.exit(f"error: {skill}/SKILL.md is not tracked by git (git add it first)")
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"{skill}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            info = zipfile.ZipInfo(f.relative_to(ROOT).as_posix(), EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, f.read_bytes())
    print(f"{zip_path}: {len(files)} files, {zip_path.stat().st_size / 1024:.0f} KB")
    return zip_path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("skills", nargs="*", help="skill folders to zip (default: every folder with a SKILL.md)")
    ap.add_argument("--out", default="dist", help="output folder (default: dist)")
    args = ap.parse_args()

    available = find_skills()
    wanted = args.skills or available
    unknown = [s for s in wanted if s not in available]
    if unknown:
        sys.exit(f"error: not a skill folder: {', '.join(unknown)} (found: {', '.join(available)})")
    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    for skill in wanted:
        build(skill, out_dir)


if __name__ == "__main__":
    main()
