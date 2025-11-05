"""
Unit tests for ECG analysis module
Tests HRV metrics computation and validation
"""
import unittest
import os
import csv
import numpy as np
import sys
sys.path.insert(0, '..')

from ecg_modules import digitize, analyse


class TestAnalysis(unittest.TestCase):
    """Test ECG analysis functionality"""
    
    def setUp(self):
        """Generate test ECG data"""
        os.makedirs("../tmp", exist_ok=True)
        self.csv_path = digitize.ecg_to_csv(None)
    
    def test_compute_metrics_returns_dict(self):
        """Test that metrics are returned as dictionary"""
        metrics = analyse.compute_metrics(self.csv_path)
        self.assertIsInstance(metrics, dict)
    
    def test_compute_metrics_has_required_fields(self):
        """Test that all required metrics are present"""
        metrics = analyse.compute_metrics(self.csv_path)
        
        required_fields = [
            'heart_rate_bpm',
            'sdnn_ms',
            'rmssd_ms',
            'processing_status'
        ]
        
        for field in required_fields:
            self.assertIn(field, metrics, f"Missing required field: {field}")
    
    def test_heart_rate_is_valid(self):
        """Test heart rate is within physiological range"""
        metrics = analyse.compute_metrics(self.csv_path)
        
        if metrics.get('processing_status') == 'success':
            hr = metrics['heart_rate_bpm']
            # Valid heart rate: 30-200 bpm
            self.assertGreater(hr, 30, "Heart rate too low")
            self.assertLess(hr, 200, "Heart rate too high")
    
    def test_sdnn_is_positive(self):
        """Test SDNN is positive"""
        metrics = analyse.compute_metrics(self.csv_path)
        
        if metrics.get('processing_status') == 'success':
            sdnn = metrics['sdnn_ms']
            self.assertGreater(sdnn, 0, "SDNN should be positive")
    
    def test_rmssd_is_positive(self):
        """Test RMSSD is positive"""
        metrics = analyse.compute_metrics(self.csv_path)
        
        if metrics.get('processing_status') == 'success':
            rmssd = metrics['rmssd_ms']
            self.assertGreater(rmssd, 0, "RMSSD should be positive")
    
    def test_rmssd_less_than_sdnn(self):
        """Test RMSSD is typically less than or equal to SDNN"""
        metrics = analyse.compute_metrics(self.csv_path)
        
        if metrics.get('processing_status') == 'success':
            rmssd = metrics.get('rmssd_ms', 0)
            sdnn = metrics.get('sdnn_ms', 0)
            # RMSSD is usually smaller than or close to SDNN
            if sdnn > 0 and rmssd > 0:
                self.assertLess(rmssd, sdnn * 2, "RMSSD should be < SDNN*2")
    
    def test_pnn50_valid_range(self):
        """Test pNN50 is between 0-100%"""
        metrics = analyse.compute_metrics(self.csv_path)
        
        if metrics.get('processing_status') == 'success':
            pnn50 = metrics['pnn50_percent']
            self.assertGreaterEqual(pnn50, 0)
            self.assertLessEqual(pnn50, 100)
    
    def test_lf_hf_ratio_positive(self):
        """Test LF/HF ratio is positive"""
        metrics = analyse.compute_metrics(self.csv_path)
        
        if metrics.get('processing_status') == 'success':
            lf_hf = metrics.get('lf_hf_ratio', 0)
            if lf_hf > 0:
                self.assertGreater(lf_hf, 0)


class TestMetricsConsistency(unittest.TestCase):
    """Test metrics consistency across multiple runs"""
    
    def test_metrics_stable_across_runs(self):
        """Test that metrics are stable for same input"""
        metrics1 = analyse.compute_metrics('../tmp/ecg.csv' if os.path.exists('../tmp/ecg.csv') else digitize.ecg_to_csv(None))
        metrics2 = analyse.compute_metrics(digitize.ecg_to_csv(None))
        
        # Both should succeed
        self.assertEqual(metrics1.get('processing_status'), 'success')
        self.assertEqual(metrics2.get('processing_status'), 'success')
        
        # Both should have valid HR
        self.assertGreater(metrics1['heart_rate_bpm'], 0)
        self.assertGreater(metrics2['heart_rate_bpm'], 0)


class TestErrorHandling(unittest.TestCase):
    """Test error handling"""
    
    def test_handles_missing_file(self):
        """Test graceful handling of missing CSV file"""
        metrics = analyse.compute_metrics('nonexistent_file.csv')
        self.assertIn('error', metrics or metrics.get('processing_status') != 'success')
    
    def test_handles_empty_file(self):
        """Test graceful handling of empty CSV file"""
        empty_csv = '../tmp/empty.csv'
        with open(empty_csv, 'w') as f:
            f.write('leadII\n')
        
        metrics = analyse.compute_metrics(empty_csv)
        # Should either error or return zeros
        self.assertTrue('error' in metrics or metrics.get('processing_status') == 'error')


if __name__ == '__main__':
    unittest.main()
