#!/bin/bash

##############################################################################
# jconfigpy Functional Test Script
# Tests the jconfigpy configuration utility using the example C project
##############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLE_DIR="$SCRIPT_DIR/example"
TEST_OUTPUT_DIR="/tmp/jconfigpy_test_$$"
PYTHON3="python3"

# Use development version if PYTHONPATH not set
if [ -z "$PYTHONPATH" ]; then
    export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
fi

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

##############################################################################
# Helper Functions
##############################################################################

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_section() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║ $1${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
}

##############################################################################
# Test 1: Module Import Test
##############################################################################

test_module_import() {
    log_section "Test 1: Module Import Test"
    
    log_info "Testing jconfigpy module imports..."
    
    if $PYTHON3 -c "
from jconfigpy import Dialog, Monitor, JConfig, FileNotExistError
print('Imported: Dialog, Monitor, JConfig, FileNotExistError')
" 2>/dev/null; then
        log_success "Module imports working correctly"
        return 0
    else
        log_error "Module import failed"
        return 1
    fi
}

##############################################################################
# Test 2: Singleton Pattern Test
##############################################################################

test_singleton_pattern() {
    log_section "Test 2: Singleton Pattern Test"
    
    log_info "Testing Monitor singleton behavior..."
    
    if $PYTHON3 << 'EOF' 2>/dev/null; then
from jconfigpy import Monitor

m1 = Monitor()
m2 = Monitor()

if m1 is m2:
    print("✓ Singleton pattern working: same instance returned")
    exit(0)
else:
    print("✗ Singleton pattern failed: different instances")
    exit(1)
EOF
        log_success "Singleton pattern working correctly"
        return 0
    else
        log_error "Singleton pattern test failed"
        return 1
    fi
}

##############################################################################
# Test 3: Configuration Parsing Test
##############################################################################

test_config_parsing() {
    log_section "Test 3: Configuration Parsing Test"
    
    log_info "Testing configuration file parsing..."
    
    if $PYTHON3 << EOF 2>/dev/null; then
from jconfigpy import JConfig
import os

config_file = "$EXAMPLE_DIR/config.json"
if not os.path.exists(config_file):
    print(f"Config file not found: {config_file}")
    exit(1)

try:
    config = JConfig(jconfig_file=config_file, root_dir="$EXAMPLE_DIR/")
    print("✓ Configuration file parsed successfully")
    exit(0)
except Exception as e:
    print(f"✗ Failed to parse configuration: {e}")
    exit(1)
EOF
        log_success "Configuration parsing working correctly"
        return 0
    else
        log_error "Configuration parsing test failed"
        return 1
    fi
}

##############################################################################
# Test 4: Config Generation Test (Non-interactive)
##############################################################################

test_config_generation() {
    log_section "Test 4: Configuration Generation Test"
    
    log_info "Creating test output directory: $TEST_OUTPUT_DIR"
    mkdir -p "$TEST_OUTPUT_DIR"
    
    log_info "Testing configuration generation (loading existing config)..."
    
    # Copy example config
    cp "$EXAMPLE_DIR/.config" "$TEST_OUTPUT_DIR/.config"
    
    if cd "$TEST_OUTPUT_DIR" && $PYTHON3 -m jconfigpy \
        -s -i .config \
        -t "$EXAMPLE_DIR/config.json" \
        -o .config.new \
        -g autogen.h 2>/dev/null; then
        
        if [ -f .config.new ] && [ -f autogen.h ]; then
            log_success "Configuration generation successful"
            log_info "Generated files:"
            log_info "  - .config.new: $(wc -l < .config.new) lines"
            log_info "  - autogen.h: $(wc -l < autogen.h) lines"
            cd - > /dev/null
            return 0
        else
            log_error "Generated files not found"
            cd - > /dev/null
            return 1
        fi
    else
        log_error "Configuration generation failed"
        cd - > /dev/null
        return 1
    fi
}

##############################################################################
# Test 5: Python 3 Syntax Validation
##############################################################################

