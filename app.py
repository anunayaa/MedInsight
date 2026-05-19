"""
MedInsight — AI-Powered Medical Lab Report Analyzer
Main Streamlit Application
"""

import os
import io
import time
import logging
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Page Config (must be first Streamlit call)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="MedInsight — AI Lab Analyzer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# Global CSS Injection
# ─────────────────────────────────────────────
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* Reset & base */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.stApp {
    background: #08080f !important;
    color: #e2e8f0 !important;
}

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Hero Header ── */
.medinsight-hero {
    background: linear-gradient(135deg, #0d0d1f 0%, #12122b 40%, #0d1f12 100%);
    border-bottom: 1px solid #1e1e3a;
    padding: 40px 60px 32px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.medinsight-hero::before {
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(ellipse at 20% 50%, rgba(99,102,241,0.08) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 50%, rgba(34,197,94,0.06) 0%, transparent 60%);
}
.hero-logo {
    display: inline-flex; align-items: center; gap: 14px;
    margin-bottom: 12px; position: relative;
}
.hero-icon { font-size: 48px; filter: drop-shadow(0 0 20px rgba(99,102,241,0.6)); }
.hero-title {
    font-size: 42px; font-weight: 900; letter-spacing: -1.5px;
    background: linear-gradient(135deg, #818cf8, #c4b5fd, #6ee7b7);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-tagline {
    color: #94a3b8; font-size: 16px; font-weight: 400;
    max-width: 560px; margin: 0 auto 20px; position: relative;
}
.hero-badges {
    display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;
    position: relative;
}
.hero-badge {
    background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px; padding: 4px 14px; font-size: 12px; color: #94a3b8;
}

/* ── Main Layout ── */
.main-container {
    max-width: 1100px; margin: 0 auto; padding: 40px 24px;
}

/* ── Upload Card ── */
.upload-card {
    background: linear-gradient(135deg, #0f0f1e, #141428);
    border: 1.5px dashed #2d2d5a; border-radius: 20px;
    padding: 60px 40px; text-align: center;
    transition: all 0.3s ease; margin-bottom: 32px;
    position: relative; overflow: hidden;
}
.upload-card::before {
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(ellipse at center, rgba(99,102,241,0.06) 0%, transparent 70%);
}
.upload-icon { font-size: 56px; margin-bottom: 16px; display: block; }
.upload-title { font-size: 22px; font-weight: 700; color: white; margin-bottom: 8px; }
.upload-sub { color: #64748b; font-size: 14px; margin-bottom: 20px; }
.upload-formats {
    display: inline-flex; gap: 8px; flex-wrap: wrap; justify-content: center;
}
.format-tag {
    background: rgba(99,102,241,0.12); border: 1px solid rgba(99,102,241,0.25);
    color: #a5b4fc; border-radius: 6px; padding: 3px 10px; font-size: 12px; font-weight: 500;
}

/* ── Patient Info Form ── */
.patient-form {
    background: #0f0f1e; border: 1px solid #1e1e3a;
    border-radius: 16px; padding: 28px 32px; margin-bottom: 32px;
}
.form-title { font-size: 16px; font-weight: 600; color: #a78bfa; margin-bottom: 20px; }

/* ── Streamlit widget overrides ── */
.stTextInput > div > div > input,
.stSelectbox > div > div > div,
.stNumberInput > div > div > input {
    background: #141428 !important;
    border: 1px solid #2d2d5a !important;
    color: #e2e8f0 !important;
    border-radius: 10px !important;
}
.stTextInput > label, .stSelectbox > label, .stNumberInput > label {
    color: #94a3b8 !important; font-size: 13px !important; font-weight: 500 !important;
}
.stFileUploader > div {
    background: transparent !important;
    border: none !important;
}
div[data-testid="stFileUploader"] {
    background: transparent !important;
}

/* ── Analyze Button ── */
.stButton > button {
    width: 100% !important;
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 16px 32px !important;
    font-size: 17px !important;
    font-weight: 700 !important;
    letter-spacing: 0.3px !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 8px 32px rgba(79,70,229,0.35) !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    box-shadow: 0 12px 40px rgba(99,102,241,0.5) !important;
    transform: translateY(-2px) !important;
}

/* ── Pipeline Steps ── */
.pipeline {
    display: flex; align-items: center; justify-content: center;
    gap: 0; margin: 32px 0; flex-wrap: wrap;
}
.pipeline-step {
    display: flex; flex-direction: column; align-items: center;
    gap: 8px; padding: 0 8px; min-width: 100px;
}
.step-circle {
    width: 52px; height: 52px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; font-weight: 800; border: 2px solid;
    transition: all 0.4s ease;
}
.step-label {
    font-size: 11px; font-weight: 600; text-align: center;
    text-transform: uppercase; letter-spacing: 0.5px; color: #64748b;
    line-height: 1.3;
}
.step-pending .step-circle { background: #12121a; border-color: #2a2a3d; color: #4a4a6a; }
.step-active .step-circle {
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    border-color: #6366f1; color: white;
    box-shadow: 0 0 20px rgba(99,102,241,0.5);
    animation: pulse-step 1.5s infinite;
}
.step-active .step-label { color: #a5b4fc; }
.step-done .step-circle { background: #052e16; border-color: #16a34a; color: #4ade80; }
.step-done .step-label { color: #4ade80; }
.pipeline-arrow { color: #2a2a3d; font-size: 20px; padding: 0 4px; margin-bottom: 30px; }

@keyframes pulse-step {
    0%, 100% { box-shadow: 0 0 20px rgba(99,102,241,0.5); }
    50% { box-shadow: 0 0 35px rgba(99,102,241,0.8); }
}

/* ── Progress messages ── */
.progress-log {
    background: #0a0a14; border: 1px solid #1e1e3a; border-radius: 12px;
    padding: 16px 20px; margin-bottom: 24px; font-family: 'Courier New', monospace;
    font-size: 13px; color: #64748b; max-height: 200px; overflow-y: auto;
}
.log-line { padding: 2px 0; }
.log-line.success { color: #4ade80; }
.log-line.info { color: #60a5fa; }
.log-line.warn { color: #facc15; }
.log-line.error { color: #f87171; }

/* ── Metrics Row ── */
.metrics-row {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 16px; margin-bottom: 32px;
}
.metric-card {
    background: #0f0f1e; border: 1px solid #1e1e3a;
    border-radius: 14px; padding: 20px; text-align: center;
}
.metric-val { font-size: 36px; font-weight: 900; margin-bottom: 4px; }
.metric-label { font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.8px; }

/* ── Divider ── */
.section-divider {
    border: none; border-top: 1px solid #1e1e3a; margin: 32px 0;
}

/* ── Error box ── */
.error-box {
    background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3);
    border-radius: 12px; padding: 20px 24px; color: #fca5a5;
    font-size: 14px; margin-bottom: 24px;
}

/* ── Sample report notice ── */
.sample-notice {
    background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.2);
    border-radius: 12px; padding: 14px 20px; color: #a5b4fc;
    font-size: 13px; margin-bottom: 20px; text-align: center;
}

/* ── Spinner override ── */
.stSpinner > div { border-top-color: #6366f1 !important; }
</style>
"""

# ─────────────────────────────────────────────
# Helper: render pipeline steps
# ─────────────────────────────────────────────
PIPELINE_STEPS = [
    ("📁", "Upload"),
    ("🔍", "OCR"),
    ("🤖", "AI Agent"),
    ("📊", "Compare"),
    ("📄", "Report"),
]

def render_pipeline(active_step: int = -1, done_steps: set = None):
    """Render the 5-step pipeline indicator. active_step is 0-indexed."""
    done_steps = done_steps or set()
    html = '<div class="pipeline">'
    for i, (icon, label) in enumerate(PIPELINE_STEPS):
        if i in done_steps:
            css = "step-done"
            circle_icon = "✓"
        elif i == active_step:
            css = "step-active"
            circle_icon = icon
        else:
            css = "step-pending"
            circle_icon = str(i + 1)

        html += f"""
        <div class="pipeline-step {css}">
          <div class="step-circle">{circle_icon}</div>
          <div class="step-label">{label}</div>
        </div>"""
        if i < len(PIPELINE_STEPS) - 1:
            html += '<div class="pipeline-arrow">›</div>'
    html += "</div>"
    return html


# ─────────────────────────────────────────────
# Session State Initialization
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "report_html": None,
        "comparison_results": None,
        "ai_findings": None,
        "ocr_result": None,
        "processing": False,
        "error": None,
        "logs": [],
        "pipeline_done": set(),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def add_log(msg: str, kind: str = "info"):
    st.session_state.logs.append({"msg": msg, "kind": kind})


def reset_state():
    for k in ["report_html", "comparison_results", "ai_findings", "ocr_result",
              "processing", "error", "logs", "pipeline_done"]:
        if k in st.session_state:
            del st.session_state[k]
    init_state()


# ─────────────────────────────────────────────
# Main App
# ─────────────────────────────────────────────
def main():
    init_state()

    # Inject global CSS
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    # ── Hero Header ──
    st.markdown("""
    <div class="medinsight-hero">
      <div class="hero-logo">
        <span class="hero-icon">🔬</span>
        <span class="hero-title">MedInsight</span>
      </div>
      <p class="hero-tagline">Upload your lab report and get an AI-powered diagnostic analysis with clinical insights, reference comparisons, and personalized recommendations.</p>
      <div class="hero-badges">
        <span class="hero-badge">🤖 Claude AI</span>
        <span class="hero-badge">🔍 Web Search</span>
        <span class="hero-badge">📋 50+ Biomarkers</span>
        <span class="hero-badge">📊 Clinical Reference Ranges</span>
        <span class="hero-badge">🔒 Private & Local</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Main Container ──
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # Check API key
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        st.markdown("""
        <div class="error-box">
          ⚠️ <strong>GEMINI_API_KEY not set.</strong>
          Create a <code>.env</code> file from <code>.env.example</code> and add your free Gemini key
          from <a href="https://aistudio.google.com" target="_blank" style="color:#a5b4fc">aistudio.google.com</a>.
        </div>
        """, unsafe_allow_html=True)

    # ── Pipeline indicator ──
    if st.session_state.report_html:
        pipeline_html = render_pipeline(active_step=-1, done_steps={0, 1, 2, 3, 4})
    elif st.session_state.processing:
        pipeline_html = render_pipeline(active_step=1)
    else:
        pipeline_html = render_pipeline(active_step=0)
    st.markdown(pipeline_html, unsafe_allow_html=True)

    # ── Two-column layout: Upload + Patient Info ──
    col1, col2 = st.columns([3, 2], gap="large")

    with col1:
        st.markdown("""
        <div class="upload-card">
          <span class="upload-icon">📂</span>
          <div class="upload-title">Upload Your Lab Report</div>
          <div class="upload-sub">Drag & drop or click to browse</div>
          <div class="upload-formats">
            <span class="format-tag">PDF</span>
            <span class="format-tag">PNG</span>
            <span class="format-tag">JPG</span>
            <span class="format-tag">JPEG</span>
            <span class="format-tag">TIFF</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Drop your lab report here",
            type=["pdf", "png", "jpg", "jpeg", "tiff", "tif"],
            label_visibility="collapsed",
            key="lab_report_uploader",
        )

        if uploaded_file:
            st.markdown(f"""
            <div style="background:#0f2417;border:1px solid #166534;border-radius:10px;
                        padding:12px 16px;margin-top:12px;font-size:13px;color:#4ade80;">
              ✅ <strong>{uploaded_file.name}</strong> uploaded
              ({uploaded_file.size / 1024:.1f} KB)
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="patient-form">', unsafe_allow_html=True)
        st.markdown('<div class="form-title">👤 Patient Information (Optional)</div>', unsafe_allow_html=True)
        patient_name = st.text_input("Full Name", placeholder="e.g., Jane Smith", key="pt_name")
        c1, c2 = st.columns(2)
        with c1:
            patient_age = st.number_input("Age", min_value=1, max_value=120, value=None,
                                           placeholder="–", key="pt_age", step=1)
        with c2:
            patient_sex = st.selectbox("Biological Sex", ["Unknown", "Male", "Female"], key="pt_sex")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Analyze Button ──
    st.markdown("<div style='margin-top:8px;'>", unsafe_allow_html=True)
    analyze_clicked = st.button("🔬 Analyze Lab Report", key="analyze_btn", disabled=not uploaded_file)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Error display ──
    if st.session_state.error:
        st.markdown(f'<div class="error-box">❌ {st.session_state.error}</div>',
                    unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # Processing Pipeline
    # ─────────────────────────────────────────────
    if analyze_clicked and uploaded_file:
        reset_state()
        st.session_state.processing = True

        file_bytes = uploaded_file.read()
        filename = uploaded_file.name
        patient_info = {
            "name": patient_name or "Patient",
            "age": str(int(patient_age)) if patient_age else "",
            "sex": patient_sex.lower() if patient_sex != "Unknown" else "unknown",
        }

        # Progress containers
        pipeline_placeholder = st.empty()
        log_placeholder = st.empty()
        status_placeholder = st.empty()

        def update_ui(active: int, msg: str, kind: str = "info"):
            add_log(msg, kind)
            pipeline_placeholder.markdown(
                render_pipeline(active_step=active, done_steps=st.session_state.pipeline_done),
                unsafe_allow_html=True,
            )
            logs_html = '<div class="progress-log">'
            for entry in st.session_state.logs[-12:]:
                logs_html += f'<div class="log-line {entry["kind"]}">▶ {entry["msg"]}</div>'
            logs_html += "</div>"
            log_placeholder.markdown(logs_html, unsafe_allow_html=True)
            status_placeholder.markdown(
                f'<div class="sample-notice">⏳ {msg}</div>', unsafe_allow_html=True
            )

        try:
            # ── Step 1: OCR ──
            update_ui(1, f"Running OCR on '{filename}'…")
            from modules.ocr_engine import OCREngine
            ocr = OCREngine()
            ocr_result = ocr.extract(file_bytes, filename)
            st.session_state.ocr_result = ocr_result

            if ocr_result.get("error"):
                raise RuntimeError(f"OCR failed: {ocr_result['error']}")
            if not ocr_result.get("raw_text"):
                raise RuntimeError("OCR returned empty text. Check the file quality.")

            st.session_state.pipeline_done.add(1)
            update_ui(
                2,
                f"OCR complete — {len(ocr_result['raw_text'])} chars extracted "
                f"via {ocr_result['method']} (confidence: {ocr_result['confidence']}%)",
                "success",
            )

            # ── Step 2: Comparison Engine ──
            update_ui(3, "Comparing values to clinical reference ranges…")
            from modules.comparison_engine import ComparisonEngine
            comp = ComparisonEngine()
            comparison_results = comp.analyze(
                ocr_result["raw_text"],
                sex=patient_info.get("sex", "unknown"),
            )
            st.session_state.comparison_results = comparison_results
            summary = comparison_results.get("summary", {})
            st.session_state.pipeline_done.add(3)
            update_ui(
                2,
                f"Comparison done — {summary.get('total_tests', 0)} tests parsed, "
                f"{summary.get('abnormal_count', 0)} abnormal, "
                f"severity score {summary.get('severity_score', 0)}/100",
                "success",
            )

            # ── Step 3: Diagnostic Agent ──
            update_ui(2, "Running AI diagnostic agent (Gemini 2.0 Flash + web search)… this may take 30-60s")
            from modules.diagnostic_agent import DiagnosticAgent
            agent = DiagnosticAgent()
            ai_findings = agent.analyze(
                ocr_text=ocr_result["raw_text"],
                comparison_results=comparison_results,
                patient_info=patient_info,
            )
            st.session_state.ai_findings = ai_findings
            st.session_state.pipeline_done.add(2)
            n_findings = len(ai_findings.get("findings", []))
            n_patterns = len(ai_findings.get("patterns_identified", []))
            n_sources = len(ai_findings.get("searched_sources", []))
            update_ui(
                4,
                f"AI analysis complete — {n_findings} findings, "
                f"{n_patterns} patterns, {n_sources} sources searched",
                "success",
            )

            # ── Step 4: Generate Report ──
            update_ui(4, "Generating HTML health report…")
            from modules.report_generator import ReportGenerator
            rg = ReportGenerator()
            report_html = rg.generate(
                comparison_results=comparison_results,
                ai_findings=ai_findings,
                patient_info=patient_info,
                filename=filename,
            )
            st.session_state.report_html = report_html
            st.session_state.pipeline_done.add(4)
            update_ui(4, "Report ready! ✅", "success")
            time.sleep(0.5)

        except Exception as e:
            logger.exception("Pipeline error")
            st.session_state.error = str(e)
            update_ui(-1, f"Error: {e}", "error")
        finally:
            st.session_state.processing = False
            status_placeholder.empty()

        st.rerun()

    # ─────────────────────────────────────────────
    # Render Report
    # ─────────────────────────────────────────────
    if st.session_state.report_html:
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # ── Quick metrics ──
        summary = (st.session_state.comparison_results or {}).get("summary", {})
        counts = summary.get("counts", {})
        score = summary.get("severity_score", 0)
        overall = summary.get("overall_status", "Unknown")
        score_color = {
            "Excellent": "#22c55e", "Good": "#4ade80",
            "Attention Needed": "#facc15", "Concerning": "#fb923c", "Critical": "#ef4444",
        }.get(overall, "#60a5fa")

        st.markdown(f"""
        <div class="metrics-row">
          <div class="metric-card">
            <div class="metric-val" style="color:#60a5fa">{summary.get('total_tests', 0)}</div>
            <div class="metric-label">Tests Analyzed</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#4ade80">{counts.get('NORMAL', 0)}</div>
            <div class="metric-label">Normal</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#fb923c">{summary.get('abnormal_count', 0)}</div>
            <div class="metric-label">Abnormal</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:{score_color}">{score}</div>
            <div class="metric-label">Risk Score / 100</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Action row: download + reset ──
        col_a, col_b = st.columns([4, 1])
        with col_a:
            st.download_button(
                label="⬇️  Download Full Report (HTML)",
                data=st.session_state.report_html,
                file_name="medinsight_health_report.html",
                mime="text/html",
                key="download_report",
            )
        with col_b:
            if st.button("🔄 New Report", key="reset_btn"):
                reset_state()
                st.rerun()

        st.markdown("<div style='margin-top:24px;'>", unsafe_allow_html=True)
        # ── Embedded HTML Report ──
        components.html(
            st.session_state.report_html,
            height=2800,
            scrolling=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    elif not st.session_state.processing and not st.session_state.report_html:
        # ── Empty state / How it works ──
        st.markdown("""
        <div style="margin-top:32px;">
          <div style="text-align:center;margin-bottom:32px;">
            <h3 style="color:#64748b;font-weight:500;font-size:15px;">HOW IT WORKS</h3>
          </div>
          <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:16px;">
        """, unsafe_allow_html=True)

        steps_info = [
            ("📂", "Upload", "Drop a PDF or image of your lab report — blood tests, metabolic panels, thyroid, and more."),
            ("🔍", "OCR", "PyMuPDF extracts text from PDFs. Tesseract handles scanned images automatically."),
            ("🤖", "AI Agent", "Claude AI reads your results and uses web search to pull real clinical guidelines."),
            ("📊", "Compare", "Each value is compared to clinical reference ranges and classified as normal, borderline, or critical."),
            ("📄", "Report", "A detailed, color-coded health report with findings, patterns, and recommendations."),
        ]
        cards = ""
        for icon, title, desc in steps_info:
            cards += f"""
            <div style="background:#0f0f1e;border:1px solid #1e1e3a;border-radius:14px;padding:24px;text-align:center;">
              <div style="font-size:36px;margin-bottom:12px;">{icon}</div>
              <div style="font-weight:700;color:white;margin-bottom:8px;">{title}</div>
              <div style="font-size:12px;color:#64748b;line-height:1.6;">{desc}</div>
            </div>"""
        st.markdown(cards + "</div></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # close main-container


if __name__ == "__main__":
    main()
