from flask import Flask, request, jsonify, send_file, send_from_directory
from ecg_modules import pdf_extract, digitize, analyse, ml_features, database
from ecg_modules.excel_export import export_to_excel
import os
import time
import io
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Ensure tmp directory exists
os.makedirs("tmp", exist_ok=True)

# Initialize database
db = database.get_db()

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

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000, use_reloader=False)
