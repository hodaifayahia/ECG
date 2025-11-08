from flask import Flask, request, jsonify, send_file, send_from_directory, Response
from ecg_modules import pdf_extract, digitize, analyse, ml_features, database
from ecg_modules.excel_export import export_to_excel
from ecg_modules.medical_text_extractor import MedicalReportExtractor
from ecg_modules.database_clinical import ClinicalDatabase
import os
import time
import io
import csv
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Ensure tmp directory exists
os.makedirs("tmp", exist_ok=True)

# Initialize database
db = database.get_db()

# Initialize clinical database and medical extractor
clinical_db = None
medical_extractor = MedicalReportExtractor()

# Initialize clinical DB with connection pool from main DB
try:
    if hasattr(db, 'connection_pool'):
        clinical_db = ClinicalDatabase(db.connection_pool)
        print("✓ Clinical database initialized")
except Exception as e:
    print(f"⚠ Clinical database not initialized: {e}")
    print("  Clinical features will not be available")

@app.route("/upload", methods=["POST"])
def upload():
    """Handle ECG PDF upload and return metrics"""
    start_time = time.time()
    
    try:
        file_obj = request.files["file"]
        filename = file_obj.filename
        file_bytes = file_obj.read()
        file_size = len(file_bytes)
        
        pdf_bytes = file_bytes
        images_or_paths = pdf_extract.split_panels(pdf_bytes)   # PyMuPDF
        csv_path = digitize.ecg_to_csv(images_or_paths, pdf_bytes=pdf_bytes)  # ECGtizer (pass PDF for mock variation)
        all_metrics = analyse.compute_metrics(csv_path)         # NeuroKit2/HeartPy
        
        # Get feature set from request (default: 'standard')
        feature_set = request.args.get('features', 'standard')
        
        # Return only important features
        if feature_set == 'all':
            metrics_to_return = all_metrics
        else:
            metrics_to_return = ml_features.select_features(all_metrics, feature_set)
        
        # Save to database
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        db.save_result(filename, all_metrics, feature_set, file_size, processing_time)
        
        return jsonify(metrics_to_return)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def index():
    """Serve the main HTML page"""
    return send_file("static/index.html")

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Explicitly serve static files"""
    return send_from_directory('static', filename)

# ===== API ENDPOINTS =====

@app.route("/api/save_results", methods=["POST"])
def save_results():
    """Save multiple results to database"""
    try:
        data = request.json
        saved_count = 0
        
        if isinstance(data, list):
            for result in data:
                db.save_result(
                    result.get('filename'),
                    result.get('metrics'),
                    result.get('features', 'standard')
                )
                saved_count += 1
        
        return jsonify({
            "status": "success",
            "saved": saved_count
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/get_data", methods=["GET"])
def get_data():
    """Get all data from database"""
    try:
        records = db.get_all_records()
        return jsonify({
            "status": "success",
            "count": len(records),
            "records": records
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/export_excel", methods=["GET"])
def export_excel():
    """Export database to Excel file"""
    try:
        records = db.get_all_records()
        
        # Create Excel file in memory
        output = io.BytesIO()
        
        # Create temporary file
        temp_path = f"tmp/ecg_export_{int(time.time())}.xlsx"
        export_to_excel(records, temp_path)
        
        # Read and send file
        with open(temp_path, 'rb') as f:
            output.write(f.read())
        
        output.seek(0)
        
        # Clean up
        os.remove(temp_path)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"ecg_analysis_{int(time.time())}.xlsx"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/statistics", methods=["GET"])
def get_statistics():
    """Get database statistics"""
    try:
        stats = db.get_statistics()
        return jsonify({
            "status": "success",
            "statistics": stats
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===== CLINICAL DATA API ENDPOINTS =====

@app.route("/api/upload_clinical_report", methods=["POST"])
def upload_clinical_report():
    """Upload coronarography PDF and extract clinical data"""
    if clinical_db is None:
        return jsonify({
            "error": "Clinical database not initialized. Please configure PostgreSQL."
        }), 503
    
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file provided"}), 400
        
        # Optional patient_id from form, otherwise create new patient
        patient_id = request.form.get('patient_id')
        
        # Extract data from PDF
        pdf_bytes = file.read()
        full_text, structured_data = medical_extractor.extract_from_pdf(pdf_bytes)
        
        # Save patient if needed
        if not patient_id:
            # Try to get patient info from extracted data
            last_name = structured_data.get('last_name', 'Unknown')
            first_name = structured_data.get('first_name', 'Unknown')
            patient_id = clinical_db.save_patient(last_name, first_name)
        else:
            patient_id = int(patient_id)
        
        # Save clinical data to database
        record_id = clinical_db.save_clinical_data(patient_id, structured_data, full_text)
        
        return jsonify({
            "status": "success",
            "patient_id": patient_id,
            "record_id": record_id,
            "extracted_data": structured_data
        })
        
    except Exception as e:
        # Log the full error for debugging but return sanitized message to user
        print(f"Error uploading clinical report: {str(e)}")
        return jsonify({"error": "Failed to process clinical report. Please check the file format."}), 500

@app.route("/api/export_ml_complete_dataset", methods=["GET"])
def export_ml_complete_dataset():
    """Export complete dataset: ECG metrics + Clinical data as CSV"""
    if clinical_db is None:
        return jsonify({
            "error": "Clinical database not initialized"
        }), 503
    
    try:
        # Get complete dataset with ECG and clinical data
        records = clinical_db.get_ml_dataset(include_ecg=True)
        
        if not records:
            return jsonify({
                "error": "No data available for export"
            }), 404
        
        # Create CSV in memory
        output = io.StringIO()
        if records:
            writer = csv.DictWriter(output, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
        
        # Convert to bytes for download
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                "Content-Disposition": f"attachment; filename=ecg_ml_dataset_{int(time.time())}.csv"
            }
        )
        
    except Exception as e:
        # Log the full error for debugging but return sanitized message to user
        print(f"Error exporting ML dataset: {str(e)}")
        return jsonify({"error": "Failed to export dataset. Please try again later."}), 500

@app.route("/api/clinical_statistics", methods=["GET"])
def get_clinical_statistics():
    """Get clinical data statistics"""
    if clinical_db is None:
        return jsonify({
            "error": "Clinical database not initialized"
        }), 503
    
    try:
        stats = clinical_db.get_clinical_statistics()
        return jsonify({
            "status": "success",
            "statistics": stats
        })
    except Exception as e:
        # Log the full error for debugging but return sanitized message to user
        print(f"Error getting clinical statistics: {str(e)}")
        return jsonify({"error": "Failed to retrieve statistics. Please try again later."}), 500

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000, use_reloader=False)
