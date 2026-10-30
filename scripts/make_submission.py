"""Submission ZIP packaging and verification tool for MiniCalc ([D-12], [D-16]).

Builds a deterministic, clean ZIP archive containing only shipped project files
under a single top-level directory, and provides an end-to-end verification mode
that extracts the archive into a clean environment to validate tests, docstrings,
CLI execution, examples, and document hygiene.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Sequence

#: Maximum allowed size for the submission ZIP (5 MB).
MAX_ZIP_BYTES: int = 5 * 1024 * 1024

#: Fixed timestamp used for deterministic ZIP member metadata (2026-10-30 00:00:00).
FIXED_ZIP_DATETIME: tuple[int, int, int, int, int, int] = (2026, 10, 30, 0, 0, 0)

#: Standard UNIX file mode for archived files (0o100644).
FILE_EXTERNAL_ATTR: int = 0o100644 << 16

#: Excluded paths and keywords that must never appear in shipped markdown documents.
EXCLUDED_DOC_PATTERNS: list[str] = [
    r"docs/reports",
    r"docs/decisions",
    r"decisions/",
    r"docs/tasks",
    r"tasks/",
    r"docs/prompts",
    r"prompts/",
    r"docs/guide",
    r"guide/",
    r"patch/",
    r"\[D-\d+\]",
    r"scripts/(?!check_docs\.py\b)",
]


def collect_manifest(repo_root: Path) -> list[tuple[Path, str]]:
    """Gather all source files to include in the submission package.

    Args:
        repo_root: The root directory of the repository.

    Returns:
        A list of tuples pairing the absolute source path with its relative path
        inside the repository (using forward slashes).

    Raises:
        FileNotFoundError: If an expected required file is missing from disk.
    """
    manifest: list[tuple[Path, str]] = []

    # 1. Root files
    root_files = [
        "main.py",
        "README.md",
        "requirements-dev.txt",
        "pytest.ini",
    ]
    for rel in root_files:
        src = repo_root / rel
        if not src.is_file():
            raise FileNotFoundError(f"Required root file missing: {rel}")
        manifest.append((src, rel))

    # 2. Package source (minicalc/)
    pkg_dir = repo_root / "minicalc"
    if not pkg_dir.is_dir():
        raise FileNotFoundError(f"Required package directory missing: {pkg_dir}")
    for path in pkg_dir.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(repo_root).as_posix()
        manifest.append((path, rel))

    # 3. Tests (tests/) - excluding test_make_submission.py and caches
    tests_dir = repo_root / "tests"
    if not tests_dir.is_dir():
        raise FileNotFoundError(f"Required tests directory missing: {tests_dir}")
    for path in tests_dir.rglob("*"):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        if path.suffix == ".pyc" or path.name.startswith(".git"):
            continue
        if path.name == "test_make_submission.py":
            continue
        rel = path.relative_to(repo_root).as_posix()
        manifest.append((path, rel))

    # 4. Examples (examples/) - all .mc files
    examples_dir = repo_root / "examples"
    if not examples_dir.is_dir():
        raise FileNotFoundError(f"Required examples directory missing: {examples_dir}")
    for path in sorted(examples_dir.glob("*.mc")):
        if path.is_file():
            rel = path.relative_to(repo_root).as_posix()
            manifest.append((path, rel))

    # 5. Shipped documentation
    shipped_docs = [
        "docs/LANGUAGE.md",
        "docs/PRESENTATION.md",
        "docs/context/language-spec.md",
        "docs/context/interface-contract.md",
    ]
    for rel in shipped_docs:
        src = repo_root / rel
        if not src.is_file():
            raise FileNotFoundError(f"Required documentation file missing: {rel}")
        manifest.append((src, rel))

    # 6. Shipped scripts (check_docs.py only)
    check_docs_path = repo_root / "scripts" / "check_docs.py"
    if not check_docs_path.is_file():
        raise FileNotFoundError("Required script missing: scripts/check_docs.py")
    manifest.append((check_docs_path, "scripts/check_docs.py"))

    # Sort manifest deterministically by relative path
    manifest.sort(key=lambda item: item[1])
    return manifest


def validate_exclusions(rel_path: str) -> None:
    """Ensure that an archived file does not violate exclusion rules.

    Args:
        rel_path: Relative path of the candidate file within the repository.

    Raises:
        ValueError: If the file path matches any forbidden pattern.
    """
    normalized = rel_path.replace("\\", "/")
    parts = normalized.split("/")

    # Check forbidden filenames
    if parts[-1] == "test_make_submission.py":
        raise ValueError(f"Forbidden test in submission: {rel_path}")

    # Check forbidden directories
    forbidden_prefixes = (
        ".git/",
        "patch/",
        "docs/reports/",
        "docs/prompts/",
        "docs/tasks/",
        "docs/decisions/",
        "docs/guide/",
        "dist/",
        ".venv/",
    )
    for prefix in forbidden_prefixes:
        if normalized.startswith(prefix) or f"/{prefix}" in f"/{normalized}":
            raise ValueError(f"Forbidden directory in submission: {rel_path}")

    # Check script restrictions
    if normalized.startswith("scripts/") and normalized != "scripts/check_docs.py":
        raise ValueError(f"Forbidden script in submission: {rel_path}")

    # Check cache / temporary extensions
    if "__pycache__" in parts or ".pytest_cache" in parts or normalized.endswith(".pyc"):
        raise ValueError(f"Cache file in submission: {rel_path}")


def build_submission(
    repo_root: Path,
    out_zip: Path,
    top_folder: str = "MiniCalc-CMPSC132-FinalProject",
) -> Path:
    """Build a deterministic submission ZIP archive.

    Args:
        repo_root: Path to the repository root directory.
        out_zip: Target output ZIP path.
        top_folder: Single top-level directory name inside the ZIP.

    Returns:
        The Path to the created ZIP file.

    Raises:
        FileNotFoundError: If any required component is missing.
        ValueError: If an excluded component is encountered.
        RuntimeError: If the resulting ZIP exceeds 5 MB.
    """
    manifest = collect_manifest(repo_root)

    # Validate every item against exclusion rules
    for _, rel in manifest:
        validate_exclusions(rel)

    out_zip.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(out_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for src_path, rel_path in manifest:
            arcname = f"{top_folder}/{rel_path}".replace("\\", "/")
            data = src_path.read_bytes()

            zinfo = zipfile.ZipInfo(arcname, date_time=FIXED_ZIP_DATETIME)
            zinfo.compress_type = zipfile.ZIP_DEFLATED
            zinfo.external_attr = FILE_EXTERNAL_ATTR
            zinfo.create_system = 3  # UNIX
            zf.writestr(zinfo, data)

    size = out_zip.stat().st_size
    if size > MAX_ZIP_BYTES:
        out_zip.unlink(missing_ok=True)
        raise RuntimeError(f"Submission ZIP exceeds 5 MB limit ({size} bytes)")

    return out_zip


def verify_submission(zip_path: Path) -> bool:
    """Extract and verify the submission archive in a clean temporary directory.

    Args:
        zip_path: Path to the submission ZIP to verify.

    Returns:
        True if all verification steps pass, False otherwise.
    """
    print(f"Verifying submission archive: {zip_path.name}")
    if not zip_path.is_file():
        print(f"[FAIL] Submission archive not found: {zip_path}")
        return False

    with tempfile.TemporaryDirectory(prefix="minicalc_verify_") as tmpdir:
        extract_dir = Path(tmpdir)
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)
        except Exception as exc:
            print(f"[FAIL] Failed to extract archive: {exc}")
            return False

        # Locate root directory inside archive
        top_entries = list(extract_dir.iterdir())
        if len(top_entries) != 1 or not top_entries[0].is_dir():
            print(f"[FAIL] Expected single top-level directory, found: {top_entries}")
            return False
        root = top_entries[0]

        env = os.environ.copy()
        env["NO_COLOR"] = "1"

        # Step 1: Check pytest availability and run test suite
        try:
            import pytest  # noqa: F401
        except ImportError:
            print("[FAIL] pytest is missing from the environment. Please install dev dependencies.")
            return False

        p = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=str(root),
            capture_output=True,
            text=True,
            env=env,
        )
        if p.returncode != 0:
            print(f"[FAIL] pytest -q failed (exit {p.returncode}):\n{p.stdout}\n{p.stderr}")
            return False
        print("[PASS] pytest -q passed")

        # Step 2: Run documentation checker
        p = subprocess.run(
            [sys.executable, "scripts/check_docs.py"],
            cwd=str(root),
            capture_output=True,
            text=True,
            env=env,
        )
        if p.returncode != 0:
            print(f"[FAIL] scripts/check_docs.py failed (exit {p.returncode}):\n{p.stdout}\n{p.stderr}")
            return False
        print("[PASS] python scripts/check_docs.py passed")

        # Step 3: Run one-shot expression evaluation
        p = subprocess.run(
            [sys.executable, "-m", "minicalc", "-e", "2+3*4"],
            cwd=str(root),
            capture_output=True,
            text=True,
            env=env,
        )
        if p.returncode != 0 or p.stdout.strip() != "= 14":
            print(f"[FAIL] minicalc -e '2+3*4' failed (exit {p.returncode}, output={p.stdout.strip()!r})")
            return False
        print("[PASS] minicalc -e '2+3*4' returned expected '= 14'")

        # Step 4: Run examples/01_basics.mc (expects exit 0)
        p = subprocess.run(
            [sys.executable, "-m", "minicalc", "examples/01_basics.mc"],
            cwd=str(root),
            capture_output=True,
            text=True,
            env=env,
        )
        if p.returncode != 0:
            print(f"[FAIL] examples/01_basics.mc failed with exit code {p.returncode}")
            return False
        print("[PASS] minicalc examples/01_basics.mc exited with 0")

        # Step 5: Run examples/05_errors.mc (expects exit 1)
        p = subprocess.run(
            [sys.executable, "-m", "minicalc", "examples/05_errors.mc"],
            cwd=str(root),
            capture_output=True,
            text=True,
            env=env,
        )
        if p.returncode != 1:
            print(f"[FAIL] examples/05_errors.mc expected exit code 1, got {p.returncode}")
            return False
        print("[PASS] minicalc examples/05_errors.mc exited with 1")

        # Step 6: Scan shipped user documentation for excluded paths (Fix 2)
        user_docs = [
            root / "README.md",
            root / "docs/LANGUAGE.md",
            root / "docs/PRESENTATION.md",
        ]
        scan_errors: list[str] = []
        for md_path in user_docs:
            if not md_path.is_file():
                continue
            text = md_path.read_text(encoding="utf-8")
            for pattern in EXCLUDED_DOC_PATTERNS:
                matches = list(re.finditer(pattern, text))
                for match in matches:
                    rel_md = md_path.relative_to(root).as_posix()
                    scan_errors.append(f"{rel_md}: matched excluded pattern {pattern!r} ({match.group(0)!r})")

        if scan_errors:
            print(f"[FAIL] Excluded path references detected in shipped markdown files:\n" + "\n".join(scan_errors))
            return False
        print("[PASS] Shipped markdown files contain no excluded path references")

    print("\nAll verification steps PASSED successfully.")
    return True


def list_archive(zip_path: Path) -> None:
    """Print the contents of a ZIP archive to standard output.

    Args:
        zip_path: Path to the ZIP file to inspect.
    """
    if not zip_path.is_file():
        print(f"Archive not found: {zip_path}")
        return
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            print(f"{info.file_size:8d}  {info.filename}")


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point for building and verifying the submission package.

    Args:
        argv: Optional sequence of command-line arguments.

    Returns:
        0 on success, non-zero on failure.
    """
    parser = argparse.ArgumentParser(
        prog="make_submission",
        description="Build and verify the MiniCalc final project submission ZIP.",
    )
    parser.add_argument(
        "--name",
        default="MiniCalc-CMPSC132-FinalProject",
        help="top-level directory name inside the ZIP (default: %(default)s)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="output ZIP path (default: dist/<name>.zip)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="extract and verify the archive in a clean temporary directory",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list files contained in the output ZIP archive",
    )

    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent
    name = args.name
    out_zip = Path(args.out) if args.out else repo_root / "dist" / f"{name}.zip"

    try:
        # Build the archive if it does not exist or if not merely listing
        if not args.list or not out_zip.is_file():
            build_submission(repo_root=repo_root, out_zip=out_zip, top_folder=name)
            sha256 = hashlib.sha256(out_zip.read_bytes()).hexdigest()
            print(f"Created submission archive: {out_zip} ({out_zip.stat().st_size} bytes)")
            print(f"SHA-256: {sha256}")

        if args.list:
            list_archive(out_zip)

        if args.verify:
            if not verify_submission(out_zip):
                return 1

        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
