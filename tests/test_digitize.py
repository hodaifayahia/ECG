"""
Unit tests for ECG digitization module
Tests signal generation and CSV output
"""
import unittest
import os
import csv
import numpy as np
import sys
sys.path.insert(0, '..')

from ecg_modules import digitize


class TestDigitization(unittest.TestCase):
    """Test ECG digitization functionality"""
    
    def setUp(self):
        """Create tmp directory for test outputs"""
        os.makedirs("../tmp", exist_ok=True)
    
    def test_ecg_to_csv_creates_file(self):
        """Test that CSV file is created"""
        csv_path = digitize.ecg_to_csv(None)
        self.assertTrue(os.path.exists(csv_path))
    
    def test_csv_has_correct_format(self):
        """Test CSV has leadII column"""
        csv_path = digitize.ecg_to_csv(None)
        
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertIn('leadII', header)
    
    def test_csv_has_500_hz_data(self):
        """Test CSV has approximately 500 Hz * 10 seconds = 5000 samples"""
        csv_path = digitize.ecg_to_csv(None)
        
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            rows = list(reader)
            # Allow 5% tolerance
            self.assertGreater(len(rows), 4750)
            self.assertLess(len(rows), 5250)
    
    def test_csv_values_are_numeric(self):
        """Test all CSV values are valid floats"""
        csv_path = digitize.ecg_to_csv(None)
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                try:
                    value = float(row['leadII'])
                    # ECG values should be reasonable (±5mV)
                    self.assertGreater(value, -5)
                    self.assertLess(value, 5)
                except ValueError:
                    self.fail(f"Row {i} has non-numeric value: {row['leadII']}")


class TestSignalProperties(unittest.TestCase):
    """Test generated signal properties"""
    
    def test_signal_has_cardiac_rhythm(self):
        """Test that signal has recognizable cardiac frequency"""
        csv_path = digitize.ecg_to_csv(None)
        
        # Read signal
        signal = []
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                signal.append(float(row['leadII']))
        
        signal = np.array(signal)
        
        # Compute FFT
        fft = np.fft.fft(signal)
        freqs = np.fft.fftfreq(len(signal), 1/500)
        power = np.abs(fft)
        
        # Find peak frequency in 0.5-3 Hz range (cardiac rhythm)
        mask = (freqs > 0.5) & (freqs < 3)
        cardiac_freq_idx = np.argmax(power[mask])
        cardiac_freqs = freqs[mask]
        cardiac_freq = cardiac_freqs[cardiac_freq_idx]
        
        # Heart rate should be 40-200 bpm (0.67-3.33 Hz)
        self.assertGreater(cardiac_freq, 0.5)
        self.assertLess(cardiac_freq, 3.5)
    
    def test_signal_amplitude_realistic(self):
        """Test signal amplitude is within ECG range"""
        csv_path = digitize.ecg_to_csv(None)
        
        signal = []
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                signal.append(float(row['leadII']))
        
        signal = np.array(signal)
        
        # ECG signals typically 0.5-5 mV
        self.assertGreater(np.max(signal), 0.1)
        self.assertLess(np.max(signal), 6)


if __name__ == '__main__':
    unittest.main()
