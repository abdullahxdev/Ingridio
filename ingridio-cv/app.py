"""
app.py
------
Ingridio CV Backend — Flask Server

Endpoints:
  GET  /          → Web UI for testing (upload image, see results)
  POST /detect    → API endpoint (used by Flutter app)
  GET  /health    → Quick check that server is running
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from detector import detect_ingredients

app = Flask(__name__)
CORS(app)  # Allow Flutter app to call this server from any origin


# ── Web UI (for CV demo — no Flutter needed) ─────────────────────────────────
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ingridio — Fridge Vision Scanner</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', sans-serif;
            background: #0f1117;
            color: #f0f0f0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 40px 20px;
        }

        .logo {
            font-size: 2.2rem;
            font-weight: 800;
            color: #4ade80;
            letter-spacing: -1px;
            margin-bottom: 6px;
        }

        .tagline {
            color: #6b7280;
            font-size: 0.95rem;
            margin-bottom: 40px;
        }

        .card {
            background: #1c1f2e;
            border: 1px solid #2a2d3e;
            border-radius: 16px;
            padding: 32px;
            width: 100%;
            max-width: 560px;
            margin-bottom: 24px;
        }

        .card h2 {
            font-size: 1rem;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 20px;
        }

        .upload-area {
            border: 2px dashed #2a2d3e;
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: border-color 0.2s;
            position: relative;
        }

        .upload-area:hover { border-color: #4ade80; }

        .upload-area input[type="file"] {
            position: absolute;
            inset: 0;
            opacity: 0;
            cursor: pointer;
            width: 100%;
            height: 100%;
        }

        .upload-icon { font-size: 2.5rem; margin-bottom: 12px; }

        .upload-area p {
            color: #6b7280;
            font-size: 0.9rem;
        }

        #preview-container { display: none; margin-top: 16px; }

        #preview {
            width: 100%;
            border-radius: 10px;
            max-height: 300px;
            object-fit: cover;
        }

        .btn {
            width: 100%;
            padding: 14px;
            background: #4ade80;
            color: #0f1117;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            margin-top: 20px;
            transition: background 0.2s;
        }

        .btn:hover { background: #22c55e; }
        .btn:disabled { background: #2a2d3e; color: #6b7280; cursor: not-allowed; }

        .spinner {
            display: none;
            text-align: center;
            padding: 20px;
            color: #4ade80;
            font-size: 0.9rem;
        }

        .results { display: none; }

        .ingredient-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 8px;
        }

        .ingredient-tag {
            background: #0f2e1a;
            border: 1px solid #4ade80;
            color: #4ade80;
            padding: 6px 14px;
            border-radius: 999px;
            font-size: 0.875rem;
        }

        .count-badge {
            background: #4ade80;
            color: #0f1117;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 0.85rem;
            display: inline-block;
            margin-bottom: 16px;
        }

        .error-box {
            display: none;
            background: #2d1515;
            border: 1px solid #ef4444;
            color: #ef4444;
            padding: 14px 18px;
            border-radius: 10px;
            margin-top: 16px;
            font-size: 0.875rem;
        }

        .pipeline-steps {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .step {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 14px;
            background: #0f1117;
            border-radius: 8px;
            font-size: 0.875rem;
            color: #6b7280;
        }

        .step-num {
            background: #2a2d3e;
            color: #9ca3af;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 700;
            flex-shrink: 0;
        }
    </style>
</head>
<body>

    <div class="logo">🥦 Ingridio</div>
    <p class="tagline">Fridge Vision Scanner — CV Project Demo</p>

    <!-- Upload Card -->
    <div class="card">
        <h2>📸 Upload Fridge Photo</h2>
        <div class="upload-area" id="upload-area">
            <input type="file" id="file-input" accept="image/*" onchange="handleFile(event)">
            <div class="upload-icon">🖼️</div>
            <p>Click to upload or drag & drop</p>
            <p style="margin-top:6px; font-size:0.8rem;">JPG, PNG supported</p>
        </div>

        <div id="preview-container">
            <img id="preview" src="" alt="Preview">
        </div>

        <button class="btn" id="scan-btn" onclick="scanImage()" disabled>
            🔍 Scan Ingredients
        </button>

        <div class="error-box" id="error-box"></div>
    </div>

    <!-- Loading -->
    <div class="card spinner" id="spinner">
        ⏳ Preprocessing image with OpenCV...<br><br>
        🤖 Sending to Gemini Vision API...<br><br>
        Please wait a moment.
    </div>

    <!-- Results Card -->
    <div class="card results" id="results-card">
        <h2>✅ Detected Ingredients</h2>
        <div class="count-badge" id="count-badge"></div>
        <div class="ingredient-grid" id="ingredient-grid"></div>
    </div>

    <!-- CV Pipeline Explanation Card -->
    <div class="card">
        <h2>⚙️ CV Pipeline</h2>
        <div class="pipeline-steps">
            <div class="step">
                <div class="step-num">1</div>
                <span><strong style="color:#f0f0f0">Image Load</strong> — Raw bytes decoded into OpenCV NumPy array</span>
            </div>
            <div class="step">
                <div class="step-num">2</div>
                <span><strong style="color:#f0f0f0">Resize</strong> — Scaled to max 1024×1024 preserving aspect ratio</span>
            </div>
            <div class="step">
                <div class="step-num">3</div>
                <span><strong style="color:#f0f0f0">Denoise</strong> — Non-Local Means denoising removes camera noise</span>
            </div>
            <div class="step">
                <div class="step-num">4</div>
                <span><strong style="color:#f0f0f0">CLAHE</strong> — Adaptive contrast enhancement for dark fridge photos</span>
            </div>
            <div class="step">
                <div class="step-num">5</div>
                <span><strong style="color:#f0f0f0">Gemini Vision</strong> — Pre-trained model detects and names all ingredients</span>
            </div>
        </div>
    </div>

    <script>
        let selectedFile = null;

        function handleFile(event) {
            selectedFile = event.target.files[0];
            if (!selectedFile) return;

            const reader = new FileReader();
            reader.onload = (e) => {
                document.getElementById('preview').src = e.target.result;
                document.getElementById('preview-container').style.display = 'block';
                document.getElementById('scan-btn').disabled = false;
                document.getElementById('results-card').style.display = 'none';
                document.getElementById('error-box').style.display = 'none';
            };
            reader.readAsDataURL(selectedFile);
        }

        async function scanImage() {
            if (!selectedFile) return;

            // Show spinner, hide results
            document.getElementById('spinner').style.display = 'block';
            document.getElementById('results-card').style.display = 'none';
            document.getElementById('error-box').style.display = 'none';
            document.getElementById('scan-btn').disabled = true;

            const formData = new FormData();
            formData.append('image', selectedFile);

            try {
                const response = await fetch('/detect', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                document.getElementById('spinner').style.display = 'none';
                document.getElementById('scan-btn').disabled = false;

                if (data.success) {
                    showResults(data.ingredients, data.count);
                } else {
                    showError(data.error || 'Detection failed. Please try again.');
                }

            } catch (err) {
                document.getElementById('spinner').style.display = 'none';
                document.getElementById('scan-btn').disabled = false;
                showError('Could not connect to server: ' + err.message);
            }
        }

        function showResults(ingredients, count) {
            const grid = document.getElementById('ingredient-grid');
            grid.innerHTML = '';

            ingredients.forEach(item => {
                const tag = document.createElement('div');
                tag.className = 'ingredient-tag';
                tag.textContent = item;
                grid.appendChild(tag);
            });

            document.getElementById('count-badge').textContent = count + ' ingredients found';
            document.getElementById('results-card').style.display = 'block';
        }

        function showError(message) {
            const box = document.getElementById('error-box');
            box.textContent = '⚠️ ' + message;
            box.style.display = 'block';
        }
    </script>

</body>
</html>
"""


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the web UI — used for CV demo."""
    return render_template_string(HTML_PAGE)


@app.route("/health")
def health():
    """Quick check that the server is alive."""
    return jsonify({"status": "ok", "message": "Ingridio CV server is running"})


@app.route("/detect", methods=["POST"])
def detect():
    """
    Main API endpoint.

    Accepts: multipart/form-data with an 'image' field
    Returns: JSON with detected ingredients

    Used by:
      - The web UI (for CV demo)
      - Flutter app (for mobile integration)
    """
    if "image" not in request.files:
        return jsonify({
            "success": False,
            "error": "No image provided. Send a multipart form with field name 'image'."
        }), 400

    image_file  = request.files["image"]
    image_bytes = image_file.read()

    if len(image_bytes) == 0:
        return jsonify({"success": False, "error": "Empty image file."}), 400

    # Run the full CV pipeline
    result = detect_ingredients(image_bytes)
    return jsonify(result)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🥦 Ingridio CV Server")
    print("=" * 40)
    print("📡 Running at: http://localhost:5000")
    print("🌐 Web UI:     http://localhost:5000")
    print("🔌 API:        POST http://localhost:5000/detect")
    print("=" * 40)
    print("Press CTRL+C to stop\n")
    app.run(debug=True, host="0.0.0.0", port=5000)