"""Build high-resolution web assets from the low-resolution source photos.

Sources in public/images are never modified. Output goes to public/images/enhanced.

Upscaling uses the EDSR x4 super-resolution network when available (via
opencv-contrib `dnn_superres`), otherwise falls back to Lanczos + unsharp mask.
Neither method can invent real detail: replace the sources with true
high-resolution originals when you have them and re-run this script.

Usage (from the frontend folder):
    python scripts/enhance_images.py [path/to/EDSR_x4.pb]
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "public", "images")
OUT = os.path.join(SRC, "enhanced")
os.makedirs(OUT, exist_ok=True)

PHOTOS = {
    "campus-life.jpg": "campus-life",
    "faculty-teaching.jpg": "faculty-teaching",
    "graduation.jpg": "graduation",
    "kepler-campus-hero.jpg": "campus-hero",
    "modern-libraly.jpg": "library",
    "student-learning.jpg": "student-learning",
    "tech-lab.jpg": "tech-lab",
    "kepler college dvc.jfif": "event-dvc",
    "kepler college first lady.jfif": "event-first-lady",
    "kepler college second imagejfif.jfif": "event-second",
}

model_path = sys.argv[1] if len(sys.argv) > 1 else None
sr = None
if model_path and os.path.exists(model_path):
    try:
        import cv2

        sr = cv2.dnn_superres.DnnSuperResImpl_create()
        sr.readModel(model_path)
        sr.setModel("edsr", 4)
    except Exception as exc:  # pragma: no cover
        print("EDSR unavailable, using Lanczos:", exc)
        sr = None


def upscale(im: Image.Image) -> Image.Image:
    if sr is not None:
        import cv2

        bgr = cv2.cvtColor(np.array(im.convert("RGB")), cv2.COLOR_RGB2BGR)
        up = sr.upsample(bgr)
        out = Image.fromarray(cv2.cvtColor(up, cv2.COLOR_BGR2RGB))
    else:
        out = im.convert("RGB").resize((im.width * 4, im.height * 4), Image.LANCZOS)
    return out.filter(ImageFilter.UnsharpMask(radius=1.4, percent=45, threshold=3))


for filename, name in PHOTOS.items():
    path = os.path.join(SRC, filename)
    if not os.path.exists(path):
        print("skip (missing):", filename)
        continue
    src = Image.open(path)
    out = upscale(src)
    out.save(os.path.join(OUT, f"{name}.webp"), "WEBP", quality=88, method=6)
    print(f"{filename}: {src.size} -> {out.size}")

logo = Image.open(os.path.join(SRC, "kepler college logo.png")).convert("RGB")
upscale(logo).save(os.path.join(OUT, "logo.png"), optimize=True)
print("logo ->", logo.size, "x4")

# ---- Imigongo artwork ----------------------------------------------------
art = Image.open(os.path.join(SRC, "imigongo white artwebp.webp")).convert("RGB")
art2 = art.resize((art.width * 2, art.height * 2), Image.LANCZOS).filter(
    ImageFilter.UnsharpMask(radius=1.2, percent=35, threshold=3)
)
art2.save(os.path.join(OUT, "imigongo.webp"), "WEBP", quality=90, method=6)

# Horizontal zig-zag strip: rotate so the chevrons run left-to-right, then crop a band.
rot = art2.rotate(90, expand=True)
band_h = 140
top = (rot.height - band_h) // 2
rot.crop((0, top, rot.width, top + band_h)).save(
    os.path.join(OUT, "imigongo-strip.webp"), "WEBP", quality=90, method=6
)
print("imigongo assets written")
