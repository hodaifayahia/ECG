"""
Test that different PDF files generate different ECG metrics
"""
import sys
sys.path.insert(0, '..')

from ecgtizer_mock import MockModel
from ecg_modules.digitize import ecg_to_csv
from ecg_modules.analyse import compute_metrics
import numpy as np

print("=" * 60)
print("Testing Mock ECGtizer Variation")
print("=" * 60)

model = MockModel()

# Test 1: Same input should give same results
print("\n1. Testing reproducibility (same input = same output):")
test_data = b"test_ecg_file_1"
signal1 = model(test_data)
signal2 = model(test_data)
print(f"   First run:  {signal1.data[:5]}")
print(f"   Second run: {signal2.data[:5]}")
print(f"   ✓ Same input = Same output: {np.array_equal(signal1.data, signal2.data)}")

# Test 2: Different inputs should give different results
print("\n2. Testing variation (different input = different output):")
test_data_a = b"ecg_patient_A_data_content"
test_data_b = b"ecg_patient_B_data_content"
test_data_c = b"ecg_patient_C_data_content"

signal_a = model(test_data_a)
signal_b = model(test_data_b)
signal_c = model(test_data_c)

print(f"   Patient A: {signal_a.data[:5]}")
print(f"   Patient B: {signal_b.data[:5]}")
print(f"   Patient C: {signal_c.data[:5]}")

different_ab = not np.array_equal(signal_a.data, signal_b.data)
different_bc = not np.array_equal(signal_b.data, signal_c.data)
different_ac = not np.array_equal(signal_a.data, signal_c.data)

print(f"   ✓ Different inputs = Different outputs: {different_ab and different_bc and different_ac}")

# Test 3: Full pipeline with metrics
print("\n3. Testing full pipeline (PDF → Metrics):")

results = []
for i, pdf_data in enumerate([test_data_a, test_data_b, test_data_c], 1):
    csv_path = ecg_to_csv(None, pdf_bytes=pdf_data)
    metrics = compute_metrics(csv_path)
    results.append({
        'patient': chr(64 + i),  # A, B, C
        'hr': metrics['heart_rate_bpm'],
        'sdnn': metrics['sdnn_ms'],
        'rmssd': metrics['rmssd_ms']
    })
    print(f"\n   Patient {chr(64 + i)}:")
    print(f"      HR: {metrics['heart_rate_bpm']:.2f} bpm")
    print(f"      SDNN: {metrics['sdnn_ms']:.2f} ms")
    print(f"      RMSSD: {metrics['rmssd_ms']:.2f} ms")

# Check all metrics are different
all_different = True
for i in range(len(results)):
    for j in range(i + 1, len(results)):
        if results[i]['hr'] == results[j]['hr']:
            all_different = False
            print(f"\n   ✗ Warning: Patient {results[i]['patient']} and {results[j]['patient']} have same HR")

if all_different:
    print(f"\n   ✓ All patients have DIFFERENT metrics!")
else:
    print(f"\n   ✗ Some patients have SAME metrics (problem!)")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
