"""
PDF extraction helper using PyMuPDF
Handles both vector and raster ECG formats
"""
import fitz
import io
from PIL import Image

def split_panels(pdf_bytes):
    """
    Extract ECG panels from PDF
    Returns SVG for vector ECGs or PIL Image for raster
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    
    # Check for vector drawings
    drawings = page.get_drawings()
    if drawings:
        # Vector ECG - preserve fidelity with SVG
        svg = page.get_svg_image()
        return svg
    
    # Raster fallback - use high DPI
    pix = page.get_pixmap(dpi=300)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    return img
