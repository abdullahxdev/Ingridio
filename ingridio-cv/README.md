# 🥦 Ingridio — CV Backend
### AI-Powered Ingredient Detection from Fridge Photos

---

## 📌 Project Overview

**Ingridio CV Backend** is the computer vision engine behind the Ingridio cooking app. It solves one specific problem: a user opens their fridge, takes a photo, and within seconds knows exactly what ingredients they have available — without typing a single word.

The system accepts any fridge or pantry photo, runs it through a multi-step OpenCV preprocessing pipeline, sends it to OpenAI's vision API, and returns a clean, structured list of detected food ingredients as JSON.

This project falls under the **Object Detection and Recognition** category of Computer Vision, using a pre-trained deep learning model to identify and name multiple objects within a single image.

---

## 🎯 Problem Being Solved

Most recipe apps require users to manually search or type ingredients. This is slow, tedious, and inaccurate. Ingridio replaces that with a single camera scan.

**Input:** A photo of a fridge, pantry shelf, or kitchen countertop  
**Output:** A structured list of all food ingredients visible in the image

**Example:**
```
Input:  [fridge photo with vegetables, fruits, dairy items]
Output: ["eggs", "milk", "cheddar cheese", "yellow bell pepper", 
         "red onion", "tomato", "lettuce", "green apples", "bananas"]
```

---

## 🛠️ Technologies & Tools Used

### Programming Language
| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.12 | Core backend language |

### Frameworks & Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| **Flask** | Latest | Web server framework — hosts the API and web UI |
| **Flask-CORS** | Latest | Allows Flutter app to call the Python server cross-origin |
| **OpenCV** (`opencv-python-headless`) | Latest | Image preprocessing — resize, denoise, contrast enhancement |
| **OpenAI Responses API** | HTTPS | Multimodal vision inference endpoint |
| **python-dotenv** | Latest | Loads API keys securely from `.env` file |
| **NumPy** | Latest | Numerical array operations for image data |

### AI Model & API

| Component | Details |
|-----------|---------|
| **Model** | Configurable via `OPENAI_VISION_MODEL` (default: `gpt-4o-mini`) |
| **Provider** | OpenAI |
| **Type** | Pre-trained multimodal large language model |
| **Capability used** | Vision — image understanding and object recognition |
| **API endpoint** | `https://api.openai.com/v1/responses` |
| **Authentication** | API Key (stored in `.env`, loaded via `python-dotenv`) |
| **Fine-tuned?** | No — used as-is with prompt engineering |

---

## 🧠 How the Model Works

A multimodal OpenAI model is used for image understanding and ingredient extraction.

**It is NOT fine-tuned for this project.** Instead, the model's behavior is controlled through **prompt engineering** — carefully written instructions sent with every image that tell the model exactly what to do:

- Only identify food ingredients
- Be specific (e.g. "cheddar cheese" not just "cheese")
- Ignore non-food items
- Return a comma-separated list only

This approach is standard in professional AI applications. Fine-tuning would only be required if the base model performed poorly on food recognition.

---

## ⚙️ CV Pipeline — Step by Step

This is the core computer vision pipeline. Every image goes through all 5 steps in order.

```
Raw Image Bytes
      │
      ▼
┌─────────────────────────────────────────┐
│  STEP 1 — Image Load                    │
│  cv2.imdecode()                         │
│  Converts raw bytes → NumPy array (BGR) │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  STEP 2 — Resize                        │
│  cv2.resize() with INTER_AREA           │
│  Scales image to max 1024×1024          │
│  preserving original aspect ratio       │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  STEP 3 — Denoise                       │
│  cv2.fastNlMeansDenoisingColored()      │
│  Non-Local Means algorithm              │
│  Removes camera noise and grain         │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  STEP 4 — CLAHE Enhancement             │
│  Contrast Limited Adaptive Histogram    │
│  Equalisation on the L channel (LAB)    │
│  Improves visibility in dark fridges    │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  STEP 5 — OpenAI Vision Detection       │
│  Pre-trained model analyzes image       │
│  Returns comma-separated ingredient list│
└─────────────────┬───────────────────────┘
                  │
                  ▼
         JSON Response to client
   {"success": true, "ingredients": [...], "count": N}
```

### Why Each Step Matters

**Step 1 — Image Load**
The image arrives as raw binary bytes (from a form upload or Flutter HTTP request). OpenCV's `imdecode` converts this into a NumPy array — a 3D matrix of pixel values in BGR (Blue-Green-Red) format. This is the standard representation for all OpenCV operations.

**Step 2 — Resize**
Sending a 12-megapixel phone photo directly to an API is wasteful and slow. We scale the image down so its longest dimension is at most 1024 pixels, preserving the aspect ratio so nothing looks stretched. `INTER_AREA` interpolation is used because it produces the best quality when shrinking images (better than bilinear or nearest-neighbor).

**Step 3 — Denoise (Non-Local Means)**
Phone cameras, especially in low light (like inside a fridge), introduce digital noise — random pixel variations that look like grain. The Non-Local Means (NLM) algorithm removes this by comparing each pixel to similar pixels across the entire image and averaging them. This gives the AI model a cleaner image to analyze, improving detection accuracy.

