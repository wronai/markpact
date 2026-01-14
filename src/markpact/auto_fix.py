"""Auto-fix runtime errors in markpact projects"""

import os
import re
import socket
import subprocess
from pathlib import Path
from typing import Optional

from .sandbox import Sandbox


def find_free_port(start_port: int = 8000, max_attempts: int = 100) -> int:
    """Find a free port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"Could not find free port in range {start_port}-{start_port + max_attempts}")


def detect_error_type(error_output: str) -> Optional[str]:
    """Detect the type of error from output."""
    if "address already in use" in error_output.lower():
        return "port_in_use"
    if "modulenotfounderror" in error_output.lower():
        return "missing_module"
    if "syntaxerror" in error_output.lower():
        return "syntax_error"
    if "importerror" in error_output.lower():
        return "import_error"
    return None


def fix_port_in_readme(readme_path: Path, new_port: int) -> bool:
    """Update the port in a README file."""
    content = readme_path.read_text()
    
    # Replace ${MARKPACT_PORT:-XXXX} with new port
    pattern = r'\$\{MARKPACT_PORT:-\d+\}'
    replacement = f'${{MARKPACT_PORT:-{new_port}}}'
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        readme_path.write_text(new_content)
        return True
    
    # Also try replacing --port XXXX directly
    pattern2 = r'--port\s+\d+'
    replacement2 = f'--port {new_port}'
    new_content = re.sub(pattern2, replacement2, content)
    
    if new_content != content:
        readme_path.write_text(new_content)
        return True
    
    return False


def run_with_auto_fix(
    cmd: str,
    sandbox: Sandbox,
    readme_path: Optional[Path] = None,
    verbose: bool = True,
    max_retries: int = 3,
) -> int:
    """Run command with automatic error detection and fixing.
    
    Args:
        cmd: Command to run
        sandbox: Sandbox instance
        readme_path: Path to README.md to update on fix
        verbose: Print verbose output
        max_retries: Maximum number of retry attempts
        
    Returns:
        Exit code (0 for success)
    """
    env = os.environ.copy()
    if sandbox.venv_bin.exists():
        env["VIRTUAL_ENV"] = str(sandbox.venv_bin.parent)
        env["PATH"] = f"{sandbox.venv_bin}:{env.get('PATH', '')}"
    
    current_cmd = cmd
    
    for attempt in range(max_retries + 1):
        if verbose:
            print(f"[markpact] RUN: {current_cmd}")
        
        try:
            # Run with output capture for error detection
            result = subprocess.run(
                current_cmd,
                shell=True,
                cwd=sandbox.path,
                env=env,
                capture_output=True,
                text=True,
            )
            
            # Print output
            if result.stdout:
                print(result.stdout, end='')
            if result.stderr:
                print(result.stderr, end='')
            
            if result.returncode == 0:
                return 0
            
            # Detect error type
            combined_output = result.stdout + result.stderr
            error_type = detect_error_type(combined_output)
            
            if error_type == "port_in_use" and attempt < max_retries:
                # Find a free port and retry
                new_port = find_free_port()
                print(f"\n[markpact] Port in use. Trying port {new_port}...")
                
                # Update README if provided
                if readme_path and readme_path.exists():
                    if fix_port_in_readme(readme_path, new_port):
                        print(f"[markpact] Updated README with new port: {new_port}")
                
                # Update command with new port
                current_cmd = re.sub(
                    r'\$\{MARKPACT_PORT:-\d+\}',
                    str(new_port),
                    cmd
                )
                # Also try direct port replacement
                current_cmd = re.sub(r'--port\s+\d+', f'--port {new_port}', current_cmd)
                
                # Set environment variable
                env["MARKPACT_PORT"] = str(new_port)
                
                continue
            
            # No auto-fix available
            return result.returncode
            
        except Exception as e:
            print(f"[markpact] ERROR: {e}")
            return 1
    
    return 1


def add_missing_dependency(readme_path: Path, module_name: str) -> bool:
    """Add a missing dependency to the README deps block."""
    content = readme_path.read_text()
    
    # Find deps block
    pattern = r'(```markpact:deps python\n)(.*?)(```)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        deps_content = match.group(2)
        if module_name not in deps_content:
            new_deps = deps_content.rstrip() + f"\n{module_name}\n"
            new_content = content[:match.start(2)] + new_deps + content[match.end(2):]
            readme_path.write_text(new_content)
            return True
    
    return False
