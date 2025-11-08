# 🏥 ECG-Mustapha ML Enhancement: Medical Data Extraction & Machine Learning

## 📋 Overview

This enhancement adds comprehensive medical data extraction from French coronarography reports and integrates it with ECG signal analysis for machine learning applications. The system extracts structured clinical data from PDF reports, converts it to numerical features, and provides ML-ready datasets.

## ✨ New Features

### 1. **Medical Text Extractor** (`ecg_modules/medical_text_extractor.py`)
- **French Medical NLP**: Regex patterns for French medical terminology
- **Patient Demographics**: Name, age, gender, exam date extraction
- **Clinical Findings**: Stenosis severity, occlusion, atheroma detection
- **Coronary Anatomy**: IVA, diagonal, circumflex, right coronary parsing
- **TIMI Flow**: Automatic extraction and conversion (I=1, II=2, III=3)
- **Risk Factors**: Diabetes, hypertension, smoking, previous MI
- **Severity Scoring**: Total stenosis score, vessel involvement (0-3)
- **Treatment Decisions**: Bypass surgery, angioplasty detection

### 2. **Clinical Database** (`ecg_modules/database_clinical.py`)
- **PostgreSQL Schema**: Production-grade database with 50+ clinical features
- **Patient Table**: Links clinical data to patient records
- **Clinical Data Table**: Comprehensive medical findings storage
- **Indexes**: Optimized for ML queries on severity, vessels, treatment
- **JSONB Support**: Stores raw extracted data for flexibility
- **ML Export**: Combines ECG + clinical data in single query

### 3. **ML Training Module** (`ml_training/train_model.py`)
- **Feature Engineering**: Numerical, binary, and categorical encoding
- **Bypass Predictor**: GradientBoostingClassifier for surgery prediction
- **Severity Classifier**: RandomForestClassifier for disease severity
- **Feature Importance**: Automatic analysis of predictive features
- **Model Persistence**: Save/load trained models
- **Cross-validation**: Proper train/test splits with stratification

### 4. **Flask API Endpoints**
```python
POST /api/upload_clinical_report
    Upload coronarography PDF and extract clinical data
    Returns: patient_id, record_id, extracted_data

GET /api/export_ml_complete_dataset
    Export CSV with ECG + Clinical features
    Returns: CSV file download

GET /api/clinical_statistics
    Get clinical data statistics
    Returns: JSON with counts and averages
```

### 5. **Enhanced Frontend UI**
- **Clinical Upload Section**: Dedicated area for medical reports
- **Real-time Extraction**: Displays extracted data immediately
- **Integrated Display**: Shows demographics, findings, severity, treatment
- **Responsive Design**: Matches existing ECG analyzer style

## 🚀 Quick Start

### Installation

```bash
# Install additional dependencies
pip install scikit-learn psycopg2-binary openpyxl

# Or update requirements.txt and install
pip install -r requirements.txt
```

### Database Setup (PostgreSQL)

```bash
# Set environment variables (optional)
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=ecg_analysis
export DB_USER=postgres
export DB_PASSWORD=postgres

# Tables are created automatically on first run
```

### Running the Application

```bash
# Start Flask server
python app.py

# Open browser
http://localhost:5000
```

### Running the Demo

```bash
# Complete ML pipeline demonstration
python demo_ml_pipeline.py
```

## 📊 Database Schema

