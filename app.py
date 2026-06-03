"""
MedInsight — AI-Powered Medical Lab Report Analyzer
Main Streamlit Application — Enhanced with streamlit.components.v1 HTML components
"""

import os
import json
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
# Page Config — MUST be first Streamlit call
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="MedInsight — AI Lab Analyzer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Global CSS Injection (Streamlit frame + widgets)
# ─────────────────────────────────────────────
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.stApp { background: #08080f !important; color: #e2e8f0 !important; }

#MainMenu, footer { visibility: hidden; }
header { background-color: transparent !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* Main Container */
.main-container { max-width: 1100px; margin: 0 auto; padding: 40px 24px; }

/* Upload Card */
.upload-card {
    background: linear-gradient(135deg, #0f0f1e, #141428);
    border: 1.5px dashed #2d2d5a; border-radius: 20px;
    padding: 60px 40px; text-align: center;
    transition: all 0.3s ease; margin-bottom: 32px;
    position: relative; overflow: hidden;
}
.upload-card::before {
    content: ''; position: absolute; inset: 0;
    background: radial-gradient(ellipse at center, rgba(99,102,241,0.06) 0%, transparent 70%);
}
.upload-icon { font-size: 56px; margin-bottom: 16px; display: block; }
.upload-title { font-size: 22px; font-weight: 700; color: white; margin-bottom: 8px; }
.upload-sub { color: #64748b; font-size: 14px; margin-bottom: 20px; }
.upload-formats { display: inline-flex; gap: 8px; flex-wrap: wrap; justify-content: center; }
.format-tag {
    background: rgba(99,102,241,0.12); border: 1px solid rgba(99,102,241,0.25);
    color: #a5b4fc; border-radius: 6px; padding: 3px 10px; font-size: 12px; font-weight: 500;
}

/* Patient Info Form */
.form-title { font-size: 16px; font-weight: 600; color: #a78bfa; margin-bottom: 20px; }

/* Streamlit widget overrides */
.stTextInput > div > div > input,
.stSelectbox > div > div > div,
.stNumberInput > div > div > input {
    background: #141428 !important; border: 1px solid #2d2d5a !important;
    color: #e2e8f0 !important; border-radius: 10px !important;
}
.stTextInput > label, .stSelectbox > label, .stNumberInput > label {
    color: #94a3b8 !important; font-size: 13px !important; font-weight: 500 !important;
}
.stFileUploader > div { background: transparent !important; border: none !important; }
div[data-testid="stFileUploader"] { background: transparent !important; }

/* Analyze Button */
.stButton > button {
    width: 100% !important;
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    color: white !important; border: none !important;
    border-radius: 14px !important; padding: 16px 32px !important;
    font-size: 17px !important; font-weight: 700 !important;
    letter-spacing: 0.3px !important; cursor: pointer !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 8px 32px rgba(79,70,229,0.35) !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    box-shadow: 0 12px 40px rgba(99,102,241,0.5) !important;
    transform: translateY(-2px) !important;
}

/* Section Divider */
.section-divider { border: none; border-top: 1px solid #1e1e3a; margin: 32px 0; }

/* Error box */
.error-box {
    background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3);
    border-radius: 12px; padding: 20px 24px; color: #fca5a5;
    font-size: 14px; margin-bottom: 24px;
}

/* Sample notice */
.sample-notice {
    background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.2);
    border-radius: 12px; padding: 14px 20px; color: #a5b4fc;
    font-size: 13px; margin-bottom: 20px; text-align: center;
}

/* Spinner override */
.stSpinner > div { border-top-color: #6366f1 !important; }

/* Download button override */
.stDownloadButton > button {
    background: rgba(99,102,241,0.12) !important;
    border: 1px solid rgba(99,102,241,0.3) !important;
    color: #a5b4fc !important; border-radius: 12px !important;
    font-weight: 600 !important;
    box-shadow: none !important;
    padding: 12px 24px !important;
    font-size: 14px !important;
}
.stDownloadButton > button:hover {
    background: rgba(99,102,241,0.22) !important;
    border-color: rgba(99,102,241,0.5) !important;
    color: white !important; transform: none !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0a0a14 !important; border-right: 1px solid #1e1e3a !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { color: #e2e8f0 !important; }
.sidebar-title {
    font-size: 18px; font-weight: 800;
    background: linear-gradient(135deg, #818cf8, #6ee7b7);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}
.sidebar-sub { color: #64748b; font-size: 12px; margin-bottom: 20px; }
.history-card {
    background: #12121a; border: 1px solid #1e1e3a;
    border-radius: 12px; padding: 14px 16px;
    margin-bottom: 8px; cursor: pointer; transition: all 0.2s ease;
}
.history-card:hover { border-color: #4f46e5; background: #16162a; }
.history-card.active { border-color: #6366f1; background: rgba(99,102,241,0.1); }
.history-filename {
    font-size: 13px; font-weight: 600; color: #e2e8f0;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.history-meta { font-size: 11px; color: #64748b; margin-top: 4px; }
.history-badge {
    display: inline-block; padding: 2px 8px;
    border-radius: 10px; font-size: 10px; font-weight: 700; margin-top: 6px;
}
</style>
"""

# ─────────────────────────────────────────────
# components.html Builders
# ─────────────────────────────────────────────

def _hero_html() -> str:
    """Animated hero header with floating orbs and entrance animations."""
    return """<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box;}
body{background:transparent;font-family:'Inter',sans-serif;overflow:hidden;}
.hero{
  background:linear-gradient(135deg,#0d0d1f 0%,#12122b 40%,#0d1f12 100%);
  border-bottom:1px solid #1e1e3a;
  padding:38px 60px 30px;text-align:center;
  position:relative;overflow:hidden;
  min-height:220px;display:flex;flex-direction:column;
  align-items:center;justify-content:center;
}
.orb{position:absolute;border-radius:50%;filter:blur(70px);animation:drift 9s ease-in-out infinite alternate;}
.o1{width:320px;height:320px;background:rgba(99,102,241,0.13);top:-100px;left:-80px;}
.o2{width:260px;height:260px;background:rgba(34,197,94,0.09);bottom:-70px;right:-50px;animation-delay:-5s;}
.o3{width:200px;height:200px;background:rgba(168,85,247,0.09);top:10px;right:22%;animation-delay:-2.5s;}
@keyframes drift{from{transform:translate(0,0) scale(1);}to{transform:translate(22px,-18px) scale(1.12);}}
.content{position:relative;z-index:2;}
.logo{display:inline-flex;align-items:center;gap:14px;margin-bottom:14px;animation:fadeDown .7s ease both;}
.logo-icon{font-size:50px;filter:drop-shadow(0 0 24px rgba(99,102,241,.75));animation:pulseIcon 3s ease-in-out infinite;}
@keyframes pulseIcon{0%,100%{filter:drop-shadow(0 0 24px rgba(99,102,241,.75));}50%{filter:drop-shadow(0 0 42px rgba(99,102,241,1));}}
.logo-text{
  font-size:46px;font-weight:900;letter-spacing:-2px;
  background:linear-gradient(135deg,#818cf8,#c4b5fd,#6ee7b7);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
}
.tagline{color:#94a3b8;font-size:15.5px;font-weight:400;max-width:640px;margin:0 auto 22px;line-height:1.65;animation:fadeDown .8s ease .1s both;}
.badges{display:flex;gap:9px;justify-content:center;flex-wrap:wrap;animation:fadeDown .9s ease .2s both;}
.badge{
  background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.11);
  border-radius:20px;padding:5px 16px;font-size:12px;color:#94a3b8;
  transition:all .2s ease;cursor:default;
}
.badge:hover{background:rgba(99,102,241,0.15);border-color:rgba(99,102,241,0.4);color:#a5b4fc;}
@keyframes fadeDown{from{opacity:0;transform:translateY(-16px);}to{opacity:1;transform:translateY(0);}}
</style></head>
<body>
<div class="hero">
  <div class="orb o1"></div><div class="orb o2"></div><div class="orb o3"></div>
  <div class="content">
    <div class="logo">
      <span class="logo-icon">🔬</span>
      <span class="logo-text">MedInsight</span>
    </div>
    <p class="tagline">Upload your lab report and get an AI-powered diagnostic analysis with clinical insights, reference comparisons, and personalised recommendations</p>
    <div class="badges">
      <span class="badge">🤖 Gemini 2.0 Flash</span>
      <span class="badge">🔍 Web Search</span>
      <span class="badge">📊 Clinical Reference Ranges</span>
      <span class="badge">🔒 Private &amp; Local</span>
      <span class="badge">💬 AI Chat</span>
    </div>
  </div>
</div>
</body></html>"""


def _pipeline_html(active_step: int = -1, done_steps: set = None) -> str:
    """Animated, JavaScript-driven pipeline step indicator."""
    done_steps = done_steps or set()
    STEPS = [("📁","Upload"),("🔍","OCR"),("🤖","AI Agent"),("📊","Compare"),("📄","Report")]

    steps_data = []
    for i, (icon, label) in enumerate(STEPS):
        if i in done_steps:
            state, display = "done", "✓"
        elif i == active_step:
            state, display = "active", icon
        else:
            state, display = "pending", str(i + 1)
        steps_data.append({"state": state, "display": display, "label": label})

    steps_json = json.dumps(steps_data)

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700;800&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:transparent;font-family:'Inter',sans-serif;overflow:hidden;}}
.pipeline{{display:flex;align-items:center;justify-content:center;padding:20px 0;flex-wrap:wrap;}}
.step{{display:flex;flex-direction:column;align-items:center;gap:9px;padding:0 10px;min-width:88px;animation:stepIn .5s ease both;}}
@keyframes stepIn{{from{{opacity:0;transform:translateY(10px);}}to{{opacity:1;transform:translateY(0);}}}}
.circle{{
  width:54px;height:54px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:20px;font-weight:800;border:2px solid;
  transition:all .4s ease;
}}
.label{{font-size:11px;font-weight:600;text-align:center;text-transform:uppercase;letter-spacing:.5px;line-height:1.3;}}
.pending .circle{{background:#12121a;border-color:#2a2a3d;color:#4a4a6a;}}
.pending .label{{color:#4a4a6a;}}
.active .circle{{
  background:linear-gradient(135deg,#4f46e5,#7c3aed);border-color:#6366f1;color:white;
  box-shadow:0 0 22px rgba(99,102,241,.65),0 0 44px rgba(99,102,241,.3);
  animation:pulseCircle 1.6s ease-in-out infinite;
}}
.active .label{{color:#a5b4fc;}}
@keyframes pulseCircle{{
  0%,100%{{box-shadow:0 0 22px rgba(99,102,241,.65),0 0 44px rgba(99,102,241,.3);transform:scale(1);}}
  50%{{box-shadow:0 0 36px rgba(99,102,241,.9),0 0 64px rgba(99,102,241,.45);transform:scale(1.06);}}
}}
.done .circle{{background:#052e16;border-color:#16a34a;color:#4ade80;}}
.done .label{{color:#4ade80;}}
.arrow{{color:#2a2a3d;font-size:22px;padding:0 2px;margin-bottom:28px;}}
.arrow.lit{{color:#16a34a;}}
</style></head>
<body>
<div class="pipeline" id="pipe"></div>
<script>
const steps={steps_json};
const c=document.getElementById('pipe');
steps.forEach((s,i)=>{{
  const el=document.createElement('div');
  el.className='step '+s.state;
  el.style.animationDelay=(i*0.08)+'s';
  el.innerHTML=`<div class="circle">${{s.display}}</div><div class="label">${{s.label}}</div>`;
  c.appendChild(el);
  if(i<steps.length-1){{
    const a=document.createElement('div');
    a.className='arrow'+(s.state==='done'?' lit':'');
    a.textContent='›';
    c.appendChild(a);
  }}
}});
</script>
</body></html>"""


def _progress_log_html(logs: list) -> str:
    """Terminal-style animated progress log."""
    color_map = {"success":"#4ade80","info":"#60a5fa","warn":"#facc15","error":"#f87171"}
    lines_html = ""
    for entry in logs[-15:]:
        color = color_map.get(entry.get("kind","info"),"#60a5fa")
        msg = str(entry["msg"]).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        lines_html += f'<div class="ln" style="color:{color}">▶ {msg}</div>\n'

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:transparent;font-family:'JetBrains Mono','Courier New',monospace;overflow:hidden;}}
.log{{
  background:#06060f;border:1px solid #1e1e3a;border-radius:12px;
  padding:14px 18px;font-size:12.5px;
  max-height:210px;overflow-y:auto;
  scrollbar-width:thin;scrollbar-color:#2d2d5a transparent;
}}
.log::-webkit-scrollbar{{width:4px;}}
.log::-webkit-scrollbar-thumb{{background:#2d2d5a;border-radius:4px;}}
.ln{{padding:2px 0;animation:slideIn .3s ease both;line-height:1.55;}}
@keyframes slideIn{{from{{opacity:0;transform:translateX(-8px);}}to{{opacity:1;transform:translateX(0);}}}}
.cursor{{
  display:inline-block;width:8px;height:14px;
  background:#6366f1;margin-left:4px;vertical-align:middle;
  animation:blink 1s step-end infinite;
}}
@keyframes blink{{0%,100%{{opacity:1;}}50%{{opacity:0;}}}}
</style></head>
<body>
<div class="log" id="logbox">
{lines_html}
<div class="ln" style="color:#3a3a5a">▶ <span class="cursor"></span></div>
</div>
<script>
const b=document.getElementById('logbox');
b.scrollTop=b.scrollHeight;
</script>
</body></html>"""


def _metrics_html(total: int, normal: int, abnormal: int, score: int, overall: str) -> str:
    """Animated metric cards with SVG ring gauge."""
    score_color = {
        "Excellent":"#22c55e","Good":"#4ade80",
        "Attention Needed":"#facc15","Concerning":"#fb923c","Critical":"#ef4444",
    }.get(overall, "#60a5fa")

    # SVG circle: circumference = 2π×45 ≈ 283
    stroke_offset = 283 - int(283 * min(score, 100) / 100)

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800;900&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:transparent;font-family:'Inter',sans-serif;overflow:hidden;}}
.grid{{
  display:grid;grid-template-columns:1fr 1fr 1fr 196px;
  gap:14px;padding:4px 0 8px;
}}
.card{{
  background:linear-gradient(135deg,#0f0f1e,#12121a);
  border:1px solid #1e1e3a;border-radius:16px;padding:22px 18px;
  text-align:center;animation:cardIn .55s ease both;
  transition:border-color .3s ease,box-shadow .3s ease;cursor:default;
}}
.card:hover{{border-color:#2d2d5a;box-shadow:0 8px 32px rgba(0,0,0,.4);}}
.card:nth-child(1){{animation-delay:.04s;}}
.card:nth-child(2){{animation-delay:.08s;}}
.card:nth-child(3){{animation-delay:.12s;}}
.card:nth-child(4){{animation-delay:.16s;}}
@keyframes cardIn{{from{{opacity:0;transform:translateY(14px);}}to{{opacity:1;transform:translateY(0);}}}}
.val{{font-size:42px;font-weight:900;margin-bottom:6px;line-height:1;}}
.lbl{{font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:.8px;}}
/* Score ring */
.score-card{{
  background:linear-gradient(135deg,#0f0f1e,#12121a);
  border:1px solid #1e1e3a;border-radius:16px;padding:18px;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  animation:cardIn .55s ease .16s both;cursor:default;
  transition:border-color .3s ease;
}}
.score-card:hover{{border-color:#2d2d5a;}}
.ring-wrap{{position:relative;width:108px;height:108px;margin-bottom:10px;}}
.ring-svg{{width:108px;height:108px;transform:rotate(-90deg);}}
.ring-bg{{fill:none;stroke:#1e1e3a;stroke-width:10;}}
.ring-fg{{
  fill:none;stroke:{score_color};stroke-width:10;stroke-linecap:round;
  stroke-dasharray:283;stroke-dashoffset:{stroke_offset};
  filter:drop-shadow(0 0 6px {score_color}99);
  animation:ringIn 1.3s cubic-bezier(.4,0,.2,1) both;
}}
@keyframes ringIn{{
  from{{stroke-dashoffset:283;}}
  to{{stroke-dashoffset:{stroke_offset};}}
}}
.ring-inner{{
  position:absolute;inset:0;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
}}
.ring-num{{font-size:28px;font-weight:900;color:{score_color};line-height:1;}}
.ring-denom{{font-size:10px;color:#64748b;}}
.ring-status{{font-size:9px;font-weight:700;color:{score_color};margin-top:2px;text-align:center;}}
.score-lbl{{font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:.8px;}}
</style></head>
<body>
<div class="grid">
  <div class="card">
    <div class="val" style="color:#60a5fa" id="t">0</div>
    <div class="lbl">Tests Analyzed</div>
  </div>
  <div class="card">
    <div class="val" style="color:#4ade80" id="n">0</div>
    <div class="lbl">Normal</div>
  </div>
  <div class="card">
    <div class="val" style="color:#fb923c" id="a">0</div>
    <div class="lbl">Abnormal</div>
  </div>
  <div class="score-card">
    <div class="ring-wrap">
      <svg class="ring-svg" viewBox="0 0 100 100">
        <circle class="ring-bg" cx="50" cy="50" r="45"/>
        <circle class="ring-fg" cx="50" cy="50" r="45"/>
      </svg>
      <div class="ring-inner">
        <div class="ring-num" id="s">0</div>
        <div class="ring-denom">/100</div>
        <div class="ring-status">{overall}</div>
      </div>
    </div>
    <div class="score-lbl">Risk Score</div>
  </div>
</div>
<script>
function count(el,target,ms){{
  let v=0,step=target/(ms/16);
  (function tick(){{
    v+=step;if(v>=target){{el.textContent=target;return;}}
    el.textContent=Math.floor(v);requestAnimationFrame(tick);
  }})();
}}
count(document.getElementById('t'),{total},700);
count(document.getElementById('n'),{normal},800);
count(document.getElementById('a'),{abnormal},900);
count(document.getElementById('s'),{score},1100);
</script>
</body></html>"""


def _chat_header_html(has_context: bool, report_name: str = "") -> str:
    """Premium chat section header with live status pill."""
    subtitle = (
        f"Report loaded: <strong style='color:#c4b5fd'>{report_name}</strong> — ask about your results"
        if has_context else "Ask any health or medical question"
    )
    dot_color = "#4ade80" if has_context else "#facc15"
    status_label = "Report Active" if has_context else "General Mode"

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:transparent;font-family:'Inter',sans-serif;overflow:hidden;}}
.header{{
  background:linear-gradient(135deg,#0d0d1f,#12122b);
  border:1px solid #1e1e3a;border-bottom:1px solid #1a1a2e;
  border-radius:20px 20px 0 0;
  padding:22px 28px;
  display:flex;align-items:center;gap:16px;
}}
.icon{{
  width:48px;height:48px;border-radius:14px;flex-shrink:0;
  background:linear-gradient(135deg,#4f46e5,#7c3aed);
  display:flex;align-items:center;justify-content:center;font-size:24px;
  box-shadow:0 4px 20px rgba(79,70,229,.45);
  animation:pop .5s cubic-bezier(.175,.885,.32,1.275) both;
}}
@keyframes pop{{from{{transform:scale(.6);opacity:0;}}to{{transform:scale(1);opacity:1;}}}}
.info{{flex:1;}}
.title{{font-size:19px;font-weight:800;color:white;margin-bottom:4px;}}
.sub{{font-size:13px;color:#64748b;}}
.pill{{
  display:flex;align-items:center;gap:7px;flex-shrink:0;
  background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
  border-radius:20px;padding:6px 14px;font-size:12px;font-weight:600;color:#94a3b8;
}}
.dot{{
  width:8px;height:8px;border-radius:50%;
  background:{dot_color};box-shadow:0 0 8px {dot_color};
  animation:pulseDot 2s ease-in-out infinite;
}}
@keyframes pulseDot{{0%,100%{{opacity:1;}}50%{{opacity:.35;}}}}
</style></head>
<body>
<div class="header">
  <div class="icon">💬</div>
  <div class="info">
    <div class="title">MedInsight Chat</div>
    <div class="sub">{subtitle}</div>
  </div>
  <div class="pill"><div class="dot"></div>{status_label}</div>
</div>
</body></html>"""


def _upload_success_html(filename: str, size_kb: float) -> str:
    """Animated upload success notification."""
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:transparent;font-family:'Inter',sans-serif;overflow:hidden;}}
.box{{
  background:#0f2417;border:1px solid #166534;border-radius:12px;
  padding:14px 18px;font-size:13px;color:#4ade80;
  display:flex;align-items:center;gap:10px;
  animation:slideUp .4s cubic-bezier(.175,.885,.32,1.275) both;
}}
@keyframes slideUp{{from{{opacity:0;transform:translateY(10px);}}to{{opacity:1;transform:translateY(0);}}}}
.check{{
  width:32px;height:32px;border-radius:50%;
  background:rgba(74,222,128,.15);border:1px solid rgba(74,222,128,.3);
  display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0;
}}
.name{{font-weight:700;color:white;}}
.meta{{font-size:12px;color:#4ade80;opacity:.7;margin-top:2px;}}
</style></head>
<body>
<div class="box">
  <div class="check">✅</div>
  <div>
    <div class="name">{filename}</div>
    <div class="meta">Ready to analyze · {size_kb:.1f} KB</div>
  </div>
</div>
</body></html>"""


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
        "chat_messages": [],
        "chat_history": [],
        "active_report_context": None,
        "active_report_id": None,
        "active_filename": "",
        "enable_location": False,
        "location_data": None,
        "radius_km": 5.0,
        "manual_location": "",
        "nearby_facilities": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def add_log(msg: str, kind: str = "info"):
    st.session_state.logs.append({"msg": msg, "kind": kind})


def reset_state():
    for k in [
        "report_html","comparison_results","ai_findings","ocr_result",
        "processing","error","logs","pipeline_done",
        "chat_messages","chat_history","active_report_context","active_report_id","active_filename",
        "nearby_facilities",
    ]:
        if k in st.session_state:
            del st.session_state[k]
    init_state()


def _location_section():
    """Renders the Location & Recommendations options section (manual input only)."""
    from modules.facility_recommender import geocode_address

    st.markdown('<div class="form-title">📍 Location & Nearby Facility Recommendations (Optional)</div>', unsafe_allow_html=True)

    enable_loc = st.checkbox(
        "Enable nearby hospital & gym recommendations based on my lab results",
        key="enable_location_chk",
        value=st.session_state.enable_location
    )
    st.session_state.enable_location = enable_loc

    if enable_loc:
        col_input, col_config = st.columns([1, 1], gap="medium")

        with col_input:
            # ── Manual location: city or pincode ──
            manual_input = st.text_input(
                "🔍 Enter your city, area or PIN code:",
                value=st.session_state.manual_location,
                placeholder="e.g., Mumbai, Delhi 110001, London SW1A",
                key="manual_loc_input_field"
            )

            search_clicked = st.button("📌 Search Location", key="search_loc_btn", use_container_width=True)

            if search_clicked and manual_input and manual_input.strip():
                with st.spinner(f"Finding '{manual_input}'..."):
                    geocode_res = geocode_address(manual_input.strip())
                    if geocode_res:
                        lat, lon, display_name = geocode_res
                        st.session_state.manual_location = manual_input.strip()
                        st.session_state.location_data = {
                            "status": "success",
                            "source": "manual",
                            "latitude": lat,
                            "longitude": lon,
                            "display_name": display_name
                        }
                    else:
                        st.session_state.location_data = {
                            "status": "error",
                            "error": f"Could not find '{manual_input}'. Try a different city name or PIN code."
                        }
            elif search_clicked and not manual_input:
                st.session_state.location_data = None
                st.session_state.manual_location = ""

            # ── Clear location button ──
            if st.session_state.location_data:
                if st.button("✕ Clear location", key="clear_loc_btn"):
                    st.session_state.location_data = None
                    st.session_state.manual_location = ""
                    st.rerun()

            # ── Location status display ──
            loc_data = st.session_state.location_data
            if loc_data and loc_data.get("status") == "success":
                display = loc_data.get("display_name", "")
                parts = display.split(", ")
                short = ", ".join(parts[:3]) if len(parts) > 3 else display
                lat = loc_data.get("latitude", 0)
                lon = loc_data.get("longitude", 0)
                st.markdown(
                    f'<div style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); '
                    f'border-radius:10px; padding:12px 16px; font-size:13px; color:#a7f3d0; margin-top:8px;">'
                    f'✅ <strong>Location set:</strong> {short}<br>'
                    f'<span style="font-size:11px; color:#6ee7b7; opacity:0.8;">'
                    f'Coords: ({lat:.4f}, {lon:.4f}) · Facilities will be searched at analysis time</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            elif loc_data and loc_data.get("status") == "error":
                st.markdown(
                    f'<div class="error-box" style="margin-top:8px; padding:10px 14px; margin-bottom:0;">'
                    f'⚠️ {loc_data.get("error", "Location error")}'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div style="background:rgba(99,102,241,0.07); border:1px solid rgba(99,102,241,0.2); '
                    'border-radius:10px; padding:12px 16px; font-size:13px; color:#94a3b8; margin-top:8px;">'
                    '📍 Enter your city or PIN code above and click <strong>Search Location</strong>'
                    '</div>',
                    unsafe_allow_html=True
                )

        with col_config:
            # ── Radius selector ──
            radius_list = ["5 km", "10 km", "25 km"]
            current_radius_str = f"{int(st.session_state.radius_km)} km"
            default_radius_idx = (
                radius_list.index(current_radius_str) if current_radius_str in radius_list else 0
            )
            radius_option = st.radio(
                "Search Radius for Facilities",
                radius_list,
                index=default_radius_idx,
                horizontal=True,
                key="radius_radio"
            )
            st.session_state.radius_km = float(radius_option.split()[0])

            # ── Info about what gets recommended ──
            st.markdown(
                '<div style="background:rgba(99,102,241,0.07); border:1px solid rgba(99,102,241,0.15); '
                'border-radius:10px; padding:14px 16px; margin-top:12px;">'
                '<div style="font-size:12px; font-weight:700; color:#a5b4fc; margin-bottom:8px;">What gets recommended?</div>'
                '<div style="font-size:12px; color:#94a3b8; line-height:1.7;">'
                '🏥 <strong style="color:#fca5a5;">Hospitals/Clinics</strong> — when any test result is abnormal or critical<br>'
                '🏋️ <strong style="color:#86efac;">Gyms/Fitness</strong> — when metabolic markers (glucose, cholesterol, triglycerides) are elevated'
                '</div>'
                '</div>',
                unsafe_allow_html=True
            )


# ─────────────────────────────────────────────
# Main App
# ─────────────────────────────────────────────
def main():
    init_state()

    # Inject global CSS
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    # Sidebar
    _render_sidebar()

    # ── Hero Header ── (components.html)
    components.html(_hero_html(), height=228, scrolling=False)

    # ── Main Container ──
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # API key warning
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        st.markdown("""
        <div class="error-box">
          ⚠️ <strong>GEMINI_API_KEY not set.</strong>
          Create a <code>.env</code> file from <code>.env.example</code> and add your free Gemini key from
          <a href="https://aistudio.google.com" target="_blank" style="color:#a5b4fc">aistudio.google.com</a>.
        </div>
        """, unsafe_allow_html=True)

    # ── Pipeline Indicator ── (components.html)
    pipeline_placeholder = st.empty()
    if st.session_state.report_html:
        with pipeline_placeholder:
            components.html(_pipeline_html(-1, {0,1,2,3,4}), height=105, scrolling=False)
    elif st.session_state.processing:
        with pipeline_placeholder:
            components.html(_pipeline_html(1), height=105, scrolling=False)
    else:
        with pipeline_placeholder:
            components.html(_pipeline_html(0), height=105, scrolling=False)

    # ── Two-column layout ──
    col1, col2 = st.columns([3, 2], gap="large")

    with col1:
        st.markdown("""
        <div class="upload-card">
          <span class="upload-icon">📂</span>
          <div class="upload-title">Upload Your Lab Report</div>
          <div class="upload-sub">Drag &amp; drop or click to browse</div>
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
            components.html(
                _upload_success_html(uploaded_file.name, uploaded_file.size / 1024),
                height=72,
                scrolling=False,
            )

    with col2:
        st.markdown('<div class="form-title">👤 Patient Information (Optional)</div>', unsafe_allow_html=True)
        patient_name = st.text_input("Full Name", placeholder="e.g., Jane Smith", key="pt_name")
        c1, c2 = st.columns(2)
        with c1:
            patient_age = st.number_input("Age", min_value=1, max_value=120, value=None,
                                          placeholder="–", key="pt_age", step=1)
        with c2:
            patient_sex = st.selectbox("Biological Sex", ["Unknown", "Male", "Female"], key="pt_sex")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    _location_section()
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Analyze Button ──
    st.markdown("<div style='margin-top:8px;'>", unsafe_allow_html=True)
    analyze_clicked = st.button("🔬 Analyze Lab Report", key="analyze_btn", disabled=not uploaded_file)
    st.markdown("</div>", unsafe_allow_html=True)

    # Error display
    if st.session_state.error:
        st.markdown(f'<div class="error-box">❌ {st.session_state.error}</div>', unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # Processing Pipeline
    # ─────────────────────────────────────────────
    if analyze_clicked and uploaded_file:
        # Check if location is enabled and valid
        has_valid_location = (
            st.session_state.enable_location 
            and st.session_state.location_data 
            and st.session_state.location_data.get("status") == "success"
        )
        
        if not has_valid_location:
            st.markdown("""
            <div style="background:rgba(251, 146, 60, 0.15); border:1px solid rgba(251, 146, 60, 0.4); 
            border-radius:10px; padding:14px 16px; margin-bottom:16px; font-size:13px; color:#fb923c;">
            ⚠️ <strong>Valid location required</strong><br>
            <span style="font-size:12px; color:#fca5a5; opacity:0.9;">
            Please enable location and enter a valid city/area/PIN code above, then click "Search Location" to get facility recommendations with your analysis.
            </span>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Location is valid, proceed with analysis
            reset_state()
            st.session_state.processing = True

            file_bytes = uploaded_file.read()
            filename = uploaded_file.name
            st.session_state.active_filename = filename
            patient_info = {
                "name": patient_name or "Patient",
                "age": str(int(patient_age)) if patient_age else "",
                "sex": patient_sex.lower() if patient_sex != "Unknown" else "unknown",
            }

            prog_pipeline = st.empty()
            prog_log      = st.empty()
            prog_status   = st.empty()

            def update_ui(active: int, msg: str, kind: str = "info"):
                add_log(msg, kind)
                with prog_pipeline:
                    components.html(
                        _pipeline_html(active, st.session_state.pipeline_done),
                        height=105, scrolling=False,
                    )
                with prog_log:
                    components.html(
                        _progress_log_html(st.session_state.logs),
                        height=240, scrolling=False,
                    )
                prog_status.markdown(
                    f'<div class="sample-notice">⏳ {msg}</div>',
                    unsafe_allow_html=True,
                )

            try:
                # Step 1: OCR
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
                    f"OCR complete — {len(ocr_result['raw_text'])} chars via {ocr_result['method']}"
                    f" (confidence: {ocr_result['confidence']}%)",
                    "success",
                )

                # Step 2: Comparison Engine
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
                    f"Comparison done — {summary.get('total_tests',0)} tests, "
                    f"{summary.get('abnormal_count',0)} abnormal, "
                    f"score {summary.get('severity_score',0)}/100",
                    "success",
                )

                # Step 3: Diagnostic Agent
                update_ui(2, "Running AI diagnostic agent (Gemini 2.0 Flash + web search)… 30–60 s")
                from modules.diagnostic_agent import DiagnosticAgent
                agent = DiagnosticAgent()
                ai_findings = agent.analyze(
                    ocr_text=ocr_result["raw_text"],
                    comparison_results=comparison_results,
                    patient_info=patient_info,
                )
                st.session_state.ai_findings = ai_findings
                st.session_state.pipeline_done.add(2)
                n_f = len(ai_findings.get("findings", []))
                n_p = len(ai_findings.get("patterns_identified", []))
                n_s = len(ai_findings.get("searched_sources", []))
                update_ui(4, f"AI analysis complete — {n_f} findings, {n_p} patterns, {n_s} sources searched", "success")

                # Step 4: Generate Report
                update_ui(4, "Generating HTML health report…")

                # Fetch nearby facility recommendations if enabled
                nearby_facilities = None
                if st.session_state.enable_location and st.session_state.location_data and st.session_state.location_data.get("status") == "success":
                    lat = st.session_state.location_data["latitude"]
                    lon = st.session_state.location_data["longitude"]
                    radius = st.session_state.radius_km
                    
                    update_ui(4, "Checking facility recommendation triggers…")
                    from modules.facility_recommender import FacilityRecommender
                    recommender = FacilityRecommender()
                    rec_hosp, rec_gyms = recommender.check_recommendations_needed(comparison_results)
                    
                    # Log diagnostic info for debugging
                    test_statuses = [r.get("status", "UNKNOWN") for r in comparison_results.get("results", [])]
                    logger.info(f"Lab test statuses found: {set(test_statuses)}")
                    logger.info(f"Recommendation check: hospitals={rec_hosp}, gyms={rec_gyms}")
                    add_log(f"Lab statuses: {', '.join(set(test_statuses)) if test_statuses else 'No tests found'}", "info")
                    
                    if rec_hosp or rec_gyms:
                        update_ui(4, f"Searching nearby facilities (radius: {radius} km)…")
                        try:
                            nearby_facilities = recommender.search_nearby(
                                lat=lat,
                                lon=lon,
                                radius_km=radius,
                                search_hospitals=rec_hosp,
                                search_gyms=rec_gyms
                            )
                            st.session_state.nearby_facilities = nearby_facilities
                            h_count = len(nearby_facilities.get("hospitals", []))
                            g_count = len(nearby_facilities.get("gyms", []))
                            add_log(f"Found {h_count} hospitals/clinics and {g_count} fitness centers nearby.", "success")
                        except Exception as rec_err:
                            logger.error(f"Failed to search nearby facilities: {rec_err}")
                            add_log("Could not retrieve nearby facilities due to API error.", "warn")
                    else:
                        add_log("Lab results within normal limits; no facility recommendations triggered.", "info")

                from modules.report_generator import ReportGenerator
                rg = ReportGenerator()
                report_html = rg.generate(
                    comparison_results=comparison_results,
                    ai_findings=ai_findings,
                    patient_info=patient_info,
                    filename=filename,
                    nearby_facilities=nearby_facilities,
                )
                st.session_state.report_html = report_html
                st.session_state.pipeline_done.add(4)
                update_ui(4, "Report ready! ✅", "success")
                time.sleep(0.5)

                # Auto-save to history
                try:
                    from modules.report_history import ReportHistoryManager
                    history_mgr = ReportHistoryManager()
                    report_id = history_mgr.save_report(
                        filename=filename,
                        patient_info=patient_info,
                        ocr_text=ocr_result.get("raw_text", ""),
                        comparison_results=comparison_results,
                        ai_findings=ai_findings,
                        location_data=st.session_state.location_data if st.session_state.enable_location else None,
                        nearby_facilities=st.session_state.nearby_facilities if st.session_state.enable_location else None,
                    )
                    st.session_state.active_report_id = report_id
                    st.session_state.active_report_context = {
                        "patient_info": patient_info,
                        "comparison_results": comparison_results,
                        "ai_findings": ai_findings,
                        "ocr_text": ocr_result.get("raw_text", "")[:500],
                        "location_data": st.session_state.location_data if st.session_state.enable_location else None,
                        "nearby_facilities": st.session_state.nearby_facilities if st.session_state.enable_location else None,
                    }
                    st.session_state.chat_messages = []
                    st.session_state.chat_history = []
                    add_log(f"Saved to history (ID: {report_id})", "success")
                except Exception as hist_err:
                    logger.warning(f"Failed to save report to history: {hist_err}")

            except Exception as e:
                logger.exception("Pipeline error")
                st.session_state.error = str(e)
                update_ui(-1, f"Error: {e}", "error")
            finally:
                st.session_state.processing = False
                prog_status.empty()

            st.rerun()

    # ─────────────────────────────────────────────
    # Render Report
    # ─────────────────────────────────────────────
    if st.session_state.report_html:
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # Animated metrics dashboard (components.html)
        summary  = (st.session_state.comparison_results or {}).get("summary", {})
        counts   = summary.get("counts", {})
        score    = summary.get("severity_score", 0)
        overall  = summary.get("overall_status", "Unknown")
        total    = summary.get("total_tests", 0)
        normal   = counts.get("NORMAL", 0)
        abnormal = summary.get("abnormal_count", 0)

        components.html(
            _metrics_html(total, normal, abnormal, score, overall),
            height=156,
            scrolling=False,
        )

        # Download + Reset
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

        st.markdown("<div style='margin-top:12px;'>", unsafe_allow_html=True)
        # Embedded HTML Report with Dynamic Height
        # Calculate height based on report content
        comparison_results = st.session_state.comparison_results or {}
        ai_findings = st.session_state.ai_findings or {}
        results = comparison_results.get("results", [])
        findings = ai_findings.get("findings", [])
        patterns = ai_findings.get("patterns_identified", [])
        nearby = st.session_state.nearby_facilities
        
        # Dynamic height estimation: base + content-based additions
        base_height = 600  # Header, summary, intro sections
        results_height = len(results) * 25  # ~25px per lab result row
        findings_height = len(findings) * 50  # ~50px per finding block
        patterns_height = len(patterns) * 40  # ~40px per pattern
        recommendations_height = 100 if ai_findings.get("recommendations") else 0
        facilities_height = 250 if nearby else 0
        sources_height = 60 if ai_findings.get("searched_sources") else 0
        
        dynamic_height = max(
            base_height + results_height + findings_height + patterns_height + 
            recommendations_height + facilities_height + sources_height + 100,  # +100 buffer
            800  # Minimum height
        )
        
        components.html(
            st.session_state.report_html,
            height=dynamic_height,
            scrolling=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Chat Section ──
    _render_chat_section()

    st.markdown("</div>", unsafe_allow_html=True)  # close main-container


# ─────────────────────────────────────────────
# Sidebar: Report History
# ─────────────────────────────────────────────
def _render_sidebar():
    """Render the sidebar with report history."""
    with st.sidebar:

        with st.sidebar.expander("ℹ️ How It Works", expanded=False):
            st.markdown("""
            <div style="display:flex;flex-direction:column;gap:12px;margin-top:8px;">
                <div style="background:#12121a;border:1px solid #1e1e3a;border-radius:10px;padding:12px;">
                    <div style="font-size:20px;margin-bottom:4px;">📂</div>
                    <div style="font-weight:700;color:white;font-size:13px;margin-bottom:2px;">1. Upload</div>
                    <div style="font-size:11px;color:#64748b;line-height:1.4;">Drop a PDF or image of your lab report.</div>
                </div>
                <div style="background:#12121a;border:1px solid #1e1e3a;border-radius:10px;padding:12px;">
                    <div style="font-size:20px;margin-bottom:4px;">🔍</div>
                    <div style="font-weight:700;color:white;font-size:13px;margin-bottom:2px;">2. OCR</div>
                    <div style="font-size:11px;color:#64748b;line-height:1.4;">PyMuPDF + Tesseract extract text automatically.</div>
                </div>
                <div style="background:#12121a;border:1px solid #1e1e3a;border-radius:10px;padding:12px;">
                    <div style="font-size:20px;margin-bottom:4px;">🤖</div>
                    <div style="font-weight:700;color:white;font-size:13px;margin-bottom:2px;">3. AI Agent</div>
                    <div style="font-size:11px;color:#64748b;line-height:1.4;">Gemini 2.0 Flash reads results and searches clinical guidelines.</div>
                </div>
                <div style="background:#12121a;border:1px solid #1e1e3a;border-radius:10px;padding:12px;">
                    <div style="font-size:20px;margin-bottom:4px;">📊</div>
                    <div style="font-weight:700;color:white;font-size:13px;margin-bottom:2px;">4. Compare</div>
                    <div style="font-size:11px;color:#64748b;line-height:1.4;">Values compared to clinical reference ranges.</div>
                </div>
                <div style="background:#12121a;border:1px solid #1e1e3a;border-radius:10px;padding:12px;">
                    <div style="font-size:20px;margin-bottom:4px;">📄</div>
                    <div style="font-weight:700;color:white;font-size:13px;margin-bottom:2px;">5. Report</div>
                    <div style="font-size:11px;color:#64748b;line-height:1.4;">Detailed, colour-coded health report is generated.</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<hr style="border-color:#1e1e3a;margin:16px 0;">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">📋 Report History</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-sub">Your past analysed reports</div>', unsafe_allow_html=True)

        try:
            from modules.report_history import ReportHistoryManager
            history_mgr = ReportHistoryManager()
            reports = history_mgr.list_reports()
        except Exception:
            reports = []

        if not reports:
            st.markdown(
                '<div style="text-align:center;color:#4a4a6a;font-size:13px;'
                'padding:24px 0;font-style:italic;">No reports yet.<br>'
                'Analyse a lab report to see it here.</div>',
                unsafe_allow_html=True,
            )
            return

        for report in reports:
            rid      = report["id"]
            fname    = report.get("filename", "Unknown")
            ts       = report.get("timestamp", "")
            csummary = report.get("comparison_summary", {})
            status   = csummary.get("overall_status", "Unknown")
            score    = csummary.get("severity_score", 0)
            ab       = csummary.get("abnormal_count", 0)

            try:
                from datetime import datetime
                dt = datetime.fromisoformat(ts)
                date_str = dt.strftime("%b %d, %Y · %I:%M %p")
            except Exception:
                date_str = ts[:16] if ts else "Unknown date"

            badge_colors = {
                "Excellent":      ("#052e16","#4ade80"),
                "Good":           ("#052e16","#4ade80"),
                "Attention Needed":("#2d2a0d","#facc15"),
                "Concerning":     ("#2d1b0e","#fb923c"),
                "Critical":       ("#2d0a0a","#f87171"),
            }
            bg, fg = badge_colors.get(status, ("#1e1e3a","#94a3b8"))
            is_active  = st.session_state.get("active_report_id") == rid
            card_class = "history-card active" if is_active else "history-card"

            st.markdown(f"""
            <div class="{card_class}">
              <div class="history-filename">📄 {fname}</div>
              <div class="history-meta">{date_str} · {ab} abnormal</div>
              <span class="history-badge" style="background:{bg};color:{fg}">{status} · {score}/100</span>
            </div>
            """, unsafe_allow_html=True)

            col_load, col_del = st.columns([3, 1])
            with col_load:
                if st.button("💬 Chat", key=f"load_{rid}", use_container_width=True):
                    _load_report_for_chat(rid)
                    st.rerun()
            with col_del:
                if st.button("🗑️", key=f"del_{rid}", use_container_width=True):
                    try:
                        history_mgr.delete_report(rid)
                        if st.session_state.get("active_report_id") == rid:
                            st.session_state.active_report_id  = None
                            st.session_state.active_report_context = None
                            st.session_state.active_filename   = ""
                            st.session_state.chat_messages     = []
                            st.session_state.chat_history      = []
                    except Exception:
                        pass
                    st.rerun()


def _load_report_for_chat(report_id: str):
    """Load a historical report's context into the chatbot and display the HTML report."""
    try:
        from modules.report_history import ReportHistoryManager
        history_mgr = ReportHistoryManager()
        record = history_mgr.load_report(report_id)
        if record:
            st.session_state.active_report_id = report_id
            st.session_state.active_report_context = {
                "patient_info": record.get("patient_info", {}),
                "comparison_results": record.get("comparison_results_full", {}),
                "ai_findings": record.get("ai_findings", {}),
                "ocr_text": record.get("ocr_text", ""),
                "location_data": record.get("location_data"),
                "nearby_facilities": record.get("nearby_facilities"),
            }
            p = record.get("patient_info", {})
            st.session_state.active_filename = p.get("name") or "Report"
            st.session_state.chat_messages   = []
            st.session_state.chat_history    = []

            # Re-generate report HTML on-the-fly to show in UI
            from modules.report_generator import ReportGenerator
            rg = ReportGenerator()
            st.session_state.report_html = rg.generate(
                comparison_results=record.get("comparison_results_full", {}),
                ai_findings=record.get("ai_findings", {}),
                patient_info=record.get("patient_info", {}),
                filename=record.get("filename", "lab_report"),
                nearby_facilities=record.get("nearby_facilities"),
            )
            st.session_state.comparison_results = record.get("comparison_results_full", {})

            # Populate location setting checkboxes so users can see current settings
            st.session_state.enable_location = record.get("location_data") is not None
            st.session_state.location_data = record.get("location_data")
            if record.get("location_data") and record.get("location_data", {}).get("source") == "manual":
                # For manual location, restore manual input text
                st.session_state.manual_location = record.get("location_data", {}).get("display_name", "")
            else:
                st.session_state.manual_location = ""
    except Exception as e:
        logger.warning(f"Failed to load report {report_id}: {e}")


# ─────────────────────────────────────────────
# Chat Section
# ─────────────────────────────────────────────
def _render_chat_section():
    """Render the interactive chat section."""
    has_context = st.session_state.get("active_report_context") is not None
    report_name = st.session_state.get("active_filename", "")

    # Premium chat header (components.html)
    components.html(
        _chat_header_html(has_context, report_name),
        height=84,
        scrolling=False,
    )

    messages = st.session_state.get("chat_messages", [])

    if not messages and not has_context:
        st.markdown(
            '<div style="background:linear-gradient(135deg,#0d0d1f,#12122b);'
            'border:1px solid #1e1e3a;border-top:none;border-bottom-left-radius:20px;'
            'border-bottom-right-radius:20px;padding:32px;'
            'text-align:center;color:#4a4a6a;font-size:13px;font-style:italic;">'
            '💡 Upload and analyse a lab report to get personalised answers, '
            'or ask any general health question below.</div>',
            unsafe_allow_html=True,
        )
    elif not messages and has_context:
        st.markdown(
            '<div style="background:linear-gradient(135deg,#0d0d1f,#12122b);'
            'border:1px solid #1e1e3a;border-top:none;border-bottom-left-radius:20px;'
            'border-bottom-right-radius:20px;padding:32px;'
            'text-align:center;color:#4a4a6a;font-size:13px;font-style:italic;">'
            '✅ Report loaded! Ask me anything — e.g., "What does my high TSH mean?" '
            'or "Should I worry about my cholesterol?"</div>',
            unsafe_allow_html=True,
        )
    else:
        # Wrap active messages in a styled container
        st.markdown(
            '<div style="background:linear-gradient(135deg,#0d0d1f,#12122b);'
            'border:1px solid #1e1e3a;border-top:none;border-bottom-left-radius:20px;'
            'border-bottom-right-radius:20px;padding:16px 24px 8px;">',
            unsafe_allow_html=True,
        )
        for msg in messages:
            with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🔬"):
                st.markdown(msg["content"])
        st.markdown("</div>", unsafe_allow_html=True)

    # Chat input
    if prompt := st.chat_input("Ask about your lab results or any health question…", key="chat_input"):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🔬"):
            with st.spinner("Thinking…"):
                try:
                    from modules.medical_chat import MedicalChatEngine
                    engine = MedicalChatEngine()
                    response, updated_history = engine.chat(
                        user_message=prompt,
                        report_context=st.session_state.get("active_report_context"),
                        chat_history=st.session_state.get("chat_history", []),
                    )
                    st.session_state.chat_history = updated_history
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
                    st.markdown(response)
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
                    st.markdown(error_msg)


if __name__ == "__main__":
    main()