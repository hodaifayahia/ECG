"""
Medical Report Extractor - Extract structured data from French coronarography reports
Handles PDF text extraction and NLP parsing for clinical data
"""
import fitz  # PyMuPDF
import re
from datetime import datetime
from typing import Dict, Tuple, Any, Optional


class MedicalReportExtractor:
    """Extract structured data from French coronarography reports"""

    def __init__(self):
        # Regex patterns for French medical terminology
        self.patterns = {
            'patient_name': r'Nom\s*:\s*([A-ZÀ-Ü]+).*?Prénom\s*:\s*([A-ZÀ-Üa-zà-ü]+)',
            'age': r'Age\s*:\s*(\d+)',
            'gender': r'Sexe\s*:\s*(M|F|H|Homme|Femme)',
            'exam_date': r'Date.*?:\s*(\d{2}[-/]\d{2}[-/]\d{4})',
            'indication': r'Indication\s*:\s*(.+?)\.', 
            'catheter_size': r'(\d)F',
            'access_radial': r'voie\s+radiale',
            'access_femoral': r'voie\s+f[eé]morale',
            'timi_flow': r'TIMI\s*(?:=\s*)?([I]{1,3})',
            'stenosis_severe': r'sténose\s+(?:très\s+)?serrée',
            'stenosis_moderate': r'sténose\s+modérée',
            'stenosis_mild': r'sténose\s+(?:légère|minime)',
            'occlusion': r'occlu[se]',
            'tritronculaire': r'tritronculaire',
            'bitroncular': r'bitronculaire',
            'monotronculaire': r'monotronculaire',
            'bypass': r'[Pp]ontage|CABG',
            'angioplasty': r'[Aa]ngioplastie|PCI',
            'atheroma': r'athérome|athéroscl[eé]rose',
            'infiltration': r'infiltration',
            'trunk': r'tronc\s+commun',
            'iva': r'IVA|inter-ventriculaire\s+ant[eé]rieure',
            'diagonal': r'diagonale',
            'circumflex': r'circonflexe|CX',
            'right_coronary': r'coronaire\s+droite|CD',
            'marginal': r'marginale',
            'collateral': r'collatérale|r[eé]seau\s+de\s+suppléance',
            'ischemic_heart': r'cardiopathie\s+isch[eé]mique',
            'scintigraphy': r'scintigraphie',
            'scanner': r'scanner|coroscanner',
            'diabetes': r'diab[eè]te',
            'hypertension': r'HTA|hypertension',
            'smoking': r'tabagisme|fumeur',
            'previous_mi': r'IDM|infarctus',
        }

    def extract_from_pdf(self, pdf_path_or_bytes) -> Tuple[str, Dict[str, Any]]:
        """
        Extract all text and structured data from PDF
        
        Args:
            pdf_path_or_bytes: Path to PDF file or bytes object
            
        Returns:
            Tuple of (full_text, structured_data)
        """
        # Open PDF
        if isinstance(pdf_path_or_bytes, bytes):
            doc = fitz.open(stream=pdf_path_or_bytes, filetype="pdf")
        else:
            doc = fitz.open(pdf_path_or_bytes)
        
        # Extract full text
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        
        doc.close()
        
        # Parse structured data
        structured_data = self._parse_medical_report(full_text)
        
        return full_text, structured_data

    def _parse_medical_report(self, text: str) -> Dict[str, Any]:
        """Parse French medical report text into structured data"""
        data = {}
        
        # Extract patient demographics
        name_match = re.search(self.patterns['patient_name'], text, re.IGNORECASE)
        if name_match:
            data['last_name'] = name_match.group(1)
            data['first_name'] = name_match.group(2)
        
        age_match = re.search(self.patterns['age'], text)
        if age_match:
            data['age'] = int(age_match.group(1))
        
        # Extract gender
        gender_match = re.search(self.patterns['gender'], text, re.IGNORECASE)
        if gender_match:
            gender = gender_match.group(1).upper()
            data['gender'] = 'M' if gender in ['M', 'H', 'HOMME'] else 'F'
        
        # Extract exam date
        date_match = re.search(self.patterns['exam_date'], text)
        if date_match:
            data['exam_date'] = date_match.group(1)
        
        # Extract clinical indication
        data['indication_ischemic_heart_disease'] = bool(re.search(
            self.patterns['ischemic_heart'], text, re.IGNORECASE))
        data['indication_positive_scintigraphy'] = bool(re.search(
            self.patterns['scintigraphy'], text, re.IGNORECASE))
        data['indication_positive_scanner'] = bool(re.search(
            self.patterns['scanner'], text, re.IGNORECASE))
        
        # Extract procedure details
        if re.search(self.patterns['access_radial'], text, re.IGNORECASE):
            data['access_point'] = 'radial'
        elif re.search(self.patterns['access_femoral'], text, re.IGNORECASE):
            data['access_point'] = 'femoral'
        
        catheter_match = re.search(self.patterns['catheter_size'], text)
        if catheter_match:
            data['catheter_size'] = float(catheter_match.group(1))
        
        # Extract clinical findings
        data['stenosis_present'] = bool(re.search(
            self.patterns['stenosis_severe'], text, re.IGNORECASE))
        data['occlusion_present'] = bool(re.search(
            self.patterns['occlusion'], text, re.IGNORECASE))
        data['atheroma_present'] = bool(re.search(
            self.patterns['atheroma'], text, re.IGNORECASE))
        
        # Extract diagnosis
        data['three_vessel_disease'] = bool(re.search(
            self.patterns['tritronculaire'], text, re.IGNORECASE))
        data['two_vessel_disease'] = bool(re.search(
            self.patterns['bitroncular'], text, re.IGNORECASE))
        data['one_vessel_disease'] = bool(re.search(
            self.patterns['monotronculaire'], text, re.IGNORECASE))
        
        # Extract treatment decision
        data['requires_bypass'] = bool(re.search(
            self.patterns['bypass'], text, re.IGNORECASE))
        data['requires_angioplasty'] = bool(re.search(
            self.patterns['angioplasty'], text, re.IGNORECASE))
        
        # Extract TIMI flow
        timi_match = re.search(self.patterns['timi_flow'], text)
        if timi_match:
            timi_roman = timi_match.group(1)
            data['timi_flow'] = len(timi_roman)  # I=1, II=2, III=3
        
        # Count stenoses and occlusions
        data['stenosis_count'] = len(re.findall(
            self.patterns['stenosis_severe'], text, re.IGNORECASE))
        data['occlusion_count'] = len(re.findall(
            self.patterns['occlusion'], text, re.IGNORECASE))
        
        # Parse coronary sections
        data['left_coronary'] = self._parse_coronary_section(text, 'gauche')
        data['right_coronary'] = self._parse_coronary_section(text, 'droite')
        
        # Extract risk factors
        data['risk_hypertension'] = bool(re.search(
            self.patterns['hypertension'], text, re.IGNORECASE))
        data['risk_diabetes'] = bool(re.search(
            self.patterns['diabetes'], text, re.IGNORECASE))
        data['risk_smoking'] = bool(re.search(
            self.patterns['smoking'], text, re.IGNORECASE))
        data['risk_previous_mi'] = bool(re.search(
            self.patterns['previous_mi'], text, re.IGNORECASE))
        
        # Calculate severity scores
        data['total_stenosis_score'] = self._calculate_stenosis_score(data)
        data['severity_level'] = self._determine_severity_level(data)
        data['vessel_involvement_score'] = self._calculate_vessel_involvement(data)
        
        return data

    def _parse_coronary_section(self, text: str, side: str) -> Dict[str, Any]:
        """Parse left or right coronary findings"""
        coronary_data = {
            'atheroma': False,
            'stenosis_present': False,
            'stenosis_severity': 0,
            'occlusion_present': False,
            'collateral_network': False
        }
        
        # Look for coronary artery mentions in context
        if side == 'gauche':
            # Check for trunk, IVA, diagonal, circumflex
            if re.search(self.patterns['trunk'], text, re.IGNORECASE):
                coronary_data['trunk_mentioned'] = True
            if re.search(self.patterns['iva'], text, re.IGNORECASE):
                coronary_data['iva_mentioned'] = True
            if re.search(self.patterns['diagonal'], text, re.IGNORECASE):
                coronary_data['diagonal_mentioned'] = True
            if re.search(self.patterns['circumflex'], text, re.IGNORECASE):
                coronary_data['circumflex_mentioned'] = True
        else:
            # Right coronary
            if re.search(self.patterns['right_coronary'], text, re.IGNORECASE):
                coronary_data['right_coronary_mentioned'] = True
        
        # Check for atheroma
        if re.search(self.patterns['atheroma'], text, re.IGNORECASE):
            coronary_data['atheroma'] = True
        
        # Check for stenosis
        if re.search(self.patterns['stenosis_severe'], text, re.IGNORECASE):
            coronary_data['stenosis_present'] = True
            coronary_data['stenosis_severity'] = 3
        elif re.search(self.patterns['stenosis_moderate'], text, re.IGNORECASE):
            coronary_data['stenosis_present'] = True
            coronary_data['stenosis_severity'] = 2
        elif re.search(self.patterns['stenosis_mild'], text, re.IGNORECASE):
            coronary_data['stenosis_present'] = True
            coronary_data['stenosis_severity'] = 1
        
        # Check for occlusion
        if re.search(self.patterns['occlusion'], text, re.IGNORECASE):
            coronary_data['occlusion_present'] = True
        
        # Check for collateral network
        if re.search(self.patterns['collateral'], text, re.IGNORECASE):
            coronary_data['collateral_network'] = True
        
        return coronary_data

    def _calculate_stenosis_score(self, data: Dict[str, Any]) -> float:
        """Calculate numerical severity score"""
        score = 0.0
        
        # Count stenoses (severe = 2 points, moderate = 1 point)
        score += data.get('stenosis_count', 0) * 2
        
        # Count occlusions (3 points each)
        score += data.get('occlusion_count', 0) * 3
        
        # Three vessel disease bonus
        if data.get('three_vessel_disease'):
            score += 5
        elif data.get('two_vessel_disease'):
            score += 3
        elif data.get('one_vessel_disease'):
            score += 1
        
        return score

    def _determine_severity_level(self, data: Dict[str, Any]) -> str:
        """Determine severity level based on findings"""
        score = data.get('total_stenosis_score', 0)
        
        if score >= 10:
            return 'severe'
        elif score >= 5:
            return 'moderate'
        else:
            return 'mild'

    def _calculate_vessel_involvement(self, data: Dict[str, Any]) -> int:
        """Calculate number of vessels affected (0-3)"""
        if data.get('three_vessel_disease'):
            return 3
        elif data.get('two_vessel_disease'):
            return 2
        elif data.get('one_vessel_disease'):
            return 1
        else:
            # Count from stenosis data if available
            count = 0
            if data.get('stenosis_count', 0) > 0:
                count = min(3, data.get('stenosis_count', 0))
            return count
