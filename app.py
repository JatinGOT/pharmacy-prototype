"""AI Pharmacy Intelligence Prototype - run with:  streamlit run app.py
PROTOTYPE ONLY. Not a certified clinical or pharmacy system."""
import datetime
import pandas as pd
import streamlit as st
import db, ocr_utils, parser_utils as pu, pdf_maker

st.set_page_config(page_title="Pharmacy Intelligence Prototype", page_icon="💊", layout="wide")
db.init()
STATUSES = ["Not recorded", "Sold", "Unavailable"]


with st.sidebar:
    st.title("💊 Pharmacy Intelligence")
    page = st.radio("Section", ["Prescription Scanner", "Medicine Demand Dashboard"], label_visibility="collapsed")
    st.divider()
    st.caption("⚠️ Prototype for testing only. Not a certified clinical or pharmacy system. "
               "A qualified person must check every result.")


def load(lines):
    ss = st.session_state
    ss.lines = lines
    ss.rows, ss.other = pu.parse(lines)
    ss.ver += 1


def page_scanner():
    ss = st.session_state
    ss.setdefault("rows", pu.empty_rows()); ss.setdefault("other", []); ss.setdefault("lines", [])
    ss.setdefault("ver", 0); ss.setdefault("scan_key", None)

    st.title("Prescription Scanner")
    st.info("🔒 **Privacy:** the photo is read on THIS computer by a free offline tool - nothing is sent to the internet. "
            "Only medicine name, strength and availability are saved for the dashboard. Patient details are never saved.")

    up = st.file_uploader("Step 1 - Upload a photo or scan of a prescription (JPG or PNG)", type=["png", "jpg", "jpeg"])
    with st.expander("Scan not working? Paste text or start with an empty table instead"):
        pasted = st.text_area("Paste prescription text (one medicine per line)", height=110)
        c1, c2 = st.columns(2)
        if c1.button("Use pasted text"):
            load([(l, 1.0) for l in pasted.splitlines() if l.strip()])
        if c2.button("Start with an empty table"):
            load([])

    if up is not None:
        key = (up.name, up.size)
        if ss.scan_key != key:
            try:
                with st.spinner("Reading the prescription... the first time can take a minute."):
                    lines = ocr_utils.read_image_lines(up.getvalue())
                ss.scan_key = key
                load(lines)
                if not lines:
                    st.warning("No text was found. Try a clearer, brighter, straight-on photo, or use the paste option above.")
            except ImportError:
                st.error("The free scanning tool is not installed. Run:  pip install rapidocr-onnxruntime  "
                         "(see README), or use the paste option above.")
            except Exception as e:
                st.error(f"Sorry, this image could not be read ({e}). Please try another photo.")
        with st.expander("Show original image (compare with the table below)", expanded=True):
            st.image(up, width=450)

    if ss.lines:
        with st.expander("Raw text found by the scanner"):
            st.dataframe(pd.DataFrame(ss.lines, columns=["Text", "Confidence"]), use_container_width=True)
            if ss.other:
                st.caption("Lines not treated as medicines: " + " | ".join(ss.other))

    st.subheader("Step 2 - Check and correct")
    st.caption("Fix any mistake by double-clicking a cell. Add a row with the + at the bottom of the table. "
               "Empty cells are never filled in for you. Flags are from the first scan - re-check rows you edit.")
    n_flag = int((ss.rows["Review flag"].fillna("") != "").sum())
    if n_flag:
        st.warning(f"⚠️ {n_flag} row(s) need manual review - see the 'Review flag' column.")
    edited = st.data_editor(
        ss.rows, num_rows="dynamic", use_container_width=True, key=f"editor_{ss.ver}",
        column_config={"Original line": st.column_config.TextColumn(disabled=True),
                       "Review flag": st.column_config.TextColumn(disabled=True),
                       "Availability": st.column_config.SelectboxColumn(
                           "Availability (for dashboard)", options=STATUSES)})
    clean = edited.fillna("").astype(str)
    clean = clean[clean["Medicine"].str.strip() != ""]

    st.subheader("Step 3 - Verify and download")
    a, b = st.columns(2)
    patient = a.text_input("Patient name or reference (optional - printed on the PDF only, never saved)")
    doctor = b.text_input("Prescriber name (as written, optional)")
    rx_date = a.text_input("Date on the original prescription (as written)")
    verified_by = b.text_input("Verified by - your name (required)")
    confirm = st.checkbox("I have compared EVERY row with the original prescription. I have not guessed, "
                          "changed or substituted any medicine, dose or duration.")
    if not (confirm and verified_by.strip() and len(clean) > 0):
        st.info("The PDF unlocks when you: enter your name, tick the box above, and have at least one medicine row.")
        return
    pdf = pdf_maker.make_pdf(clean, patient, doctor, rx_date, verified_by.strip())
    d1, d2 = st.columns(2)
    d1.download_button("⬇️ Download PDF transcription", pdf, f"transcription_{datetime.date.today()}.pdf", "application/pdf")
    if d2.button("📊 Save these medicines to demand records (click once)"):
        db.add_records([(r["Medicine"], r["Strength"], r["Availability"] if r["Availability"] in STATUSES else "Not recorded")
                        for _, r in clean.iterrows()])
        st.success(f"Saved {len(clean)} medicine line(s). Open the Medicine Demand Dashboard to see them.")


