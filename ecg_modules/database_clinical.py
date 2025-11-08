"""
Clinical Database Module - Extension for patient clinical data
Handles storage and retrieval of coronarography findings
"""
import psycopg2
from psycopg2 import extras
import json
import os
from datetime import datetime
from contextlib import contextmanager
from typing import Dict, Any, Optional, List


class ClinicalDatabase:
    """
    Database extension for clinical coronarography data
    Works alongside the main ECG database
    """
    
    def __init__(self, connection_pool, verbose: bool = None):
        """
        Initialize with existing connection pool from ECGDatabasePostgres
        
        Args:
            connection_pool: psycopg2 connection pool
            verbose: Enable verbose logging (default: from DEBUG_LOGGING env var)
        """
        self.connection_pool = connection_pool
        self.verbose = verbose if verbose is not None else os.getenv('DEBUG_LOGGING', 'false').lower() == 'true'
        self._create_clinical_tables()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = self.connection_pool.getconn()
        try:
            yield conn
        finally:
            self.connection_pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, commit=True):
        """Context manager for database cursor with automatic commit/rollback"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()
    
    def _create_clinical_tables(self):
        """Create clinical data tables if they don't exist"""
        
        # Create patients table if not exists
        patients_table_sql = """
        CREATE TABLE IF NOT EXISTS patients (
            id SERIAL PRIMARY KEY,
            last_name VARCHAR(100),
            first_name VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_patient_name ON patients(last_name, first_name);
        """
        
        # Create patient clinical data table
        clinical_table_sql = """
        CREATE TABLE IF NOT EXISTS patient_clinical_data (
            id SERIAL PRIMARY KEY,
            patient_id INTEGER REFERENCES patients(id),
            
            -- Demographics
            age INTEGER,
            gender VARCHAR(10),
            exam_date DATE,
            
            -- Clinical Indication (binary)
            indication_ischemic_heart_disease BOOLEAN,
            indication_positive_scintigraphy BOOLEAN,
            indication_positive_scanner BOOLEAN,
            
            -- Procedure Details
            access_point VARCHAR(20),  -- 'radial' or 'femoral'
            catheter_size FLOAT,  -- 6.0, 7.0, etc.
            
            -- LEFT CORONARY - Trunk
            trunk_size INTEGER,  -- 1=small, 2=medium, 3=large
            trunk_infiltration BOOLEAN,
            trunk_stenosis BOOLEAN,
            trunk_stenosis_severity INTEGER,  -- 0-3
            
            -- LEFT CORONARY - IVA (LAD)
            iva_developed BOOLEAN,
            iva_atheroma BOOLEAN,
            iva_stenosis_severity INTEGER,  -- 0-3
            iva_stenosis_location VARCHAR(20),  -- 'proximal', 'middle', 'distal'
            iva_stenosis_length VARCHAR(10),  -- 'short' or 'long'
            iva_timi_flow INTEGER,  -- 1, 2, or 3
            
            -- LEFT CORONARY - Diagonal
            diagonal_present BOOLEAN,
            diagonal_caliber INTEGER,  -- 1=small, 2=good, 3=large
            diagonal_stenosis_severity INTEGER,  -- 0-3
            diagonal_stenosis_location VARCHAR(20),
            
            -- LEFT CORONARY - Circumflex
            circumflex_atheroma BOOLEAN,
            circumflex_stenosis_severity INTEGER,  -- 0-3
            circumflex_stenosis_location VARCHAR(20),
            circumflex_occlusion BOOLEAN,
            circumflex_occlusion_location VARCHAR(20),
            circumflex_collateral_network BOOLEAN,
            circumflex_marginals_count INTEGER,
            
            -- LEFT CORONARY - Bissectrice (if present)
            bissectrice_present BOOLEAN,
            bissectrice_stenosis_severity INTEGER,
            bissectrice_stenosis_location VARCHAR(20),
            
            -- RIGHT CORONARY
            right_coronary_atheroma BOOLEAN,
            right_coronary_stenosis_severity INTEGER,  -- 0-3
            right_coronary_stenosis_length VARCHAR(10),
            right_coronary_stenosis_location VARCHAR(20),
            right_coronary_occlusion BOOLEAN,
            right_coronary_occlusion_location VARCHAR(20),
            right_coronary_collateral_network BOOLEAN,
            
            -- COMPUTED SCORES
            total_stenosis_score FLOAT,  -- sum of all stenosis severities
            vessel_involvement_score INTEGER,  -- 0-3 (number of vessels affected)
            occlusion_count INTEGER,  -- total number of occlusions
            severity_index FLOAT,  -- weighted severity score
            
            -- DIAGNOSIS (TARGET VARIABLES)
            diagnosis_three_vessel_disease BOOLEAN,
            diagnosis_vessels_affected_count INTEGER,
            diagnosis_severity_level VARCHAR(20),  -- 'mild', 'moderate', 'severe'
            
            -- TREATMENT DECISION (TARGET VARIABLES)
            treatment_bypass_surgery BOOLEAN,
            treatment_angioplasty BOOLEAN,
            treatment_medical_only BOOLEAN,
            treatment_adhoc BOOLEAN,
            treatment_urgency_score INTEGER,  -- 0-3
            
            -- Risk Factors
            risk_hypertension BOOLEAN,
            risk_diabetes BOOLEAN,
            risk_smoking BOOLEAN,
            risk_previous_mi BOOLEAN,
            risk_family_history BOOLEAN,
            
            -- Raw data storage
            raw_text TEXT,  -- Original PDF text
            raw_extracted_data JSONB,  -- All extracted data in JSON format
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create indexes for ML queries
        CREATE INDEX IF NOT EXISTS idx_clinical_severity ON patient_clinical_data(severity_index);
        CREATE INDEX IF NOT EXISTS idx_clinical_treatment ON patient_clinical_data(treatment_bypass_surgery, treatment_angioplasty);
        CREATE INDEX IF NOT EXISTS idx_clinical_vessels ON patient_clinical_data(vessel_involvement_score);
        CREATE INDEX IF NOT EXISTS idx_clinical_patient ON patient_clinical_data(patient_id);
        CREATE INDEX IF NOT EXISTS idx_clinical_exam_date ON patient_clinical_data(exam_date);
        """
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(patients_table_sql)
                cursor.execute(clinical_table_sql)
            print("✓ Clinical tables and indexes created")
        except Exception as e:
            print(f"✗ Error creating clinical tables: {e}")
            raise
    
    def save_patient(self, last_name: str, first_name: str) -> int:
        """
        Save or get patient record
        
        Args:
            last_name: Patient last name
            first_name: Patient first name
            
        Returns:
            int: Patient ID
        """
        # Check if patient exists
        select_sql = """
        SELECT id FROM patients 
        WHERE last_name = %s AND first_name = %s
        LIMIT 1
        """
        
        insert_sql = """
        INSERT INTO patients (last_name, first_name)
        VALUES (%s, %s)
        RETURNING id
        """
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(select_sql, (last_name, first_name))
                result = cursor.fetchone()
                
                if result:
                    return result['id']
                
                # Insert new patient
                cursor.execute(insert_sql, (last_name, first_name))
                result = cursor.fetchone()
                return result['id']
        except Exception as e:
            print(f"✗ Error saving patient: {e}")
            raise
    
    def save_clinical_data(self, patient_id: int, clinical_data: Dict[str, Any], 
                          raw_text: Optional[str] = None) -> int:
        """
        Save clinical coronarography data
        
        Args:
            patient_id: Patient ID from patients table
            clinical_data: Dictionary of extracted clinical data
            raw_text: Original PDF text
            
        Returns:
            int: Clinical data record ID
        """
        insert_sql = """
        INSERT INTO patient_clinical_data (
            patient_id, age, gender, exam_date,
            indication_ischemic_heart_disease, indication_positive_scintigraphy, 
            indication_positive_scanner,
            access_point, catheter_size,
            iva_timi_flow,
            total_stenosis_score, vessel_involvement_score, occlusion_count,
            diagnosis_three_vessel_disease, diagnosis_vessels_affected_count,
            diagnosis_severity_level,
            treatment_bypass_surgery, treatment_angioplasty,
            risk_hypertension, risk_diabetes, risk_smoking, risk_previous_mi,
            raw_text, raw_extracted_data
        ) VALUES (
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s,
            %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s, %s, %s,
            %s, %s
        ) RETURNING id
        """
        
        # Parse exam_date if string
        exam_date = clinical_data.get('exam_date')
        if isinstance(exam_date, str):
            try:
                # Try parsing DD-MM-YYYY or DD/MM/YYYY
                for fmt in ['%d-%m-%Y', '%d/%m/%Y']:
                    try:
                        exam_date = datetime.strptime(exam_date, fmt).date()
                        break
                    except ValueError:
                        continue
            except:
                exam_date = None
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(insert_sql, (
                    patient_id,
                    clinical_data.get('age'),
                    clinical_data.get('gender'),
                    exam_date,
                    clinical_data.get('indication_ischemic_heart_disease', False),
                    clinical_data.get('indication_positive_scintigraphy', False),
                    clinical_data.get('indication_positive_scanner', False),
                    clinical_data.get('access_point'),
                    clinical_data.get('catheter_size'),
                    clinical_data.get('timi_flow'),
                    clinical_data.get('total_stenosis_score', 0.0),
                    clinical_data.get('vessel_involvement_score', 0),
                    clinical_data.get('occlusion_count', 0),
                    clinical_data.get('three_vessel_disease', False),
                    clinical_data.get('vessel_involvement_score', 0),
                    clinical_data.get('severity_level', 'mild'),
                    clinical_data.get('requires_bypass', False),
                    clinical_data.get('requires_angioplasty', False),
                    clinical_data.get('risk_hypertension', False),
                    clinical_data.get('risk_diabetes', False),
                    clinical_data.get('risk_smoking', False),
                    clinical_data.get('risk_previous_mi', False),
                    raw_text,
                    json.dumps(clinical_data)
                ))
                result = cursor.fetchone()
                record_id = result['id']
                # Only log patient IDs if verbose logging is enabled (for HIPAA/GDPR compliance)
                # CodeQL: Intentional logging of patient_id when DEBUG_LOGGING=true for audit purposes
                if self.verbose:
                    print(f"✓ Saved clinical data record ID {record_id} for patient {patient_id}")  # nosec
                else:
                    print(f"✓ Saved clinical data record ID {record_id}")
                return record_id
        except Exception as e:
            print(f"✗ Error saving clinical data: {e}")
            raise
    
    def get_ml_dataset(self, include_ecg: bool = True) -> List[Dict[str, Any]]:
        """
        Export complete dataset for ML training
        Joins clinical data with ECG analyses
        
        Args:
            include_ecg: Whether to include ECG metrics in export
            
        Returns:
            List of dictionaries with combined data
        """
        if include_ecg:
            query = """
            SELECT 
                p.id as patient_id,
                c.age,
                c.gender,
                c.indication_ischemic_heart_disease,
                c.indication_positive_scintigraphy,
                c.indication_positive_scanner,
                c.access_point,
                c.catheter_size,
                c.iva_timi_flow,
                c.total_stenosis_score,
                c.vessel_involvement_score,
                c.occlusion_count,
                c.diagnosis_three_vessel_disease,
                c.diagnosis_vessels_affected_count,
                c.diagnosis_severity_level,
                c.treatment_bypass_surgery,
                c.treatment_angioplasty,
                c.risk_hypertension,
                c.risk_diabetes,
                c.risk_smoking,
                c.risk_previous_mi,
                e.heart_rate_bpm,
                e.sdnn_ms,
                e.rmssd_ms,
                e.pnn50_percent,
                e.sd1_ms,
                e.sd2_ms,
                e.lf_power,
                e.hf_power,
                e.lf_hf_ratio
            FROM patient_clinical_data c
            LEFT JOIN patients p ON c.patient_id = p.id
            LEFT JOIN ecg_analyses e ON p.id = e.id
            WHERE c.total_stenosis_score IS NOT NULL
            ORDER BY c.created_at DESC
            """
        else:
            query = """
            SELECT 
                p.id as patient_id,
                c.*
            FROM patient_clinical_data c
            LEFT JOIN patients p ON c.patient_id = p.id
            WHERE c.total_stenosis_score IS NOT NULL
            ORDER BY c.created_at DESC
            """
        
        try:
            with self.get_cursor(commit=False) as cursor:
                cursor.execute(query)
                records = cursor.fetchall()
                
                # Convert to list of dicts
                result = []
                for record in records:
                    record_dict = dict(record)
                    # Convert dates to ISO format
                    if record_dict.get('exam_date'):
                        record_dict['exam_date'] = record_dict['exam_date'].isoformat()
                    if record_dict.get('created_at'):
                        record_dict['created_at'] = record_dict['created_at'].isoformat()
                    result.append(record_dict)
                
                return result
        except Exception as e:
            print(f"✗ Error getting ML dataset: {e}")
            raise
    
    def get_clinical_statistics(self) -> Dict[str, Any]:
        """Get statistics about clinical data"""
        query = """
        SELECT 
            COUNT(*) as total_patients,
            AVG(age) as avg_age,
            COUNT(CASE WHEN gender = 'M' THEN 1 END) as male_count,
            COUNT(CASE WHEN gender = 'F' THEN 1 END) as female_count,
            AVG(total_stenosis_score) as avg_stenosis_score,
            AVG(vessel_involvement_score) as avg_vessel_involvement,
            COUNT(CASE WHEN diagnosis_three_vessel_disease THEN 1 END) as three_vessel_count,
            COUNT(CASE WHEN treatment_bypass_surgery THEN 1 END) as bypass_count,
            COUNT(CASE WHEN treatment_angioplasty THEN 1 END) as angioplasty_count,
            COUNT(CASE WHEN diagnosis_severity_level = 'severe' THEN 1 END) as severe_count,
            COUNT(CASE WHEN diagnosis_severity_level = 'moderate' THEN 1 END) as moderate_count,
            COUNT(CASE WHEN diagnosis_severity_level = 'mild' THEN 1 END) as mild_count
        FROM patient_clinical_data
        """
        
        try:
            with self.get_cursor(commit=False) as cursor:
                cursor.execute(query)
                result = cursor.fetchone()
                return dict(result) if result else {}
        except Exception as e:
            print(f"✗ Error getting clinical statistics: {e}")
            raise
