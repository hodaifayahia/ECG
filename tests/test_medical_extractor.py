"""
Test Medical Text Extractor Module
Tests extraction of clinical data from French coronarography reports
"""
import unittest
import sys
import os

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(current_dir))

from ecg_modules.medical_text_extractor import MedicalReportExtractor


class TestMedicalTextExtractor(unittest.TestCase):
    """Test medical report extraction functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = MedicalReportExtractor()
    
    def test_extractor_initialization(self):
        """Test that extractor initializes correctly"""
        self.assertIsNotNone(self.extractor)
        self.assertIsNotNone(self.extractor.patterns)
        self.assertIn('patient_name', self.extractor.patterns)
        self.assertIn('stenosis_severe', self.extractor.patterns)
    
    def test_pattern_matching_stenosis(self):
        """Test stenosis pattern detection"""
        test_text = "L'IVA présente une sténose serrée au niveau proximal."
        import re
        match = re.search(self.extractor.patterns['stenosis_severe'], test_text, re.IGNORECASE)
        self.assertIsNotNone(match)
    
    def test_pattern_matching_occlusion(self):
        """Test occlusion pattern detection"""
        test_text = "La coronaire droite est occluse à son segment moyen."
        import re
        match = re.search(self.extractor.patterns['occlusion'], test_text, re.IGNORECASE)
        self.assertIsNotNone(match)
    
    def test_pattern_matching_tritronculaire(self):
        """Test three-vessel disease detection"""
        test_text = "Conclusion: Maladie coronaire tritronculaire."
        import re
        match = re.search(self.extractor.patterns['tritronculaire'], test_text, re.IGNORECASE)
        self.assertIsNotNone(match)
    
    def test_parse_medical_report_basic(self):
        """Test basic medical report parsing"""
        test_text = """
        Patient: Nom: DUPONT Prénom: Jean
        Age: 65
        Sexe: M
        Indication: cardiopathie ischémique
        
        Résultats:
        - IVA: sténose serrée proximale
        - Coronaire droite: occlusion
        - Conclusion: tritronculaire
        - Traitement: pontage coronaire
        """
        
        data = self.extractor._parse_medical_report(test_text)
        
        # Check demographics
        self.assertEqual(data.get('last_name'), 'DUPONT')
        self.assertEqual(data.get('first_name'), 'Jean')
        self.assertEqual(data.get('age'), 65)
        self.assertEqual(data.get('gender'), 'M')
        
        # Check findings
        self.assertTrue(data.get('indication_ischemic_heart_disease'))
        self.assertTrue(data.get('stenosis_present'))
        self.assertTrue(data.get('occlusion_present'))
        self.assertTrue(data.get('three_vessel_disease'))
        
        # Check treatment
        self.assertTrue(data.get('requires_bypass'))
        
        # Check scores
        self.assertGreater(data.get('total_stenosis_score', 0), 0)
        self.assertEqual(data.get('severity_level'), 'severe')
    
    def test_severity_calculation(self):
        """Test severity score calculation"""
        data = {
            'stenosis_count': 2,
            'occlusion_count': 1,
            'three_vessel_disease': True
        }
        
        score = self.extractor._calculate_stenosis_score(data)
        # 2 stenoses * 2 + 1 occlusion * 3 + 3-vessel disease * 5 = 12
        self.assertEqual(score, 12.0)
        
        severity = self.extractor._determine_severity_level({'total_stenosis_score': 12})
        self.assertEqual(severity, 'severe')
    
    def test_severity_levels(self):
        """Test different severity levels"""
        # Mild
        mild_data = {'total_stenosis_score': 3}
        self.assertEqual(self.extractor._determine_severity_level(mild_data), 'mild')
        
        # Moderate
        moderate_data = {'total_stenosis_score': 7}
        self.assertEqual(self.extractor._determine_severity_level(moderate_data), 'moderate')
        
        # Severe
        severe_data = {'total_stenosis_score': 12}
        self.assertEqual(self.extractor._determine_severity_level(severe_data), 'severe')
    
    def test_vessel_involvement_calculation(self):
        """Test vessel involvement score"""
        # Three vessel disease
        data1 = {'three_vessel_disease': True}
        self.assertEqual(self.extractor._calculate_vessel_involvement(data1), 3)
        
        # Two vessel disease
        data2 = {'two_vessel_disease': True}
        self.assertEqual(self.extractor._calculate_vessel_involvement(data2), 2)
        
        # One vessel disease
        data3 = {'one_vessel_disease': True}
        self.assertEqual(self.extractor._calculate_vessel_involvement(data3), 1)
    
    def test_coronary_section_parsing(self):
        """Test coronary artery section parsing"""
        test_text = """
        Coronaire gauche:
        - Tronc commun sans lésion
        - IVA: athérome diffus, sténose modérée proximale
        - Circonflexe: sténose serrée, réseau de suppléance
        """
        
        left_coronary = self.extractor._parse_coronary_section(test_text, 'gauche')
        
        self.assertTrue(left_coronary.get('atheroma'))
        self.assertTrue(left_coronary.get('stenosis_present'))
        self.assertGreater(left_coronary.get('stenosis_severity', 0), 0)
        self.assertTrue(left_coronary.get('collateral_network'))
    
    def test_risk_factors_extraction(self):
        """Test extraction of cardiovascular risk factors"""
        test_text = """
        Antécédents: HTA, diabète type 2, tabagisme actif
        Histoire familiale: IDM chez le père
        """
        
        data = self.extractor._parse_medical_report(test_text)
        
        self.assertTrue(data.get('risk_hypertension'))
        self.assertTrue(data.get('risk_diabetes'))
        self.assertTrue(data.get('risk_smoking'))
        self.assertTrue(data.get('risk_previous_mi'))
    
    def test_timi_flow_extraction(self):
        """Test TIMI flow grade extraction"""
        # TIMI III
        text1 = "Flux TIMI III en aval"
        data1 = self.extractor._parse_medical_report(text1)
        self.assertEqual(data1.get('timi_flow'), 3)
        
        # TIMI II
        text2 = "Flux TIMI II"
        data2 = self.extractor._parse_medical_report(text2)
        self.assertEqual(data2.get('timi_flow'), 2)
        
        # TIMI I
        text3 = "Flux TIMI I"
        data3 = self.extractor._parse_medical_report(text3)
        self.assertEqual(data3.get('timi_flow'), 1)


class TestClinicalDataValidation(unittest.TestCase):
    """Test validation of extracted clinical data"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = MedicalReportExtractor()
    
    def test_age_validation(self):
        """Test age extraction and validation"""
        test_text = "Age: 72"
        data = self.extractor._parse_medical_report(test_text)
        self.assertEqual(data.get('age'), 72)
        self.assertIsInstance(data.get('age'), int)
    
    def test_gender_parsing(self):
        """Test gender parsing variations"""
        # Male variations
        for text in ["Sexe: M", "Sexe: H", "Sexe: Homme"]:
            data = self.extractor._parse_medical_report(text)
            self.assertEqual(data.get('gender'), 'M')
        
        # Female
        data = self.extractor._parse_medical_report("Sexe: F")
        self.assertEqual(data.get('gender'), 'F')
    
    def test_catheter_size_extraction(self):
        """Test catheter size extraction"""
        test_text = "Cathéter 6F utilisé via voie radiale"
        data = self.extractor._parse_medical_report(test_text)
        self.assertEqual(data.get('catheter_size'), 6.0)
    
    def test_access_point_detection(self):
        """Test access point (radial/femoral) detection"""
        # Radial
        text1 = "Abord par voie radiale droite"
        data1 = self.extractor._parse_medical_report(text1)
        self.assertEqual(data1.get('access_point'), 'radial')
        
        # Femoral
        text2 = "Abord par voie fémorale"
        data2 = self.extractor._parse_medical_report(text2)
        self.assertEqual(data2.get('access_point'), 'femoral')


if __name__ == '__main__':
    unittest.main()
