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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="markpact",
        description="Executable Markdown Runtime – run projects from README.md",
    )
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
                        help="LLM model to use (default: ollama/qwen2.5-coder:7b)")
    parser.add_argument("--api-base", metavar="URL",
                        help="API base URL (default: http://localhost:11434)")
    parser.add_argument("--list-examples", action="store_true",
                        help="List available example prompts")
    parser.add_argument("--example", "-e", metavar="NAME",
                        help="Use example prompt by name (see --list-examples)")

    args = parser.parse_args(argv)
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
        except ImportError:
            print("[markpact] ERROR: litellm not installed. Run: pip install markpact[llm]", file=sys.stderr)
            return 1
        
        prompt = args.prompt or get_example_prompt(args.example)
        
        # Build config from args
        config = GeneratorConfig.from_env()
        if args.model:
            config.model = args.model
        if args.api_base:
            config.api_base = args.api_base
        
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
        print(f"[markpact] Run with: markpact {output_path}")
        
        # If --dry-run not set and user wants to run immediately
        if not args.dry_run and args.readme != "README.md":
            return 0
        
        # Continue to execute if no explicit output was set
        if args.output:
            return 0
        
        # Use generated content for execution
        args.readme = str(output_path)
    
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

    if deps:
        if args.dry_run:
            print(f"[markpact] Would install: {', '.join(deps)}")
        else:
            install_deps(deps, sandbox, verbose)

    if run_command:
        if args.dry_run:
            print(f"[markpact] Would run: {run_command}")
        else:
            run_cmd(run_command, sandbox, verbose)
    elif verbose:
        print("[markpact] No run command defined")

    return 0


if __name__ == "__main__":
    sys.exit(main())
