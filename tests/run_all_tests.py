#!/usr/bin/env python3
"""
Unified Test Runner

Runs all three integration test suites:
1. Discord Integration Tests
2. GPT Integration Tests
3. Webull Integration Tests

Run with: python tests/run_all_tests.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.test_discord_integration import run_discord_tests
from tests.test_gpt_integration import run_gpt_tests
from tests.test_webull_integration import run_webull_tests


def run_all_tests():
    """Run all test suites"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  STOCKTALK DISCORD BOT - INTEGRATION TEST SUITE  ".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    results = {}
    
    # Run Discord tests
    print("\n")
    results['Discord'] = run_discord_tests()
    
    # Run GPT tests
    print("\n")
    results['GPT'] = run_gpt_tests()
    
    # Run Webull tests
    print("\n")
    results['Webull'] = run_webull_tests()
    
    # Summary
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  TEST SUMMARY  ".center(58) + "║")
    print("║" + " "*58 + "║")
    
    for suite, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"║  {suite:.<40} {status:>15} ║")
    
    print("║" + " "*58 + "║")
    
    all_passed = all(results.values())
    if all_passed:
        print("║" + "  🎉 ALL TESTS PASSED - BOT IS READY!  ".center(58) + "║")
    else:
        print("║" + "  ❌ SOME TESTS FAILED - FIX ISSUES ABOVE  ".center(58) + "║")
    
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝\n")
    
    return all_passed


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
