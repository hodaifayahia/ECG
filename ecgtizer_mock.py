"""
Mock ECGtizer module for testing without the full library
Simulates realistic ECG digitization with variation based on input
"""
import numpy as np
import os
import hashlib
import time

class MockSignal:
    """Mock signal object that mimics ECGtizer output"""
    def __init__(self, data):
        self.data = data
    
    def to_csv(self, path, index=False):
        """Save signal to CSV"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        
        import csv
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['leadII'])
            for value in self.data:
                writer.writerow([value])

def load(model_name):
    """Mock load function - returns a mock model"""
    return MockModel()

class MockModel:
    """Mock model that simulates ECG digitization with realistic variation"""
    def __call__(self, panel):
        """
        Simulate ECG digitization with variation based on input
        Each different input generates different realistic ECG data
        """
        # Generate unique seed based on input + time
        if panel is not None:
            # If panel is bytes (PDF content), hash it
            if isinstance(panel, bytes):
                seed = int(hashlib.md5(panel).hexdigest()[:8], 16)
            # If panel is a file path or other object
            else:
                seed = int(hashlib.md5(str(panel).encode() + str(time.time()).encode()).hexdigest()[:8], 16)
        else:
            # Use time-based seed for None input
            seed = int(time.time() * 1000000) % (2**32)
        
        # Set seed based on input
        np.random.seed(seed)
        
        # Generate 10 seconds of synthetic ECG data at 500 Hz
        duration = 10  # seconds
        sampling_rate = 500
        t = np.linspace(0, duration, sampling_rate * duration)
        
        # Randomized realistic heart rate (60-100 bpm)
        heart_rate = np.random.uniform(60, 100)
        hr_freq = heart_rate / 60  # Hz
        
        # Randomized HRV parameters
        hrv_variation = np.random.uniform(0.02, 0.08)  # Heart rate variability
        
        # Create ECG-like signal with realistic variation
        ecg = np.zeros(len(t))
        
        for i in range(len(t)):
            # Add beat-to-beat variation
            beat_variation = 1.0 + hrv_variation * np.sin(2 * np.pi * 0.1 * t[i])
            
            ecg[i] = (
                1.0 * np.sin(2 * np.pi * hr_freq * beat_variation * t[i]) +  # Main rhythm
                0.3 * np.sin(2 * np.pi * hr_freq * 2 * beat_variation * t[i]) +  # P-wave
                0.2 * np.sin(2 * np.pi * hr_freq * 3 * beat_variation * t[i]) +  # T-wave
                0.05 * np.random.randn()  # Baseline noise
            )
        
        # Add some baseline wander
        baseline_wander = 0.1 * np.sin(2 * np.pi * 0.2 * t)
        ecg += baseline_wander
        
        return MockSignal(ecg)
