#!/usr/bin/env python3
"""
Master test runner for all music agent integrations.
Run all or specific integration tests with detailed reporting.
"""

import sys
import os
import time
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test status colors
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE} {text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")


def print_status(service: str, status: str, details: str = ""):
    """Print test status with color."""
    if status == "PASS":
        color = Colors.GREEN
        symbol = "✅"
    elif status == "FAIL":
        color = Colors.RED
        symbol = "❌"
    elif status == "SKIP":
        color = Colors.YELLOW
        symbol = "⏭️"
    else:
        color = Colors.BLUE
        symbol = "🔄"
    
    print(f"{symbol} {color}{service:15} {status:6}{Colors.ENDC} {details}")


def run_discogs_tests() -> Tuple[bool, str]:
    """Run Discogs integration tests."""
    try:
        from tests.discogs.test_connection import test_connection
        
        # Run connection test
        success = test_connection()
        
        if success:
            return True, "All endpoints tested successfully"
        else:
            return False, "Some tests failed"
    except ImportError:
        return False, "Test module not found"
    except Exception as e:
        return False, str(e)


def run_integration_tests(integrations: List[str]) -> Dict[str, Tuple[bool, str]]:
    """Run tests for specified integrations."""
    results = {}
    
    # Map of integration names to test functions
    test_map = {
        'discogs': run_discogs_tests,
        # Add more as they're implemented:
        # 'musicbrainz': run_musicbrainz_tests,
        # 'spotify': run_spotify_tests,
        # 'deezer': run_deezer_tests,
        # 'beatport': run_beatport_tests,
        # 'soundcloud': run_soundcloud_tests,
        # 'bandcamp': run_bandcamp_tests,
        # 'mixcloud': run_mixcloud_tests,
        # 'youtube': run_youtube_tests,
        # 'soulseek': run_soulseek_tests,
    }
    
    for integration in integrations:
        if integration in test_map:
            print(f"\nTesting {integration}...")
            start_time = time.time()
            
            success, details = test_map[integration]()
            
            elapsed = time.time() - start_time
            results[integration] = (success, f"{details} ({elapsed:.2f}s)")
        else:
            results[integration] = (False, "No tests available")
    
    return results


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(
        description='Run music agent integration tests'
    )
    parser.add_argument(
        'integrations',
        nargs='*',
        help='Specific integrations to test (default: all)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Default to all available integrations
    all_integrations = [
        'discogs',
        'musicbrainz',
        'spotify',
        'deezer',
        'beatport',
        'soundcloud',
        'bandcamp',
        'mixcloud',
        'youtube',
        'soulseek'
    ]
    
    integrations = args.integrations if args.integrations else ['discogs']  # Only test what's ready
    
    # Print header
    print_header("MUSIC AGENT INTEGRATION TESTS")
    print(f"Testing: {', '.join(integrations)}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load environment variables
    from dotenv import load_dotenv
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Loaded environment from {env_path}")
    else:
        print(f"⚠️  No .env file found at {env_path}")
    
    # Run tests
    print_header("Running Tests")
    results = run_integration_tests(integrations)
    
    # Print results
    print_header("Test Results")
    
    passed = 0
    failed = 0
    skipped = 0
    
    for integration, (success, details) in results.items():
        if success is None:
            status = "SKIP"
            skipped += 1
        elif success:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1
        
        print_status(integration, status, details)
    
    # Summary
    print_header("Summary")
    total = passed + failed + skipped
    print(f"Total: {total} integrations")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.ENDC}")
    if failed > 0:
        print(f"{Colors.RED}Failed: {failed}{Colors.ENDC}")
    if skipped > 0:
        print(f"{Colors.YELLOW}Skipped: {skipped}{Colors.ENDC}")
    
    # Generate report file
    report_path = Path(__file__).parent / 'test_report.md'
    with open(report_path, 'w') as f:
        f.write(f"# Test Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Results\n\n")
        f.write(f"| Integration | Status | Details |\n")
        f.write(f"|------------|--------|----------|\n")
        for integration, (success, details) in results.items():
            status = "✅ PASS" if success else "❌ FAIL" if success is False else "⏭️ SKIP"
            f.write(f"| {integration} | {status} | {details} |\n")
        f.write(f"\n## Summary\n")
        f.write(f"- Total: {total}\n")
        f.write(f"- Passed: {passed}\n")
        f.write(f"- Failed: {failed}\n")
        f.write(f"- Skipped: {skipped}\n")
    
    print(f"\n📄 Report saved to {report_path}")
    
    # Exit code
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())