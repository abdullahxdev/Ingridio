"""
detector.py
-----------
Ingridio — Computer Vision Pipeline

Category: Image Filtering and Manipulation
  - Noise Removal  : Gaussian Blur, Median Blur, Non-Local Means (NLM)
  - Edge Detection : Sobel (X/Y/combined), Canny

Full pipeline for a single image:
  1. Load  (bytes → OpenCV NumPy array)
  2. Resize (aspect-ratio-preserving, max 1024px)
  3. Denoise — Gaussian Blur → Median Blur → NLM
  4. CLAHE  — adaptive contrast on the Lightness channel
  5. Edge Detection — Sobel + Canny on a grayscale copy
    6. OpenAI Vision API — ingredient identification

Each CV step is its own named function so viva questions can be answered
about any single step independently.
"""

import cv2
import numpy as np
import base64
import json
import os
from urllib import error as urlerror
from urllib import request as urlrequest
from dotenv import load_dotenv

# ── Configuration ─────────────────────────────────────────────────────────────
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

TARGET_SIZE = (1024, 1024)   # max dimension sent to OpenAI
DENOISE_H = 10               # NLM denoising strength (luminance)
OPENAI_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini").strip()
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


# ════════════════════════════════════════════════════════════════════════════════
# STEP 1 — IMAGE LOADING
# ════════════════════════════════════════════════════════════════════════════════

def load_image_from_bytes(image_bytes: bytes) -> np.ndarray:
    """
    Decode raw image bytes (JPG / PNG) into an OpenCV BGR NumPy array.

    cv2.imdecode works in-memory — no temp files needed.
    Returns a uint8 array with shape (H, W, 3).
    """
    np_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image    = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image. Ensure the file is a valid JPG or PNG.")
    return image


# ════════════════════════════════════════════════════════════════════════════════
# STEP 2 — RESIZE
# ════════════════════════════════════════════════════════════════════════════════

def resize_image(image: np.ndarray,
                 max_size: tuple[int, int] = TARGET_SIZE) -> np.ndarray:
    """
    Downscale the image so neither dimension exceeds max_size,
    while preserving the original aspect ratio.

    Uses INTER_AREA interpolation — best quality for downscaling because
    it averages pixel blocks rather than sampling individual pixels.
    If the image is already smaller than max_size, it is returned unchanged.
    """
    h, w  = image.shape[:2]
    scale = min(max_size[0] / w, max_size[1] / h, 1.0)   # never upscale
    if scale == 1.0:
        return image
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)


# ════════════════════════════════════════════════════════════════════════════════
# STEP 3 — NOISE REMOVAL  (three distinct methods)
# ════════════════════════════════════════════════════════════════════════════════

def apply_gaussian_blur(image: np.ndarray,
                        kernel_size: int = 5,
                        sigma: float = 0) -> np.ndarray:
    """
    Gaussian Blur — low-pass spatial filter.

    Every output pixel is a weighted average of its neighbours, where weights
    follow a 2-D Gaussian distribution (bell curve). This blurs both noise AND
    edges, which is why it is applied BEFORE edge detection, not after.

    kernel_size : must be odd (3, 5, 7, …); larger = more blur
    sigma       : standard deviation; 0 = auto-computed from kernel_size
    """
    # Kernel must be odd and positive
    k = kernel_size if kernel_size % 2 == 1 else kernel_size + 1
    return cv2.GaussianBlur(image, (k, k), sigma)


def apply_median_blur(image: np.ndarray,
                      kernel_size: int = 5) -> np.ndarray:
    """
    Median Blur — non-linear rank-order filter.

    Replaces each pixel with the MEDIAN of its neighbourhood.
    Unlike Gaussian blur, it completely discards extreme outlier values
    (salt-and-pepper noise), making it highly effective for impulse noise
    found in low-quality fridge photos.

    kernel_size : must be odd (3, 5, 7, …)
    """
    k = kernel_size if kernel_size % 2 == 1 else kernel_size + 1
    return cv2.medianBlur(image, k)


def apply_nlm_denoise(image: np.ndarray,
                      h: int = DENOISE_H) -> np.ndarray:
    """
    Non-Local Means (NLM) Denoising — state-of-the-art noise removal.

    Unlike local filters, NLM compares PATCHES across the entire image.
    For each pixel, it searches for similar patches everywhere and averages
    them — preserving textures and fine details that Gaussian/Median blur
    would destroy.

    h : filter strength; higher = smoother but may lose fine detail
    The two '7' and '21' parameters are the template patch size (7×7) and
    the search window size (21×21).

    This is the highest-quality denoiser in OpenCV, used as the final
    denoising step before CLAHE.
    """
    return cv2.fastNlMeansDenoisingColored(image, None, h, h, 7, 21)


