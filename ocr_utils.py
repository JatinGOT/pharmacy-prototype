"""Reads text from an image using RapidOCR (free, runs offline on your computer)."""
import io
import numpy as np
from PIL import Image, ImageOps

_engine = None


def read_image_lines(image_bytes):
    """Returns a list of (line_text, confidence_0_to_1)."""
    global _engine
    from rapidocr_onnxruntime import RapidOCR  # raises ImportError if not installed
    if _engine is None:
        _engine = RapidOCR()
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes))).convert("RGB")
    result, _ = _engine(np.array(img))
    if not result:
        return []
    items = []
    for box, text, score in result:
        ys = [p[1] for p in box]
        xs = [p[0] for p in box]
        items.append({"x": min(xs), "yc": sum(ys) / 4, "h": max(ys) - min(ys),
                      "text": str(text), "conf": float(score)})
    items.sort(key=lambda d: d["yc"])
    lines = []
    for it in items:  # join boxes that sit on the same visual line
        if lines and abs(it["yc"] - lines[-1]["yc"]) < 0.6 * max(it["h"], 1):
            lines[-1]["parts"].append(it)
        else:
            lines.append({"yc": it["yc"], "parts": [it]})
    out = []
    for ln in lines:
        parts = sorted(ln["parts"], key=lambda d: d["x"])
        out.append((" ".join(p["text"] for p in parts), min(p["conf"] for p in parts)))
    return out
