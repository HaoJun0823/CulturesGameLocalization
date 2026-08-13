# -*- coding: utf-8 -*-
"""
Cultures Saga — Build & Publish to GitHub Release
===================================================
Runs build_text.py, packages _build/ into a dated UTF-8 zip,
and publishes it to a GitHub Release using the gh CLI.

Usage:
  python publish_build.py                  # build + zip + publish (new release)
  python publish_build.py --no-build       # reuse existing _build/, only zip+publish
  python publish_build.py --tag v1.2       # custom release tag
  python publish_build.py --dry-run        # build + zip only, no release

Requirements:
  - gh CLI installed and authenticated (gh auth login)
  - Git repo with a GitHub remote configured
"""
import argparse
import datetime
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

PROJ_ROOT = Path(__file__).resolve().parent
BUILD_ROOT = PROJ_ROOT / "_build"
ZIP_DIR = PROJ_ROOT / "dist"


def run(cmd, check=True):
    """Run a shell command and return CompletedProcess."""
    print(f"  $ {cmd}")
    proc = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    if check and proc.returncode != 0:
        sys.exit(f"ERROR: command failed with exit code {proc.returncode}")
    return proc


def get_remote_url():
    """Get the origin remote URL."""
    proc = run("git remote get-url origin", check=False)
    url = proc.stdout.strip()
    if not url:
        print("WARNING: no 'origin' remote found — release upload will fail")
    return url


def make_zip(tag: str) -> Path:
    """Zip the _build directory into dist/<tag>.zip."""
    if not BUILD_ROOT.exists():
        sys.exit(f"ERROR: {BUILD_ROOT} does not exist. Run build_text.py first.")
    ZIP_DIR.mkdir(exist_ok=True)
    zip_path = ZIP_DIR / f"{tag}.zip"
    if zip_path.exists():
        zip_path.unlink()

    print(f"\n  Packaging {BUILD_ROOT} → {zip_path} ...")
    count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for f in sorted(BUILD_ROOT.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(BUILD_ROOT))
                count += 1
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"  Packed {count} files, {size_mb:.1f} MB")
    return zip_path


def publish(tag: str, zip_path: Path, notes: str):
    """Create a GitHub release and upload the zip."""
    remote = get_remote_url()
    if not remote:
        sys.exit("Cannot determine GitHub repo. Set 'origin' remote first.")

    print(f"\n  Publishing release '{tag}' ...")
    # Check if release exists
    proc = run(f'gh release view "{tag}" --json name', check=False)
    if proc.returncode == 0:
        print(f"  Release '{tag}' already exists — uploading asset only")
        run(f'gh release upload "{tag}" "{zip_path}" --clobber')
    else:
        notes_file = ZIP_DIR / f"{tag}_notes.md"
        notes_file.write_text(notes, encoding="utf-8")
        run(f'gh release create "{tag}" "{zip_path}" --title "{tag}" --notes-file "{notes_file}"')
    print(f"  ✅ Released: {remote.strip()}")

    # Show the release URL
    print(f"  Release URL: https://github.com/{remote.split('github.com/')[-1].strip('/').removesuffix('.git')}/releases/tag/{tag}")
    return "https://github.com"


def build_notes(tag: str, zip_path: Path) -> str:
    """Build release notes markdown."""
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""## Cultures Saga - Multi-language Build

- **Date:** {now}
- **Tag:** {tag}
- **Size:** {size_mb:.1f} MB

### Contents
- Data/maps/ - Main campaign maps with localized text (CHN/ger/eng/pol)
- DataX/UserCampaigns/ - User campaign maps
- Data/Text/ - Game system text (hypertext, encyclopedia)
- map_languages.csv - Per-map language summary

### Notes
- Built as UTF-8 (l10 Chinese localization)
- Map.dat files are original game data, not modified
"""


def main():
    ap = argparse.ArgumentParser(
        description="Build + package + publish _build to GitHub Release"
    )
    ap.add_argument("--no-build", action="store_true",
                    help="Skip build_text.py, use existing _build/")
    ap.add_argument("--tag", default=None,
                    help=f"Custom release tag (default: v<yyyyMMdd>-utf8)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Build + zip only, no GitHub release")
    args = ap.parse_args()

    tag = args.tag or f"v{datetime.datetime.now().strftime('%Y%m%d')}-utf8"

    print(f"{'='*60}")
    print(f"  Cultures Saga Build & Publish")
    print(f"  Tag: {tag}")
    print(f"  Mode: {'DRY-RUN (no release)' if args.dry_run else 'full'}")
    print(f"{'='*60}")

    # 1) Build
    if args.no_build:
        print(f"\n  Skipping build (reusing {BUILD_ROOT})")
    else:
        t0 = time.time()
        run(f'python "{PROJ_ROOT / "build_text.py"}"')
        print(f"  Build finished in {time.time() - t0:.0f}s")

    # 2) Zip
    zip_path = make_zip(tag)

    # 3) Publish
    if args.dry_run:
        print(f"\n  [DRY-RUN] Would publish '{tag}' with {zip_path}")
    else:
        publish(tag, zip_path, build_notes(tag, zip_path))

    print(f"\n  All done!")


if __name__ == "__main__":
    main()