test_syntax_validation() {
    log_section "Test 5: Python 3 Syntax Validation"
    
    log_info "Validating Python 3 syntax for all jconfigpy modules..."
    
    local failed=0
    for file in "$SCRIPT_DIR"/jconfigpy/*.py; do
        if $PYTHON3 -m py_compile "$file" 2>/dev/null; then
            log_info "  ✓ $(basename "$file")"
        else
            log_error "  ✗ $(basename "$file")"
            failed=$((failed + 1))
        fi
    done
    
    if [ $failed -eq 0 ]; then
        log_success "All files passed syntax validation"
        return 0
    else
        log_error "$failed file(s) failed syntax validation"
        return 1
    fi
}

##############################################################################
# Test 6: Direct Script Execution Test
##############################################################################

test_direct_script_execution() {
    log_section "Test 6: Direct Script Execution Test"
    
    log_info "Testing direct script execution (not as module)..."
    
    if cd "$TEST_OUTPUT_DIR" && $PYTHON3 "$SCRIPT_DIR/jconfigpy/__main__.py" \
        -s -i "$EXAMPLE_DIR/.config" \
        -t "$EXAMPLE_DIR/config.json" \
        -o .config.direct \
        -g autogen_direct.h 2>/dev/null; then
        
        if [ -f .config.direct ] && [ -f autogen_direct.h ]; then
            log_success "Direct script execution successful"
            log_info "Generated files:"
            log_info "  - .config.direct: $(wc -l < .config.direct) lines"
            log_info "  - autogen_direct.h: $(wc -l < autogen_direct.h) lines"
            cd - > /dev/null
            return 0
        else
            log_error "Generated files not found"
            cd - > /dev/null
            return 1
        fi
    else
        log_error "Direct script execution failed"
        cd - > /dev/null
        return 1
    fi
}

##############################################################################
# Test 7: File I/O Operations Test
##############################################################################

test_file_io() {
    log_section "Test 7: File I/O Operations Test"
    
    log_info "Testing Monitor file write operations..."
    
    if $PYTHON3 << EOF 2>/dev/null; then
from jconfigpy import Monitor
import os

monitor = Monitor()
monitor.notify_variable_change("CONFIG_TEST_VAR", "test_value")
monitor.notify_variable_change("CONFIG_DEBUG", "y")

test_file = "$TEST_OUTPUT_DIR/config_test.txt"
with open(test_file, "w") as f:
    monitor.write(f)

if os.path.exists(test_file):
    with open(test_file, "r") as f:
        content = f.read()
    if "CONFIG_TEST_VAR" in content and "CONFIG_DEBUG" in content:
        print("✓ File I/O operations successful")
        exit(0)
    else:
        print("✗ Variable values not found in file")
        exit(1)
else:
    print("✗ Output file not created")
    exit(1)
EOF
        log_success "File I/O operations working correctly"
        return 0
    else
        log_error "File I/O operations test failed"
        return 1
    fi
}

##############################################################################
# Cleanup
##############################################################################

cleanup() {
    if [ -d "$TEST_OUTPUT_DIR" ]; then
        rm -rf "$TEST_OUTPUT_DIR"
        log_info "Cleaned up test directory: $TEST_OUTPUT_DIR"
    fi
}

##############################################################################
# Main Test Suite Execution
##############################################################################

main() {
    log_section "jconfigpy Functional Test Suite"
    
    log_info "Python version: $($PYTHON3 --version)"
    log_info "Script directory: $SCRIPT_DIR"
    log_info "Example directory: $EXAMPLE_DIR"
    log_info "Test output directory: $TEST_OUTPUT_DIR"
    log_info "PYTHONPATH: ${PYTHONPATH:-<not set>}"
    log_info "Using development version from: $SCRIPT_DIR"
    
    local total_tests=0
    local passed_tests=0
    
    # Run all tests
    tests=(
        test_module_import
        test_singleton_pattern
        test_config_parsing
        test_syntax_validation
        test_file_io
        test_config_generation
        test_direct_script_execution
    )
    
    for test in "${tests[@]}"; do
        total_tests=$((total_tests + 1))
        if $test; then
            passed_tests=$((passed_tests + 1))
        fi
    done
    
    # Print summary
    log_section "Test Summary"
    
    if [ $passed_tests -eq $total_tests ]; then
        log_success "All $total_tests tests PASSED! ✨"
        result=0
    else
        failed_tests=$((total_tests - passed_tests))
        log_error "$failed_tests out of $total_tests tests FAILED"
        result=1
    fi
    
    echo ""
    echo "Passed: $passed_tests/$total_tests"
    echo ""
    
    # Cleanup
    cleanup
    
    return $result
}

##############################################################################
# Script Entry Point
##############################################################################

if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    cat << 'HELP'
jconfigpy Functional Test Script

Usage: test_jconfigpy.sh [OPTIONS]

DESCRIPTION:
    This script tests the jconfigpy development version in-place without 
    requiring installation. It uses PYTHONPATH to load the local modules.

OPTIONS:
    -h, --help      Show this help message
    -v, --verbose   Show verbose output
    --cleanup-only  Only cleanup test files
    --use-installed Use installed version instead of development version

TESTS:
    1. Module Import Test      - Verify all modules can be imported
    2. Singleton Pattern Test  - Verify Monitor singleton works
    3. Config Parsing Test     - Verify configuration files can be parsed
    4. Syntax Validation       - Verify Python 3 syntax compliance
    5. File I/O Operations     - Verify file operations work
    6. Config Generation Test  - Verify config generation (module mode)
    7. Direct Script Execution - Verify config generation (script mode)

ENVIRONMENT:
    PYTHONPATH     Will be set to development directory automatically
    PYTHON3        Python 3 executable to use (default: python3)

EXAMPLE:
    ./test_jconfigpy.sh                    # Run all tests with dev version
    ./test_jconfigpy.sh --use-installed    # Run tests with installed version
    ./test_jconfigpy.sh --cleanup-only     # Clean up test files

HELP
    exit 0
fi

if [ "$1" = "--cleanup-only" ]; then
    cleanup
    exit 0
fi

if [ "$1" = "--use-installed" ]; then
    # Use installed version - don't modify PYTHONPATH
    unset PYTHONPATH
fi

# Run main test suite
main
exit $?
