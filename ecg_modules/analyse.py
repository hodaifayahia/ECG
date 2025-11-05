"""
Analysis layer using HeartPy (Python 3.8 compatible)
Computes HRV metrics and ECG intervals
"""
import heartpy as hp
import numpy as np
from scipy import signal as scipy_signal
import csv

def compute_metrics(csv_path):
    """
    Compute comprehensive ECG metrics from digitized signal
    Returns dictionary of HRV and rhythm metrics
    """
    # Load the signal from CSV
    ecg_signal = []
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ecg_signal.append(float(row.get('leadII', 0)))
                except (ValueError, KeyError):
                    pass
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return {"error": f"Failed to read ECG data: {str(e)}"}
    
    if not ecg_signal:
        return {"error": "No ECG data found in file"}
    
    ecg_signal = np.array(ecg_signal)
    
    # Preprocessing: Bandpass filter to remove noise
    try:
        # Design bandpass filter (0.5-40 Hz for ECG)
        nyquist = 500 / 2
        low = 0.5 / nyquist
        high = 40 / nyquist
        b, a = scipy_signal.butter(2, [low, high], btype='band')
        ecg_signal = scipy_signal.filtfilt(b, a, ecg_signal)
    except Exception:
        pass  # Use raw signal if filtering fails
    
    # Process with HeartPy
    try:
        wd, measures = hp.process(ecg_signal, 500)
        
        # Extract key metrics
        metrics = {
            "heart_rate_bpm": round(measures.get("bpm", 0), 2),
            "ibi_ms": round(measures.get("ibi", 0), 2),
            "sdnn_ms": round(measures.get("sdnn", 0), 2),
            "rmssd_ms": round(measures.get("rmssd", 0), 2),
            "pnn50_percent": round(measures.get("pnn50", 0), 2),
            "pnn20_percent": round(measures.get("pnn20", 0), 2),
            "sd1_ms": round(measures.get("sd1", 0), 2),
            "sd2_ms": round(measures.get("sd2", 0), 2),
            "lf_power": round(measures.get("lf", 0), 2),
            "hf_power": round(measures.get("hf", 0), 2),
            "lf_hf_ratio": round(measures.get("lf/hf", 0), 2),
            "breathingrate": round(measures.get("breathingrate", 0), 2),
            "total_peaks": len(wd.get("peaklist", [])),
            "processing_status": "success"
        }
        
    except Exception as e:
        # Return error info if processing fails
        metrics = {
            "processing_status": "error",
            "error_message": str(e),
            "heart_rate_bpm": 0,
            "sdnn_ms": 0,
            "rmssd_ms": 0
        }
    
    return metrics
