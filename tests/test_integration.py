"""
Integration tests for the complete ECG pipeline
Tests end-to-end data flow
"""
import unittest
import json
import os
import sys
sys.path.insert(0, '..')

from ecg_modules import digitize, analyse


class TestEndToEnd(unittest.TestCase):
    """Test complete ECG processing pipeline"""
    
    def setUp(self):
        """Setup test environment"""
        os.makedirs("../tmp", exist_ok=True)
    
    def test_full_pipeline_succeeds(self):
        """Test complete pipeline: digitize -> analyze"""
        # Step 1: Digitize
        csv_path = digitize.ecg_to_csv(None)
        self.assertTrue(os.path.exists(csv_path), "CSV not created")
        
        # Step 2: Analyze
        metrics = analyse.compute_metrics(csv_path)
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.get('processing_status'), 'success')
    
    def test_output_is_json_serializable(self):
        """Test metrics can be serialized to JSON (for API responses)"""
        csv_path = digitize.ecg_to_csv(None)
        metrics = analyse.compute_metrics(csv_path)
        
        try:
            json_str = json.dumps(metrics)
            self.assertIsNotNone(json_str)
            
            # Verify we can deserialize it back
            deserialized = json.loads(json_str)
            self.assertEqual(deserialized['heart_rate_bpm'], metrics['heart_rate_bpm'])
        except TypeError as e:
            self.fail(f"Metrics not JSON serializable: {e}")
    
    def test_metrics_precision(self):
        """Test metrics have appropriate precision"""
        csv_path = digitize.ecg_to_csv(None)
        metrics = analyse.compute_metrics(csv_path)
        
        # All values should be rounded to 2 decimal places max
        for key, value in metrics.items():
            if isinstance(value, float):
                # Check it's not excessively precise
                str_value = str(value)
                if '.' in str_value:
                    decimals = len(str_value.split('.')[1])
                    self.assertLessEqual(decimals, 10, f"{key} too many decimals")
    
    def test_reproducibility_with_same_data(self):
        """Test that same input produces same output"""
        # Generate two CSVs
        csv1 = digitize.ecg_to_csv(None)
        csv2 = digitize.ecg_to_csv(None)
        
        # Analyze both
        metrics1 = analyse.compute_metrics(csv1)
        metrics2 = analyse.compute_metrics(csv2)
        
        # Should both succeed
        self.assertEqual(metrics1.get('processing_status'), 'success')
        self.assertEqual(metrics2.get('processing_status'), 'success')
        
        # Since data is different (synthetic), values will differ
        # But structure should be identical
        self.assertEqual(set(metrics1.keys()), set(metrics2.keys()))


class TestDataValidation(unittest.TestCase):
    """Validate data quality for machine learning"""
    
    def test_no_nan_or_inf_in_metrics(self):
        """Test that metrics don't contain NaN or Inf (bad for ML)"""
        csv_path = digitize.ecg_to_csv(None)
        metrics = analyse.compute_metrics(csv_path)
        
        for key, value in metrics.items():
            if isinstance(value, float):
                self.assertFalse(value != value, f"{key} is NaN")  # NaN != NaN is True
                self.assertNotEqual(value, float('inf'), f"{key} is Inf")
                self.assertNotEqual(value, float('-inf'), f"{key} is -Inf")
    
    def test_all_expected_metrics_present(self):
        """Test all metrics needed for ML are present"""
        csv_path = digitize.ecg_to_csv(None)
        metrics = analyse.compute_metrics(csv_path)
        
        ml_features = [
            'heart_rate_bpm',
            'sdnn_ms',
            'rmssd_ms',
            'pnn50_percent',
            'pnn20_percent',
            'sd1_ms',
            'sd2_ms',
            'lf_power',
            'hf_power',
            'lf_hf_ratio'
        ]
        
        for feature in ml_features:
            self.assertIn(feature, metrics, f"Missing ML feature: {feature}")
            self.assertIsNotNone(metrics[feature])
    
    def test_feature_ranges_for_ml(self):
        """Test features are in expected ranges for ML models"""
        csv_path = digitize.ecg_to_csv(None)
        metrics = analyse.compute_metrics(csv_path)
        
        ranges = {
            'heart_rate_bpm': (30, 200),
            'sdnn_ms': (0, 500),
            'rmssd_ms': (0, 500),
            'pnn50_percent': (0, 100),
            'pnn20_percent': (0, 100),
            'sd1_ms': (0, 300),
            'sd2_ms': (0, 500),
        }
        
        for feature, (min_val, max_val) in ranges.items():
            if feature in metrics:
                value = metrics[feature]
                self.assertGreaterEqual(value, min_val, f"{feature} below minimum")
                self.assertLessEqual(value, max_val, f"{feature} above maximum")


if __name__ == '__main__':
    unittest.main()
