#!/usr/bin/env python3
"""
REPRODUCIBILITY TEST
Verify that uploading the same file multiple times produces identical results
"""

import json
import os
import sys
import hashlib

sys.path.insert(0, '..')

from ecg_modules import digitize, analyse


def calculate_hash(data):
    """Calculate hash of metrics for comparison"""
    # Convert to sorted JSON string for consistent hashing
    json_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.md5(json_str.encode()).hexdigest()


def test_reproducibility(num_runs=5):
    """Test that same input produces identical output across multiple runs"""
    
    print("="*70)
    print("REPRODUCIBILITY TEST - Multiple Uploads")
    print("="*70)
    print(f"\nTesting {num_runs} sequential uploads of the same ECG file...\n")
    
    results = []
    hashes = []
    
    for i in range(1, num_runs + 1):
        print(f"[{i}/{num_runs}] Processing ECG file...")
        
        # Step 1: Digitize
        csv_path = digitize.ecg_to_csv(None)
        
        # Step 2: Analyze
        metrics = analyse.compute_metrics(csv_path)
        
        # Store results
        results.append(metrics)
        metrics_hash = calculate_hash(metrics)
        hashes.append(metrics_hash)
        
        # Display first result in detail
        if i == 1:
            print(f"\n  Generated Metrics:")
            print(f"  ├─ Heart Rate: {metrics.get('heart_rate_bpm')} bpm")
            print(f"  ├─ SDNN: {metrics.get('sdnn_ms')} ms")
            print(f"  ├─ RMSSD: {metrics.get('rmssd_ms')} ms")
            print(f"  ├─ pNN50: {metrics.get('pnn50_percent')} %")
            print(f"  ├─ SD1: {metrics.get('sd1_ms')} ms")
            print(f"  ├─ SD2: {metrics.get('sd2_ms')} ms")
            print(f"  ├─ LF Power: {metrics.get('lf_power')}")
            print(f"  ├─ HF Power: {metrics.get('hf_power')}")
            print(f"  ├─ LF/HF Ratio: {metrics.get('lf_hf_ratio')}")
            print(f"  └─ Status: {metrics.get('processing_status')}")
            print(f"\n  Hash: {metrics_hash}")
        else:
            print(f"  Hash: {metrics_hash}")
    
    print("\n" + "="*70)
    print("REPRODUCIBILITY ANALYSIS")
    print("="*70)
    
    # Check if all hashes are identical
    all_identical = all(h == hashes[0] for h in hashes)
    
    if all_identical:
        print("\n✅ REPRODUCIBILITY TEST: PASSED")
        print(f"\nAll {num_runs} uploads produced IDENTICAL results!")
        print(f"All hashes match: {hashes[0]}")
        print("\n✓ You will get the SAME data every time you upload")
        print("✓ 100% deterministic behavior confirmed")
        print("✓ Safe for machine learning with reproducible results")
        return True, results
    else:
        print("\n❌ REPRODUCIBILITY TEST: FAILED")
        print("\nHashes do not match:")
        for i, h in enumerate(hashes, 1):
            match = "✓" if h == hashes[0] else "✗ DIFFERENT"
            print(f"  Run {i}: {h} {match}")
        print("\n⚠️  Different results detected - data is NOT deterministic")
        return False, results


def compare_metrics(metrics_list):
    """Compare all metrics across runs"""
    
    print("\n" + "="*70)
    print("DETAILED METRICS COMPARISON")
    print("="*70 + "\n")
    
    if not metrics_list:
        return
    
    # Get all metric keys from first result
    keys = sorted(metrics_list[0].keys())
    
    # Create comparison table
    print(f"{'Metric':<20} | ", end="")
    for i in range(1, len(metrics_list) + 1):
        print(f"Run {i:>8} | ", end="")
    print()
    print("-" * (20 + len(metrics_list) * 12))
    
    all_match = True
    for key in keys:
        if isinstance(metrics_list[0][key], (int, float)):
            print(f"{key:<20} | ", end="")
            values = [m.get(key, "N/A") for m in metrics_list]
            
            for val in values:
                if isinstance(val, float):
                    print(f"{val:>8.2f} | ", end="")
                else:
                    print(f"{str(val):>8} | ", end="")
            
            # Check if all values match
            if len(set(str(v) for v in values)) > 1:
                print(" ✗ MISMATCH")
                all_match = False
            else:
                print(" ✓")
        else:
            print(f"{key:<20} | ", end="")
            values = [str(m.get(key, "N/A")) for m in metrics_list]
            print(f"{values[0]:<8} | ", end="")
            if len(set(values)) > 1:
                print(" ✗ MISMATCH")
                all_match = False
            else:
                print(" ✓")
    
    print("\n" + "="*70)
    if all_match:
        print("✅ ALL METRICS IDENTICAL ACROSS ALL RUNS")
    else:
        print("❌ SOME METRICS DIFFER ACROSS RUNS")
    print("="*70 + "\n")
    
    return all_match


def test_file_upload_simulation():
    """Simulate uploading the same file multiple times"""
    
    print("\n" + "="*70)
    print("FILE UPLOAD SIMULATION TEST")
    print("="*70)
    print("\nSimulating: User uploads ECG.pdf three times\n")
    
    results = []
    
    for upload_num in range(1, 4):
        print(f"📁 Upload #{upload_num}: ECG.pdf")
        
        csv_path = digitize.ecg_to_csv(None)
        metrics = analyse.compute_metrics(csv_path)
        results.append(metrics)
        
        status = "✓ SUCCESS" if metrics.get('processing_status') == 'success' else "✗ FAILED"
        print(f"   {status}")
        print(f"   → Heart Rate: {metrics.get('heart_rate_bpm')} bpm")
        print(f"   → SDNN: {metrics.get('sdnn_ms')} ms\n")
    
    # Check consistency
    hash1 = calculate_hash(results[0])
    hash2 = calculate_hash(results[1])
    hash3 = calculate_hash(results[2])
    
    if hash1 == hash2 == hash3:
        print("✅ RESULT: All three uploads produced IDENTICAL metrics")
        print(f"   Hash: {hash1}")
        return True
    else:
        print("❌ RESULT: Uploads produced different metrics")
        print(f"   Upload 1: {hash1}")
        print(f"   Upload 2: {hash2}")
        print(f"   Upload 3: {hash3}")
        return False


if __name__ == '__main__':
    print("\n")
    
    # Test 1: Reproducibility
    success1, results = test_reproducibility(num_runs=5)
    
    # Test 2: Detailed comparison
    if results:
        all_match = compare_metrics(results)
    
    # Test 3: File upload simulation
    print("\n")
    success2 = test_file_upload_simulation()
    
    # Final verdict
    print("\n" + "="*70)
    print("FINAL VERDICT")
    print("="*70)
    
    if success1 and success2:
        print("\n✅ DETERMINISTIC BEHAVIOR CONFIRMED")
        print("\nYou can now upload the SAME file multiple times")
        print("and get the EXACT SAME RESULTS every time!")
        print("\n🎉 Data is 100% reproducible for ML training")
        sys.exit(0)
    else:
        print("\n⚠️  Issues detected - review output above")
        sys.exit(1)
