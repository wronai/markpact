"""Command execution"""

import os
import subprocess
import sys
from pathlib import Path

from .sandbox import Sandbox


def run_cmd(cmd: str, sandbox: Sandbox, verbose: bool = True) -> int:
    """Run command in sandbox with venv-aware PATH"""
    if verbose:
        print(f"[markpact] RUN: {cmd}")

    env = os.environ.copy()
    if sandbox.venv_bin.exists():
        env["VIRTUAL_ENV"] = str(sandbox.venv_bin.parent)
        env["PATH"] = f"{sandbox.venv_bin}:{env.get('PATH', '')}"

    return subprocess.check_call(cmd, shell=True, cwd=sandbox.path, env=env)


def ensure_venv(sandbox: Sandbox, verbose: bool = True) -> None:
    """Create venv in sandbox if not exists and not disabled"""
    if os.environ.get("MARKPACT_NO_VENV") == "1":
        return
    if sandbox.has_venv():
        return
    run_cmd(f"{sys.executable} -m venv .venv", sandbox, verbose)


def install_deps(deps: list[str], sandbox: Sandbox, verbose: bool = True) -> None:
    """Install Python dependencies in sandbox"""
    if not deps:
        return

    ensure_venv(sandbox, verbose)
    sandbox.write_requirements(deps)

    pip = ".venv/bin/pip" if sandbox.venv_pip.exists() else "pip"
    run_cmd(f"{pip} install -r requirements.txt", sandbox, verbose)
