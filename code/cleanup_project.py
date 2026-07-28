from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove generated development files from GalleryOS.")
    parser.add_argument("--apply", action="store_true", help="Actually remove files. Without this flag, only show what would be removed.")
    args = parser.parse_args()

    targets = sorted(ROOT.rglob("__pycache__"))
    targets.extend(sorted(ROOT.rglob("*.pyc")))
    targets.extend(sorted(ROOT.glob("GalleryOS-Sprint-*.zip")))

    unique: list[Path] = []
    seen: set[Path] = set()
    for target in targets:
        if target not in seen and target.exists():
            seen.add(target)
            unique.append(target)

    if not unique:
        print("Nothing to clean.")
        return 0

    verb = "Removing" if args.apply else "Would remove"
    for target in unique:
        print(f"{verb}: {target.relative_to(ROOT)}")
        if args.apply:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()

    if not args.apply:
        print("\nDry run only. Run with --apply to remove these files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
