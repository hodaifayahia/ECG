"""
Reproducibility validation test
Ensures same input produces same output (critical for ML)
"""
import unittest
import hashlib
import json
import sys
sys.path.insert(0, '..')

from ecg_modules import digitize, analyse


def calculate_hash(data):
    """Calculate hash of metrics"""
    json_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.md5(json_str.encode()).hexdigest()


class TestReproducibility(unittest.TestCase):
    """Test that results are reproducible (deterministic)"""
    
    def test_same_result_on_repeat_run(self):
        """Test that same file produces same result"""
        # Generate metrics twice
        csv1 = digitize.ecg_to_csv(None)
        metrics1 = analyse.compute_metrics(csv1)
        
        csv2 = digitize.ecg_to_csv(None)
        metrics2 = analyse.compute_metrics(csv2)
        
        # Check hashes match
        hash1 = calculate_hash(metrics1)
        hash2 = calculate_hash(metrics2)
        
        self.assertEqual(hash1, hash2, "Results not reproducible - hashes differ")
    
    def test_metrics_identical_across_5_runs(self):
        """Test 5 consecutive runs produce identical results"""
        hashes = []
        metrics_list = []
        
        for _ in range(5):
            csv_path = digitize.ecg_to_csv(None)
            metrics = analyse.compute_metrics(csv_path)
            metrics_list.append(metrics)
            hashes.append(calculate_hash(metrics))
        
        # All hashes should be identical
        for h in hashes:
            self.assertEqual(h, hashes[0], "Hash mismatch - non-deterministic output")
    
    def test_all_metric_values_identical(self):
        """Test that all metric values are identical across runs"""
        metrics_run1 = analyse.compute_metrics(digitize.ecg_to_csv(None))
        metrics_run2 = analyse.compute_metrics(digitize.ecg_to_csv(None))
        metrics_run3 = analyse.compute_metrics(digitize.ecg_to_csv(None))
        
        # Compare numeric values
        for key in metrics_run1.keys():
            if isinstance(metrics_run1[key], (int, float)):
                val1 = metrics_run1[key]
                val2 = metrics_run2[key]
                val3 = metrics_run3[key]
                
                self.assertEqual(val1, val2, f"{key} differs between run 1 and 2")
                self.assertEqual(val2, val3, f"{key} differs between run 2 and 3")
    
    def test_heart_rate_consistent(self):
        """Test heart rate is consistent across runs"""
        hr_values = []
        for _ in range(3):
            metrics = analyse.compute_metrics(digitize.ecg_to_csv(None))
            hr_values.append(metrics['heart_rate_bpm'])
        
        # All should be identical
        self.assertEqual(hr_values[0], hr_values[1])
        self.assertEqual(hr_values[1], hr_values[2])
    
    def test_sdnn_consistent(self):
        """Test SDNN is consistent across runs"""
        sdnn_values = []
        for _ in range(3):
            metrics = analyse.compute_metrics(digitize.ecg_to_csv(None))
            sdnn_values.append(metrics['sdnn_ms'])
        
        # All should be identical
        self.assertEqual(sdnn_values[0], sdnn_values[1])
        self.assertEqual(sdnn_values[1], sdnn_values[2])
    
    def test_rmssd_consistent(self):
        """Test RMSSD is consistent across runs"""
        rmssd_values = []
        for _ in range(3):
            metrics = analyse.compute_metrics(digitize.ecg_to_csv(None))
            rmssd_values.append(metrics['rmssd_ms'])
        
        # All should be identical
        self.assertEqual(rmssd_values[0], rmssd_values[1])
        self.assertEqual(rmssd_values[1], rmssd_values[2])
    
    def test_deterministic_for_ml_training(self):
        """Test that data is deterministic (safe for ML training)"""
        # Simulate ML training with same data
        features_run1 = []
        features_run2 = []
        
        for _ in range(2):
            metrics = analyse.compute_metrics(digitize.ecg_to_csv(None))
            features = [
                metrics['heart_rate_bpm'],
                metrics['sdnn_ms'],
                metrics['rmssd_ms'],
                metrics['pnn50_percent'],
                metrics['pnn20_percent'],
                metrics['sd1_ms'],
                metrics['sd2_ms']
            ]
            features_run1.append(features)
        
        for _ in range(2):
            metrics = analyse.compute_metrics(digitize.ecg_to_csv(None))
            features = [
                metrics['heart_rate_bpm'],
                metrics['sdnn_ms'],
                metrics['rmssd_ms'],
                metrics['pnn50_percent'],
                metrics['pnn20_percent'],
                metrics['sd1_ms'],
                metrics['sd2_ms']
            ]
            features_run2.append(features)
        
        # All features should match
        for f1, f2 in zip(features_run1, features_run2):
            self.assertEqual(f1, f2, "ML features are not reproducible")


if __name__ == '__main__':
    unittest.main(verbosity=2)
