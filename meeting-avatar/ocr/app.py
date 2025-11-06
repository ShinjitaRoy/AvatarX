import os
import time
import math
import shutil
import re
from datetime import datetime
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
import pytesseract as tess
import pyautogui
from difflib import SequenceMatcher

# ----------------------
# Configuration (edit these)
# ----------------------
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # update as needed
tess.pytesseract.tesseract_cmd = TESSERACT_CMD

interval_seconds = 2        # default interval (seconds) between captures
duration_seconds = 6        # default total duration (seconds)
start_delay_seconds = 5     # seconds to wait before starting capture so you can focus the Zoom window
include_endpoint = False    # if True, include capture at t == duration

# Output folders/files
screenshots_dir = "screenshots"       # raw screenshots (will be cleared each run)
kept_images_dir = "kept_images"       # cropped images saved for every shot for inspection
combined_text_file = "combined_ocr.txt"

# Center-detection / crop tuning
CENTER_WINDOW_PCT = 0.9     # fraction of screen (centered) to search for content
VAR_ROW_FRAC = 0.12          # fraction of max row variance to count as content
VAR_COL_FRAC = 0.12
EXPAND_PX = 12               # expand detected bbox by this many pixels
MIN_CROP_W = 160
MIN_CROP_H = 120
FALLBACK_CROP_FRAC = 0.75     # fallback centered crop fraction if detection fails

# Preprocessing for OCR
ENHANCE_CONTRAST = 1.6
ENHANCE_SHARPNESS = 1.3
APPLY_MEDIAN = True
RESIZE_IF_SMALL = True
RESIZE_MIN_DIM = 900
RESIZE_SCALE = 2

# Tesseract config
TESSERACT_CONFIG = r'--psm 6'

# OCR word-filtering parameters (NEW)
MIN_WORD_CONF = 30            # 0-100 confidence threshold for keeping words
MIN_WORD_LEN = 1              # minimum length for kept tokens (unless numeric)
WORD_ALLOW_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9\-\':,\.() ]+$')  # whitelist pattern for tokens

# Deduplication of sequential OCR text
DEDUP_SIMILARITY_THRESHOLD = 0.95

# Behavior
CLEAR_SCREENSHOTS_ON_START = True
PRESERVE_OCR_FILE = False   # if False combined_text_file will be overwritten each run

# ----------------------
# Helpers
# ----------------------

def ensure_dirs():
    os.makedirs(screenshots_dir, exist_ok=True)
    os.makedirs(kept_images_dir, exist_ok=True)

