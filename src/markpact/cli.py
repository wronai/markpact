#!/usr/bin/env python3
"""Markpact CLI"""

import argparse
import sys
from pathlib import Path

from . import __version__
from .converter import convert_markdown_to_markpact, print_conversion_report
from .parser import parse_blocks
from .runner import install_deps, run_cmd
from .sandbox import Sandbox


def handle_config(args) -> int:
    """Handle config subcommand"""
    from .config import (
        load_env, save_env, init_env, set_model, set_api_key, set_api_base,
        apply_preset, show_config, list_providers, get_env_path, PROVIDER_PRESETS
    )
    
    # Init config if requested
    if args.init:
        path, created = init_env(force=args.force)
        if created:
            print(f"[markpact] Created config file: {path}")
        else:
            print(f"[markpact] Config file already exists: {path}")
            print(f"[markpact] Use --force to overwrite")
        return 0
    
    # List providers
    if args.list_providers:
        print(list_providers())
        return 0
    
    # Apply preset
    if args.provider:
        if args.provider not in PROVIDER_PRESETS:
            print(f"[markpact] ERROR: Unknown provider '{args.provider}'", file=sys.stderr)
            print(f"[markpact] Available: {', '.join(PROVIDER_PRESETS.keys())}", file=sys.stderr)
            return 1
        
        config = apply_preset(args.provider, args.set_api_key)
        print(f"[markpact] Applied preset: {args.provider}")
        if args.provider != "ollama" and not args.set_api_key:
            print(f"[markpact] NOTE: Don't forget to set API key with: markpact config --api-key YOUR_KEY")
        return 0
    
    # Set individual values
    if args.set_model:
        set_model(args.set_model)
        print(f"[markpact] Model set to: {args.set_model}")
        return 0
    
    if args.set_api_key:
        set_api_key(args.set_api_key)
        print(f"[markpact] API key updated")
        return 0
    
    if args.set_api_base:
        set_api_base(args.set_api_base)
        print(f"[markpact] API base set to: {args.set_api_base}")
        return 0
    
    # Show config (default)
    env_path = get_env_path()
    if not env_path.exists():
        print(f"[markpact] No config file found at: {env_path}")
        print(f"[markpact] Run 'markpact config --init' to create one")
        print()
    
    print(show_config())
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="markpact",
        description="Executable Markdown Runtime – run projects from README.md",
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Config subcommand
    config_parser = subparsers.add_parser("config", help="Manage LLM configuration")
    config_parser.add_argument("--init", action="store_true", help="Initialize .env config file")
    config_parser.add_argument("--force", action="store_true", help="Overwrite existing config")
    config_parser.add_argument("--provider", metavar="NAME", help="Apply provider preset (ollama, openrouter, openai, anthropic, groq)")
    config_parser.add_argument("--list-providers", action="store_true", help="List available provider presets")
    config_parser.add_argument("--model", dest="set_model", metavar="MODEL", help="Set LLM model")
    config_parser.add_argument("--api-key", dest="set_api_key", metavar="KEY", help="Set API key")
    config_parser.add_argument("--api-base", dest="set_api_base", metavar="URL", help="Set API base URL")
    
    # Main parser arguments
    parser.add_argument("readme", nargs="?", default="README.md", help="Path to README.md")
    parser.add_argument("--sandbox", "-s", help="Sandbox directory (default: ./sandbox)")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Show what would be done")
    parser.add_argument("--convert", "-c", action="store_true", 
                        help="Convert regular Markdown to markpact format on-the-fly")
    parser.add_argument("--convert-only", action="store_true",
                        help="Only convert and print result, don't execute")
    parser.add_argument("--save-converted", metavar="FILE",
                        help="Save converted markpact to file")
    parser.add_argument("--auto", "-a", action="store_true",
                        help="Auto-detect and convert if no markpact blocks found")
    parser.add_argument("--version", "-V", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress output")
    
    # LLM generation options
    parser.add_argument("--prompt", "-p", metavar="TEXT",
                        help="Generate markpact contract from text prompt using LLM")
    parser.add_argument("--output", "-o", metavar="FILE",
                        help="Output file for generated contract (default: README.md)")
    parser.add_argument("--model", "-m", metavar="MODEL",
                        help="LLM model to use (overrides config)")
    parser.add_argument("--api-base", metavar="URL",
                        help="API base URL (overrides config)")
    parser.add_argument("--api-key", metavar="KEY",
                        help="API key (overrides config)")
    parser.add_argument("--list-examples", action="store_true",
                        help="List available example prompts")
    parser.add_argument("--example", "-e", metavar="NAME",
                        help="Use example prompt by name (see --list-examples)")
    parser.add_argument("--run", "-r", action="store_true",
                        help="Run immediately after generating (with --prompt or --example)")
    parser.add_argument("--docker", action="store_true",
                        help="Run in Docker container (isolated sandbox)")
    parser.add_argument("--auto-fix", action="store_true", default=True,
                        help="Auto-fix runtime errors (e.g., port in use) - enabled by default")
    parser.add_argument("--no-auto-fix", action="store_true",
                        help="Disable auto-fix for runtime errors")

    args = parser.parse_args(argv)
    
    # Handle config subcommand
    if args.command == "config":
        return handle_config(args)
    
    verbose = not args.quiet
    
    # Handle --list-examples
    if args.list_examples:
        from .generator import list_example_prompts
        print("\n[markpact] Available example prompts:\n")
        for name, desc in list_example_prompts().items():
            print(f"  {name:15} - {desc}")
        print(f"\nUsage: markpact -e todo-api -o my-project/README.md")
        return 0
    
    # Handle --prompt or --example (LLM generation)
    if args.prompt or args.example:
        try:
            from .generator import generate_contract, GeneratorConfig, get_example_prompt
            from .config import load_env, init_env
        except ImportError:
            print("[markpact] ERROR: litellm not installed. Run: pip install markpact[llm]", file=sys.stderr)
            return 1
        
        # Auto-init config on first use
        init_env(force=False)
        
        prompt = args.prompt or get_example_prompt(args.example)
        
        # Build config from .env + args overrides
        env_config = load_env()
        config = GeneratorConfig(
            model=args.model or env_config.get("MARKPACT_MODEL", "ollama/qwen2.5-coder:14b"),
            api_base=args.api_base or env_config.get("MARKPACT_API_BASE", "http://localhost:11434"),
            api_key=getattr(args, 'api_key', None) or env_config.get("MARKPACT_API_KEY", ""),
            temperature=float(env_config.get("MARKPACT_TEMPERATURE", "0.7")),
            max_tokens=int(env_config.get("MARKPACT_MAX_TOKENS", "4096")),
        )
        
        print(f"[markpact] Generating contract with {config.model}...")
        print(f"[markpact] Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
        
        try:
            content = generate_contract(prompt, config, verbose=verbose)
        except Exception as e:
            print(f"[markpact] ERROR: {e}", file=sys.stderr)
            return 1
        
        output_path = Path(args.output) if args.output else Path("README.md")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)
        
        print(f"[markpact] Generated contract saved to: {output_path}")
        
        # If --run flag is set, continue to execute the generated contract
        if args.run:
            print(f"[markpact] Running generated contract...")
            args.readme = str(output_path)
            # Fall through to execution
        else:
            print(f"[markpact] Run with: markpact {output_path}")
            if args.docker:
                print(f"[markpact] Or with Docker: markpact {output_path} --docker")
            return 0
    
    readme = Path(args.readme)

    if not readme.exists():
        print(f"[markpact] ERROR: {readme} not found", file=sys.stderr)
        return 1

    sandbox = Sandbox(args.sandbox)
    verbose = not args.quiet
    
    # Read original content
    original_text = readme.read_text()
    text_to_parse = original_text
    
    # Check if conversion is needed
    has_markpact = "```markpact:" in original_text
    
    if args.convert or args.convert_only or (args.auto and not has_markpact):
        if verbose:
            print(f"[markpact] Converting {readme} to markpact format...")
        
        result = convert_markdown_to_markpact(original_text)
        
        if verbose or args.convert_only:
            print_conversion_report(result)
        
        if args.save_converted:
            save_path = Path(args.save_converted)
            save_path.write_text(result.converted_text)
            print(f"[markpact] Saved converted file to {save_path}")
        
        if args.convert_only:
            # Print converted content and exit
            print("\n--- CONVERTED CONTENT ---\n")
            print(result.converted_text)
            return 0
        
        text_to_parse = result.converted_text
    
    elif not has_markpact and verbose:
        # Suggest conversion
        print(f"[markpact] WARNING: No markpact blocks found in {readme}")
        print(f"[markpact] TIP: Use --convert or --auto to convert regular Markdown")
        print(f"[markpact]      markpact {readme} --convert")
        print()

    if verbose:
        print(f"[markpact] Parsing {readme}")

    blocks = parse_blocks(text_to_parse)
    deps: list[str] = []
    run_command: str | None = None

    for block in blocks:
        if block.kind == "bootstrap":
            continue  # skip bootstrap itself

        if block.kind == "file":
            path = block.get_path()
            if not path:
                print(f"[markpact] ERROR: markpact:file requires path=..., got: {block.meta}", file=sys.stderr)
                return 1
            if args.dry_run:
                print(f"[markpact] Would write {sandbox.path / path}")
            else:
                f = sandbox.write_file(path, block.body)
                if verbose:
                    print(f"[markpact] wrote {f}")

        elif block.kind == "deps" and "python" in block.meta:
            deps.extend(line.strip() for line in block.body.splitlines() if line.strip())

        elif block.kind == "run":
            run_command = block.body

    # Docker mode
    if args.docker:
        from .docker_runner import generate_dockerfile, build_and_run_docker, check_docker_available
        
        if not check_docker_available():
            print("[markpact] ERROR: Docker is not available. Install Docker first.", file=sys.stderr)
            return 1
        
        if args.dry_run:
            print(f"[markpact] Would build and run Docker container")
            print(f"[markpact] Deps: {', '.join(deps)}")
            print(f"[markpact] Run: {run_command}")
            return 0
        
        # Generate Dockerfile
        generate_dockerfile(sandbox.path, deps, run_command.strip() if run_command else "python -m http.server 8000")
        
        # Build and run
        return build_and_run_docker(sandbox.path, verbose=verbose)
    
    # Normal mode
    if deps:
        if args.dry_run:
            print(f"[markpact] Would install: {', '.join(deps)}")
        else:
            install_deps(deps, sandbox, verbose)

    if run_command:
        if args.dry_run:
            print(f"[markpact] Would run: {run_command}")
        else:
            use_auto_fix = args.auto_fix and not args.no_auto_fix
            if use_auto_fix:
                from .auto_fix import run_with_auto_fix
                run_with_auto_fix(run_command, sandbox, readme_path=readme, verbose=verbose)
            else:
                run_cmd(run_command, sandbox, verbose)
    elif verbose:
        print("[markpact] No run command defined")

    return 0


if __name__ == "__main__":
    sys.exit(main())
