# 🔬 MedInsight — AI-Powered Medical Lab Report Analyzer

An intelligent Streamlit application that analyzes medical lab reports using OCR, Claude AI, web search, and clinical reference ranges to generate detailed health reports.

---

## 🏗️ Architecture

```
User Upload (Streamlit)
        ↓
[1] File Uploader     — Streamlit + custom HTML/CSS UI
        ↓
[2] OCR Engine        — PyMuPDF (PDF) + Tesseract (images/scanned PDFs)
        ↓
[3] Diagnostic Agent  — Claude claude-3-5-sonnet + Tavily web search tool use
        ↓
[4] Comparison Engine — Python logic + clinical reference ranges JSON
        ↓
[5] Health Report     — Rich HTML/CSS rendered via st.components.v1.html
```

---

## ⚙️ Prerequisites

### 1. Python 3.10+

### 2. Tesseract OCR (required for image files and scanned PDFs)

**Windows:**
```
winget install UB-Mannheim.TesseractOCR
```
Or download from: https://github.com/UB-Mannheim/tesseract/wiki

After install, add to PATH or set in `.env`:
```
TESSERACT_CMD=C:/Program Files/Tesseract-OCR/tesseract.exe
```

### 3. Poppler (optional — only needed for scanned PDFs)

**Windows:**
- Download from: https://github.com/oschwartz10612/poppler-windows/releases
- Extract and set in `.env`:
```
POPPLER_PATH=C:/poppler/Library/bin
```

---

## 🚀 Setup

### 1. Clone / open the project folder
```bash
cd "medical bot"
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API keys
```bash
copy .env.example .env
```
Edit `.env` and add your keys:
```env
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=tvly-...
```

- **Anthropic API key**: https://console.anthropic.com/
- **Tavily API key** (free tier — 1000 searches/month): https://app.tavily.com/

### 5. Run the app
```bash
streamlit run app.py
```

---

## 📁 Project Structure

```
medical bot/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── .env                        # API keys (create from .env.example)
├── .env.example                # Environment variable template
├── modules/
│   ├── __init__.py
│   ├── ocr_engine.py           # PDF + image OCR (PyMuPDF + Tesseract)
│   ├── diagnostic_agent.py     # Claude API + Tavily web search tool use
│   ├── comparison_engine.py    # Lab value parsing + reference comparison
│   └── report_generator.py    # HTML health report builder
├── data/
│   └── reference_ranges.json  # Clinical reference database (50+ biomarkers)
└── README.md
```

---

## 🧪 Supported Lab Tests

| Category | Tests |
|---|---|
| **CBC** | WBC, RBC, Hemoglobin, Hematocrit, MCV, MCH, MCHC, Platelets, Differential |
| **Metabolic** | Glucose, BUN, Creatinine, eGFR, Electrolytes, Calcium, Uric Acid |
| **Liver** | ALT, AST, ALP, GGT, Bilirubin, Albumin, Total Protein |
| **Lipid Panel** | Total Cholesterol, LDL, HDL, Triglycerides, VLDL |
| **Thyroid** | TSH, Free T3, Free T4 |
| **Diabetes** | HbA1c, Fasting Glucose, Insulin, C-Peptide |
| **Vitamins** | Vitamin D, B12, Folate, A, E |
| **Iron** | Serum Iron, Ferritin, TIBC, Transferrin Saturation |
| **Cardiac** | Troponin I, CK-MB, BNP, CRP, hs-CRP, Homocysteine |
| **Hormones** | Testosterone, Estradiol, Cortisol, DHEA-S, Prolactin |
| **Urinalysis** | pH, Specific Gravity, Protein, Creatinine |

---

## 🛡️ Supported File Formats

| Format | Method |
|---|---|
| PDF (digital) | PyMuPDF native text extraction |
| PDF (scanned) | pdf2image + Tesseract OCR |
| PNG, JPG, JPEG | Pillow + Tesseract OCR |
| TIFF, TIF | Pillow + Tesseract OCR |

---

## 📋 Health Report Sections

1. **Executive Summary** — Patient info, overall status, severity score (0–100), test count breakdown
2. **Lab Results Table** — Color-coded table grouped by category (green/yellow/orange/red)
3. **AI Diagnostic Findings** — Per-abnormal-test cards with interpretation, causes, and recommendations
4. **Clinical Patterns** — Multi-test patterns (e.g., Iron Deficiency Anemia) with urgency levels
5. **Recommendations** — Lifestyle and follow-up action items
6. **Sources** — Web sources searched by the AI agent
7. **Medical Disclaimer**

---

## ⚠️ Disclaimer

MedInsight is for **informational purposes only** and does not constitute medical advice. Always consult a qualified healthcare professional for diagnosis and treatment decisions.

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ Yes | Claude API key |
| `TAVILY_API_KEY` | ⚡ Recommended | Web search API key (free tier available) |
| `TESSERACT_CMD` | Windows only | Path to tesseract.exe if not in PATH |
| `POPPLER_PATH` | Optional | Path to Poppler bin (for scanned PDFs) |
