"""Turns scanned text lines into table rows using simple, visible rules.
IMPORTANT: this file NEVER guesses or corrects a medicine, dose or duration.
If something is missing it stays blank and gets a review flag."""
import re, difflib
import pandas as pd
import db
from sample_data import SAMPLE_MEDICINES

COLUMNS = ["Medicine", "Strength", "Dose / Frequency", "Duration", "Original line", "Review flag", "Availability"]
KNOWN = db.load_formulary() | {m[0].lower() for m in SAMPLE_MEDICINES}

FORMS = r"(?:tab|tabs|tablet|cap|caps|capsule|syp|syr|syrup|inj|injection|drops?|oint|ointment|cream|gel|susp|suspension|lotion|sachet)"
LINE_START = re.compile(rf"^\s*(?:\d{{1,2}}\s*[\).:-]\s*)?(?:Rx\s*[:.]?\s*)?({FORMS})\b\.?\s*(.*)$", re.I)
_U = r"(?:mg|mcg|gm|g|ml|iu|%)(?![a-z])"
STRENGTH = re.compile(rf"\d+(?:\.\d+)?\s?{_U}(?:\s?/\s?\d+(?:\.\d+)?\s?{_U})?", re.I)
DOSE = re.compile(r"\b\d+(?:\.\d+)?\s?(?:tabs?|caps?|tsp|drops?|puffs?)\b", re.I)
FREQ = re.compile(
    r"\b\d\s?-\s?\d\s?-\s?\d(?:\s?-\s?\d)?\b|\b(?:OD|BD|BID|TDS|TID|QID|HS|SOS|PRN|STAT)\b"
    r"|\b(?:once|twice|thrice)\s+(?:a\s+|per\s+)?(?:daily|day)\b"
    r"|\b(?:before|after|with)\s+(?:food|meals?|breakfast|lunch|dinner)\b|\bat\s+night\b|\bempty stomach\b", re.I)
DUR = re.compile(r"(?:\bx\s*|\bfor\s+)?(\d+\s*(?:days?|weeks?|wks?|months?)\b)", re.I)


def empty_rows():
    return pd.DataFrame(columns=COLUMNS)


def _flags(name, strength, freq, dur, conf):
    f = []
    if conf < 0.80:
        f.append("Low scan confidence")
    if not name:
        f.append("Medicine name missing")
    elif name.lower() not in KNOWN:
        close = difflib.get_close_matches(name.lower(), list(KNOWN), n=1, cutoff=0.75)
        f.append(f"Name unclear - looks similar to '{close[0].title()}' (NOT changed)" if close
                 else "Name not in sample list - check")
    if not strength:
        f.append("Strength missing")
    if not freq:
        f.append("Dose/frequency missing")
    if not dur:
        f.append("Duration missing")
    return "; ".join(f)


def parse(lines):
    """lines = [(text, confidence)] -> (table, leftover_lines)"""
    rows, other = [], []
    for text, conf in lines:
        t = text.strip()
        m = LINE_START.match(t)
        if not (m or (STRENGTH.search(t) and FREQ.search(t))):
            other.append(t)
            continue
        rest = m.group(2) if m else t
        starts = [x.search(rest).start() for x in (STRENGTH, DOSE, FREQ, DUR) if x.search(rest)]
        name = (rest[:min(starts)] if starts else rest).strip(" -,.:;|")
        sm = STRENGTH.search(rest)
        strength = sm.group(0).strip() if sm else ""
        freq = " ".join([x.group(0) for x in DOSE.finditer(rest)] + [x.group(0) for x in FREQ.finditer(rest)])
        dm = DUR.search(rest)
        dur = dm.group(1).strip() if dm else ""
        rows.append({"Medicine": name, "Strength": strength, "Dose / Frequency": freq, "Duration": dur,
                     "Original line": t, "Review flag": _flags(name, strength, freq, dur, conf),
                     "Availability": "Not recorded"})
    return pd.DataFrame(rows, columns=COLUMNS), other
