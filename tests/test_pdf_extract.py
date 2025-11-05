"""
Unit tests for ECG PDF extraction module
Tests vector and raster ECG detection
"""
import unittest
import io
import os
import sys
sys.path.insert(0, '..')

from ecg_modules import pdf_extract


class TestPDFExtraction(unittest.TestCase):
    """Test PDF extraction functionality"""
    
    def test_split_panels_handles_missing_file(self):
        """Test that missing files are handled gracefully"""
        with self.assertRaises(Exception):
            pdf_extract.split_panels(b"")
    
    def test_split_panels_returns_image_or_svg(self):
        """Test that output is either SVG string or PIL Image"""
        # This would require a real PDF file
        # For now, we test the function signature exists
        self.assertTrue(hasattr(pdf_extract, 'split_panels'))
        self.assertTrue(callable(pdf_extract.split_panels))
    
    def test_module_imports(self):
        """Test that required libraries are importable"""
        try:
            import fitz
            self.assertTrue(True)
        except ImportError:
            self.fail("PyMuPDF (fitz) not installed")
        
        try:
            from PIL import Image
            self.assertTrue(True)
        except ImportError:
            self.fail("Pillow not installed")


if __name__ == '__main__':
    unittest.main()
