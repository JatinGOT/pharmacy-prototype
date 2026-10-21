"""Creates 3 FICTIONAL prescription images for testing. Run: python make_sample_images.py"""
from PIL import Image, ImageDraw, ImageFont
H = ["Dr. A. Sample, MBBS  (FICTIONAL CLINIC - TEST ONLY)", "Date: 12/10/2026    Patient: Test Patient", "Rx"]
SAMPLES = {
    "sample_prescription_1.png": H + ["1) Tab Paracetamol 500 mg 1-0-1 after food x 5 days", "2) Tab Azithromycin 500 mg OD x 3 days",
        "3) Syp Cetirizine 5 ml HS x 5 days", "4) Tab Pantoprazole 40 mg OD before food x 7 days"],
    "sample_prescription_2.png": H + ["1) Tab Metformin 500 mg 1-0-1 after food x 30 days", "2) Tab Amlodipine 5 mg 1-0-0 x 30 days",
        "3) Tab Atorvastatin 10 mg HS x 30 days", "4) Tab Telmisartan 40 mg OD x 30 days"],
    "sample_prescription_3.png": H + ["TEST SHEET - contains unclear items", "1) Tab Pantoprazol 4O mg OD",
        "2) Tab Azithromicin 500 mg BD x 3 days", "3) Tab Levothyroxine 50 mcg empty stomach", "4) Cap Xyzorin 250 mg TDS x 5 days"],
}
try:
    font = ImageFont.truetype("DejaVuSans.ttf", 30)
except Exception:
    try:
        font = ImageFont.load_default(size=30)
    except Exception:
        font = ImageFont.load_default()
for fname, lines in SAMPLES.items():
    img = Image.new("RGB", (1500, 150 + 70 * len(lines)), "white")
    d = ImageDraw.Draw(img)
    for i, ln in enumerate(lines):
        d.text((50, 50 + 70 * i), ln, fill="black", font=font)
    img.save(f"sample_prescriptions/{fname}")
print("Done: sample images saved in the sample_prescriptions folder.")
