// ECG PDF Analyzer - Client-side JavaScript (PRODUCTION VERSION)

document.addEventListener('DOMContentLoaded', function() {
    console.log("✓ DOM Ready - Initializing app");
    initializeApp();
});

function initializeApp() {
    // Get DOM elements
    const fileInput = document.getElementById("file");
    const uploadArea = document.getElementById("uploadArea");
    const uploadSection = document.getElementById("uploadSection");
    const loading = document.getElementById("loading");
    const output = document.getElementById("output");
    const metricsDiv = document.getElementById("metrics");
    const featureSetSelector = document.getElementById("featureSet");
    
    // Store in window scope
    window.DOM = { fileInput, uploadArea, uploadSection, loading, output, metricsDiv, featureSetSelector };
    window.selectedFeatureSet = 'standard';
    window.uploadedResults = [];
    
    console.log("✓ DOM elements initialized");
    
    // Feature set selector - event listener
    if (featureSetSelector) {
        featureSetSelector.addEventListener("change", function(e) {
            window.selectedFeatureSet = this.value;
            console.log("✓ Feature set changed to:", window.selectedFeatureSet);
        });
        console.log("✓ Feature selector event listener added");
    } else {
        console.error("❌ Feature selector not found!");
    }
    
    // File input change handler
    if (fileInput) {
        fileInput.addEventListener("change", async function() {
            if (this.files && this.files.length > 0) {
                console.log("✓ Files selected:", this.files.length);
                await uploadFiles(Array.from(this.files));
            }
        });
        console.log("✓ File input listener added");
    }
    
    // Click to upload
    if (uploadArea) {
        uploadArea.addEventListener("click", function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log("✓ Upload area clicked");
            fileInput.click();
        });
        
        // Drag and drop
        uploadArea.addEventListener("dragover", function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.add("dragging");
        });
        
        uploadArea.addEventListener("dragleave", function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove("dragging");
        });
        
        uploadArea.addEventListener("drop", function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove("dragging");
            
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                const files = Array.from(e.dataTransfer.files);
                const pdfFiles = files.filter(f => f.type === "application/pdf");
                
                if (pdfFiles.length > 0) {
                    console.log("✓ Dropped files:", pdfFiles.length);
                    uploadFiles(pdfFiles);
                } else {
                    alert("Please drop PDF files only");
                }
            }
        });
        console.log("✓ Upload area listeners added");
    }
}

// Upload and process multiple files
async function uploadFiles(files) {
    console.log(`Starting upload: ${files.length} files, feature set: ${window.selectedFeatureSet}`);
    
    const { uploadSection, loading, output, metricsDiv } = window.DOM;
    
    // Show loading state
    uploadSection.style.display = "none";
    loading.style.display = "block";
    output.style.display = "none";
    window.uploadedResults = [];
    
    let processed = 0;
    let failed = 0;
    
    for (const file of files) {
        try {
            // Create form data
            const fd = new FormData();
            fd.append("file", file);
            
            // Send to server with feature set parameter
            const url = `/upload?features=${window.selectedFeatureSet}`;
            console.log(`Uploading: ${file.name} to ${url}`);
            
            const res = await fetch(url, {
                method: "POST",
                body: fd
            });
            
            const data = await res.json();
            
            if (res.ok) {
                // Store result with filename
                window.uploadedResults.push({
                    filename: file.name,
                    timestamp: new Date().toISOString(),
                    features: window.selectedFeatureSet,
                    metrics: data
                });
                processed++;
                console.log(`✓ Processed: ${file.name}`);
            } else {
                failed++;
                console.error(`✗ Failed: ${file.name} - ${data.error}`);
            }
        } catch (error) {
            failed++;
            console.error(`✗ Error processing ${file.name}: ${error.message}`);
        }
    }
    
    // Hide loading
    loading.style.display = "none";
    
    if (processed > 0) {
        console.log(`✓ Upload complete: ${processed} success, ${failed} failed`);
        
        // Display results
        displayMetrics(window.uploadedResults);
        output.style.display = "block";
        
        // Try to save to database
        await saveToDatabase(window.uploadedResults);
    } else {
        displayError(`Failed to process ${failed} file(s). Please check the files and try again.`);
    }
}