def clear_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        return
    for entry in os.listdir(folder_path):
        path = os.path.join(folder_path, entry)
        try:
            if os.path.isfile(path) or os.path.islink(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
        except Exception:
            pass

def timestamp_filename():
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

def format_offset(seconds):
    mm = seconds // 60
    ss = seconds % 60
    return f"{mm:02d}:{ss:02d}"

def similar_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()

# ----------------------
# Compute deterministic offsets
# ----------------------

def compute_offsets(interval, duration, include_endpoint_flag):
    """
    Deterministic offsets:
      - include first capture at t=0
      - with include_endpoint False, captures at offsets 0, interval, 2*interval, ... < duration
      - with include_endpoint True, include t==duration if it aligns
    """
    if interval <= 0:
        return [0]
    if include_endpoint_flag:
        count = math.floor(duration / interval) + 1
        offsets = [i * interval for i in range(0, int(count))]
        offsets = [o for o in offsets if o <= duration]
        return offsets
    else:
        count = duration // interval
        return [i * interval for i in range(int(count))]

# ----------------------
# Center detection (variance-based, run every shot)
# ----------------------

def fallback_centered_box(w, h, frac):
    cw = max(1, int(w * frac))
    ch = max(1, int(h * frac))
    left = (w - cw) // 2
    top = (h - ch) // 2
    return (left, top, left + cw, top + ch)

def best_continuous_run(indices, length_limit=None):
    if not indices:
        return None
    runs = []
    start = indices[0]
    prev = indices[0]
    for idx in indices[1:]:
        if idx == prev + 1:
            prev = idx
            continue
        runs.append((start, prev))
        start = idx
        prev = idx
    runs.append((start, prev))
    if length_limit is None:
        return max(runs, key=lambda r: (r[1] - r[0]))
    center = length_limit / 2.0
    best = None
    best_dist = None
    for s, e in runs:
        mid = (s + e) / 2.0
        dist = abs(mid - center)
        if best is None or dist < best_dist or (dist == best_dist and (e - s) > (best[1] - best[0])):
            best = (s, e)
            best_dist = dist
    return best

def detect_center_content_bbox(pil_img,
                               center_search_frac=CENTER_WINDOW_PCT,
                               var_row_frac=VAR_ROW_FRAC,
                               var_col_frac=VAR_COL_FRAC,
                               expand_px=EXPAND_PX,
                               min_w=MIN_CROP_W,
                               min_h=MIN_CROP_H,
                               fallback_frac=FALLBACK_CROP_FRAC):
    """
    Heuristic detection focused on center region. Runs on each shot.
    Returns (left, top, right, bottom).
    """
    w, h = pil_img.size

    # define centered search window
    sw = int(w * center_search_frac)
    sh = int(h * center_search_frac)
    left0 = max(0, (w - sw) // 2)
    top0 = max(0, (h - sh) // 2)
    right0 = min(w, left0 + sw)
    bottom0 = min(h, top0 + sh)
    center_crop = pil_img.crop((left0, top0, right0, bottom0)).convert("L")

    # downscale lightly for speed but keep detail
    down_w = max(1, center_crop.width // 2)
    down_h = max(1, center_crop.height // 2)
    small = center_crop.resize((down_w, down_h))
    sp = small.load()
    sw2, sh2 = small.size

    # per-row variance
    row_vars = []
    for y in range(sh2):
        row = [sp[x, y] for x in range(sw2)]
        mean = sum(row) / sw2
        var = sum((v - mean) ** 2 for v in row) / sw2
        row_vars.append(var)
    col_vars = []
    for x in range(sw2):
        col = [sp[x, y] for y in range(sh2)]
        mean = sum(col) / sh2
        var = sum((v - mean) ** 2 for v in col) / sh2
        col_vars.append(var)

    if not row_vars or not col_vars:
        return fallback_centered_box(w, h, fallback_frac)

    max_row_var = max(row_vars)
    max_col_var = max(col_vars)
    if max_row_var <= 0 or max_col_var <= 0:
        return fallback_centered_box(w, h, fallback_frac)

    row_thresh = max_row_var * var_row_frac
    col_thresh = max_col_var * var_col_frac

    content_rows = [y for y, v in enumerate(row_vars) if v >= row_thresh]
    content_cols = [x for x, v in enumerate(col_vars) if v >= col_thresh]

    if not content_rows or not content_cols:
        return fallback_centered_box(w, h, fallback_frac)

    row_run = best_continuous_run(content_rows, length_limit=sh2)
    col_run = best_continuous_run(content_cols, length_limit=sw2)
    if not row_run or not col_run:
        return fallback_centered_box(w, h, fallback_frac)

    r0, r1 = row_run
    c0, c1 = col_run

    # Map small indices back to original coords
    row_scale = center_crop.height / sh2
    col_scale = center_crop.width / sw2
    top = int(top0 + max(0, r0 * row_scale) - expand_px)
    bottom = int(top0 + min(center_crop.height, (r1 + 1) * row_scale) + expand_px)
    left = int(left0 + max(0, c0 * col_scale) - expand_px)
    right = int(left0 + min(center_crop.width, (c1 + 1) * col_scale) + expand_px)

    left = max(0, left)
    top = max(0, top)
    right = min(w, right)
    bottom = min(h, bottom)

    if (right - left) < min_w or (bottom - top) < min_h:
        return fallback_centered_box(w, h, fallback_frac)
    return (left, top, right, bottom)

# ----------------------
# Preprocessing + OCR (with word-level filtering)
# ----------------------

def preprocess_for_ocr(img):
    im = img.convert("L")
    if ENHANCE_CONTRAST != 1.0:
        im = ImageEnhance.Contrast(im).enhance(ENHANCE_CONTRAST)
    if ENHANCE_SHARPNESS != 1.0:
        im = ImageEnhance.Sharpness(im).enhance(ENHANCE_SHARPNESS)
    if APPLY_MEDIAN:
        im = im.filter(ImageFilter.MedianFilter(size=3))
    w, h = im.size
    if RESIZE_IF_SMALL and min(w, h) < RESIZE_MIN_DIM:
        im = im.resize((int(w * RESIZE_SCALE), int(h * RESIZE_SCALE)), Image.LANCZOS)
    return im

def ocr_with_word_filter(pil_img):
    """
    Run pytesseract.word-level OCR (image_to_data) and filter words by confidence, length, and token regex.
    Returns cleaned joined text (or empty string).
    """
    pre = preprocess_for_ocr(pil_img)
    # Use image_to_data for word-level info
    try:
        data = tess.image_to_data(pre, output_type=tess.Output.DICT, config=TESSERACT_CONFIG)
    except Exception:
        # fallback to simple string extraction if data call fails
        try:
            raw = tess.image_to_string(pre, config=TESSERACT_CONFIG)
            return re.sub(r'\s+', ' ', raw).strip()
        except Exception:
            return ""

    words = []
    n = len(data.get('text', []))
    for i in range(n):
        txt = str(data.get('text', [''])[i]).strip()
        if not txt:
            continue
        # attempt to parse confidence; some versions provide '-1' or strings
        conf_raw = data.get('conf', [None] * n)[i]
        try:
            conf = int(float(conf_raw))
        except Exception:
            conf = -1
        if conf < MIN_WORD_CONF:
            continue
        # length rule (allow numbers)
        if len(txt) < MIN_WORD_LEN and not txt.isdigit():
            continue
        # whitelist regex
        if not WORD_ALLOW_RE.match(txt):
            continue
        words.append(txt)
    out = ' '.join(words)
    out = re.sub(r'\s+', ' ', out).strip()
    return out

# ----------------------
# Utility: save visualization
# ----------------------

def save_visual(full_img, bbox, out_path):
    try:
        vis = full_img.copy().convert("RGB")
        draw = ImageDraw.Draw(vis)
        left, top, right, bottom = bbox
        draw.rectangle([left, top, right, bottom], outline=(255, 0, 0), width=4)
        vis.save(out_path)
    except Exception:
        pass

# ----------------------
# Main capture flow
# ----------------------

def capture_and_ocr(interval_seconds=interval_seconds, duration_seconds=duration_seconds,
                    start_delay_seconds=start_delay_seconds, include_endpoint=include_endpoint):
    ensure_dirs()
    if CLEAR_SCREENSHOTS_ON_START:
        clear_folder(screenshots_dir)
        clear_folder(kept_images_dir)   # <-- clear kept_images folder every run as requested

    mode = "a" if PRESERVE_OCR_FILE else "w"
    with open(combined_text_file, mode, encoding="utf-8") as f:
        if not PRESERVE_OCR_FILE:
            f.write(f"Combined OCR started at {datetime.now().isoformat()}\n")
            f.write(f"interval={interval_seconds}s duration={duration_seconds}s start_delay={start_delay_seconds}s\n\n")
        else:
            f.write(f"\n\n--- New run at {datetime.now().isoformat()} ---\n")

    offsets = compute_offsets(interval_seconds, duration_seconds, include_endpoint)
    if not offsets:
        offsets = [0]

    print(f"Starting in {start_delay_seconds}s; captures at offsets: {offsets}")
    time.sleep(start_delay_seconds)
    start_time = time.time()

    last_saved_text = None
    kept_count = 0

    for i, offset in enumerate(offsets):
        scheduled = start_time + offset
        now = time.time()
        if scheduled > now:
            time.sleep(scheduled - now)

        # Capture full screen then detect center bbox each shot
        full = pyautogui.screenshot()

        bbox = detect_center_content_bbox(full)  # detect on each shot
        left, top, right, bottom = bbox
        cropped = full.crop((left, top, right, bottom))

        # Save visualization for this shot
        vis_name = f"vis_{timestamp_filename()}.png"
        vis_path = os.path.join(screenshots_dir, vis_name)
        save_visual(full, bbox, vis_path)

        # Always save the cropped image (so you can inspect failures)
        kept_name = f"crop_{timestamp_filename()}.png"
        kept_path = os.path.join(kept_images_dir, kept_name)
        try:
            cropped.convert("RGB").save(kept_path)
            kept_count += 1
        except Exception:
            pass

        # Run filtered OCR (word-level)
        filtered_text = ocr_with_word_filter(cropped)
        if not filtered_text or len(filtered_text.strip()) == 0:
            print(f"[{format_offset(offset)}] No readable filtered text detected; crop saved to {kept_path} for inspection.")
            continue

        if last_saved_text and similar_ratio(filtered_text, last_saved_text) >= DEDUP_SIMILARITY_THRESHOLD:
            print(f"[{format_offset(offset)}] OCR near-duplicate of previous; skipping append.")
            continue

        with open(combined_text_file, "a", encoding="utf-8") as f:
            f.write(f"--- {format_offset(offset)} ---\n")
            f.write(filtered_text + "\n\n")

        last_saved_text = filtered_text
        print(f"[{format_offset(offset)}] OCR appended; crop saved to {kept_path}")

    with open(combined_text_file, "a", encoding="utf-8") as f:
        f.write(f"--- End of capture at {datetime.now().isoformat()} ---\n")
        f.write(f"Kept cropped images: {kept_count}\n")
    print(f"Done. Combined OCR saved to {combined_text_file}. Cropped images saved: {kept_count}")

# ----------------------
# Run (default values)
# ----------------------
if __name__ == "__main__":
    capture_and_ocr()