### `patients` Table
```sql
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    last_name VARCHAR(100),
    first_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `patient_clinical_data` Table (50+ columns)
```sql
CREATE TABLE patient_clinical_data (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    
    -- Demographics
    age INTEGER,
    gender VARCHAR(10),
    exam_date DATE,
    
    -- Clinical Indication
    indication_ischemic_heart_disease BOOLEAN,
    indication_positive_scintigraphy BOOLEAN,
    indication_positive_scanner BOOLEAN,
    
    -- Procedure Details
    access_point VARCHAR(20),
    catheter_size FLOAT,
    
    -- Coronary Findings (IVA, Diagonal, Circumflex, Right)
    iva_timi_flow INTEGER,
    iva_stenosis_severity INTEGER,
    circumflex_stenosis_severity INTEGER,
    right_coronary_stenosis_severity INTEGER,
    
    -- Computed Scores
    total_stenosis_score FLOAT,
    vessel_involvement_score INTEGER,
    occlusion_count INTEGER,
    severity_index FLOAT,
    
    -- Diagnosis
    diagnosis_three_vessel_disease BOOLEAN,
    diagnosis_severity_level VARCHAR(20),
    
    -- Treatment
    treatment_bypass_surgery BOOLEAN,
    treatment_angioplasty BOOLEAN,
    
    -- Risk Factors
    risk_hypertension BOOLEAN,
    risk_diabetes BOOLEAN,
    risk_smoking BOOLEAN,
    risk_previous_mi BOOLEAN,
    
    -- Raw Data
    raw_text TEXT,
    raw_extracted_data JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔬 Medical Text Extraction Examples

### French Terminology Support

The system recognizes French medical terms:

- **Stenosis**: "sténose serrée" (severe), "sténose modérée" (moderate)
- **Occlusion**: "occlu[se]", "occlusion"
- **Vessels**: "IVA", "circonflexe", "coronaire droite"
- **Diagnosis**: "tritronculaire", "bitronculaire", "monotronculaire"
- **Treatment**: "pontage" (bypass), "angioplastie" (PCI)
- **TIMI Flow**: "TIMI I", "TIMI II", "TIMI III"

### Sample Report Processing

```python
from ecg_modules.medical_text_extractor import MedicalReportExtractor

extractor = MedicalReportExtractor()

# From PDF file
full_text, data = extractor.extract_from_pdf("report.pdf")

# From bytes
with open("report.pdf", "rb") as f:
    full_text, data = extractor.extract_from_pdf(f.read())

# Extracted data includes:
print(data['age'])                    # 68
print(data['severity_level'])         # 'severe'
print(data['requires_bypass'])        # True
print(data['total_stenosis_score'])   # 10.0
print(data['vessel_involvement_score']) # 2
```

## 🤖 Machine Learning Usage

### Training Models

```python
from ml_training.train_model import CoronaryDiseasePredictor
from ecg_modules.database_clinical import ClinicalDatabase
import pandas as pd

# Get data
clinical_db = ClinicalDatabase(connection_pool)
data = clinical_db.get_ml_dataset(include_ecg=True)
df = pd.DataFrame(data)

# Train bypass predictor
predictor = CoronaryDiseasePredictor()
results = predictor.train_bypass_predictor(df)

# Train severity classifier
classifier = CoronaryDiseasePredictor()
results = classifier.train_severity_classifier(df)

# Save models
predictor.save_model('models/bypass_predictor.pkl')
classifier.save_model('models/severity_classifier.pkl')
```

### Making Predictions

```python
# Load model
predictor = CoronaryDiseasePredictor()
predictor.load_model('models/bypass_predictor.pkl')

# Prepare new patient data
new_patient = pd.DataFrame([{
    'age': 65,
    'total_stenosis_score': 12.0,
    'vessel_involvement_score': 3,
    'heart_rate_bpm': 75,
    # ... other features
}])

# Predict
prediction = predictor.predict(new_patient)
print(f"Requires bypass: {prediction[0]}")
```

### Feature Engineering

The system automatically handles:
- **Numerical features**: Age, scores, ECG metrics
- **Binary features**: Boolean flags for risk factors
- **Categorical encoding**: One-hot encoding for gender, access point
- **Feature scaling**: StandardScaler for all features
- **Missing value handling**: Fillna with appropriate defaults

## 📈 Exported Dataset Structure

The ML dataset includes ~70+ features:

```csv
patient_id,age,gender,access_point,catheter_size,
iva_timi_flow,total_stenosis_score,vessel_involvement_score,
occlusion_count,diagnosis_three_vessel_disease,
diagnosis_severity_level,treatment_bypass_surgery,
treatment_angioplasty,risk_hypertension,risk_diabetes,
risk_smoking,risk_previous_mi,heart_rate_bpm,sdnn_ms,
rmssd_ms,pnn50_percent,sd1_ms,sd2_ms,lf_power,
hf_power,lf_hf_ratio,...
```

## 🧪 Testing

### Run Unit Tests

```bash
# Test medical extractor
python tests/test_medical_extractor.py

# All tests (15 tests for medical extraction)
python tests/run_tests.py
```

### Test Coverage

- ✅ Pattern matching for French medical terms
- ✅ Demographic extraction (name, age, gender)
- ✅ Stenosis severity detection (mild, moderate, severe)
- ✅ Occlusion detection
- ✅ TIMI flow extraction
- ✅ Risk factor identification
- ✅ Severity score calculation
- ✅ Vessel involvement scoring
- ✅ Treatment decision extraction

## 🔒 Security Considerations

1. **SQL Injection**: Uses parameterized queries throughout
2. **Input Validation**: PDF file type checking
3. **Error Handling**: Comprehensive try/catch blocks
4. **Connection Pooling**: Prevents connection exhaustion
5. **Data Privacy**: Raw text stored separately, can be encrypted

## 🎯 Use Cases

### 1. Clinical Decision Support
- Predict bypass surgery requirement based on findings
- Classify disease severity automatically
- Identify high-risk patients

### 2. Research & Analytics
- Aggregate clinical data across patient population
- Correlate ECG metrics with coronary disease
- Study treatment outcomes

### 3. Quality Assurance
- Compare manual vs automated extraction
- Validate consistency of diagnoses
- Track severity distributions

### 4. Predictive Modeling
- Train custom ML models for specific populations
- Feature importance analysis
- Risk stratification

## 📝 Example API Usage

### Upload Clinical Report

```bash
curl -X POST http://localhost:5000/api/upload_clinical_report \
  -F "file=@coronarography_report.pdf" \
  -F "patient_id=123"
```

### Export ML Dataset

```bash
curl http://localhost:5000/api/export_ml_complete_dataset \
  -o ecg_ml_dataset.csv
```

### Get Statistics

```bash
curl http://localhost:5000/api/clinical_statistics
```

## 🔄 Integration with Existing System

The enhancement integrates seamlessly:

1. **Database**: Uses same PostgreSQL connection pool
2. **UI**: Adds new section without modifying existing ECG analyzer
3. **API**: New endpoints don't conflict with existing routes
4. **Testing**: Extends existing test framework

## 📦 File Structure

```
ECG/
├── ecg_modules/
│   ├── medical_text_extractor.py   # NEW: French medical NLP
│   ├── database_clinical.py        # NEW: Clinical data storage
│   ├── analyse.py                  # Existing: ECG analysis
│   └── ...
├── ml_training/
│   ├── __init__.py                 # NEW: ML module
│   └── train_model.py              # NEW: ML training pipeline
├── tests/
│   ├── test_medical_extractor.py   # NEW: 15 unit tests
│   └── ...
├── static/
│   └── index.html                  # UPDATED: Clinical upload UI
├── app.py                          # UPDATED: New API routes
├── demo_ml_pipeline.py             # NEW: Complete demo
└── ML_ENHANCEMENT_GUIDE.md         # NEW: This documentation
```

## 🚧 Future Enhancements

Potential additions:
- [ ] Image-based stenosis measurement (CV/CNN)
- [ ] Multi-language support (English, Arabic)
- [ ] DICOM integration for angiography images
- [ ] Real-time model serving API
- [ ] Automated report generation
- [ ] Longitudinal patient tracking

## 📞 Support

For issues or questions:
1. Check test results: `python tests/test_medical_extractor.py`
2. Run demo: `python demo_ml_pipeline.py`
3. Review logs in Flask console
4. Check PostgreSQL connection settings

## 📄 License

Same as parent ECG project (MIT License)
