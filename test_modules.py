"""Quick smoke test for all modules."""

print("Testing imports...")
from modules.ocr_engine import OCREngine
from modules.comparison_engine import ComparisonEngine
from modules.report_generator import ReportGenerator
print("  [OK] OCR Engine")
print("  [OK] Comparison Engine")
print("  [OK] Report Generator")

# ── Test Comparison Engine with realistic dummy text ──
print("\nTesting Comparison Engine...")
ce = ComparisonEngine()
dummy_text = """
COMPLETE BLOOD COUNT
Hemoglobin       10.2    g/dL
WBC              12.5    x10/uL
Platelets        148     x10/uL
MCV              72.0    fL

THYROID
TSH              6.8     mIU/L

LIPID PANEL
LDL              145     mg/dL
HDL              38      mg/dL
Total Cholesterol 210    mg/dL
Triglycerides    185     mg/dL

VITAMINS
Vitamin D        18      ng/mL
Vitamin B12      190     pg/mL

METABOLIC
Glucose          112     mg/dL
Creatinine       1.1     mg/dL
"""

result = ce.analyze(dummy_text)
summary = result["summary"]
print(f"  Parsed:         {len(result['results'])} values matched to reference DB")
print(f"  Unrecognized:   {len(result['unrecognized'])} values")
print(f"  Abnormal:       {summary['abnormal_count']}")
print(f"  Critical:       {summary['critical_count']}")
print(f"  Severity Score: {summary['severity_score']}/100")
print(f"  Overall Status: {summary['overall_status']}")

# ── Test Report Generator with mock AI findings ──
print("\nTesting Report Generator...")
mock_ai = {
    "patient_summary": "This patient shows several abnormal values including low hemoglobin, elevated TSH, and borderline lipid values.",
    "findings": [
        {
            "test": "Hemoglobin",
            "value": "10.2 g/dL",
            "status": "LOW",
            "interpretation": "Below normal range, may indicate anemia.",
            "possible_causes": ["Iron deficiency", "B12 deficiency", "Chronic disease"],
            "severity": "moderate",
            "recommendation": "Consult physician for further evaluation and iron studies.",
        },
        {
            "test": "TSH",
            "value": "6.8 mIU/L",
            "status": "HIGH",
            "interpretation": "Elevated TSH suggests hypothyroidism.",
            "possible_causes": ["Hashimoto thyroiditis", "Primary hypothyroidism"],
            "severity": "moderate",
            "recommendation": "Endocrinologist referral recommended.",
        },
    ],
    "patterns_identified": [
        {
            "pattern_name": "Possible Iron Deficiency Anemia",
            "tests_involved": ["Hemoglobin", "MCV"],
            "clinical_significance": "Low hemoglobin with low MCV suggests microcytic anemia, commonly caused by iron deficiency.",
            "urgency": "soon",
        }
    ],
    "lifestyle_recommendations": [
        "Increase iron-rich food intake (red meat, spinach, lentils)",
        "Limit processed foods high in saturated fats",
        "30 minutes of moderate exercise 5 days per week",
    ],
    "follow_up_recommendations": [
        "See physician within 2 weeks to discuss thyroid function",
        "Request full iron panel: serum iron, ferritin, TIBC",
        "Repeat lipid panel in 3 months after lifestyle changes",
    ],
    "searched_sources": [
        "Hypothyroidism — Mayo Clinic (mayoclinic.org)",
        "Iron Deficiency Anemia — MedlinePlus (medlineplus.gov)",
    ],
    "overall_assessment": "This patient has multiple co-occurring abnormalities affecting the thyroid, red blood cell production, and cardiovascular risk. The pattern of low hemoglobin and low MCV is consistent with iron deficiency anemia. The elevated TSH strongly suggests hypothyroidism requiring medical evaluation.",
    "disclaimer": "This analysis is for informational purposes only and does not constitute medical advice. Always consult a qualified healthcare provider.",
}

rg = ReportGenerator()
html = rg.generate(
    comparison_results=result,
    ai_findings=mock_ai,
    patient_info={"name": "Test Patient", "age": "35", "sex": "female"},
    filename="sample_lab_report.pdf",
)

# Save sample report for inspection
with open("sample_report.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"  [OK] Report generated: {len(html):,} chars")
print(f"  [OK] Saved to sample_report.html — open in browser to preview")

print("\n✅ All tests PASSED. Ready to run: streamlit run app.py")
