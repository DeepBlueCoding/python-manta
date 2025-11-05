#!/usr/bin/env python3
"""
Test runner script for python_manta test suite.

This script provides various test running options including:
- Unit tests only (fast, no external dependencies)  
- Integration tests (require demo files)
- Full test suite with coverage
- Performance tests
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_unit_tests():
    """Run only unit tests (fast, no external dependencies)."""
    print("🧪 Running unit tests...")
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/test_models.py",
        "tests/test_parser.py", 
        "tests/test_convenience.py",
        "tests/test_edge_cases.py",
        "-m", "unit",
        "-v"
    ]
    return subprocess.run(cmd, cwd=Path(__file__).parent)


def run_integration_tests():
    """Run integration tests (require demo files and shared library)."""
    print("🔗 Running integration tests...")
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_integration.py", 
        "-m", "integration",
        "-v"
    ]
    return subprocess.run(cmd, cwd=Path(__file__).parent)


def run_all_tests():
    """Run complete test suite."""
    print("🎯 Running complete test suite...")
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v"
    ]
    return subprocess.run(cmd, cwd=Path(__file__).parent)


def run_with_coverage():
    """Run tests with coverage reporting."""
    print("📊 Running tests with coverage analysis...")
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "--cov=python_manta",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-fail-under=85",
        "-v"
    ]
    return subprocess.run(cmd, cwd=Path(__file__).parent)


def run_performance_tests():
    """Run performance-focused tests.""" 
    print("⚡ Running performance tests...")
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-m", "slow",
        "-v"
    ]
    return subprocess.run(cmd, cwd=Path(__file__).parent)


def run_specific_test(test_path):
    """Run a specific test file or test function."""
    print(f"🔍 Running specific test: {test_path}")
    cmd = [
        sys.executable, "-m", "pytest",
        test_path,
        "-v"
    ]
    return subprocess.run(cmd, cwd=Path(__file__).parent)


def check_dependencies():
    """Check if test dependencies are available."""
    try:
        import pytest
        import pydantic
        print("✅ Core dependencies available")
        
        # Check optional dependencies
        optional_deps = []
        try:
            import pytest_cov
            optional_deps.append("pytest-cov")
        except ImportError:
            pass
            
        try:
            import pytest_xdist
            optional_deps.append("pytest-xdist")
        except ImportError:
            pass
            
        if optional_deps:
            print(f"✅ Optional dependencies: {', '.join(optional_deps)}")
        else:
            print("ℹ️  No optional test dependencies found")
            
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\n💡 To install test dependencies, run:")
        print("   pip install -e '.[dev]'")
        print("   OR with uv:")
        print("   uv pip install -e '.[dev]'")
        return False


def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(
        description="Python Manta Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --unit           # Run unit tests only
  python run_tests.py --integration    # Run integration tests
  python run_tests.py --coverage       # Run with coverage
  python run_tests.py --all            # Run all tests
  python run_tests.py --perf           # Run performance tests
  python run_tests.py tests/test_models.py  # Run specific test file
        """
    )
    
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage")
    parser.add_argument("--perf", action="store_true", help="Run performance tests")
    parser.add_argument("--check", action="store_true", help="Check dependencies")
    parser.add_argument("test_path", nargs="?", help="Run specific test file/function")
    
    args = parser.parse_args()
    
    # Check dependencies first
    if not check_dependencies():
        return 1
    
    if args.check:
        return 0
    
    # Run tests based on arguments
    if args.unit:
        result = run_unit_tests()
    elif args.integration:
        result = run_integration_tests()
    elif args.coverage:
        result = run_with_coverage()
    elif args.perf:
        result = run_performance_tests()
    elif args.all:
        result = run_all_tests()
    elif args.test_path:
        result = run_specific_test(args.test_path)
    else:
        # Default: run unit tests
        print("No specific test type specified, running unit tests...")
        result = run_unit_tests()
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())