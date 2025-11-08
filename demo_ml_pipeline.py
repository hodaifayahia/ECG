"""
Demo Script: Medical Data Extraction and ML Pipeline
Demonstrates the complete workflow from PDF upload to ML training
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ecg_modules.medical_text_extractor import MedicalReportExtractor
from ml_training.train_model import CoronaryDiseasePredictor, export_dataset_to_csv
import pandas as pd


def create_sample_clinical_data():
    """Create sample clinical data for demonstration"""
    print("="*70)
    print("DEMO: Medical Data Extraction & ML Pipeline")
    print("="*70)
    print()
    
    # Sample French coronarography report text
    sample_report = """
    COMPTE RENDU DE CORONAROGRAPHIE
    
    Patient: Nom: MARTIN Prénom: Jacques
    Age: 68
    Sexe: M
    Date: 15-03-2024
    
    Indication: cardiopathie ischémique, scintigraphie myocardique positive
    
    Procédure:
    - Abord: voie radiale droite
    - Cathéter: 6F
    
    Résultats:
    
    CORONAIRE GAUCHE:
    - Tronc commun: court, de bon calibre, sans lésion
    - IVA: athérome diffus, sténose serrée au segment proximal (70-80%)
    - Diagonale: de bon calibre, sans lésion significative
    - Circonflexe: sténose modérée au segment proximal (50%), athérome diffus
    
    CORONAIRE DROITE:
    - Athérome diffus
    - Sténose serrée au segment moyen (80-90%)
    - Occlusion au segment distal avec réseau de suppléance
    - Flux TIMI II en aval
    
    CONCLUSION:
    Maladie coronaire bitronculaire sévère
    
    DÉCISION:
    Pontage coronaire programmé
    
    Facteurs de risque:
    - HTA
    - Diabète type 2
    - Tabagisme sevré depuis 2 ans
    """
    
    print("Sample Report Text:")
    print("-" * 70)
    print(sample_report)
    print("-" * 70)
    print()
    
    # Extract data using direct text parsing for demo
    extractor = MedicalReportExtractor()
    structured_data = extractor._parse_medical_report(sample_report)
    
    print("Extracted Structured Data:")
    print("-" * 70)
    for key, value in structured_data.items():
        if not key.startswith('left_') and not key.startswith('right_'):
            print(f"  {key}: {value}")
    print("-" * 70)
    print()
    
    return structured_data


def demonstrate_ml_training():
    """Demonstrate ML model training with sample data"""
    print("="*70)
    print("DEMO: Machine Learning Model Training")
    print("="*70)
    print()
    
    # Create synthetic dataset for demonstration
    print("Creating synthetic clinical dataset...")
    
    data = []
    import random
    
    # Generate 100 sample patients
    for i in range(100):
        record = {
            'patient_id': i + 1,
            'age': random.randint(45, 85),
            'gender': random.choice(['M', 'F']),
            'catheter_size': random.choice([6.0, 7.0]),
            'access_point': random.choice(['radial', 'femoral']),
            'iva_timi_flow': random.randint(1, 3),
            'total_stenosis_score': random.uniform(0, 15),
            'vessel_involvement_score': random.randint(0, 3),
            'occlusion_count': random.randint(0, 2),
            'indication_ischemic_heart_disease': random.choice([True, False]),
            'indication_positive_scintigraphy': random.choice([True, False]),
            'indication_positive_scanner': random.choice([True, False]),
            'diagnosis_three_vessel_disease': random.choice([True, False]),
            'risk_hypertension': random.choice([True, False]),
            'risk_diabetes': random.choice([True, False]),
            'risk_smoking': random.choice([True, False]),
            'risk_previous_mi': random.choice([True, False]),
            # ECG features (simulated)
            'heart_rate_bpm': random.uniform(60, 100),
            'sdnn_ms': random.uniform(20, 80),
            'rmssd_ms': random.uniform(15, 60),
            'pnn50_percent': random.uniform(5, 30),
            'sd1_ms': random.uniform(10, 50),
            'sd2_ms': random.uniform(20, 100),
            'lf_power': random.uniform(100, 1000),
            'hf_power': random.uniform(50, 500),
            'lf_hf_ratio': random.uniform(0.5, 3.0),
        }
        
        # Derive target variables based on severity
        if record['total_stenosis_score'] >= 10:
            record['diagnosis_severity_level'] = 'severe'
            record['treatment_bypass_surgery'] = True
            record['treatment_angioplasty'] = False
        elif record['total_stenosis_score'] >= 5:
            record['diagnosis_severity_level'] = 'moderate'
            record['treatment_bypass_surgery'] = random.choice([True, False])
            record['treatment_angioplasty'] = not record['treatment_bypass_surgery']
        else:
            record['diagnosis_severity_level'] = 'mild'
            record['treatment_bypass_surgery'] = False
            record['treatment_angioplasty'] = random.choice([True, False])
        
        data.append(record)
    
    df = pd.DataFrame(data)
    print(f"✓ Generated {len(df)} synthetic patient records")
    print(f"  Features: {len(df.columns)}")
    print()
    
    # Train bypass predictor
    print("Training Bypass Surgery Prediction Model...")
    print("-" * 70)
    predictor = CoronaryDiseasePredictor()
    results = predictor.train_bypass_predictor(df, include_ecg=True)
    print()
    
    # Train severity classifier
    print("Training Disease Severity Classification Model...")
    print("-" * 70)
    classifier = CoronaryDiseasePredictor()
    results2 = classifier.train_severity_classifier(df, include_ecg=True)
    print()
    
    # Save models
    os.makedirs('tmp/models', exist_ok=True)
    predictor.save_model('tmp/models/bypass_predictor.pkl')
    classifier.save_model('tmp/models/severity_classifier.pkl')
    print()
    
    # Export dataset
    print("Exporting dataset to CSV...")
    export_path = 'tmp/ml_dataset_demo.csv'
    export_dataset_to_csv(data, export_path)
    print(f"✓ Dataset saved to {export_path}")
    print()
    
    return df, predictor, classifier


def show_feature_importance(predictor):
    """Display feature importance from trained model"""
    print("="*70)
    print("FEATURE IMPORTANCE ANALYSIS")
    print("="*70)
    print()
    print("Top 15 Most Important Features:")
    print("-" * 70)
    
    if predictor.model is not None and hasattr(predictor.model, 'feature_importances_'):
        import pandas as pd
        feature_importance = pd.DataFrame({
            'feature': predictor.feature_names,
            'importance': predictor.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        for idx, row in feature_importance.head(15).iterrows():
            bar_length = int(row['importance'] * 50)
            bar = '█' * bar_length
            print(f"  {row['feature']:<30} {row['importance']:.4f} {bar}")
    
    print("-" * 70)
    print()


def main():
    """Run complete demo"""
    print("\n")
    print("╔" + "═"*68 + "╗")
    print("║" + " "*15 + "ECG-Mustapha ML Enhancement Demo" + " "*21 + "║")
    print("║" + " "*10 + "Medical Data Extraction & Machine Learning" + " "*15 + "║")
    print("╚" + "═"*68 + "╝")
    print("\n")
    
    # Part 1: Medical Text Extraction
    clinical_data = create_sample_clinical_data()
    
    input("Press Enter to continue to ML training demo...")
    print("\n")
    
    # Part 2: ML Training
    df, predictor, classifier = demonstrate_ml_training()
    
    input("Press Enter to see feature importance analysis...")
    print("\n")
    
    # Part 3: Feature Importance
    show_feature_importance(predictor)
    
    print("="*70)
    print("DEMO COMPLETED SUCCESSFULLY!")
    print("="*70)
    print()
    print("Next Steps:")
    print("  1. Start the Flask server: python app.py")
    print("  2. Open browser to: http://localhost:5000")
    print("  3. Upload coronarography PDFs via the web interface")
    print("  4. Export complete dataset: /api/export_ml_complete_dataset")
    print("  5. Train production models with real data")
    print()
    print("Files Created:")
    print("  - tmp/models/bypass_predictor.pkl")
    print("  - tmp/models/severity_classifier.pkl")
    print("  - tmp/ml_dataset_demo.csv")
    print()


if __name__ == '__main__':
    main()