def page_dashboard():
    st.title("Medicine Demand Dashboard")
    inc = st.checkbox("Include FICTIONAL sample data", value=True)
    if inc:
        st.warning("🧪 **SAMPLE DATA IS FICTIONAL.** It was invented for testing and does not describe any real pharmacy or area.")
    df = db.load_records(inc)
    if df.empty:
        st.info("No records yet. Verify a prescription in the Scanner and click 'Save', or tick the sample-data box above.")
        return
    df["Medicine"] = (df["medicine"].str.strip() + " " + df["strength"].fillna("").str.strip()).str.strip()
    g = df.groupby(df["Medicine"].str.lower()).agg(
        Medicine=("Medicine", "first"), name=("medicine", lambda s: s.iloc[0].strip().lower()),
        Times=("id", "count"), Sold=("status", lambda s: int((s == "Sold").sum())),
        Unavail=("status", lambda s: int((s == "Unavailable").sum())),
        NotRec=("status", lambda s: int((s == "Not recorded").sum()))).reset_index(drop=True)
    form = db.load_formulary()
    g["Formulary"] = g["name"].map(lambda n: "Yes" if n in form else "⚠ Not in formulary") if form else "Unknown"
    g = g.sort_values(["Times", "Medicine"], ascending=[False, True]).reset_index(drop=True)
    g.insert(0, "Rank", g.index + 1)
    out = g.rename(columns={"Times": "Times prescribed", "Unavail": "Unavailable", "NotRec": "Not recorded"}).drop(columns="name")

    m = st.columns(4)
    m[0].metric("Prescribed lines", len(df))
    m[1].metric("Different medicines", len(out))
    m[2].metric("Times unavailable", int(out["Unavailable"].sum()))
    m[3].metric("Medicines outside formulary", int((out["Formulary"] != "Yes").sum()))

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Top 10 most prescribed")
        st.bar_chart(out.head(10).set_index("Medicine")["Times prescribed"], horizontal=True)
    with c2:
        st.subheader("Top 10 prescribed but unavailable")
        un = out[out["Unavailable"] > 0].sort_values("Unavailable", ascending=False).head(10)
        if un.empty:
            st.caption("No unavailable medicines recorded.")
        else:
            st.bar_chart(un.set_index("Medicine")["Unavailable"], horizontal=True)

    st.subheader("Full ranking")
    st.caption("'Unavailable' = prescribed but could not be supplied. It is NOT a sale and is counted separately from 'Sold'. "
               "Yellow rows are not in data/formulary.csv.")
    hl = lambda r: ["background-color:#FFF3CD" if str(r["Formulary"]).startswith("⚠") else "" for _ in r]
    st.dataframe(out.style.apply(hl, axis=1), use_container_width=True, hide_index=True)
    st.caption("ℹ️ These numbers come only from this one pharmacy's records. They do NOT represent demand across the local area. "
               "Use them as one input to purchasing decisions, not the only one.")

    with st.expander("Manage my saved records"):
        st.caption("Deletes only records you saved from verified prescriptions. Sample data is not touched.")
        if st.button("Delete my saved records"):
            db.clear_my_records()
            st.rerun()


(page_scanner if page == "Prescription Scanner" else page_dashboard)()
