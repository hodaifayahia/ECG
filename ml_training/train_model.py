"""
Machine Learning Training Module
Trains models for coronary disease prediction and severity classification
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from typing import Tuple, Dict, Any, List, Optional
import pickle
import os


class CoronaryDiseasePredictor:
    """ML model for predicting coronary disease severity and treatment"""

    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.model = None
        self.feature_names = []
        
    def prepare_features(self, df: pd.DataFrame, 
                        include_ecg: bool = True) -> Tuple[pd.DataFrame, List[str]]:
        """
        Prepare numerical features for ML
        
        Args:
            df: DataFrame with clinical and ECG data
            include_ecg: Whether to include ECG features
            
        Returns:
            Tuple of (feature_dataframe, feature_names)
        """
        
        # Numerical features - Clinical
        numerical_features = [
            'age',
            'catheter_size',
            'iva_timi_flow',
            'total_stenosis_score',
            'vessel_involvement_score',
            'occlusion_count',
        ]
        
        # Add ECG features if available
        if include_ecg:
            ecg_features = [
                'heart_rate_bpm',
                'sdnn_ms',
                'rmssd_ms',
                'pnn50_percent',
                'sd1_ms',
                'sd2_ms',
                'lf_power',
                'hf_power',
                'lf_hf_ratio'
            ]
            numerical_features.extend([f for f in ecg_features if f in df.columns])
        
        # Binary features - Clinical indications and risk factors
        binary_features = [
            'indication_ischemic_heart_disease',
            'indication_positive_scintigraphy',
            'indication_positive_scanner',
            'diagnosis_three_vessel_disease',
            'risk_hypertension',
            'risk_diabetes',
            'risk_smoking',
            'risk_previous_mi',
        ]
        
        # Categorical features (will be one-hot encoded)
        categorical_features = [
            'gender',
            'access_point',
        ]
        
        # Extract numerical and binary features
        available_numerical = [f for f in numerical_features if f in df.columns]
        available_binary = [f for f in binary_features if f in df.columns]
        available_categorical = [f for f in categorical_features if f in df.columns]
        
        # Create feature dataframe
        X_numerical = df[available_numerical].fillna(0)
        X_binary = df[available_binary].fillna(False).astype(int)
        
        # One-hot encode categorical features
        X_categorical_list = []
        if available_categorical:
            X_categorical = pd.get_dummies(
                df[available_categorical], 
                drop_first=True, 
                prefix=available_categorical
            )
            X_categorical_list.append(X_categorical)
        
        # Combine all features
        feature_dfs = [X_numerical, X_binary] + X_categorical_list
        X = pd.concat(feature_dfs, axis=1)
        
        return X, list(X.columns)
    
    def train_bypass_predictor(self, df: pd.DataFrame, 
                               include_ecg: bool = True,
                               test_size: float = 0.2,
                               random_state: int = 42) -> Dict[str, Any]:
        """
        Train model to predict bypass surgery requirement
        
        Args:
            df: DataFrame with clinical and ECG data
            include_ecg: Whether to include ECG features
            test_size: Proportion of data for testing
            random_state: Random seed for reproducibility
            
        Returns:
            Dictionary with training results and metrics
        """
        # Prepare features
        X, feature_names = self.prepare_features(df, include_ecg)
        self.feature_names = feature_names
        
        # Target variable
        y = df['treatment_bypass_surgery'].fillna(False).astype(int)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model = GradientBoostingClassifier(
            n_estimators=100, 
            max_depth=5,
            learning_rate=0.1,
            random_state=random_state
        )
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred_train = self.model.predict(X_train_scaled)
        y_pred_test = self.model.predict(X_test_scaled)
        
        # Get feature importances
        feature_importance = pd.DataFrame({
            'feature': feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        results = {
            'model_type': 'bypass_surgery_predictor',
            'train_accuracy': accuracy_score(y_train, y_pred_train),
            'test_accuracy': accuracy_score(y_test, y_pred_test),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'classification_report': classification_report(y_test, y_pred_test, output_dict=True),
            'confusion_matrix': confusion_matrix(y_test, y_pred_test).tolist(),
            'feature_importance': feature_importance.to_dict('records'),
            'features_used': feature_names
        }
        
        print("="*60)
        print("BYPASS SURGERY PREDICTION MODEL")
        print("="*60)
        print(f"Train Accuracy: {results['train_accuracy']:.3f}")
        print(f"Test Accuracy: {results['test_accuracy']:.3f}")
        print(f"\nClassification Report:")
        print(classification_report(y_test, y_pred_test))
        print(f"\nTop 10 Important Features:")
        for idx, row in feature_importance.head(10).iterrows():
            print(f"  {row['feature']}: {row['importance']:.4f}")
        print("="*60)
        
        return results
    
    def train_severity_classifier(self, df: pd.DataFrame,
                                  include_ecg: bool = True,
                                  test_size: float = 0.2,
                                  random_state: int = 42) -> Dict[str, Any]:
        """
        Train model to classify disease severity
        
        Args:
            df: DataFrame with clinical and ECG data
            include_ecg: Whether to include ECG features
            test_size: Proportion of data for testing
            random_state: Random seed for reproducibility
            
        Returns:
            Dictionary with training results and metrics
        """
        # Prepare features
        X, feature_names = self.prepare_features(df, include_ecg)
        self.feature_names = feature_names
        
        # Target variable - encode severity levels
        y = df['diagnosis_severity_level'].fillna('mild')
        le = LabelEncoder()
        y_encoded = le.fit_transform(y)
        self.label_encoders['severity'] = le
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=test_size, random_state=random_state, stratify=y_encoded
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=random_state
        )
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred_train = self.model.predict(X_train_scaled)
        y_pred_test = self.model.predict(X_test_scaled)
        
        # Get feature importances
        feature_importance = pd.DataFrame({
            'feature': feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        results = {
            'model_type': 'severity_classifier',
            'train_accuracy': accuracy_score(y_train, y_pred_train),
            'test_accuracy': accuracy_score(y_test, y_pred_test),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'classes': le.classes_.tolist(),
            'classification_report': classification_report(
                y_test, y_pred_test, 
                target_names=le.classes_,
                output_dict=True
            ),
            'confusion_matrix': confusion_matrix(y_test, y_pred_test).tolist(),
            'feature_importance': feature_importance.to_dict('records'),
            'features_used': feature_names
        }
        
        print("="*60)
        print("DISEASE SEVERITY CLASSIFICATION MODEL")
        print("="*60)
        print(f"Train Accuracy: {results['train_accuracy']:.3f}")
        print(f"Test Accuracy: {results['test_accuracy']:.3f}")
        print(f"\nClassification Report:")
        print(classification_report(y_test, y_pred_test, target_names=le.classes_))
        print(f"\nTop 10 Important Features:")
        for idx, row in feature_importance.head(10).iterrows():
            print(f"  {row['feature']}: {row['importance']:.4f}")
        print("="*60)
        
        return results
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions on new data
        
        Args:
            X: DataFrame with features
            
        Returns:
            Array of predictions
        """
        if self.model is None:
            raise ValueError("Model not trained yet. Call train_bypass_predictor or train_severity_classifier first.")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def save_model(self, filepath: str):
        """Save model to file"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_names': self.feature_names
        }
        
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        print(f"✓ Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load model from file"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.label_encoders = model_data['label_encoders']
        self.feature_names = model_data['feature_names']
        print(f"✓ Model loaded from {filepath}")


def export_dataset_to_csv(data: List[Dict[str, Any]], output_path: str):
    """
    Export dataset to CSV format for ML analysis
    
    Args:
        data: List of data records
        output_path: Path to save CSV file
    """
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"✓ Dataset exported to {output_path}")
    print(f"  Total records: {len(df)}")
    print(f"  Total features: {len(df.columns)}")
    return df