def full_denoise_pipeline(image: np.ndarray) -> np.ndarray:
    """
    Apply all three noise-removal steps in sequence:
      1. Gaussian blur  — smooth out Gaussian/electronic noise
      2. Median blur    — eliminate salt-and-pepper impulse noise
      3. NLM denoise    — high-quality final pass preserving texture

    Returns the cleaned BGR image.
    """
    step1 = apply_gaussian_blur(image, kernel_size=3)   # light pass first
    step2 = apply_median_blur(step1,   kernel_size=3)
    step3 = apply_nlm_denoise(step2,   h=DENOISE_H)
    return step3


# ════════════════════════════════════════════════════════════════════════════════
# STEP 4 — CONTRAST ENHANCEMENT (CLAHE)
# ════════════════════════════════════════════════════════════════════════════════

def apply_clahe(image: np.ndarray,
                clip_limit: float = 2.0,
                tile_grid: tuple[int, int] = (8, 8)) -> np.ndarray:
    """
    CLAHE — Contrast Limited Adaptive Histogram Equalisation.

    Standard histogram equalisation stretches contrast globally, which can
    over-brighten some regions. CLAHE divides the image into a grid of tiles
    (tile_grid) and equalises each tile independently, then stitches them
    back together with bilinear interpolation.

    clip_limit : maximum slope of the CDF per tile; prevents over-amplifying
                 noise in very uniform regions.

    Applied only on the Lightness (L) channel in LAB colour space so that
    hue and saturation (A, B channels) are untouched — colours stay natural.
    """
    lab              = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b          = cv2.split(lab)
    clahe            = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid)
    l_enhanced       = clahe.apply(l)
    lab_enhanced     = cv2.merge([l_enhanced, a, b])
    return cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)


# ════════════════════════════════════════════════════════════════════════════════
# STEP 5 — EDGE DETECTION  (two distinct methods)
# ════════════════════════════════════════════════════════════════════════════════

def apply_sobel_edges(image: np.ndarray) -> dict:
    """
    Sobel Edge Detection — gradient-based method.

    Computes the image gradient in X (vertical edges) and Y (horizontal edges)
    using 3×3 Sobel kernels — a smoothed finite-difference approximation of the
    first derivative.

    Sobel X kernel:  [[-1, 0, 1],   Sobel Y kernel:  [[-1, -2, -1],
                      [-2, 0, 2],                      [ 0,  0,  0],
                      [-1, 0, 1]]                      [ 1,  2,  1]]

    Magnitude = sqrt(Gx² + Gy²) approximated as |Gx| + |Gy| for speed.

    Returns a dict with:
      'sobel_x'    : edges in vertical direction (responds to horizontal changes)
      'sobel_y'    : edges in horizontal direction (responds to vertical changes)
      'sobel_combined' : magnitude of both — complete edge map
    """
    gray    = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)   # dx=1, dy=0
    sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)   # dx=0, dy=1

    # Convert to uint8 for display
    abs_x   = cv2.convertScaleAbs(sobel_x)
    abs_y   = cv2.convertScaleAbs(sobel_y)
    combined = cv2.addWeighted(abs_x, 0.5, abs_y, 0.5, 0)

    return {
        "sobel_x":        abs_x,
        "sobel_y":        abs_y,
        "sobel_combined": combined,
    }


