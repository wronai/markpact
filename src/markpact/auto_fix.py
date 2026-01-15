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
        except KeyboardInterrupt:
            if verbose:
                print("\n[markpact] Stopped by user (Ctrl+C)")
            return 130  # Standard exit code for SIGINT
            
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


def extract_module_name(error_output: str) -> Optional[str]:
    """Extract missing module name from ModuleNotFoundError."""
    # Pattern: ModuleNotFoundError: No module named 'xyz'
    match = re.search(r"No module named ['\"]([^'\"]+)['\"]", error_output)
    if match:
        return match.group(1).split('.')[0]  # Get top-level module
    return None


def fix_with_llm(
    readme_path: Path,
    error_output: str,
    error_type: str,
    verbose: bool = True,
) -> bool:
    """Use LLM to fix errors in the README.
    
    Args:
        readme_path: Path to README.md
        error_output: Error output from failed run
        error_type: Type of error detected
        verbose: Print verbose output
        
    Returns:
        True if fix was applied, False otherwise
    """
    try:
        from .generator import generate_contract
        from .config import GeneratorConfig
    except ImportError:
        if verbose:
            print("[markpact] LLM support not available for auto-fix")
        return False
    
    content = readme_path.read_text()
    
    # Build fix prompt
    fix_prompt = f"""Fix the following error in this markpact README.

ERROR TYPE: {error_type}
ERROR OUTPUT:
{error_output[:2000]}

CURRENT README:
{content[:4000]}

Instructions:
1. Analyze the error and identify the root cause
2. Fix ONLY the problematic code block(s)
3. Return the COMPLETE fixed README with all markpact blocks
4. Do NOT add explanations, just return the fixed README content
"""
    
    try:
        config = GeneratorConfig()
        fixed_content = generate_contract(fix_prompt, config)
        
        if fixed_content and "markpact:" in fixed_content:
            readme_path.write_text(fixed_content)
            if verbose:
                print(f"[markpact] LLM applied fix for {error_type}")
            return True
    except Exception as e:
        if verbose:
            print(f"[markpact] LLM fix failed: {e}")
    
    return False


def run_with_auto_fix_llm(
    cmd: str,
    sandbox: Sandbox,
    readme_path: Optional[Path] = None,
    verbose: bool = True,
    max_retries: int = 3,
    use_llm: bool = False,
) -> int:
    """Run command with automatic error detection and fixing (with optional LLM).
    
    Args:
        cmd: Command to run
        sandbox: Sandbox instance
        readme_path: Path to README.md to update on fix
        verbose: Print verbose output
        max_retries: Maximum number of retry attempts
        use_llm: Use LLM for complex error fixes
        
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
            print(f"[markpact] RUN: {current_cmd}" + (f" (attempt {attempt + 1})" if attempt > 0 else ""))
        
        try:
            result = subprocess.run(
                current_cmd,
                shell=True,
                cwd=sandbox.path,
                env=env,
                capture_output=True,
                text=True,
            )
        except KeyboardInterrupt:
            if verbose:
                print("\n[markpact] Stopped by user (Ctrl+C)")
            return 130
            
        if result.stdout:
            print(result.stdout, end='')
        if result.stderr:
            print(result.stderr, end='')
        
        if result.returncode == 0:
            return 0
        
        if attempt >= max_retries:
            break
            
        combined_output = result.stdout + result.stderr
        error_type = detect_error_type(combined_output)
        
        if not error_type:
            if verbose:
                print(f"[markpact] Unknown error, cannot auto-fix")
            break
        
        fixed = False
        
        # Port in use - simple fix
        if error_type == "port_in_use":
            new_port = find_free_port()
            print(f"\n[markpact] Port in use. Trying port {new_port}...")
            
            if readme_path and readme_path.exists():
                if fix_port_in_readme(readme_path, new_port):
                    print(f"[markpact] Updated README with new port: {new_port}")
            
            current_cmd = re.sub(r'\$\{MARKPACT_PORT:-\d+\}', str(new_port), cmd)
            current_cmd = re.sub(r'--port\s+\d+', f'--port {new_port}', current_cmd)
            env["MARKPACT_PORT"] = str(new_port)
            fixed = True
        
        # Missing module - add dependency
        elif error_type == "missing_module":
            module_name = extract_module_name(combined_output)
            if module_name and readme_path and readme_path.exists():
                print(f"\n[markpact] Missing module: {module_name}")
                if add_missing_dependency(readme_path, module_name):
                    print(f"[markpact] Added {module_name} to dependencies")
                    # Re-install dependencies
                    from .runner import install_deps
                    install_deps([module_name], sandbox, verbose)
                    fixed = True
        
        # LLM fix for other errors
        elif use_llm and readme_path and readme_path.exists():
            print(f"\n[markpact] Attempting LLM fix for {error_type}...")
            if fix_with_llm(readme_path, combined_output, error_type, verbose):
                # Re-parse and re-run
                fixed = True
        
        if not fixed:
            if verbose:
                print(f"[markpact] Could not auto-fix {error_type}")
            break
    
    return result.returncode if 'result' in dir() else 1
