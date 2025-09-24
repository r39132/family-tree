#!/usr/bin/env python3
"""
Test runner for comprehensive space-specific functionality testing.
Runs all test suites and generates coverage reports.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "app"))


def run_backend_tests():
    """Run backend unit tests for space functionality"""
    print("\n🧪 Running Backend Space-Specific Tests...")

    test_files = ["test_comprehensive_spaces.py", "test_tree_bugs.py", "test_integration_spaces.py"]

    results = {}

    for test_file in test_files:
        test_path = project_root / test_file
        if not test_path.exists():
            print(f"⚠️  Test file not found: {test_file}")
            continue

        print(f"\n📝 Running {test_file}...")

        try:
            # Try to run with pytest if available
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_path), "-v", "--tb=short", "--no-header"],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                print(f"✅ {test_file} - PASSED")
                results[test_file] = "PASSED"
            else:
                print(f"❌ {test_file} - FAILED")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                results[test_file] = "FAILED"

        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback to running as regular Python script
            try:
                result = subprocess.run(
                    [sys.executable, str(test_path)], capture_output=True, text=True, timeout=60
                )

                if result.returncode == 0:
                    print(f"✅ {test_file} - PASSED (fallback)")
                    results[test_file] = "PASSED"
                else:
                    print(f"❌ {test_file} - FAILED (fallback)")
                    print("Output:", result.stdout)
                    print("Errors:", result.stderr)
                    results[test_file] = "FAILED"

            except Exception as e:
                print(f"💥 {test_file} - ERROR: {e}")
                results[test_file] = "ERROR"

    return results


def run_frontend_tests():
    """Run frontend tests for space functionality"""
    print("\n🖥️ Running Frontend Space-Specific Tests...")

    frontend_dir = project_root.parent / "frontend"
    if not frontend_dir.exists():
        print("⚠️  Frontend directory not found")
        return {}

    test_files = ["__tests__/space-isolation.test.tsx", "__tests__/tree-bugs.test.tsx"]

    results = {}

    for test_file in test_files:
        test_path = frontend_dir / test_file
        if not test_path.exists():
            print(f"⚠️  Frontend test file not found: {test_file}")
            continue

        print(f"\n📝 Running {test_file}...")

        try:
            # Run with npm test
            result = subprocess.run(
                ["npm", "test", "--", "--testPathPattern", test_file, "--watchAll=false"],
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                print(f"✅ {test_file} - PASSED")
                results[test_file] = "PASSED"
            else:
                print(f"❌ {test_file} - FAILED")
                print("Output:", result.stdout)
                print("Errors:", result.stderr)
                results[test_file] = "FAILED"

        except Exception as e:
            print(f"💥 {test_file} - ERROR: {e}")
            results[test_file] = "ERROR"

    return results


def check_space_implementation():
    """Check if space-specific fixes are implemented"""
    print("\n🔍 Checking Space-Specific Implementation...")

    routes_file = project_root / "app" / "routes_tree.py"
    if not routes_file.exists():
        print("❌ routes_tree.py not found")
        return False

    implementation_checks = {
        "space_specific_active_version": False,
        "space_validation": False,
        "normalized_comparison": False,
        "space_id_in_save": False,
    }

    try:
        content = routes_file.read_text()

        # Check for space-specific active version
        if "active_version_{space_id}" in content or 'f"active_version_{space_id}"' in content:
            implementation_checks["space_specific_active_version"] = True
            print("✅ Space-specific active version tracking implemented")
        else:
            print("❌ Space-specific active version tracking NOT implemented")

        # Check for space validation
        if "version_space_id != space_id" in content or "space validation" in content.lower():
            implementation_checks["space_validation"] = True
            print("✅ Space validation implemented")
        else:
            print("❌ Space validation NOT implemented")

        # Check for normalized comparison
        if "normalize_relations" in content or "normalized" in content:
            implementation_checks["normalized_comparison"] = True
            print("✅ Normalized relation comparison implemented")
        else:
            print("❌ Normalized relation comparison NOT implemented")

        # Check for space_id in save operations
        if '"space_id": space_id' in content:
            implementation_checks["space_id_in_save"] = True
            print("✅ Space ID included in save operations")
        else:
            print("❌ Space ID NOT included in save operations")

    except Exception as e:
        print(f"💥 Error checking implementation: {e}")
        return False

    total_checks = len(implementation_checks)
    passed_checks = sum(implementation_checks.values())

    print(f"\n📊 Implementation Status: {passed_checks}/{total_checks} checks passed")

    return passed_checks == total_checks


def run_data_analysis():
    """Run data analysis to check current database state"""
    print("\n📊 Running Data Analysis...")

    analysis_script = project_root / "analyze_data.py"
    if not analysis_script.exists():
        print("⚠️  Data analysis script not found")
        return

    try:
        result = subprocess.run(
            [sys.executable, str(analysis_script)], capture_output=True, text=True, timeout=60
        )

        if result.returncode == 0:
            print("✅ Data analysis completed successfully")
            print("Output preview:")
            lines = result.stdout.split("\n")[:20]  # Show first 20 lines
            for line in lines:
                if line.strip():
                    print(f"  {line}")
            if len(result.stdout.split("\n")) > 20:
                print("  ... (output truncated)")
        else:
            print("❌ Data analysis failed")
            print("Errors:", result.stderr)

    except Exception as e:
        print(f"💥 Data analysis error: {e}")


def generate_test_report(backend_results, frontend_results, implementation_status):
    """Generate comprehensive test report"""
    print("\n📋 Generating Test Report...")

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "backend_tests": backend_results,
        "frontend_tests": frontend_results,
        "implementation_status": implementation_status,
        "summary": {
            "total_backend_tests": len(backend_results),
            "passed_backend_tests": sum(
                1 for result in backend_results.values() if result == "PASSED"
            ),
            "total_frontend_tests": len(frontend_results),
            "passed_frontend_tests": sum(
                1 for result in frontend_results.values() if result == "PASSED"
            ),
            "implementation_complete": implementation_status,
        },
    }

    # Save detailed report
    report_file = project_root / "test_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    # Print summary
    print("\n" + "=" * 50)
    print("🎯 TEST SUMMARY")
    print("=" * 50)

    backend_passed = report["summary"]["passed_backend_tests"]
    backend_total = report["summary"]["total_backend_tests"]
    frontend_passed = report["summary"]["passed_frontend_tests"]
    frontend_total = report["summary"]["total_frontend_tests"]

    print(f"Backend Tests:  {backend_passed}/{backend_total} passed")
    print(f"Frontend Tests: {frontend_passed}/{frontend_total} passed")
    print(f"Implementation: {'✅ Complete' if implementation_status else '❌ Incomplete'}")

    overall_success = (
        backend_passed == backend_total
        and frontend_passed == frontend_total
        and implementation_status
    )

    print(f"\nOverall Status: {'🎉 SUCCESS' if overall_success else '⚠️ NEEDS WORK'}")
    print(f"Detailed report saved to: {report_file}")

    return overall_success


def main():
    """Main test runner"""
    print("🚀 Starting Comprehensive Space-Specific Test Suite")
    print("=" * 60)

    start_time = time.time()

    # Check implementation status first
    implementation_status = check_space_implementation()

    # Run backend tests
    backend_results = run_backend_tests()

    # Run frontend tests
    frontend_results = run_frontend_tests()

    # Run data analysis
    run_data_analysis()

    # Generate report
    success = generate_test_report(backend_results, frontend_results, implementation_status)

    elapsed = time.time() - start_time
    print(f"\n⏱️  Total execution time: {elapsed:.2f} seconds")

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
