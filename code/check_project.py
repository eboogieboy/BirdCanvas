from __future__ import annotations

import argparse
import json
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_FILES = [
    "VERSION",
    "README.md",
    "CHANGELOG.md",
    "ROADMAP.md",
    "requirements.txt",
    "code/server.py",
    "code/gallery_library.py",
    "code/display_controller.py",
    "code/display_settings.py",
    "code/display.py",
    "output/index.html",
    "output/control/index.html",
    "output/gallery/index.html",
]
JSON_FILES = [
    "data/galleryos_state.json",
    "data/display_settings.json",
    "data/last_good_artwork.json",
    "output/current/manifest.json",
    "output/gallery/library.json",
]


def ok(message: str) -> None:
    print(f"✓ {message}")


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)
    print(f"✗ {message}")


def check_required_files(failures: list[str]) -> None:
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        if path.is_file():
            ok(f"Found {relative}")
        else:
            fail(f"Missing required file: {relative}", failures)


def check_json(failures: list[str]) -> None:
    for relative in JSON_FILES:
        path = ROOT / relative
        if not path.exists():
            print(f"• Optional JSON not present: {relative}")
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
            ok(f"Valid JSON: {relative}")
        except (OSError, json.JSONDecodeError) as error:
            fail(f"Invalid JSON in {relative}: {error}", failures)


def check_manifests(failures: list[str]) -> None:
    archive = ROOT / "output/archive"
    if not archive.exists():
        print("• No archive directory yet")
        return
    count = 0
    for manifest_path in archive.glob("*/manifest.json"):
        count += 1
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            fail(f"Damaged manifest {manifest_path.relative_to(ROOT)}: {error}", failures)
            continue
        image_name = str(manifest.get("image", "")).strip()
        if not image_name:
            fail(f"Manifest has no image: {manifest_path.relative_to(ROOT)}", failures)
        elif not (manifest_path.parent / image_name).is_file():
            fail(
                f"Manifest image missing: {(manifest_path.parent / image_name).relative_to(ROOT)}",
                failures,
            )
    ok(f"Checked {count} archive manifest(s)")


def check_python(failures: list[str]) -> None:
    python_files = sorted((ROOT / "code").glob("*.py"))
    compile_failed = False
    for path in python_files:
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as error:
            compile_failed = True
            fail(f"Python compile failed for {path.relative_to(ROOT)}: {error.msg}", failures)
    if not compile_failed:
        ok(f"Compiled {len(python_files)} Python file(s)")


def run_tests(failures: list[str]) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT,
        check=False,
    )
    if result.returncode == 0:
        ok("Automated test suite passed")
    else:
        fail("Automated test suite failed", failures)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the GalleryOS project.")
    parser.add_argument("--skip-tests", action="store_true", help="Skip the unittest suite.")
    args = parser.parse_args()

    failures: list[str] = []
    print("GalleryOS project check\n")
    check_required_files(failures)
    check_json(failures)
    check_manifests(failures)
    check_python(failures)
    if not args.skip_tests:
        run_tests(failures)

    print()
    if failures:
        print(f"Project check failed with {len(failures)} issue(s).")
        return 1
    print("Project check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
