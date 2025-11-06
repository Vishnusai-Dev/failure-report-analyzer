
import streamlit as st
import pandas as pd
import io
from io import BytesIO
import warnings
import tempfile

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

st.set_page_config(page_title="Failure Report Analyzer (v2 Optimized)", layout="wide")

st.title("Failure Report Analyzer — v2 (Optimized)")
st.caption("Handles 5k+ SKUs & 50+ tabs: streamed sheet loading • selective Analysis columns • faster export")

# ---- Embedded tier mapping (from your Mapping sheet, normalized) ----
MAPPING = {
  "tier1_errors": [
    "Article Type In Title",
    "Description Bullets",
    "Description Length",
    "Description Unicode",
    "Lv Title Length",
    "Ideal LVN",
    "LVN Presence Check",
    "LVN Sequence Check",
    "Ideal PDN",
    "PDN Presence Check",
    "PDN Sequence Check",
    "Specification Count",
    "Title Casing",
    "Title Length",
    "Title Unicode"
  ],
  "tier2_data_image_coherence": [
    "Attribute Image Match",
    "Black And White Flag",
    "Blacklisted Country Of Origin",
    "Brand Consistency Flag",
    "Celebrity Licensed Content Flag",
    "Color Inconsistency Flag",
    "Duplicate Images Flag",
    "Fake Photoshopped Flag",
    "Fit Consistency Flag",
    "Flat Shot Flag",
    "Gender Age Group Match Flag",
    "Geometric Distortion Flag",
    "Headless Flag",
    "Image Availability",
    "Image Completeness Flag",
    "Image Quality Issues Flag",
    "Inappropriate Content Flag",
    "Key Brand Logo Flag",
    "Poor Editing Artifacts Flag",
    "Product Consistency Flag",
    "Religious Political Content Flag",
    "Restricted Product Promotion Flag",
    "Text Infographic Logo Flag",
    "Watermark Flag"
  ],
  "tier2_size_fit_description_completeness": [
    "Material Care Info",
    "Standard Sizes In Chart"
  ],
  "tier2_article_type_consistency": [
    "Article Type Match Flag",
    "Country Of Origin Available",
    "Description Content Match (%)",
    "Importer Address Valid",
    "Importer Details Available",
    "Manufacturer Address Valid",
    "Manufacturer Details Available",
    "Net Quantity Available",
    "Net Quantity Unit Available",
    "Package Contains Info Available",
    "Packer Address Valid",
    "Packer Details Available",
    "Title Content Match (%)"
  ]
}

REQUIRED_ANALYSIS_COLS = ["Failure Rate", "Failure Summary", "Failure Report", "styleId"]

def normalize_pass_fail(val):
    if pd.isna(val):
        return "Fail"
    s = str(val).strip().lower()
    return "Pass" if s == "passed" else "Fail"

def compute_tier_flags(merged_df: pd.DataFrame) -> pd.DataFrame:
    out = merged_df.copy()
    for tier, cols in MAPPING.items():
        present = [c for c in cols if c in out.columns]
        if len(present) == 0:
            out[tier] = "N/A"
            continue
        # Normalize and require all pass
        mask_all_pass = out[present].applymap(normalize_pass_fail).eq("Pass").all(axis=1)
        out[tier] = mask_all_pass.map(lambda x: "Pass" if x else "Fail")
    return out

def collate_input_to_master_streamed(input_xls_bytes: bytes) -> pd.DataFrame:
    xls = pd.ExcelFile(io.BytesIO(input_xls_bytes))
    frames = []
    progress = st.progress(0, text="Reading Input sheets...")
    total = len(xls.sheet_names)
    for i, sheet in enumerate(xls.sheet_names, start=1):
        df = pd.read_excel(xls, sheet_name=sheet)
        if not df.empty:
            if "styleId" not in df.columns:
                st.warning(f"Sheet '{sheet}' has no 'styleId' column — rows will not join with Analysis.")
            df["Tab Name"] = sheet
            frames.append(df)
        progress.progress(i/total, text=f"Reading sheet {i}/{total}: {sheet}")
    progress.empty()
    if not frames:
        return pd.DataFrame()
    master = pd.concat(frames, ignore_index=True)
    return master

def merge_analysis_selective(master: pd.DataFrame, analysis_xls_bytes: bytes) -> pd.DataFrame:
    axls = pd.ExcelFile(io.BytesIO(analysis_xls_bytes))
    if "Analysis Results" not in axls.sheet_names:
        st.error("Analysis.xlsx must contain a sheet named 'Analysis Results'")
        st.stop()
    # Build required columns list (styleId + Fail trio + all tier checks)
    needed = list(dict.fromkeys(["styleId"] + REQUIRED_ANALYSIS_COLS + sum(MAPPING.values(), [])))
    # Selectively load only needed columns (massive memory/time savings)
    a = pd.read_excel(axls, sheet_name="Analysis Results", usecols=lambda c: c in needed)
    if "styleId" not in a.columns:
        st.error("The 'Analysis Results' sheet must contain a 'styleId' column.")
        st.stop()
    merged = master.merge(a, on="styleId", how="left", suffixes=("", "_analysis"))
    return merged

def write_excel_fast(df: pd.DataFrame) -> bytes:
    # Use temp file to avoid large BytesIO memory spikes
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        with pd.ExcelWriter(tmp.name, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Master", index=False)
        data = open(tmp.name, "rb").read()
    return data

# ---- UI ----
left, right = st.columns(2)
with left:
    input_file = st.file_uploader("Upload Input.xlsx (multi-tab)", type=["xlsx"], help="Large files supported: reads one sheet at a time")
with right:
    analysis_file = st.file_uploader("Upload Analysis.xlsx (must include 'Analysis Results')", type=["xlsx"], help="App reads only required columns")

if st.button("Generate Master File (Optimized)"):
    if not input_file or not analysis_file:
        st.error("Please upload both Input.xlsx and Analysis.xlsx")
        st.stop()

    with st.status("Processing Input.xlsx...", expanded=False) as status:
        master = collate_input_to_master_streamed(input_file.read())
        if master.empty:
            st.warning("Input.xlsx has no data rows.")
            st.stop()
        if "styleId" not in master.columns:
            st.error("Input.xlsx must contain a 'styleId' column in each data sheet.")
            st.stop()
        status.update(label="Merging with Analysis.xlsx...", state="running")

    merged = merge_analysis_selective(master, analysis_file.read())

    with st.status("Computing Tier Flags...", expanded=False) as status:
        final_df = compute_tier_flags(merged)
        status.update(label="Tiers computed", state="complete")

    st.subheader("Preview (first 200 rows)")
    st.dataframe(final_df.head(200), use_container_width=True)

    # Metrics
    st.markdown("### Summary")
    total_rows = len(final_df)
    colA, colB, colC, colD = st.columns(4)
    for col, tier in zip([colA, colB, colC, colD], MAPPING.keys()):
        if tier in final_df.columns:
            passes = int((final_df[tier] == "Pass").sum())
            fails = int((final_df[tier] == "Fail").sum())
            col.metric(tier, f"Pass {passes}", delta=f"Fail {fails} / {total_rows}")

    xldata = write_excel_fast(final_df)
    st.download_button(
        label="⬇️ Download Master_Final.xlsx",
        data=xldata,
        file_name="Master_Final_optimized.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.caption("If a tier shows 'N/A', the required check columns were not found in the uploaded Analysis file.")
