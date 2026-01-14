"""Multi-registry publisher for markpact projects"""

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .sandbox import Sandbox


@dataclass
class PublishConfig:
    """Configuration for publishing"""
    registry: str  # pypi, npm, docker, github
    name: str
    version: str
    description: str = ""
    author: str = ""
    license: str = "MIT"
    repository: str = ""
    keywords: list[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


@dataclass
class PublishResult:
    """Result of a publish operation"""
    success: bool
    registry: str
    message: str
    version: str = ""
    url: str = ""


def bump_version(version: str, bump_type: str = "patch") -> str:
    """Bump semantic version.
    
    Args:
        version: Current version (e.g., "1.2.3")
        bump_type: Type of bump ("major", "minor", "patch")
        
    Returns:
        New version string
    """
    # Remove 'v' prefix if present
    v = version.lstrip("v")
    
    parts = v.split(".")
    if len(parts) != 3:
        parts = ["0", "0", "0"]
    
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2].split("-")[0])
    
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


def extract_version_from_readme(readme_path: Path) -> Optional[str]:
    """Extract version from README markpact:publish block."""
    content = readme_path.read_text()
    
    # Look for version in publish block
    match = re.search(r'```markpact:publish[^\n]*\n(.*?)```', content, re.DOTALL)
    if match:
        block = match.group(1)
        version_match = re.search(r'version\s*[=:]\s*["\']?([^"\'\n]+)', block)
        if version_match:
            return version_match.group(1).strip()
    
    # Look for version in pyproject.toml style
    version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
    if version_match:
        return version_match.group(1)
    
    return "0.1.0"


def update_version_in_readme(readme_path: Path, new_version: str) -> bool:
    """Update version in README file."""
    content = readme_path.read_text()
    
    # Update version in publish block
    new_content = re.sub(
        r'(version\s*[=:]\s*["\']?)[\d\.]+(["\']?)',
        f'\\g<1>{new_version}\\g<2>',
        content
    )
    
    if new_content != content:
        readme_path.write_text(new_content)
        return True
    
    return False


# ============================================================================
# PyPI Publisher
# ============================================================================

def generate_pyproject_toml(config: PublishConfig, sandbox: Sandbox) -> Path:
    """Generate pyproject.toml for PyPI publishing."""
    content = f'''[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{config.name}"
version = "{config.version}"
description = "{config.description}"
readme = "README.md"
license = "{config.license}"
authors = [{{ name = "{config.author}" }}]
keywords = {json.dumps(config.keywords)}
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]
requires-python = ">=3.10"

[project.urls]
Homepage = "{config.repository}"
'''
    
    path = sandbox.path / "pyproject.toml"
    path.write_text(content)
    return path


def publish_pypi(
    config: PublishConfig,
    sandbox: Sandbox,
    test: bool = False,
    verbose: bool = True,
) -> PublishResult:
    """Publish package to PyPI."""
    
    if verbose:
        print(f"[markpact] Publishing {config.name} v{config.version} to {'TestPyPI' if test else 'PyPI'}...")
    
    # Generate pyproject.toml if not exists
    pyproject = sandbox.path / "pyproject.toml"
    if not pyproject.exists():
        generate_pyproject_toml(config, sandbox)
    
    # Create README.md in sandbox if not exists
    readme = sandbox.path / "README.md"
    if not readme.exists():
        readme.write_text(f"# {config.name}\n\n{config.description}\n")
    
    # Build package
    if verbose:
        print("[markpact] Building package...")
    
    build_result = subprocess.run(
        [sys.executable, "-m", "build"],
        cwd=sandbox.path,
        capture_output=True,
        text=True,
    )
    
    if build_result.returncode != 0:
        return PublishResult(
            success=False,
            registry="pypi",
            message=f"Build failed: {build_result.stderr[:200]}",
            version=config.version,
        )
    
    # Upload to PyPI
    if verbose:
        print("[markpact] Uploading to PyPI...")
    
    upload_cmd = [sys.executable, "-m", "twine", "upload"]
    if test:
        upload_cmd.extend(["--repository", "testpypi"])
    upload_cmd.append("dist/*")
    
    upload_result = subprocess.run(
        " ".join(upload_cmd),
        shell=True,
        cwd=sandbox.path,
        capture_output=True,
        text=True,
    )
    
    if upload_result.returncode != 0:
        return PublishResult(
            success=False,
            registry="pypi",
            message=f"Upload failed: {upload_result.stderr[:200]}",
            version=config.version,
        )
    
    url = f"https://{'test.' if test else ''}pypi.org/project/{config.name}/"
    return PublishResult(
        success=True,
        registry="pypi",
        message=f"Published to {'TestPyPI' if test else 'PyPI'}",
        version=config.version,
        url=url,
    )


