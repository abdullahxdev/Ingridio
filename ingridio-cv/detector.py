"""
detector.py
-----------
The Computer Vision brain of Ingridio.

Pipeline:
  1. Load image (from file path or raw bytes)
  2. Preprocess with OpenCV (resize, denoise, colour-normalise)
  3. Send preprocessed image to Gemini Vision API
  4. Parse and return a clean ingredient list
"""

import cv2
import numpy as np
from google import genai
from PIL import Image
import os
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()

# New google-genai client (replaces deprecated google.generativeai)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ── Constants ────────────────────────────────────────────────────────────────
TARGET_SIZE  = (1024, 1024)   # max dimension we send to Gemini
DENOISE_H    = 10             # OpenCV denoising strength (higher = more blur)
GEMINI_MODEL = "gemini-2.5-flash"

# ── Step 1: Load image from bytes ────────────────────────────────────────────
def load_image_from_bytes(image_bytes: bytes) -> np.ndarray:
    """
    Convert raw image bytes (received from Flutter or web form)
    into an OpenCV numpy array (BGR format).
    """
    np_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image    = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image. Make sure it is a valid JPG or PNG.")
    return image


# ── Step 2: Preprocess with OpenCV ───────────────────────────────────────────
def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Clean and normalise the image before sending to Gemini.

    Steps:
      a) Resize  — keep aspect ratio, cap longest side at TARGET_SIZE
      b) Denoise — remove camera noise with Non-Local Means (NLM)
      c) CLAHE   — Contrast Limited Adaptive Histogram Equalisation
                   improves visibility in dark fridge photos
    Returns the processed image as a numpy array (BGR).
    """

    # (a) Resize while keeping aspect ratio
    h, w    = image.shape[:2]
    scale   = min(TARGET_SIZE[0] / w, TARGET_SIZE[1] / h)
    new_w   = int(w * scale)
    new_h   = int(h * scale)
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # (b) Denoise — works in BGR space
    denoised = cv2.fastNlMeansDenoisingColored(resized, None, DENOISE_H, DENOISE_H, 7, 21)

    # (c) CLAHE on the Lightness channel (convert BGR → LAB, apply, convert back)
    lab            = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
    l, a, b        = cv2.split(lab)
    clahe          = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_enhanced     = clahe.apply(l)
    lab_enhanced   = cv2.merge([l_enhanced, a, b])
    processed      = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

    return processed


# ── Step 3: Convert OpenCV image → PIL Image (for Gemini) ────────────────────
def opencv_to_pil(image: np.ndarray) -> Image.Image:
    """
    Gemini SDK accepts PIL Images.
    OpenCV uses BGR, PIL uses RGB — we must swap channels.
    """
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb_image)


# ── Step 4: Send to Gemini Vision and parse result ───────────────────────────
def detect_ingredients_with_gemini(pil_image: Image.Image) -> list[str]:
    """
    Send the image to Gemini Vision with a structured prompt.
    Returns a Python list of ingredient strings.
    """
    prompt = """
    You are an expert kitchen assistant with perfect ingredient identification skills.
    
    Look at this image carefully and identify ALL food ingredients, items, or groceries visible.
    
    Rules:
    - List every distinct food item you can see
    - Be specific (e.g. "cheddar cheese" not just "cheese", "cherry tomatoes" not just "tomatoes")
    - If an item looks nearly expired or leftover, still include it with a note e.g. "leftover rice"
    - Do NOT include non-food items (bottles of cleaning products, etc.)
    - Return ONLY a comma-separated list, nothing else
    - No numbering, no bullet points, no explanation — just the list
    
    Example output format:
    eggs, milk, cheddar cheese, bell pepper, leftover rice, lemon, butter
    """

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[prompt, pil_image]
    )

    raw_text    = response.text.strip()
    ingredients = [item.strip() for item in raw_text.split(",") if item.strip()]
    return ingredients


# ── Main public function ──────────────────────────────────────────────────────
def detect_ingredients(image_bytes: bytes) -> dict:
    """
    Full pipeline: bytes → OpenCV preprocessing → Gemini → ingredient list.

    Returns a dict:
    {
        "success": True,
        "ingredients": ["eggs", "milk", ...],
        "count": 7
    }
    """
    try:
        # Step 1: Load
        image = load_image_from_bytes(image_bytes)

        # Step 2: Preprocess with OpenCV
        processed_image = preprocess_image(image)

        # Step 3: Convert for Gemini
        pil_image = opencv_to_pil(processed_image)

        # Step 4: Detect with Gemini Vision
        ingredients = detect_ingredients_with_gemini(pil_image)

        return {
            "success": True,
            "ingredients": ingredients,
            "count": len(ingredients)
        }

    except Exception as e:
        return {
            "success": False,
            "ingredients": [],
            "count": 0,
            "error": str(e)
        }