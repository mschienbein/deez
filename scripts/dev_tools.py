#!/usr/bin/env python3
"""
Development tools for Deez Music Agent
"""

import subprocess
import sys
from pathlib import Path
import shutil


def run_lint():
    """Run linting with ruff"""
    print("🔍 Running linter...")
    result = subprocess.run(["ruff", "check", "src/"], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ No linting issues found")
    else:
        print(result.stdout)
        print("❌ Linting issues found")
        sys.exit(1)


def run_format():
    """Format code with ruff"""
    print("🎨 Formatting code...")
    result = subprocess.run(["ruff", "format", "src/"], capture_output=True, text=True)
    print(result.stdout)
    print("✅ Code formatted")


def run_typecheck():
    """Run type checking with mypy"""
    print("🔍 Running type checker...")
    result = subprocess.run(["mypy", "src/"], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ No type issues found")
    else:
        print(result.stdout)
        print("⚠️  Type issues found")


def clean_project():
    """Clean up build artifacts and caches"""
    print("🧹 Cleaning project...")
    
    # Directories to clean
    dirs_to_clean = [
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "build",
        "dist",
        "*.egg-info",
        ".coverage",
        "htmlcov",
    ]
    
    project_root = Path(__file__).parent.parent
    
    for pattern in dirs_to_clean:
        for path in project_root.rglob(pattern):
            if path.is_dir():
                print(f"  Removing {path}")
                shutil.rmtree(path)
            elif path.is_file():
                print(f"  Removing {path}")
                path.unlink()
    
    # Clean .pyc files
    for pyc in project_root.rglob("*.pyc"):
        pyc.unlink()
    
    for pyo in project_root.rglob("*.pyo"):
        pyo.unlink()
    
    print("✅ Project cleaned")


def run_tests(args: list[str] = None):
    """Run tests with pytest"""
    print("🧪 Running tests...")
    
    cmd = ["pytest"]
    if args:
        cmd.extend(args)
    else:
        cmd.extend(["tests/", "-v"])
    
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def check_all():
    """Run all checks"""
    print("🔍 Running all checks...\n")
    
    # Run format
    print("=" * 60)
    run_format()
    
    # Run lint
    print("\n" + "=" * 60)
    run_lint()
    
    # Run typecheck
    print("\n" + "=" * 60)
    run_typecheck()
    
    # Run tests
    print("\n" + "=" * 60)
    run_tests()
    
    print("\n" + "=" * 60)
    print("✅ All checks passed!")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python dev_tools.py [lint|format|typecheck|clean|test|check-all]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "lint":
        run_lint()
    elif command == "format":
        run_format()
    elif command == "typecheck":
        run_typecheck()
    elif command == "clean":
        clean_project()
    elif command == "test":
        run_tests(sys.argv[2:])
    elif command == "check-all":
        check_all()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()