"""
Test runner and quality report generator
Validates data accuracy for machine learning
"""
import unittest
import json
import sys
import os
from datetime import datetime

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(current_dir))

# Import all test modules (from current directory)
from test_pdf_extract import TestPDFExtraction
from test_digitize import TestDigitization, TestSignalProperties
from test_analyse import TestAnalysis, TestMetricsConsistency, TestErrorHandling
from test_integration import TestEndToEnd, TestDataValidation

# Import reproducibility test from current directory
import importlib.util
spec = importlib.util.spec_from_file_location("test_repro", os.path.join(current_dir, "test_reproducibility.py"))
test_repro = importlib.util.module_from_spec(spec)
spec.loader.exec_module(test_repro)
TestReproducibility = test_repro.TestReproducibility


def run_all_tests():
    """Run all tests and generate report"""
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPDFExtraction))
    suite.addTests(loader.loadTestsFromTestCase(TestDigitization))
    suite.addTests(loader.loadTestsFromTestCase(TestSignalProperties))
    suite.addTests(loader.loadTestsFromTestCase(TestAnalysis))
    suite.addTests(loader.loadTestsFromTestCase(TestMetricsConsistency))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEnd))
    suite.addTests(loader.loadTestsFromTestCase(TestDataValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestReproducibility))
    
    # Add ML features tests
    from test_ml_features import TestMLFeatures
    suite.addTests(loader.loadTestsFromTestCase(TestMLFeatures))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generate report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": result.testsRun,
        "passed": result.testsRun - len(result.failures) - len(result.errors),
        "failed": len(result.failures),
        "errors": len(result.errors),
        "success_rate": ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0,
        "failures": [str(test) for test, _ in result.failures],
        "errors": [str(test) for test, _ in result.errors]
    }
    
    return result, report


def print_quality_report(report):
    """Print formatted quality report"""
    print("\n" + "="*70)
    print("ECG ANALYSIS QUALITY REPORT")
    print("="*70)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Total Tests: {report['total_tests']}")
    print(f"Passed: {report['passed']} ✓")
    print(f"Failed: {report['failed']} ✗")
    print(f"Errors: {report['errors']} ⚠")
    print(f"Success Rate: {report['success_rate']:.1f}%")
    print("="*70)
    
    if report['success_rate'] >= 95:
        print("✓ DATA QUALITY: EXCELLENT (>95% tests passed)")
        print("✓ SAFE FOR MACHINE LEARNING: YES")
    elif report['success_rate'] >= 80:
        print("⚠ DATA QUALITY: GOOD (80-95% tests passed)")
        print("⚠ SAFE FOR MACHINE LEARNING: WITH CAUTION")
    else:
        print("✗ DATA QUALITY: NEEDS IMPROVEMENT (<80% tests passed)")
        print("✗ SAFE FOR MACHINE LEARNING: NO - FIX ISSUES FIRST")
    
    if report['failures']:
        print("\nFailed Tests:")
        for test in report['failures']:
            print(f"  - {test}")
    
    if report['errors']:
        print("\nTests with Errors:")
        for test in report['errors']:
            print(f"  - {test}")
    
    print("="*70 + "\n")
    
    return report['success_rate'] >= 95


if __name__ == '__main__':
    result, report = run_all_tests()
    
    # Save report to file
    os.makedirs("../reports", exist_ok=True)
    report_path = f"../reports/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport saved to: {report_path}")
    
    # Print formatted report
    is_production_ready = print_quality_report(report)
    
    # Exit with appropriate code
    sys.exit(0 if is_production_ready else 1)
