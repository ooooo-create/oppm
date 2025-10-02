#!/usr/bin/env python3
"""
Smoke test for oppm package.
This test verifies that the basic functionality works correctly.
"""

import io
import sys
from contextlib import redirect_stderr, redirect_stdout


def test_import():
    """Test that we can import the main module."""
    try:
        from oppm.cli import main

        print("✓ Successfully imported oppm.cli")
    except Exception as e:
        print(f"✗ Failed to import oppm.cli: {e}")
        raise AssertionError(f"Failed to import oppm.cli: {e}") from e


def test_help():
    """Test that the CLI can show help."""
    try:
        # Test help by actually running the CLI with --help argument
        import argparse
        import sys

        from oppm.cli import main

        # Save original sys.argv
        old_argv = sys.argv[:]

        # Initialize variables
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            # Set up arguments to trigger help
            sys.argv = ["oppm", "--help"]

            # Try to call main, but it will raise SystemExit
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                main()

        except SystemExit as e:
            # This is expected when argparse shows help
            sys.argv = old_argv  # Restore sys.argv
            output = stdout_capture.getvalue()
            if "help" in output.lower() or "usage" in output.lower():
                print("✓ Help functionality works correctly")
            else:
                raise AssertionError("Help output doesn't contain expected content") from e
        except Exception as e:
            sys.argv = old_argv  # Restore sys.argv
            raise AssertionError(f"Failed to test help functionality: {e}") from e

    except Exception as e:
        raise AssertionError(f"Failed to test help functionality: {e}") from e


def test_basic_functionality():
    """Test basic functionality of the oppm module."""
    try:
        from oppm.commands import BINARY_ARCHIVE_TYPES, UNARY_ARCHIVE_TYPES

        # Simple test to verify the sets are defined
        assert len(UNARY_ARCHIVE_TYPES) > 0
        assert len(BINARY_ARCHIVE_TYPES) > 0
        print("✓ Basic functionality test passed")
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        raise AssertionError(f"Basic functionality test failed: {e}") from e


if __name__ == "__main__":
    print("Running smoke tests for oppm...")

    tests = [test_import, test_help, test_basic_functionality]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()  # Call the test function
            passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")

    if failed > 0:
        sys.exit(1)
    else:
        print("All smoke tests passed!")
        sys.exit(0)
