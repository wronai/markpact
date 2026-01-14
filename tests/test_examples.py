"""Smoke tests for examples/*

We intentionally run examples in --dry-run mode to validate:
- README parsing
- markpact block formatting
- writing targets / sandbox paths

We do NOT execute external toolchains (npm/go/docker) in CI.
"""

from __future__ import annotations

from pathlib import Path

from markpact.cli import main


def test_examples_dry_run(tmp_path: Path):
    examples_dir = Path(__file__).resolve().parent.parent / "examples"
    readmes = sorted(p for p in examples_dir.glob("*/README.md") if p.is_file())
    assert readmes, "No examples found"

    for readme in readmes:
        # Use isolated sandbox per example
        sandbox = tmp_path / f"sandbox-{readme.parent.name}"
        rc = main([str(readme), "--dry-run", "-s", str(sandbox)])
        assert rc == 0, f"Dry-run failed for {readme}"