# ============================================================================
# npm Publisher
# ============================================================================

def generate_package_json(config: PublishConfig, sandbox: Sandbox) -> Path:
    """Generate package.json for npm publishing."""
    package = {
        "name": config.name,
        "version": config.version,
        "description": config.description,
        "main": "index.js",
        "scripts": {
            "test": "echo \"No tests specified\" && exit 0"
        },
        "keywords": config.keywords,
        "author": config.author,
        "license": config.license,
        "repository": {
            "type": "git",
            "url": config.repository
        } if config.repository else {}
    }
    
    path = sandbox.path / "package.json"
    path.write_text(json.dumps(package, indent=2))
    return path


def publish_npm(
    config: PublishConfig,
    sandbox: Sandbox,
    registry: str = "https://registry.npmjs.org",
    verbose: bool = True,
) -> PublishResult:
    """Publish package to npm registry."""
    
    if verbose:
        print(f"[markpact] Publishing {config.name} v{config.version} to npm...")
    
    # Generate package.json if not exists
    package_json = sandbox.path / "package.json"
    if not package_json.exists():
        generate_package_json(config, sandbox)
    
    # Create index.js if not exists
    index_js = sandbox.path / "index.js"
    if not index_js.exists():
        index_js.write_text(f'module.exports = {{ name: "{config.name}", version: "{config.version}" }};\n')
    
    # Publish
    cmd = ["npm", "publish", "--access", "public"]
    if registry != "https://registry.npmjs.org":
        cmd.extend(["--registry", registry])
    
    result = subprocess.run(
        cmd,
        cwd=sandbox.path,
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        return PublishResult(
            success=False,
            registry="npm",
            message=f"Publish failed: {result.stderr[:200]}",
            version=config.version,
        )
    
    return PublishResult(
        success=True,
        registry="npm",
        message="Published to npm",
        version=config.version,
        url=f"https://www.npmjs.com/package/{config.name}",
    )


# ============================================================================
# Docker Publisher
# ============================================================================

def generate_dockerfile(config: PublishConfig, sandbox: Sandbox, base_image: str = "python:3.12-slim") -> Path:
    """Generate Dockerfile for Docker publishing."""
    content = f'''FROM {base_image}

LABEL maintainer="{config.author}"
LABEL version="{config.version}"
LABEL description="{config.description}"

WORKDIR /app

COPY . .

RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

CMD ["python", "-m", "http.server", "8000"]
'''
    
    path = sandbox.path / "Dockerfile"
    path.write_text(content)
    return path


def publish_docker(
    config: PublishConfig,
    sandbox: Sandbox,
    registry: str = "docker.io",
    tag: Optional[str] = None,
    verbose: bool = True,
) -> PublishResult:
    """Build and push Docker image to registry."""
    
    image_name = f"{registry}/{config.name}" if registry != "docker.io" else config.name
    image_tag = tag or config.version
    full_image = f"{image_name}:{image_tag}"
    
    if verbose:
        print(f"[markpact] Building Docker image: {full_image}...")
    
    # Generate Dockerfile if not exists
    dockerfile = sandbox.path / "Dockerfile"
    if not dockerfile.exists():
        generate_dockerfile(config, sandbox)
    
    # Build image
    build_result = subprocess.run(
        ["docker", "build", "-t", full_image, "-t", f"{image_name}:latest", "."],
        cwd=sandbox.path,
        capture_output=True,
        text=True,
    )
    
    if build_result.returncode != 0:
        return PublishResult(
            success=False,
            registry="docker",
            message=f"Build failed: {build_result.stderr[:200]}",
            version=config.version,
        )
    
    if verbose:
        print(f"[markpact] Pushing to {registry}...")
    
    # Push image
    push_result = subprocess.run(
        ["docker", "push", full_image],
        cwd=sandbox.path,
        capture_output=True,
        text=True,
    )
    
    if push_result.returncode != 0:
        return PublishResult(
            success=False,
            registry="docker",
            message=f"Push failed: {push_result.stderr[:200]}",
            version=config.version,
        )
    
    # Also push latest
    subprocess.run(
        ["docker", "push", f"{image_name}:latest"],
        cwd=sandbox.path,
        capture_output=True,
    )
    
    return PublishResult(
        success=True,
        registry="docker",
        message=f"Pushed to {registry}",
        version=config.version,
        url=f"https://hub.docker.com/r/{config.name}" if registry == "docker.io" else f"{registry}/{config.name}",
    )


# ============================================================================
# GitHub Packages Publisher
# ============================================================================

def publish_github_packages(
    config: PublishConfig,
    sandbox: Sandbox,
    package_type: str = "npm",  # npm, docker, maven, nuget
    verbose: bool = True,
) -> PublishResult:
    """Publish to GitHub Packages."""
    
    if package_type == "npm":
        return publish_npm(
            config, sandbox,
            registry="https://npm.pkg.github.com",
            verbose=verbose,
        )
    elif package_type == "docker":
        return publish_docker(
            config, sandbox,
            registry="ghcr.io",
            verbose=verbose,
        )
    else:
        return PublishResult(
            success=False,
            registry="github",
            message=f"Unsupported package type: {package_type}",
            version=config.version,
        )


# ============================================================================
# Main publish function
# ============================================================================

def parse_publish_block(block_body: str) -> PublishConfig:
    """Parse publish block content into config."""
    config = {
        "registry": "pypi",
        "name": "my-package",
        "version": "0.1.0",
        "description": "",
        "author": "",
        "license": "MIT",
        "repository": "",
        "keywords": [],
    }
    
    for line in block_body.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        
        if "=" in line:
            key, _, value = line.partition("=")
        elif ":" in line:
            key, _, value = line.partition(":")
        else:
            continue
        
        key = key.strip().lower()
        value = value.strip().strip('"\'')
        
        if key in config:
            if key == "keywords":
                config[key] = [k.strip() for k in value.split(",")]
            else:
                config[key] = value
    
    return PublishConfig(**config)


def publish(
    config: PublishConfig,
    sandbox: Sandbox,
    bump: Optional[str] = None,
    verbose: bool = True,
) -> PublishResult:
    """Publish to specified registry.
    
    Args:
        config: Publish configuration
        sandbox: Sandbox with files to publish
        bump: Version bump type ("major", "minor", "patch") or None
        verbose: Print progress
        
    Returns:
        PublishResult
    """
    # Bump version if requested
    if bump:
        config.version = bump_version(config.version, bump)
        if verbose:
            print(f"[markpact] Bumped version to {config.version}")
    
    # Dispatch to appropriate publisher
    if config.registry == "pypi":
        return publish_pypi(config, sandbox, verbose=verbose)
    elif config.registry == "pypi-test":
        return publish_pypi(config, sandbox, test=True, verbose=verbose)
    elif config.registry == "npm":
        return publish_npm(config, sandbox, verbose=verbose)
    elif config.registry == "docker":
        return publish_docker(config, sandbox, verbose=verbose)
    elif config.registry == "github":
        return publish_github_packages(config, sandbox, verbose=verbose)
    elif config.registry == "ghcr":
        return publish_docker(config, sandbox, registry="ghcr.io", verbose=verbose)
    else:
        return PublishResult(
            success=False,
            registry=config.registry,
            message=f"Unknown registry: {config.registry}",
            version=config.version,
        )
