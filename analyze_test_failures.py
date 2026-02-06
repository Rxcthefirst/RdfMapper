#!/usr/bin/env python3
"""
Quick script to identify common patterns in failing tests that need v3 updates.
"""

import subprocess
import sys

def run_tests_and_get_failures():
    """Run tests and extract failure information."""
    result = subprocess.run(
        ["python", "-m", "pytest", "--tb=no", "-q"],
        capture_output=True,
        text=True,
        timeout=120
    )

    output = result.stdout + result.stderr

    # Extract FAILED lines
    failures = []
    for line in output.split('\n'):
        if line.strip().startswith('FAILED'):
            failures.append(line.strip())

    return failures

def categorize_failures(failures):
    """Categorize failures by type."""
    categories = {
        'v3_sheets': [],
        'v3_columns': [],
        'v3_as_field': [],
        'matcher_count': [],
        'model_validation': [],
        'other': []
    }

    for failure in failures:
        if "'MappingConfig' object has no attribute 'sheets'" in failure:
            categories['v3_sheets'].append(failure)
        elif "'SheetMapping' object has no attribute 'columns'" in failure or "'.columns'" in failure:
            categories['v3_columns'].append(failure)
        elif "'as' in" in failure or "['as']" in failure:
            categories['v3_as_field'].append(failure)
        elif "Expected 17 matchers" in failure or "matchers to fire" in failure:
            categories['matcher_count'].append(failure)
        elif "ValidationError" in failure or "pydantic" in failure:
            categories['model_validation'].append(failure)
        else:
            categories['other'].append(failure)

    return categories

def main():
    print("🔍 Analyzing test failures...")
    print("=" * 70)

    try:
        failures = run_tests_and_get_failures()

        if not failures:
            print("✅ No failures found!")
            return 0

        print(f"\n📊 Total Failures: {len(failures)}\n")

        categories = categorize_failures(failures)

        for category, items in categories.items():
            if items:
                print(f"\n{category.upper().replace('_', ' ')} ({len(items)} failures):")
                print("-" * 70)
                for item in items[:5]:  # Show first 5
                    print(f"  • {item[:100]}...")
                if len(items) > 5:
                    print(f"  ... and {len(items) - 5} more")

        print("\n" + "=" * 70)
        print(f"✅ Analysis complete!")

    except subprocess.TimeoutExpired:
        print("⏰ Tests timed out")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())

