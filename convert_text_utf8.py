# -*- coding: utf-8 -*-
"""
Cultures Saga — Convert All .ini/.txt Files in Localization\text to UTF-8
==========================================================================
Recursively scans Localization/text/ for all .ini and .txt files,
detects their encoding, and converts non-UTF-8 files to UTF-8 (without BOM).
Skips _backup_* directories to avoid modifying archived originals.

Usage:
  python convert_text_utf8.py           # Convert all files
  python convert_text_utf8.py --dry-run # Preview only, no changes
  python convert_text_utf8.py --all     # Include _backup_* directories too
"""
import argparse
import sys
import time
from pathlib import Path

# ============================================================
# Path Configuration
# ============================================================

# Project root (parent of this script)
PROJ_ROOT = Path(__file__).resolve().parent

# Text directory to scan
TEXT_DIR = PROJ_ROOT / "Localization" / "text"

# Skip these directories (lowercase comparison)
SKIP_DIRS = {"_backup_l10_20260812", "_backup_l10_align_20260812"}

# Known encodings to try, in order of preference
# CP1252 = Western European (German), GBK = Chinese (simplified)
ENCODINGS_TO_TRY = ["utf-8-sig", "utf-8", "gbk", "cp1252", "latin-1"]


def detect_encoding(data: bytes) -> str | None:
    """Detect the encoding of a byte buffer.

    Returns the first matching encoding, or None if all attempts fail
    (latin-1 always succeeds, so this should never happen).
    """
    for enc in ENCODINGS_TO_TRY:
        try:
            data.decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return None


def is_utf8(enc: str) -> bool:
    """Return True if the encoding is already UTF-8 based."""
    return enc in ("utf-8", "utf-8-sig")


def convert_file(path: Path, dry_run: bool = False) -> tuple[bool, str]:
    """Convert a single file to UTF-8 if needed.

    Returns (changed, message) where 'changed' is True if the file
    was actually converted (or would be in dry-run mode).
    """
    raw = path.read_bytes()

    enc = detect_encoding(raw)
    if enc is None:
        return False, f"SKIP: cannot detect encoding"

    if is_utf8(enc):
        return False, f"SKIP: already UTF-8 ({enc})"

    # Decode in detected encoding, write as UTF-8
    text = raw.decode(enc)
    if dry_run:
        return True, f"WOULD CONVERT: {enc} → utf-8"

    path.write_bytes(text.encode("utf-8"))
    return True, f"CONVERTED: {enc} → utf-8"


def scan_and_convert(include_backups: bool = False, dry_run: bool = False) -> tuple[int, int, int]:
    """Scan TEXT_DIR and convert all .ini/.txt files.

    Returns (converted, skipped_utf8, skipped_other).
    """
    converted = 0
    skipped_utf8 = 0
    skipped_other = 0

    files = []
    for ext in ("*.ini", "*.txt"):
        files.extend(sorted(TEXT_DIR.rglob(ext)))

    if not files:
        print("  No .ini or .txt files found.")
        return 0, 0, 0

    for f in files:
        # Check if file is inside a skipped directory
        if not include_backups:
            rel = f.relative_to(TEXT_DIR)
            parts = rel.parts
            if any(p.lower() in SKIP_DIRS or p.startswith("_backup") for p in parts):
                continue

        changed, msg = convert_file(f, dry_run=dry_run)
        if changed:
            converted += 1
        elif msg.startswith("SKIP: already UTF-8"):
            skipped_utf8 += 1
        else:
            skipped_other += 1

        print(f"  {msg:45s} {f.relative_to(PROJ_ROOT)}")

    return converted, skipped_utf8, skipped_other


def main():
    ap = argparse.ArgumentParser(
        description="Convert all .ini/.txt files in Localization/text to UTF-8"
    )
    ap.add_argument("--dry-run", action="store_true",
                    help="Preview only, no changes written")
    ap.add_argument("--all", action="store_true",
                    help="Include _backup_* directories (skipped by default)")
    args = ap.parse_args()

    if not TEXT_DIR.exists():
        print(f"ERROR: {TEXT_DIR} not found")
        sys.exit(1)

    print(f"{'='*60}")
    print(f"  Cultures Saga — Convert Text to UTF-8")
    print(f"  Scan:  {TEXT_DIR}")
    if args.dry_run:
        print(f"  Mode:  DRY-RUN (no files will be modified)")
    if not args.all:
        print(f"  Note:  Skipping _backup_* directories (use --all to include)")
    print(f"{'='*60}")

    t0 = time.time()
    converted, skipped_utf8, skipped_other = scan_and_convert(
        include_backups=args.all,
        dry_run=args.dry_run,
    )
    elapsed = time.time() - t0

    if args.dry_run:
        action = "would convert"
    else:
        action = "converted"

    print(f"\n{'='*60}")
    print(f"  Done! {elapsed:.1f} seconds")
    print(f"  {action}: {converted}")
    print(f"  already UTF-8: {skipped_utf8}")
    print(f"  skipped (other): {skipped_other}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()