"""Unit tests for the submission ZIP packager (scripts/make_submission.py).

Verifies that the submission builder adheres to [D-12] and [D-16]:
- Includes all required runtime, test, example, and documentation files.
- Excludes internal governance artifacts (.git, patch, docs/reports, tasks, etc.).
- Excludes tests/test_make_submission.py so the shipped test suite has no broken dependencies.
- Enforces a single top-level directory with forward slashes.
- Produces deterministic, byte-identical archives across builds.
- Does not run --verify during tests to prevent recursive execution.
"""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

from scripts.make_submission import (
    MAX_ZIP_BYTES,
    build_submission,
    collect_manifest,
    validate_exclusions,
)


def test_collect_manifest_inclusions(tmp_path: Path) -> None:
    """Verify that collect_manifest includes all required project deliverables.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    repo_root = Path(__file__).resolve().parent.parent
    manifest = collect_manifest(repo_root)
    relative_paths = [rel for _, rel in manifest]

    # Required files and directories
    assert "README.md" in relative_paths
    assert "main.py" in relative_paths
    assert "requirements-dev.txt" in relative_paths
    assert "pytest.ini" in relative_paths
    assert "docs/LANGUAGE.md" in relative_paths
    assert "docs/PRESENTATION.md" in relative_paths
    assert "docs/context/language-spec.md" in relative_paths
    assert "docs/context/interface-contract.md" in relative_paths
    assert "scripts/check_docs.py" in relative_paths

    # Packages and examples
    assert any(p.startswith("minicalc/") for p in relative_paths)
    assert any(p.startswith("tests/") for p in relative_paths)
    assert any(p.startswith("examples/") for p in relative_paths)
    assert "examples/01_basics.mc" in relative_paths
    assert "examples/05_errors.mc" in relative_paths
    assert "examples/06_showcase.mc" in relative_paths


def test_manifest_exclusions() -> None:
    """Verify that governance, temporary, and build files are excluded from manifest."""
    repo_root = Path(__file__).resolve().parent.parent
    manifest = collect_manifest(repo_root)
    relative_paths = [rel for _, rel in manifest]

    # test_make_submission.py must NOT be included ([D-16])
    assert "tests/test_make_submission.py" not in relative_paths

    # Internal governance and tooling must NOT be included
    assert not any(p.startswith(".git") for p in relative_paths)
    assert not any(p.startswith("patch/") for p in relative_paths)
    assert not any(p.startswith("docs/reports/") for p in relative_paths)
    assert not any(p.startswith("docs/prompts/") for p in relative_paths)
    assert not any(p.startswith("docs/tasks/") for p in relative_paths)
    assert not any(p.startswith("docs/decisions/") for p in relative_paths)
    assert not any(p.startswith("docs/guide/") for p in relative_paths)
    assert not any(p.startswith("dist/") for p in relative_paths)

    # Only check_docs.py is allowed from scripts/
    script_files = [p for p in relative_paths if p.startswith("scripts/")]
    assert script_files == ["scripts/check_docs.py"]

    # No Python bytecode or caches
    assert not any("__pycache__" in p for p in relative_paths)
    assert not any(p.endswith(".pyc") for p in relative_paths)


def test_build_submission_structure(tmp_path: Path) -> None:
    """Verify ZIP internal layout, single root folder, and forward slashes.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    repo_root = Path(__file__).resolve().parent.parent
    zip_path = tmp_path / "test_out.zip"
    top_folder = "MiniCalc-CMPSC132-FinalProject"

    build_submission(repo_root=repo_root, out_zip=zip_path, top_folder=top_folder)
    assert zip_path.is_file()

    with zipfile.ZipFile(zip_path, "r") as zf:
        members = zf.namelist()
        assert len(members) > 0

        for member in members:
            # Single top-level folder
            assert member.startswith(f"{top_folder}/")
            # Strictly forward slashes
            assert "\\" not in member

        # Inclusions inside ZIP
        assert f"{top_folder}/README.md" in members
        assert f"{top_folder}/scripts/check_docs.py" in members
        assert f"{top_folder}/docs/LANGUAGE.md" in members

        # Exclusions inside ZIP
        assert f"{top_folder}/tests/test_make_submission.py" not in members
        assert not any("docs/reports" in m for m in members)
        assert not any(".git" in m for m in members)
        assert not any("patch/" in m for m in members)


def test_build_submission_determinism(tmp_path: Path) -> None:
    """Verify that two independent builds produce identical SHA-256 hashes.

    Args:
        tmp_path: Pytest temporary directory fixture.
    """
    repo_root = Path(__file__).resolve().parent.parent
    zip1 = tmp_path / "build1.zip"
    zip2 = tmp_path / "build2.zip"

    build_submission(repo_root=repo_root, out_zip=zip1)
    build_submission(repo_root=repo_root, out_zip=zip2)

    hash1 = hashlib.sha256(zip1.read_bytes()).hexdigest()
    hash2 = hashlib.sha256(zip2.read_bytes()).hexdigest()

    assert hash1 == hash2, "Builds must be byte-identical"
    assert zip1.stat().st_size == zip2.stat().st_size
    assert zip1.stat().st_size < MAX_ZIP_BYTES


def test_validate_exclusions_raises() -> None:
    """Verify that validate_exclusions raises ValueError on forbidden paths."""
    forbidden = [
        "tests/test_make_submission.py",
        ".git/config",
        "patch/something.patch",
        "docs/reports/report.md",
        "docs/prompts/prompt.md",
        "docs/tasks/status.md",
        "docs/decisions/decision-log.md",
        "docs/guide/checklist.md",
        "scripts/make_submission.py",
        "scripts/task-worktree.sh",
        "minicalc/__pycache__/lexer.cpython-310.pyc",
        "dist/archive.zip",
    ]
    for path in forbidden:
        try:
            validate_exclusions(path)
            assert False, f"Expected ValueError for {path}"
        except ValueError:
            pass
