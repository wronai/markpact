"""Docker sandbox runner for Markpact"""

import subprocess
import sys
from pathlib import Path
from typing import Optional

DOCKERFILE_TEMPLATE = '''FROM python:3.12-slim

WORKDIR /app

# Install dependencies if requirements.txt exists
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Copy application code
COPY . .

# Default port
ENV MARKPACT_PORT=8000
EXPOSE ${MARKPACT_PORT}

# Run command will be provided at runtime
CMD ["python", "-m", "http.server", "8000"]
'''


def generate_dockerfile(sandbox_path: Path, deps: list[str], run_command: str) -> Path:
    """Generate a Dockerfile for the markpact project."""
    dockerfile_path = sandbox_path / "Dockerfile"
    
    # Create requirements.txt
    if deps:
        requirements_path = sandbox_path / "requirements.txt"
        requirements_path.write_text("\n".join(deps))
    
    # Determine CMD based on run_command
    if "uvicorn" in run_command:
        cmd = run_command.replace("${MARKPACT_PORT:-8000}", "${MARKPACT_PORT}")
        cmd_parts = cmd.split()
        cmd_json = str(cmd_parts).replace("'", '"')
    else:
        cmd_parts = run_command.strip().split()
        cmd_json = str(cmd_parts).replace("'", '"')
    
    dockerfile_content = f'''FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Copy application code
COPY . .

# Default port
ENV MARKPACT_PORT=8000
EXPOSE 8000

CMD {cmd_json}
'''
    
    dockerfile_path.write_text(dockerfile_content)
    return dockerfile_path


def build_and_run_docker(
    sandbox_path: Path,
    image_name: str = "markpact-app",
    port: int = 8000,
    verbose: bool = True,
) -> int:
    """Build and run Docker container from sandbox."""
    
    if verbose:
        print(f"[markpact] Building Docker image: {image_name}")
    
    # Build image
    build_result = subprocess.run(
        ["docker", "build", "-t", image_name, "."],
        cwd=sandbox_path,
        capture_output=not verbose,
    )
    
    if build_result.returncode != 0:
        print(f"[markpact] ERROR: Docker build failed", file=sys.stderr)
        if not verbose:
            print(build_result.stderr.decode(), file=sys.stderr)
        return build_result.returncode
    
    if verbose:
        print(f"[markpact] Running container on port {port}")
        print(f"[markpact] Access at: http://localhost:{port}")
        print(f"[markpact] Press Ctrl+C to stop")
    
    # Run container
    try:
        run_result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-p", f"{port}:{port}",
                "-e", f"MARKPACT_PORT={port}",
                "--name", f"{image_name}-container",
                image_name,
            ],
            cwd=sandbox_path,
        )
        return run_result.returncode
    except KeyboardInterrupt:
        print(f"\n[markpact] Stopping container...")
        subprocess.run(["docker", "stop", f"{image_name}-container"], capture_output=True)
        return 0


def check_docker_available() -> bool:
    """Check if Docker is available."""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False
