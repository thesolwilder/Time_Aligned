"""
Test Runner - Run All Tests for Time Tracker

This script discovers and runs all unit tests in the tests directory.
Use this to execute the complete test suite with a single command.

Usage:
    python run_all_tests.py              # Run all tests
    python run_all_tests.py -v           # Run with verbose output
    python run_all_tests.py TestClass    # Run specific test class
"""

import unittest
import sys
import os
import gc
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class GarbageCollectingTestRunner(unittest.TextTestRunner):
    """Custom test runner that performs garbage collection between test classes

    This helps prevent "Variable.__del__" errors in large test suites with many
    tkinter roots by forcing cleanup of orphaned tkinter variables between classes.
    """

    def run(self, test):
        """Run tests with garbage collection between test classes"""
        result = self._makeResult()
        result.failfast = self.failfast
        result.buffer = self.buffer
        result.tb_locals = self.tb_locals

        startTestRun = getattr(result, "startTestRun", None)
        if startTestRun is not None:
            startTestRun()

        try:
            # Track previous test class to detect class changes
            prev_test_class = None

            # Iterate through all tests
            for test_case in self._flatten_suite(test):
                # Get current test class
                current_test_class = test_case.__class__.__name__

                # If we switched to a different test class, force garbage collection
                if (
                    prev_test_class is not None
                    and current_test_class != prev_test_class
                ):
                    collected = gc.collect()
                    if collected > 0:
                        print(
                            f"\n[GC] Switching from {prev_test_class} to {current_test_class}: collected {collected} objects\n"
                        )

                prev_test_class = current_test_class

                # Run the individual test
                test_case(result)

                if result.shouldStop:
                    break

            # Final garbage collection after all tests
            collected = gc.collect()
            if collected > 0:
                print(f"\n[GC] Final cleanup: collected {collected} objects\n")

        finally:
            stopTestRun = getattr(result, "stopTestRun", None)
            if stopTestRun is not None:
                stopTestRun()

        return result

    def _flatten_suite(self, suite):
        """Flatten a test suite into individual test cases"""
        for test in suite:
            if isinstance(test, unittest.TestSuite):
                yield from self._flatten_suite(test)
            else:
                yield test


def run_all_tests(verbosity=2, pattern="test_*.py"):
    """
    Discover and run all tests in the tests directory

    Args:
        verbosity: Output verbosity level (0=quiet, 1=normal, 2=verbose)
        pattern: File pattern to match test files

    Returns:
        TestResult object
    """
    # Get the directory containing this script
    test_dir = os.path.dirname(os.path.abspath(__file__))

    # Create test loader
    loader = unittest.TestLoader()

    # Discover all tests in the current directory
    suite = loader.discover(test_dir, pattern=pattern)

    # Create custom test runner with garbage collection
    runner = GarbageCollectingTestRunner(verbosity=verbosity)

    # Run tests
    print(f"\n{'='*70}")
    print("TIME TRACKER TEST SUITE")
    print(f"{'='*70}\n")
    print(f"Discovering tests in: {test_dir}")
    print(f"Pattern: {pattern}\n")

    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    total_seconds = end_time - start_time

    # Print failed/errored tests details
    if result.failures or result.errors:
        print(f"\n{'='*70}")
        print("FAILED/ERRORED TESTS")
        print(f"{'='*70}")

        if result.failures:
            print("\nFAILURES:")
            for test, traceback in result.failures:
                print(f"\n  - {test}")
                # Extract the actual AssertionError message
                lines = traceback.strip().split("\n")

                # Find the AssertionError line (contains the actual error message)
                assertion_error = None
                assertion_line = None

                for i, line in enumerate(lines):
                    if line.strip().startswith("AssertionError:"):
                        assertion_error = line.strip()
                        # Look backwards for the assertion call
                        for j in range(i - 1, max(i - 5, -1), -1):
                            if "self.assert" in lines[j]:
                                assertion_line = lines[j].strip()
                                break
                        break

                if assertion_error:
                    if assertion_line:
                        print(f"    Failed: {assertion_line}")
                    print(f"    {assertion_error}")
                else:
                    # Fallback: print last non-empty line
                    for line in reversed(lines):
                        if line.strip():
                            print(f"    Cause: {line.strip()}")
                            break

        if result.errors:
            print("\nERRORS:")
            for test, traceback in result.errors:
                print(f"\n  - {test}")
                # Extract the exception type and message
                lines = traceback.strip().split("\n")

                # Find the actual exception line (usually last non-empty line)
                for line in reversed(lines):
                    stripped = line.strip()
                    if (
                        stripped
                        and not stripped.startswith("File ")
                        and ":" in stripped
                    ):
                        print(f"    {stripped}")
                        break

        print(f"\n{'='*70}")

    # Print summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Total time: {total_seconds:.2f} seconds ({total_seconds/60:.2f} minutes)")


def run_specific_test(test_name, verbosity=2):
    """
    Run a specific test class or test method

    Args:
        test_name: Name of test class or method (e.g., 'TestTimeTrackingAccuracy'
                   or 'test_time_tracking.TestTimeTrackingAccuracy.test_session_start')
        verbosity: Output verbosity level

    Returns:
        TestResult object
    """
    # Create test loader
    loader = unittest.TestLoader()

    # Load specific test
    suite = loader.loadTestsFromName(test_name)

    # Create custom test runner with garbage collection
    runner = GarbageCollectingTestRunner(verbosity=verbosity)

    # Run tests
    print(f"\n{'='*70}")
    print(f"Running specific test: {test_name}")
    print(f"{'='*70}\n")

    result = runner.run(suite)

    return result


def print_test_categories():
    """Print available test categories"""
    print("\n" + "=" * 70)
    print("AVAILABLE TEST CATEGORIES")
    print("=" * 70)
    print(
        """
Test Files:
  - test_time_tracking.py   : Time recording accuracy and duration calculations
  - test_backup.py          : Backup save functionality and crash recovery
  - test_analysis.py        : Analysis frame filtering and data aggregation
  - test_screenshots.py     : Screenshot timing and window focus detection
  - test_settings.py        : Default sphere/projects and settings persistence
  - test_idle_tracking.py   : Idle detection and period recording
  - test_helpers.py         : Testing utilities and mock objects

Priority Areas (Data Accuracy):
  ✓ Time period recording accuracy
  ✓ Backup saves every 60 seconds
  ✓ Analysis filtering by date/sphere/project
  ✓ Screenshot timing enforcement
  ✓ Default settings retrieval
  ✓ Idle threshold detection

Usage Examples:
  python run_all_tests.py                                    # Run all tests
  python run_all_tests.py -v                                 # Verbose output
  python run_all_tests.py test_time_tracking                 # Run one file
  python run_all_tests.py test_backup.TestBackupSaveFunctionality  # Run one class
    """
    )
    print("=" * 70 + "\n")


if __name__ == "__main__":
    # Parse command line arguments
    result = None

    if len(sys.argv) > 1:
        arg = sys.argv[1]

        # Check for help flag
        if arg in ["-h", "--help", "help"]:
            print_test_categories()
            sys.exit(0)

        # Check for verbose flag
        elif arg in ["-v", "--verbose"]:
            result = run_all_tests(verbosity=2)

        # Check for quiet flag
        elif arg in ["-q", "--quiet"]:
            result = run_all_tests(verbosity=0)

        # Run specific test
        else:
            result = run_specific_test(arg, verbosity=2)
    else:
        # Run all tests with default verbosity
        result = run_all_tests(verbosity=2)

    # Exit with appropriate code
    sys.exit(0 if result and result.wasSuccessful() else 1)
