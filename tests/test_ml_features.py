"""
Test ML feature selection functionality
"""
import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ecg_modules import ml_features, digitize, analyse


class TestMLFeatures(unittest.TestCase):
    """Test feature selection"""
    
    def setUp(self):
        """Generate test metrics"""
        csv_path = digitize.ecg_to_csv(None)
        self.all_metrics = analyse.compute_metrics(csv_path)
    
    def test_basic_features_count(self):
        """Test that basic set has 5 features"""
        basic = ml_features.select_features(self.all_metrics, 'basic')
        self.assertEqual(len(basic), 5, "Basic set should have 5 features")
    
    def test_standard_features_count(self):
        """Test that standard set has 7 features"""
        standard = ml_features.select_features(self.all_metrics, 'standard')
        self.assertEqual(len(standard), 7, "Standard set should have 7 features")
    
    def test_complete_features_count(self):
        """Test that complete set has 10 features"""
        complete = ml_features.select_features(self.all_metrics, 'complete')
        self.assertEqual(len(complete), 10, "Complete set should have 10 features")
    
    def test_basic_features_are_subset(self):
        """Test that basic features are subset of standard"""
        basic = ml_features.select_features(self.all_metrics, 'basic')
        standard = ml_features.select_features(self.all_metrics, 'standard')
        basic_keys = set(basic.keys())
        standard_keys = set(standard.keys())
        self.assertTrue(basic_keys.issubset(standard_keys), 
                       "Basic should be subset of standard")
    
    def test_standard_features_are_subset(self):
        """Test that standard features are subset of complete"""
        standard = ml_features.select_features(self.all_metrics, 'standard')
        complete = ml_features.select_features(self.all_metrics, 'complete')
        standard_keys = set(standard.keys())
        complete_keys = set(complete.keys())
        self.assertTrue(standard_keys.issubset(complete_keys), 
                       "Standard should be subset of complete")
    
    def test_feature_values_preserved(self):
        """Test that feature values are not modified"""
        standard = ml_features.select_features(self.all_metrics, 'standard')
        for key, value in standard.items():
            self.assertEqual(value, self.all_metrics[key], 
                           f"Value for {key} should not be modified")
    
    def test_invalid_feature_set_raises_error(self):
        """Test that invalid feature set raises error"""
        with self.assertRaises(ValueError):
            ml_features.select_features(self.all_metrics, 'invalid_set')
    
    def test_get_feature_names(self):
        """Test getting feature names"""
        names = ml_features.get_feature_names('basic')
        self.assertEqual(len(names), 5)
        self.assertIn('heart_rate_bpm', names)
    
    def test_get_feature_count(self):
        """Test getting feature count"""
        count = ml_features.get_feature_count('standard')
        self.assertEqual(count, 7)
    
    def test_get_feature_info(self):
        """Test getting feature information"""
        info = ml_features.get_feature_info('basic')
        self.assertEqual(len(info), 5)
        self.assertIn('heart_rate_bpm', info)
        self.assertIn('unit', info['heart_rate_bpm'])
        self.assertIn('description', info['heart_rate_bpm'])
    
    def test_all_features_have_values(self):
        """Test that selected features have valid numeric values"""
        standard = ml_features.select_features(self.all_metrics, 'standard')
        for key, value in standard.items():
            self.assertIsNotNone(value, f"{key} should not be None")
            self.assertIsInstance(value, (int, float), 
                                f"{key} should be numeric, got {type(value)}")
            self.assertFalse(float('inf') == value, f"{key} should not be inf")
            # Check if not NaN
            import math
            self.assertFalse(math.isnan(value), f"{key} should not be NaN")
    
    def test_feature_sets_are_hierarchical(self):
        """Test that feature sets form a hierarchy: basic ⊂ standard ⊂ complete"""
        basic = set(ml_features.get_feature_names('basic'))
        standard = set(ml_features.get_feature_names('standard'))
        complete = set(ml_features.get_feature_names('complete'))
        
        # Basic is subset of standard
        self.assertTrue(basic.issubset(standard))
        # Standard is subset of complete
        self.assertTrue(standard.issubset(complete))
        # All are distinct
        self.assertGreater(len(standard), len(basic))
        self.assertGreater(len(complete), len(standard))


if __name__ == '__main__':
    unittest.main(verbosity=2)
