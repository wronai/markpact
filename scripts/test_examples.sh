#!/usr/bin/env bash
# Test all examples in examples/*/README.md
# Usage: ./scripts/test_examples.sh [--dry-run] [--verbose]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
EXAMPLES_DIR="$PROJECT_ROOT/examples"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Defaults
DRY_RUN=true
VERBOSE=false
TIMEOUT=30

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --run)
            DRY_RUN=false
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [--run] [--verbose] [--timeout SECONDS]"
            echo ""
            echo "Options:"
            echo "  --run       Actually run examples (default: dry-run only)"
            echo "  --verbose   Show detailed output"
            echo "  --timeout   Timeout per example in seconds (default: 30)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Categories of examples
PYTHON_EXAMPLES=(
    "fastapi-todo"
    "flask-blog"
    "cli-tool"
    "streamlit-dashboard"
    "kivy-mobile"
    "python-typer-cli"
)

NODE_EXAMPLES=(
    "node-express-api"
    "electron-desktop"
    "react-typescript-spa"
    "typescript-node-api"
)

OTHER_EXAMPLES=(
    "go-http-api"
    "rust-axum-api"
    "php-cli"
    "static-frontend"
)

PUBLISH_EXAMPLES=(
    "pypi-publish"
    "npm-publish"
    "docker-publish"
)

CONVERTER_EXAMPLES=(
    "markdown-converter"
)

# Statistics
PASSED=0
FAILED=0
SKIPPED=0
declare -a FAILED_EXAMPLES=()

log() {
    echo -e "$1"
}

log_verbose() {
    if [[ "$VERBOSE" == true ]]; then
        echo -e "$1"
    fi
}

test_example() {
    local example_name="$1"
    local readme_path="$EXAMPLES_DIR/$example_name/README.md"
    
    if [[ ! -f "$readme_path" ]]; then
        log "${YELLOW}⚠ SKIP${NC} $example_name - README.md not found"
        ((SKIPPED++))
        return 0
    fi
    
    log_verbose "${BLUE}Testing${NC} $example_name..."
    
    # Test parsing with --dry-run
    local output
    local exit_code=0
    
    if [[ "$DRY_RUN" == true ]]; then
        output=$(timeout "$TIMEOUT" markpact "$readme_path" --dry-run 2>&1) || exit_code=$?
    else
        # For actual run, use timeout and background
        output=$(timeout "$TIMEOUT" markpact "$readme_path" 2>&1) || exit_code=$?
    fi
    
    if [[ $exit_code -eq 0 ]] || [[ $exit_code -eq 124 && "$DRY_RUN" == false ]]; then
        log "${GREEN}✓ PASS${NC} $example_name"
        log_verbose "$output"
        ((PASSED++))
        return 0
    else
        log "${RED}✗ FAIL${NC} $example_name (exit code: $exit_code)"
        log_verbose "$output"
        ((FAILED++))
        FAILED_EXAMPLES+=("$example_name")
        return 1
    fi
}

test_publish_example() {
    local example_name="$1"
    local readme_path="$EXAMPLES_DIR/$example_name/README.md"
    
    if [[ ! -f "$readme_path" ]]; then
        log "${YELLOW}⚠ SKIP${NC} $example_name - README.md not found"
        ((SKIPPED++))
        return 0
    fi
    
    log_verbose "${BLUE}Testing publish${NC} $example_name..."
    
    # Test parsing with --publish --dry-run
    local output
    local exit_code=0
    
    output=$(timeout "$TIMEOUT" markpact "$readme_path" --publish --dry-run 2>&1) || exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        log "${GREEN}✓ PASS${NC} $example_name (publish)"
        log_verbose "$output"
        ((PASSED++))
        return 0
    else
        log "${RED}✗ FAIL${NC} $example_name (publish, exit code: $exit_code)"
        log_verbose "$output"
        ((FAILED++))
        FAILED_EXAMPLES+=("$example_name")
        return 1
    fi
}

test_converter_example() {
    local example_name="$1"
    local sample_path="$EXAMPLES_DIR/$example_name/sample.md"
    
    if [[ ! -f "$sample_path" ]]; then
        log "${YELLOW}⚠ SKIP${NC} $example_name - sample.md not found"
        ((SKIPPED++))
        return 0
    fi
    
    log_verbose "${BLUE}Testing converter${NC} $example_name..."
    
    local output
    local exit_code=0
    
    output=$(timeout "$TIMEOUT" markpact "$sample_path" --convert-only 2>&1) || exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        log "${GREEN}✓ PASS${NC} $example_name (converter)"
        log_verbose "$output"
        ((PASSED++))
        return 0
    else
        log "${RED}✗ FAIL${NC} $example_name (converter, exit code: $exit_code)"
        log_verbose "$output"
        ((FAILED++))
        FAILED_EXAMPLES+=("$example_name")
        return 1
    fi
}

# Main
echo "=============================================="
echo "       Markpact Examples Test Suite"
echo "=============================================="
echo ""
echo "Mode: $(if [[ "$DRY_RUN" == true ]]; then echo 'Dry-run (parsing only)'; else echo 'Full run'; fi)"
echo "Timeout: ${TIMEOUT}s per example"
echo ""

# Clean sandbox
rm -rf "$PROJECT_ROOT/sandbox"

echo "--- Python Examples ---"
for example in "${PYTHON_EXAMPLES[@]}"; do
    test_example "$example" || true
done

echo ""
echo "--- Node.js Examples ---"
for example in "${NODE_EXAMPLES[@]}"; do
    test_example "$example" || true
done

echo ""
echo "--- Other Language Examples ---"
for example in "${OTHER_EXAMPLES[@]}"; do
    test_example "$example" || true
done

echo ""
echo "--- Publish Examples ---"
for example in "${PUBLISH_EXAMPLES[@]}"; do
    test_publish_example "$example" || true
done

echo ""
echo "--- Converter Examples ---"
for example in "${CONVERTER_EXAMPLES[@]}"; do
    test_converter_example "$example" || true
done

# Summary
echo ""
echo "=============================================="
echo "                 SUMMARY"
echo "=============================================="
echo -e "${GREEN}Passed:${NC}  $PASSED"
echo -e "${RED}Failed:${NC}  $FAILED"
echo -e "${YELLOW}Skipped:${NC} $SKIPPED"
echo ""

if [[ $FAILED -gt 0 ]]; then
    echo -e "${RED}Failed examples:${NC}"
    for example in "${FAILED_EXAMPLES[@]}"; do
        echo "  - $example"
    done
    exit 1
fi

echo -e "${GREEN}All tests passed!${NC}"
exit 0
