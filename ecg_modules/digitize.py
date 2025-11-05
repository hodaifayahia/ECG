"""
Digitization wrapper using ECGtizer
Converts ECG images/vectors to 500 Hz CSV time series
Falls back to mock implementation if ECGtizer not installed
"""
try:
    import ecgtizer as et
    ECGTIZER_AVAILABLE = True
except ImportError:
    try:
        import sys
        sys.path.insert(0, '..')
        import ecgtizer_mock as et
        ECGTIZER_AVAILABLE = True
        print("Using mock ECGtizer for testing")
    except ImportError:
        ECGTIZER_AVAILABLE = False
        print("Warning: ecgtizer not installed and mock failed. Install with: pip install git+https://github.com/alphanumericslab/ecgtizer.git")

def ecg_to_csv(panel, pdf_bytes=None):
    """
    Convert ECG panel (SVG or Image) to CSV using ECGtizer
    
    Args:
        panel: ECG panel image/vector data
        pdf_bytes: Original PDF bytes (used by mock for variation)
    
    Returns:
        Path to generated CSV file
    """
    if not ECGTIZER_AVAILABLE:
        raise ImportError("ecgtizer is not installed. Please install it first.")
    
    # Load the Frag model (lowest Soft-DTW error)
    model = et.load("Frag")
    
    # Process the signal
    # If using mock and pdf_bytes provided, pass it for variation
    if hasattr(model, '__module__') and 'mock' in model.__module__:
        signal = model(pdf_bytes or panel)
    else:
        signal = model(panel)
    
    # Save to CSV
    csv_path = "tmp/ecg.csv"
    signal.to_csv(csv_path, index=False)
    
    return csv_path