**Step 4 — CLAHE (Contrast Enhancement)**
Fridges are often darker inside than outside. Low contrast makes it hard for any model to distinguish objects. CLAHE (Contrast Limited Adaptive Histogram Equalisation) solves this by enhancing contrast in small local regions of the image rather than globally — so bright areas don't get overexposed while dark areas become clearer. We apply it only to the Lightness (L) channel after converting to LAB color space, so colors remain natural.

**Step 5 — OpenAI Vision**
The preprocessed image is encoded and sent to the OpenAI Responses API with a structured prompt. The model returns a plain text, comma-separated list of ingredients, which is then parsed into JSON.

---

## 📁 Project Structure

```
ingridio-cv/
│
├── app.py              ← Flask server (API endpoints + web UI)
├── detector.py         ← Full CV pipeline (OpenCV + OpenAI Vision)
├── requirements.txt    ← All Python dependencies
├── .env                ← API key (never share or commit this)
├── README.md           ← This file
└── test_images/        ← Sample images for testing
```

### File Responsibilities

**`detector.py`** — The brain of the project. Contains the entire CV pipeline as modular functions:
- `load_image_from_bytes()` — Step 1
- `preprocess_image()` — Steps 2, 3, 4
- `opencv_to_data_url()` — OpenAI-compatible image conversion
- `detect_ingredients_with_openai()` — Step 5
- `detect_ingredients()` — Master function that calls all steps in order

**`app.py`** — The Flask web server. Contains:
- `GET /` — Serves the web UI (HTML page for testing without Flutter)
- `POST /detect` — Main API endpoint used by Flutter and the web UI
- `GET /health` — Quick check to confirm server is running

**`.env`** — Contains the OpenAI API key in this format:
```
OPENAI_API_KEY=your_key_here
```

---

## 🔌 API Reference

### POST `/detect`

Detects all food ingredients in an uploaded image.

**Request:**
```
Method:       POST
Content-Type: multipart/form-data
Field name:   image
Field value:  (JPG or PNG image file)
```

**Success Response:**
```json
{
  "success": true,
  "ingredients": [
    "eggs",
    "milk",
    "cheddar cheese",
    "yellow bell pepper",
    "red onion",
    "tomato",
    "lettuce",
    "green apples",
    "bananas"
  ],
  "count": 9
}
```

**Error Response:**
```json
{
  "success": false,
  "ingredients": [],
  "count": 0,
  "error": "Error description here"
}
```

### GET `/health`

```json
{"status": "ok", "message": "Ingridio CV server is running"}
```

---

## 🚀 Setup & Running

### Prerequisites
- Python 3.9 or above
- An OpenAI API key

### Installation

**1. Install all dependencies:**
```bash
py -m pip install -r requirements.txt
```

**2. Configure your API key:**

Open `.env` and replace the placeholder:
```
OPENAI_API_KEY=your_actual_openai_api_key_here
```

**3. Start the server:**
```bash
py app.py
```

**4. Open the web UI:**

Go to `http://localhost:5000` in your browser. Upload any fridge photo and click **Scan Ingredients**.

---

## 🔗 Flutter Integration

This backend is designed to be called from the Ingridio Flutter mobile app. The Flutter app:

1. Captures a photo using the device camera (`image_picker` package)
2. Sends it as a multipart POST request to `http://<server-ip>:5000/detect`
3. Receives the JSON ingredient list
4. Displays it to the user for confirmation and editing

**Flutter HTTP call (Dart):**
```dart
var request = http.MultipartRequest('POST', Uri.parse('http://localhost:5000/detect'));
request.files.add(await http.MultipartFile.fromPath('image', imageFile.path));
var response = await request.send();
var body = await response.stream.bytesToString();
var data = jsonDecode(body);
List<String> ingredients = List<String>.from(data['ingredients']);
```

During local development, both devices must be on the same WiFi network. For production, the Flask server would be deployed to a cloud platform (Render, Railway, etc.) and the URL updated in Flutter.

---

## 📊 Results

Tested on various fridge and pantry images. The system consistently detects:
- Fresh vegetables and fruits
- Dairy products (milk, cheese, butter, yogurt)
- Packaged items and beverages
- Leftovers in containers
- Items partially hidden behind other ingredients

**Sample result on test image:**
- Input: Full fridge photo with mixed items
- Detected: 23 ingredients including orange juice, milk, eggplant, garlic, dill, green onions, yellow bell pepper, red onion, tomato, lettuce, eggs, pastries, cheese, bananas, apples, plums, coconut, tangerine, pears
- Processing time: ~2-3 seconds

---

## ⚠️ Limitations

- Requires internet connection (OpenAI Vision is a cloud API)
- Very dark or blurry images reduce detection accuracy
- Items fully hidden behind other objects cannot be detected
- Free tier API limit: 250 requests/day (sufficient for development and demo)
- Server must be running for the Flutter app to work (local development only)

---

## 🔮 Future Scope

- Recipe generation from detected ingredients (implemented in Flutter app)
- Real-time camera stream detection (live video feed)
- Local on-device model for offline support
- Confidence scores and bounding boxes per ingredient
- Expiry date estimation from visual cues
- Deploy backend to cloud for 24/7 availability

---

## 👨‍💻 Author

**Ingridio CV Backend**  
Computer Vision Project — BSDS/BAI Semester 5/6  
COMSATS University Islamabad  
Subject: Computer Vision | Instructor: Maheen Gul