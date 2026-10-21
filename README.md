# AI Pharmacy Intelligence Prototype (₹0, runs on your own computer)

**Prototype for testing only. Not a certified clinical or pharmacy system. A qualified person must check every result.**

## Folder structure
```
pharmacy_prototype/
├── app.py                 <- the web app (screens and buttons)
├── ocr_utils.py           <- reads text from images (free, offline)
├── parser_utils.py        <- sorts text into medicine / strength / dose / duration
├── pdf_maker.py           <- builds the printable PDF
├── db.py                  <- saves records (SQLite file, created automatically)
├── sample_data.py         <- FICTIONAL demand data
├── make_sample_images.py  <- makes the fictional test prescriptions
├── requirements.txt       <- list of free tools to install
├── data/formulary.csv     <- your formulary (open in Excel/Notepad and edit)
└── sample_prescriptions/  <- 3 fictional test images
```

## Install (one time)
1. Install **Python 3.10, 3.11 or 3.12** from python.org. On Windows, tick **"Add Python to PATH"**. (Do not use 3.13 - the OCR tool does not support it yet.)
2. Unzip this folder. Open a terminal in it (Windows: open the folder, click the address bar, type `cmd`, press Enter. Mac: right-click the folder > "New Terminal at Folder").
3. Type each line and press Enter:
   - `python -m venv venv`
   - Windows: `venv\Scripts\activate`   |   Mac/Linux: `source venv/bin/activate`
   - `pip install -r requirements.txt`  (takes a few minutes; needs internet once)

## Run (every time)
Activate the venv (step 3 above), then: `streamlit run app.py`
Your browser opens the app. To stop it, press Ctrl+C in the terminal.

## How to use (no coding needed)
**Prescription Scanner**
1. Upload a prescription image (try `sample_prescriptions/sample_prescription_1.png`).
2. Wait for the table to appear. Compare it with the original image.
3. Fix mistakes by double-clicking cells. Rows with a **Review flag** need extra care. Empty cells stay empty - never fill a dose in unless it is written on the original.
4. Optionally set each row's **Availability** (Sold / Unavailable / Not recorded) for the dashboard.
5. Enter your name, tick the verification box. The **Download PDF** button appears.
6. Click **Save these medicines to demand records** (once) to feed the dashboard.

**Medicine Demand Dashboard** - shows ranking, charts, formulary warnings (yellow) and unavailable medicines. Tick/untick the fictional sample data. To use your own formulary, edit `data/formulary.csv` (one medicine name per line).

## About AI and free tiers
This version uses **no API key and no paid service**: OCR runs offline on your computer. Cloud AI vision services (e.g. Gemini free tier) need an API key, have daily limits, and free tiers may use your data to improve products - so **do not send real patient prescriptions to them** unless your organisation has approved it. Handwritten prescriptions are read poorly by free OCR; that is why human verification is mandatory.

## Known limits
- Names not in the sample list are flagged "not in sample list" - expected. Add names to `data/formulary.csv` to reduce flags.
- The PDF supports English/Latin text only (Hindi/Gurmukhi characters will not print).
- Dashboard counts are from this one pharmacy's records only - not area-wide demand.

## Testing checklist
- [ ] App opens; sidebar has exactly two sections
- [ ] Dashboard shows red "SAMPLE DATA IS FICTIONAL" warning, 4 numbers, 2 charts, ranking table
- [ ] Yellow rows = Empagliflozin, Vildagliptin, Ivermectin, Montelukast + Levocetirizine
- [ ] Unavailable column is separate from Sold
- [ ] Upload sample 1: 4 medicines found, no flags
- [ ] Upload sample 3: "Pantoprazol 4O mg" flagged as similar to Pantoprazole but NOT changed; Levothyroxine "Duration missing"; "Xyzorin" flagged unknown
- [ ] Missing doses stay blank (never invented)
- [ ] You can edit a cell and add a new row
- [ ] PDF button stays hidden until name entered AND box ticked
- [ ] PDF says "DIGITAL TRANSCRIPTION" and "NOT a prescription"; blanks show "[not stated on original]"; PDF opens and prints
- [ ] After "Save", the dashboard (sample data unticked) shows your entries
- [ ] "Delete my saved records" removes only your entries
- [ ] Upload a non-prescription photo: no crash, a helpful message appears
- [ ] Paste-text fallback works with OCR uninstalled
