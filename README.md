
# Failure Report Analyzer

A Streamlit app that:
- Collates all tabs from **Input.xlsx** into one **Master** sheet (adds `Tab Name`)
- Appends `Failure Rate`, `Failure Summary`, `Failure Report` from **Analysis.xlsx** (`Analysis Results` sheet)
- Computes tier flags based on an embedded mapping

## Tiers
This build embeds your current mapping from the `Mapping` sheet of your Analysis workbook, normalized into 4 tiers:
{
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

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Cloud
1. Push these files to a GitHub repo
2. Create a new app on https://share.streamlit.io
3. Point it to `app.py` in your repo
