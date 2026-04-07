"""
app.py
------
Ingridio — Flask Backend

Endpoints:
  GET  /         — Web UI (upload photo, view ingredients + edge detection results)
  POST /detect   — API used by Flutter app — returns ingredients + edge photos
  GET  /health   — Server liveness check
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from detector import detect_ingredients

app  = Flask(__name__)
CORS(app)


# ── Web UI ────────────────────────────────────────────────────────────────────
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ingridio</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { 
            box-sizing: border-box;
        }

        html, body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #FFFFFF;
            color: #1F2937;
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        body {
            padding: 56px 24px;
        }

        /* ─── Header ─────────────────────────────────────────────────────────── */
        .header {
            text-align: center;
            width: 100%;
            max-width: 720px;
            margin-bottom: 56px;
        }

        .logo {
            font-size: 36px;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: #10B981;
            margin: 0;
            padding: 0;
            line-height: 1;
        }

        .tagline {
            color: #6B7280;
            font-size: 15px;
            font-weight: 500;
            letter-spacing: 0.2px;
            margin-top: 12px;
            padding: 0;
        }

        /* ─── Container ──────────────────────────────────────────────────────── */
        .container {
            width: 100%;
            max-width: 720px;
        }

        .card {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 40px;
            margin-bottom: 32px;
            transition: all 0.2s ease;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }

        .card:hover {
            border-color: #D1D5DB;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        }

        .card-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 28px;
            padding-bottom: 20px;
            border-bottom: 1px solid #F3F4F6;
        }

        .card-title {
            font-size: 15px;
            font-weight: 600;
            letter-spacing: 0.4px;
            color: #1F2937;
            text-transform: uppercase;
            margin: 0;
            padding: 0;
        }

        .icon {
            width: 22px;
            height: 22px;
            stroke: #10B981;
            stroke-width: 1.5;
            flex-shrink: 0;
        }

        /* ─── Upload Area ────────────────────────────────────────────────────── */
        .upload-container {
            position: relative;
            border: 2px dashed #D1D5DB;
            border-radius: 10px;
            padding: 72px 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.25s ease;
            background: #FAFBFC;
        }

        .upload-container:hover {
            border-color: #10B981;
            background: #F0FDF4;
        }

        .upload-container input {
            position: absolute;
            inset: 0;
            opacity: 0;
            cursor: pointer;
            width: 100%;
            height: 100%;
        }

        .upload-icon {
            width: 56px;
            height: 56px;
            stroke: #6B7280;
            stroke-width: 1.5;
            margin: 0 auto 20px;
            display: block;
            transition: stroke 0.2s ease;
        }

        .upload-container:hover .upload-icon {
            stroke: #10B981;
        }

        .upload-text {
            font-size: 16px;
            font-weight: 600;
            color: #1F2937;
            margin: 0 0 8px 0;
            padding: 0;
        }

        .upload-subtext {
            font-size: 14px;
            color: #9CA3AF;
            margin: 0;
            padding: 0;
        }

        /* ─── Preview ────────────────────────────────────────────────────────── */
        #preview-container {
            display: none;
            position: relative;
            border-radius: 10px;
            overflow: hidden;
            background: #F9FAFB;
            border: 1px solid #E5E7EB;
            margin-top: 32px;
        }

        #preview {
            width: 100%;
            max-height: 420px;
            object-fit: cover;
            display: block;
        }

        .preview-remove {
            position: absolute;
            top: 16px;
            right: 16px;
            background: rgba(31, 41, 55, 0.85);
            color: #FFFFFF;
            border: none;
            padding: 10px 16px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s ease;
            font-family: 'Inter', sans-serif;
        }

        .preview-remove:hover {
            background: rgba(31, 41, 55, 0.95);
        }

        /* ─── Button ─────────────────────────────────────────────────────────── */
        .btn {
            width: 100%;
            padding: 14px 20px;
            background: linear-gradient(135deg, #10B981 0%, #059669 100%);
            color: #FFFFFF;
            border: none;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 600;
            letter-spacing: 0.3px;
            cursor: pointer;
            margin-top: 32px;
            transition: all 0.2s ease;
            font-family: 'Inter', sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2);
        }

        .btn:hover:not(:disabled) {
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(16, 185, 129, 0.3);
        }

        .btn:active:not(:disabled) {
            transform: translateY(0);
        }

        .btn:disabled {
            background: #E5E7EB;
            color: #9CA3AF;
            cursor: not-allowed;
            box-shadow: none;
        }

        /* ─── Loading State ──────────────────────────────────────────────────── */
        .loader {
            display: none;
            text-align: center;
            padding: 48px 32px;
        }

        .loader-text {
            font-size: 15px;
            color: #6B7280;
            margin-bottom: 24px;
            font-weight: 500;
        }

        .loader-bar {
            width: 100%;
            height: 3px;
            background: #E5E7EB;
            border-radius: 2px;
            overflow: hidden;
        }

        .loader-progress {
            height: 100%;
            background: linear-gradient(90deg, #10B981, #059669);
            animation: loading 2.5s ease-in-out infinite;
        }

        @keyframes loading {
            0% { width: 0%; }
            50% { width: 100%; }
            100% { width: 0%; }
        }

        /* ─── Results ────────────────────────────────────────────────────────── */
        #results-card, #edges-card {
            display: none;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .count-badge {
            display: inline-block;
            background: #F0FDF4;
            border: 1px solid #BBEF63;
            color: #15803D;
            padding: 10px 18px;
            border-radius: 24px;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 24px;
        }

        .ingredients-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-top: 16px;
        }

        .ingredient-tag {
            background: #F0FDF4;
            border: 1px solid #DCFCE7;
            color: #15803D;
            padding: 10px 16px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s ease;
        }

        .ingredient-tag:hover {
            background: #DCFCE7;
            border-color: #10B981;
            box-shadow: 0 2px 8px rgba(16, 185, 129, 0.15);
        }

        /* ─── Edge Detection Grid ────────────────────────────────────────────── */
        .edge-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }

        @media (max-width: 640px) {
            .edge-grid {
                grid-template-columns: 1fr;
            }
        }

        .edge-item {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .edge-label {
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.5px;
            color: #6B7280;
            text-transform: uppercase;
        }

        .edge-item img {
            width: 100%;
            border-radius: 10px;
            border: 1px solid #E5E7EB;
            background: #F9FAFB;
            transition: all 0.2s ease;
            display: block;
        }

        .edge-item img:hover {
            border-color: #10B981;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);
        }

        /* ─── Error ──────────────────────────────────────────────────────────── */
        .error-box {
            display: none;
            background: #FEF2F2;
            border: 1px solid #FECACA;
            color: #991B1B;
            padding: 14px 18px;
            border-radius: 10px;
            margin-top: 20px;
            font-size: 14px;
            font-weight: 500;
            animation: slideDown 0.2s ease;
        }

        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* ─── Pipeline Steps ─────────────────────────────────────────────────── */
        .pipeline-steps {
            display: flex;
            flex-direction: column;
            gap: 14px;
        }

        .step {
            display: flex;
            gap: 18px;
            padding: 18px;
            background: #F9FAFB;
            border: 1px solid #E5E7EB;
            border-radius: 10px;
            transition: all 0.2s ease;
        }

        .step:hover {
            background: #F3F4F6;
            border-color: #D1D5DB;
        }

        .step-num {
            background: linear-gradient(135deg, #10B981 0%, #059669 100%);
            color: #FFFFFF;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            font-weight: 700;
            flex-shrink: 0;
        }

        .step-content {
            flex: 1;
        }

        .step-title {
            font-size: 15px;
            font-weight: 600;
            color: #1F2937;
            margin: 0 0 6px 0;
            padding: 0;
        }

        .step-desc {
            font-size: 14px;
            color: #6B7280;
            line-height: 1.6;
            margin: 0;
            padding: 0;
        }

        /* ─── Responsive ─────────────────────────────────────────────────────── */
        @media (max-width: 640px) {
            body {
                padding: 40px 16px;
            }

            .header {
                margin-bottom: 40px;
            }

            .logo {
                font-size: 32px;
            }

            .card {
                padding: 28px;
            }

            .upload-container {
                padding: 48px 24px;
            }
        }
    </style>
</head>
<body>

<div class="header">
    <h1 class="logo">Ingridio</h1>
    <p class="tagline">AI-Powered Ingredient Detection</p>
</div>

<div class="container">

    <!-- Upload Card -->
    <div class="card">
        <div class="card-header">
            <svg class="icon" fill="none" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
            </svg>
            <h2 class="card-title">Upload Photo</h2>
        </div>
        <div class="upload-container">
            <input type="file" id="file-input" accept="image/*" onchange="handleFile(event)">
            <svg class="upload-icon" fill="none" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
            </svg>
            <p class="upload-text">Click to upload or drag and drop</p>
            <p class="upload-subtext">JPG, PNG — up to 10 MB</p>
        </div>
        <div id="preview-container">
            <img id="preview" src="" alt="Photo preview">
            <button class="preview-remove" onclick="clearPreview()">Remove</button>
        </div>
        <button class="btn" id="scan-btn" onclick="scanImage()" disabled>
            <svg class="icon" fill="none" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
            Analyze Ingredients
        </button>
        <div class="error-box" id="error-box"></div>
    </div>

    <!-- Loading State -->
    <div class="card loader" id="loader">
        <p class="loader-text">Processing photo...</p>
        <div class="loader-bar">
            <div class="loader-progress"></div>
        </div>
    </div>

    <!-- Results Card -->
    <div class="card" id="results-card">
        <div class="card-header">
            <svg class="icon" fill="none" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <h2 class="card-title">Detected Ingredients</h2>
        </div>
        <div class="count-badge" id="count-badge"></div>
        <div class="ingredients-grid" id="ingredients-grid"></div>
    </div>

    <!-- Edge Detection Card -->
    <div class="card" id="edges-card">
        <div class="card-header">
            <svg class="icon" fill="none" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 5a2 2 0 012-2h12a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V5z"/>
            </svg>
            <h2 class="card-title">Edge Detection Results</h2>
        </div>
        <div class="edge-grid">
            <div class="edge-item">
                <span class="edge-label">Sobel X — Vertical Edges</span>
                <img id="img-sobel-x" src="" alt="Sobel X">
            </div>
            <div class="edge-item">
                <span class="edge-label">Sobel Y — Horizontal Edges</span>
                <img id="img-sobel-y" src="" alt="Sobel Y">
            </div>
            <div class="edge-item">
                <span class="edge-label">Sobel Full — All Edges</span>
                <img id="img-sobel-combined" src="" alt="Sobel Full">
            </div>
            <div class="edge-item">
                <span class="edge-label">Canny — Optimal Detection</span>
                <img id="img-canny" src="" alt="Canny">
            </div>
        </div>
    </div>

    <!-- Pipeline Card -->
    <div class="card">
        <div class="card-header">
            <svg class="icon" fill="none" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
            </svg>
            <h2 class="card-title">Processing Pipeline</h2>
        </div>
        <div class="pipeline-steps">
            <div class="step">
                <div class="step-num">1</div>
                <div class="step-content">
                    <p class="step-title">Photo Load</p>
                    <p class="step-desc">Raw bytes decoded into OpenCV array (BGR format) using cv2.imdecode</p>
                </div>
            </div>
            <div class="step">
                <div class="step-num">2</div>
                <div class="step-content">
                    <p class="step-title">Resize</p>
                    <p class="step-desc">Aspect-ratio-preserving downscale to 1024×1024 using INTER_AREA interpolation</p>
                </div>
            </div>
            <div class="step">
                <div class="step-num">3</div>
                <div class="step-content">
                    <p class="step-title">Noise Reduction</p>
                    <p class="step-desc">Three-step filtering: Gaussian Blur (electronic noise), Bilateral Filter (salt-and-pepper), NLM Denoise (texture-preserving)</p>
                </div>
            </div>
            <div class="step">
                <div class="step-num">4</div>
                <div class="step-content">
                    <p class="step-title">Contrast Enhancement</p>
                    <p class="step-desc">CLAHE adaptive histogram equalisation (8×8 tiles, clip 2.0) on L channel in LAB space</p>
                </div>
            </div>
            <div class="step">
                <div class="step-num">5</div>
                <div class="step-content">
                    <p class="step-title">Edge Detection</p>
                    <p class="step-desc">Sobel (3×3 kernels) and Canny (5-stage: Gaussian, Sobel, suppression, threshold, hysteresis)</p>
                </div>
            </div>
            <div class="step">
                <div class="step-num">6</div>
                <div class="step-content">
                    <p class="step-title">AI Analysis</p>
                    <p class="step-desc">Processed photo sent to OpenAI Vision for ingredient identification</p>
                </div>
            </div>
        </div>
    </div>

</div>

<script>
    let selectedFile = null;

    function handleFile(event) {
        selectedFile = event.target.files[0];
        if (!selectedFile) return;
        const reader = new FileReader();
        reader.onload = e => {
            document.getElementById('preview').src = e.target.result;
            document.getElementById('preview-container').style.display = 'block';
            document.getElementById('scan-btn').disabled = false;
            document.getElementById('results-card').style.display = 'none';
            document.getElementById('edges-card').style.display = 'none';
            document.getElementById('error-box').style.display = 'none';
        };
        reader.readAsDataURL(selectedFile);
    }

    function clearPreview() {
        selectedFile = null;
        document.getElementById('file-input').value = '';
        document.getElementById('preview-container').style.display = 'none';
        document.getElementById('scan-btn').disabled = true;
        document.getElementById('results-card').style.display = 'none';
        document.getElementById('edges-card').style.display = 'none';
    }

    async function scanImage() {
        if (!selectedFile) return;

        document.getElementById('loader').style.display = 'block';
        document.getElementById('results-card').style.display = 'none';
        document.getElementById('edges-card').style.display = 'none';
        document.getElementById('error-box').style.display = 'none';
        document.getElementById('scan-btn').disabled = true;

        const formData = new FormData();
        formData.append('image', selectedFile);

        try {
            const response = await fetch('/detect', { method: 'POST', body: formData });
            const data = await response.json();

            document.getElementById('loader').style.display = 'none';
            document.getElementById('scan-btn').disabled = false;

            if (data.success) {
                showIngredients(data.ingredients, data.count);
                if (data.edges) showEdges(data.edges);
            } else {
                showError(data.error || 'Analysis failed. Please try again.');
            }
        } catch (err) {
            document.getElementById('loader').style.display = 'none';
            document.getElementById('scan-btn').disabled = false;
            showError('Could not connect to server: ' + err.message);
        }
    }

    function showIngredients(ingredients, count) {
        const grid = document.getElementById('ingredients-grid');
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

    function showEdges(edges) {
        const map = {
            'sobel_x':        'img-sobel-x',
            'sobel_y':        'img-sobel-y',
            'sobel_combined': 'img-sobel-combined',
            'canny':          'img-canny',
        };
        for (const [key, id] of Object.entries(map)) {
            if (edges[key]) {
                document.getElementById(id).src = 'data:image/png;base64,' + edges[key];
            }
        }
        document.getElementById('edges-card').style.display = 'block';
    }

    function showError(message) {
        const box = document.getElementById('error-box');
        box.textContent = message;
        box.style.display = 'block';
    }
</script>
</body>
</html>
"""


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "message": "Ingridio CV server is running"})


@app.route("/detect", methods=["POST"])
def detect():
    """
    Primary API endpoint.

    Accepts : multipart/form-data with field 'image' (JPG or PNG)
    Returns : JSON with detected ingredients AND base64-encoded edge photos

    Response shape:
    {
        "success":     true,
        "ingredients": ["eggs", "cheese", ...],
        "count":       7,
        "edges": {
            "sobel_x":        "<base64 PNG>",
            "sobel_y":        "<base64 PNG>",
            "sobel_combined": "<base64 PNG>",
            "canny":          "<base64 PNG>"
        }
    }
    """
    if "image" not in request.files:
        return jsonify({
            "success": False,
            "error": "No photo provided. Send with field 'image'."
        }), 400

    image_bytes = request.files["image"].read()
    if len(image_bytes) == 0:
        return jsonify({"success": False, "error": "Empty photo file."}), 400

    result = detect_ingredients(image_bytes)
    return jsonify(result)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\nIngridio CV Server")
    print("=" * 45)
    print("Running at : http://localhost:5000")
    print("Web UI     : http://localhost:5000")
    print("API        : POST http://localhost:5000/detect")
    print("=" * 45)
    print("Press CTRL+C to stop\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