def apply_canny_edges(image: np.ndarray,
                      low_threshold: int  = 50,
                      high_threshold: int = 150) -> np.ndarray:
    """
    Canny Edge Detection — multi-stage optimal edge detector.

    Canny is the gold standard for edge detection. It runs five stages:
      1. Gaussian smoothing      — reduce noise before differentiation
      2. Gradient computation    — Sobel in X and Y
      3. Non-maximum suppression — thin edges to single-pixel width
      4. Double thresholding     — classify pixels as strong / weak / non-edge
      5. Edge tracking by hysteresis — keep weak pixels only if connected
                                       to a strong pixel

    low_threshold  : pixels below this are discarded
    high_threshold : pixels above this are definite edges
    Pixels between the two thresholds are kept only if connected to a strong edge.

    Returns a binary (0 / 255) uint8 grayscale edge map.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Canny(gray, low_threshold, high_threshold)


def run_edge_detection(image: np.ndarray) -> dict:
    """
    Run both Sobel and Canny on the preprocessed image.

    Returns a dict with all four edge images as base64-encoded PNGs
    (ready to embed directly in HTML <img> tags for the web demo).

    Keys: 'sobel_x', 'sobel_y', 'sobel_combined', 'canny'
    """
    sobel_results = apply_sobel_edges(image)
    canny_result  = apply_canny_edges(image)

    output = {}
    edge_images = {
        "sobel_x":        sobel_results["sobel_x"],
        "sobel_y":        sobel_results["sobel_y"],
        "sobel_combined": sobel_results["sobel_combined"],
        "canny":          canny_result,
    }

    for key, img in edge_images.items():
        _, buf = cv2.imencode(".png", img)
        output[key] = base64.b64encode(buf).decode("utf-8")

    return output


# ════════════════════════════════════════════════════════════════════════════════
# STEP 6 — OPENAI VISION
# ════════════════════════════════════════════════════════════════════════════════

def opencv_to_data_url(image: np.ndarray) -> str:
    """
    Encode an OpenCV image to JPEG and return a base64 data URL.
    This can be sent directly to the OpenAI vision endpoints.
    """
    ok, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
    if not ok:
        raise ValueError("Failed to encode image for OpenAI request.")
    b64 = base64.b64encode(encoded.tobytes()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def _extract_openai_text(payload: dict) -> str:
    """
    Extract text robustly from OpenAI Responses API payload.
    """
    if isinstance(payload.get("output_text"), str) and payload["output_text"].strip():
        return payload["output_text"].strip()

    output = payload.get("output")
    if isinstance(output, list):
        chunks = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") in {"output_text", "text"}:
                    text_val = block.get("text")
                    if isinstance(text_val, str) and text_val.strip():
                        chunks.append(text_val.strip())
        if chunks:
            return "\n".join(chunks)

    raise ValueError("OpenAI response did not contain text output.")


def detect_ingredients_with_openai(data_url: str) -> list[str]:
    """
    Send the preprocessed image to OpenAI Vision and parse a clean ingredient list.
    """
    if not OPENAI_API_KEY:
        raise ValueError("Missing OPENAI_API_KEY in environment.")

    prompt = """
    You are an expert kitchen assistant with perfect ingredient identification skills.

    Look at this image carefully and identify ALL food ingredients, items, or groceries visible.

    Rules:
    - List every distinct food item you can see
    - Be specific (e.g. "cheddar cheese" not just "cheese")
    - Include nearly-expired items with a note e.g. "leftover rice"
    - Do NOT include non-food items
    - Return ONLY a comma-separated list, nothing else
    - No numbering, no bullets, no explanation — just the list

    Example: eggs, milk, cheddar cheese, bell pepper, leftover rice, lemon, butter
    """.strip()

    payload = {
        "model": OPENAI_MODEL,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": data_url},
                ],
            }
        ],
        "temperature": 0,
    }

    req = urlrequest.Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlrequest.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
    except urlerror.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
        raise ValueError(f"OpenAI request failed ({exc.code}): {detail}") from exc
    except urlerror.URLError as exc:
        raise ValueError(f"Could not reach OpenAI API: {exc.reason}") from exc

    response_json = json.loads(body)
    raw_text = _extract_openai_text(response_json)
    ingredients = [item.strip() for item in raw_text.split(",") if item.strip()]
    return ingredients


# ════════════════════════════════════════════════════════════════════════════════
# PUBLIC API — single entry point used by app.py
# ════════════════════════════════════════════════════════════════════════════════

def detect_ingredients(image_bytes: bytes) -> dict:
    """
    Full CV pipeline:
      bytes → load → resize → denoise (Gaussian + Median + NLM)
                        → CLAHE → edge detection (Sobel + Canny) → OpenAI Vision

    Returns:
    {
        "success":      True,
        "ingredients":  ["eggs", "milk", ...],
        "count":        7,
        "edges": {
            "sobel_x":        "<base64 PNG>",
            "sobel_y":        "<base64 PNG>",
            "sobel_combined": "<base64 PNG>",
            "canny":          "<base64 PNG>"
        }
    }
    """
    try:
        # 1 — Load
        image = load_image_from_bytes(image_bytes)

        # 2 — Resize
        image = resize_image(image)

        # 3 — Denoise (Gaussian + Median + NLM)
        denoised = full_denoise_pipeline(image)

        # 4 — CLAHE contrast enhancement
        enhanced = apply_clahe(denoised)

        # 5 — Edge detection (Sobel + Canny) on the enhanced image
        edge_images = run_edge_detection(enhanced)

        # 6 — Ingredient detection via OpenAI Vision
        image_data_url = opencv_to_data_url(enhanced)
        ingredients = detect_ingredients_with_openai(image_data_url)

        return {
            "success":     True,
            "ingredients": ingredients,
            "count":       len(ingredients),
            "edges":       edge_images,
        }

    except Exception as e:
        return {
            "success":     False,
            "ingredients": [],
            "count":       0,
            "edges":       {},
            "error":       str(e),
        }






