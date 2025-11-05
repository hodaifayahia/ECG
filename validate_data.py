#!/usr/bin/env python3
"""
ECG Data Validation Checklist
Run this before using data in machine learning
"""

import json
import os
import sys

sys.path.insert(0, '..')

from ecg_modules import digitize, analyse


def validate_single_extraction():
    """Validate one complete extraction cycle"""
    print("=" * 70)
    print("ECG DATA VALIDATION CHECKLIST")
    print("=" * 70)
    
    checklist = {
        "extraction": False,
        "csv_created": False,
        "metrics_computed": False,
        "no_nan_inf": False,
        "all_features": False,
        "ranges_valid": False,
        "json_compatible": False,
        "final_status": "NOT STARTED"
    }
    
    try:
        # 1. Extract ECG data
        print("\n[1/7] Generating ECG data...")
        csv_path = digitize.ecg_to_csv(None)
        checklist["extraction"] = True
        print(f"     ✓ Data generated at: {csv_path}")
        
        # 2. Verify CSV created
        print("[2/7] Verifying CSV file...")
        if os.path.exists(csv_path):
            size = os.path.getsize(csv_path)
            checklist["csv_created"] = True
            print(f"     ✓ CSV file exists ({size} bytes)")
        else:
            raise Exception("CSV file not created")
        
        # 3. Compute metrics
        print("[3/7] Computing HRV metrics...")
        metrics = analyse.compute_metrics(csv_path)
        if metrics.get('processing_status') == 'success':
            checklist["metrics_computed"] = True
            print(f"     ✓ Metrics computed ({len(metrics)} fields)")
        else:
            raise Exception(f"Metrics computation failed: {metrics}")
        
        # 4. Check for NaN/Inf
        print("[4/7] Checking for NaN/Inf values...")
        has_invalid = False
        invalid_fields = []
        for key, value in metrics.items():
            if isinstance(value, float):
                if value != value:  # NaN check
                    has_invalid = True
                    invalid_fields.append(f"{key}: NaN")
                elif value == float('inf') or value == float('-inf'):
                    has_invalid = True
                    invalid_fields.append(f"{key}: Inf")
        
        if not has_invalid:
            checklist["no_nan_inf"] = True
            print("     ✓ No NaN or Inf values found")
        else:
            for field in invalid_fields:
                print(f"     ✗ INVALID: {field}")
        
        # 5. Verify all features present
        print("[5/7] Checking for all required ML features...")
        required_features = [
            'heart_rate_bpm', 'sdnn_ms', 'rmssd_ms', 'pnn50_percent',
            'pnn20_percent', 'sd1_ms', 'sd2_ms', 'lf_power', 'hf_power', 'lf_hf_ratio'
        ]
        missing = [f for f in required_features if f not in metrics]
        if not missing:
            checklist["all_features"] = True
            print(f"     ✓ All {len(required_features)} required features present")
        else:
            print(f"     ✗ MISSING FEATURES: {', '.join(missing)}")
        
        # 6. Validate feature ranges
        print("[6/7] Validating feature ranges...")
        ranges_valid = True
        range_checks = {
            'heart_rate_bpm': (30, 200),
            'sdnn_ms': (0, 500),
            'rmssd_ms': (0, 500),
            'pnn50_percent': (0, 100),
            'pnn20_percent': (0, 100),
            'sd1_ms': (0, 300),
            'sd2_ms': (0, 500),
        }
        
        for feature, (min_val, max_val) in range_checks.items():
            if feature in metrics:
                value = metrics[feature]
                if not (min_val <= value <= max_val):
                    print(f"     ✗ {feature}={value} out of range [{min_val}, {max_val}]")
                    ranges_valid = False
        
        if ranges_valid:
            checklist["ranges_valid"] = True
            print("     ✓ All features within valid ranges")
        
        # 7. Check JSON compatibility
        print("[7/7] Testing JSON serialization...")
        try:
            json_str = json.dumps(metrics)
            deserialized = json.loads(json_str)
            checklist["json_compatible"] = True
            print("     ✓ Data is JSON serializable and deserializable")
        except TypeError as e:
            print(f"     ✗ JSON serialization failed: {e}")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        checklist["final_status"] = "FAILED"
        return False, checklist
    
    # Calculate final status
    passed = sum(1 for v in checklist.values() if v is True)
    total = sum(1 for v in checklist.values() if isinstance(v, bool))
    
    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)
    
    for check, status in checklist.items():
        if check != "final_status":
            symbol = "✓" if status else "✗"
            print(f"  {symbol} {check.replace('_', ' ').title()}: {'PASS' if status else 'FAIL'}")
    
    print(f"\nTotal: {passed}/{total} checks passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n✅ DATA QUALITY: EXCELLENT")
        print("✅ READY FOR MACHINE LEARNING")
        checklist["final_status"] = "PASSED"
        return True, checklist
    elif passed >= total * 0.95:
        print("\n⚠️  DATA QUALITY: GOOD (but review failures)")
        checklist["final_status"] = "PASSED_WITH_WARNINGS"
        return True, checklist
    else:
        print("\n✗ DATA QUALITY: FAILED - DO NOT USE")
        checklist["final_status"] = "FAILED"
        return False, checklist


if __name__ == '__main__':
    success, results = validate_single_extraction()
    
    # Save results
    report_file = f"validation_check_{os.path.basename(__file__)}.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nReport saved to: {report_file}\n")
    sys.exit(0 if success else 1)