// Display metrics for all results
function displayMetrics(results) {
    if (!results || results.length === 0) {
        displayError("No results to display");
        return;
    }
    
    const { metricsDiv } = window.DOM;
    
    let html = '';
    
    // If multiple files, show summary
    if (results.length > 1) {
        html += `<div style="background: #e8eaff; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <strong>📊 Summary: ${results.length} files processed</strong>
                    <div style="margin-top: 10px; font-size: 13px;">
                        <strong>Feature Set:</strong> ${results[0].features}
                        <br><strong>Timestamp:</strong> ${new Date().toLocaleString()}
                    </div>
                </div>`;
    }
    
    // Show results for each file
    results.forEach((result, index) => {
        html += `<div style="margin-bottom: 20px; padding: 15px; background: #f8f9ff; border-radius: 8px; border-left: 3px solid #667eea;">
                    <div style="font-weight: 600; color: #333; margin-bottom: 10px;">
                        ${index + 1}. ${result.filename}
                    </div>`;
        
        html += '<div class="metrics-grid">';
        
        // Define important metrics with friendly names
        const metricNames = {
            "heart_rate_bpm": "Heart Rate (bpm)",
            "sdnn_ms": "SDNN (ms)",
            "rmssd_ms": "RMSSD (ms)",
            "pnn50_percent": "pNN50 (%)",
            "pnn20_percent": "pNN20 (%)",
            "sd1_ms": "SD1 (ms)",
            "sd2_ms": "SD2 (ms)",
            "lf_power": "LF Power",
            "hf_power": "HF Power",
            "lf_hf_ratio": "LF/HF Ratio",
        };
        
        // Display known metrics
        for (const [key, label] of Object.entries(metricNames)) {
            if (result.metrics.hasOwnProperty(key) && result.metrics[key] !== null && result.metrics[key] !== undefined) {
                const value = typeof result.metrics[key] === 'number' ? result.metrics[key].toFixed(2) : result.metrics[key];
                html += `
                    <div class="metric-card">
                        <div class="metric-label">${label}</div>
                        <div class="metric-value">${value}</div>
                    </div>
                `;
            }
        }
        
        html += '</div>';
        
        // Add raw JSON for debugging
        html += `<details style="margin-top: 10px;">
                    <summary style="cursor: pointer; color: #667eea; font-weight: 600; font-size: 12px;">View Raw Data</summary>
                    <pre style="margin-top: 10px;">${JSON.stringify(result.metrics, null, 2)}</pre>
                </details>`;
        
        html += '</div>';
    });
    
    metricsDiv.innerHTML = html;
}

// Display error message
function displayError(message) {
    const { metricsDiv, output } = window.DOM;
    
    metricsDiv.innerHTML = `
        <div class="metric-card error">
            <div class="metric-label">Error</div>
            <div style="color: #c00; margin-top: 10px;">${message}</div>
        </div>
    `;
    output.style.display = "block";
}

// Reset to upload another file
function resetUpload() {
    console.log("Reset upload form");
    const { uploadSection, loading, output, fileInput } = window.DOM;
    
    uploadSection.style.display = "block";
    loading.style.display = "none";
    output.style.display = "none";
    fileInput.value = "";
    window.uploadedResults = [];
}

// Save results to database
async function saveToDatabase(results) {
    try {
        console.log(`Saving ${results.length} results to database...`);
        
        const response = await fetch('/api/save_results', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(results)
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log("✓ Results saved to database:", data);
        } else {
            const err = await response.json();
            console.warn("Database save warning:", err);
        }
    } catch (error) {
        console.warn("Could not save to database:", error.message);
    }
}

// Export to Excel
function exportToExcel() {
    console.log("Exporting to Excel...");
    
    const btn = event.target;
    btn.disabled = true;
    const originalText = btn.textContent;
    btn.textContent = "⏳ Exporting...";
    
    fetch('/api/export_excel')
        .then(response => {
            if (response.ok) {
                return response.blob();
            } else {
                throw new Error("Export failed with status " + response.status);
            }
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `ecg_analysis_${new Date().getTime()}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
            
            console.log("✓ Excel file downloaded successfully");
            btn.disabled = false;
            btn.textContent = originalText;
        })
        .catch(error => {
            console.error("Export error:", error);
            alert(`Error: ${error.message}`);
            btn.disabled = false;
            btn.textContent = originalText;
        });
}

// View database
function viewDatabase() {
    console.log("Loading database view...");
    
    const btn = event.target;
    btn.disabled = true;
    const originalText = btn.textContent;
    btn.textContent = "⏳ Loading...";
    
    fetch('/api/get_data')
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error("Database load failed with status " + response.status);
            }
        })
        .then(data => {
            console.log(`✓ Loaded ${data.records.length} records from database`);
            
            const { metricsDiv, uploadSection, output } = window.DOM;
            
            // Display in a formatted way
            let html = `<div style="background: #f0f2ff; padding: 15px; border-radius: 8px;">
                        <strong>📊 Database Records: ${data.records.length}</strong>
                        <table style="width: 100%; margin-top: 10px; border-collapse: collapse; font-size: 12px;">
                            <tr style="background: #667eea; color: white;">
                                <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">File</th>
                                <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Date</th>
                                <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">HR (bpm)</th>
                                <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">SDNN (ms)</th>
                                <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">RMSSD (ms)</th>
                            </tr>`;
            
            data.records.forEach(record => {
                const metrics = record.metrics || record;
                const dateStr = record.timestamp || record.upload_timestamp || new Date().toISOString();
                const date = new Date(dateStr).toLocaleString();
                
                html += `<tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 8px; border: 1px solid #ddd;">${record.filename}</td>
                            <td style="padding: 8px; border: 1px solid #ddd;">${date}</td>
                            <td style="padding: 8px; text-align: center; border: 1px solid #ddd;">${metrics.heart_rate_bpm ? metrics.heart_rate_bpm.toFixed(1) : 'N/A'}</td>
                            <td style="padding: 8px; text-align: center; border: 1px solid #ddd;">${metrics.sdnn_ms ? metrics.sdnn_ms.toFixed(1) : 'N/A'}</td>
                            <td style="padding: 8px; text-align: center; border: 1px solid #ddd;">${metrics.rmssd_ms ? metrics.rmssd_ms.toFixed(1) : 'N/A'}</td>
                        </tr>`;
            });
            
            html += '</table></div>';
            
            metricsDiv.innerHTML = html;
            uploadSection.style.display = "none";
            output.style.display = "block";
            
            btn.disabled = false;
            btn.textContent = originalText;
        })
        .catch(error => {
            console.error("Database error:", error);
            alert(`Error: ${error.message}`);
            btn.disabled = false;
            btn.textContent = originalText;
        });
}
