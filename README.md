# ECG PDF Analyzer

A lightweight Flask + JavaScript prototype that turns uploaded ECG PDFs into cleaned, clinically useful waveforms entirely in the browser and on the server with proven open-source tools.

## Features

- 📄 **PDF Extraction**: Vector and raster ECG detection using PyMuPDF
- 🔬 **Digitization**: 500 Hz signal extraction with ECGtizer
- 📊 **Analysis**: Comprehensive HRV metrics via NeuroKit2 and HeartPy
- 🌐 **Web Interface**: Clean, modern single-page application
- 🚀 **Lightweight**: Minimal dependencies, runs locally

## Project Structure

```
ecg_webapp/
├── app.py                 # Flask back-end
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── static/
│   ├── index.html         # Single-page UI
│   └── app.js             # PDF.js + fetch calls
└── ecg_modules/
    ├── __init__.py        # Module initialization
    ├── pdf_extract.py     # PyMuPDF helpers
    ├── digitize.py        # ECGtizer wrapper
    └── analyse.py         # NeuroKit2 / HeartPy analysis
```

## Installation

### 1. Create and activate virtual environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Install ECGtizer from GitHub

```bash
pip install git+https://github.com/alphanumericslab/ecgtizer.git
```

## Running the Application

```bash
python app.py
```

Then open your browser to: **http://localhost:5000**

## Usage

1. Click the upload area or drag-and-drop an ECG PDF file
2. Wait for processing (typically 10-30 seconds)
3. View computed metrics including:
   - Heart Rate Variability (HRV)
   - NN intervals (mean, SDNN, RMSSD)
   - Time-domain metrics
   - Frequency-domain metrics (via NeuroKit2)

## Key Technologies

- **PyMuPDF**: PDF parsing with vector/raster detection via `page.get_drawings()`
- **ECGtizer**: State-of-the-art digitization (Frag model, ~0.08 mV error, ~26 ms RR error)
- **NeuroKit2**: Comprehensive ECG cleaning, peak detection, and HRV analysis
- **HeartPy**: Lightweight fallback for resource-constrained environments
- **Flask**: Simple REST API backend
- **Vanilla JavaScript**: No-framework frontend with drag-and-drop support

## Clinical Metrics

The application computes 60+ metrics including:

- **Time-domain HRV**: SDNN, RMSSD, pNN50, NN intervals
- **Frequency-domain**: LF, HF, LF/HF ratio
- **Nonlinear**: SD1, SD2, DFA
- **Heart Rate**: Instantaneous and average

## Notes

- First run will download ECGtizer models (~100 MB)
- Supports both vector-based ECGs (high precision) and scanned images
- 300 DPI rasterization for optimal digitization quality
- Tmp directory is created automatically for intermediate files

## Troubleshooting

**ECGtizer not found:**
```bash
pip install git+https://github.com/alphanumericslab/ecgtizer.git
```

**Memory errors on low-resource devices:**
- HeartPy fallback will activate automatically
- Reduce PDF DPI in `pdf_extract.py` if needed

**Port 5000 already in use:**
Edit `app.py` and change the port number:
```python
app.run(debug=True, host="0.0.0.0", port=5001)
```

## License

MIT License - Feel free to use for research and clinical applications

## Contributing

Contributions welcome! Please submit issues and pull requests on GitHub.
