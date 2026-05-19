"""
Report Generator — Builds a rich HTML health report from diagnostic results.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional


STATUS_COLORS = {
    "NORMAL": {"bg": "#0d3320", "border": "#22c55e", "text": "#4ade80", "badge": "#166534"},
    "BORDERLINE": {"bg": "#2d2a0d", "border": "#eab308", "text": "#facc15", "badge": "#713f12"},
    "LOW": {"bg": "#1e1a2e", "border": "#a78bfa", "text": "#c4b5fd", "badge": "#4c1d95"},
    "HIGH": {"bg": "#2d1b0e", "border": "#f97316", "text": "#fb923c", "badge": "#7c2d12"},
    "CRITICAL LOW": {"bg": "#2d0a0a", "border": "#ef4444", "text": "#f87171", "badge": "#7f1d1d"},
    "CRITICAL HIGH": {"bg": "#2d0a0a", "border": "#ef4444", "text": "#f87171", "badge": "#7f1d1d"},
}

SEVERITY_CONFIG = {
    "Excellent": {"color": "#22c55e", "icon": "✓", "gradient": "linear-gradient(135deg, #052e16, #166534)"},
    "Good": {"color": "#4ade80", "icon": "↑", "gradient": "linear-gradient(135deg, #052e16, #15803d)"},
    "Attention Needed": {"color": "#facc15", "icon": "!", "gradient": "linear-gradient(135deg, #1c1917, #713f12)"},
    "Concerning": {"color": "#fb923c", "icon": "⚠", "gradient": "linear-gradient(135deg, #1c1917, #7c2d12)"},
    "Critical": {"color": "#ef4444", "icon": "✕", "gradient": "linear-gradient(135deg, #1c1917, #7f1d1d)"},
}

CATEGORY_ICONS = {
    "CBC": "🩸", "Metabolic": "⚗️", "Liver": "🫀", "Lipid": "💊",
    "Thyroid": "🦋", "Diabetes": "🍬", "Vitamins": "🌿", "Iron": "⚙️",
    "Cardiac": "❤️", "Hormones": "🧬", "Urinalysis": "🔬",
}


class ReportGenerator:
    """Generates a full HTML health report from comparison + diagnostic results."""

    def generate(
        self,
        comparison_results: Dict[str, Any],
        ai_findings: Dict[str, Any],
        patient_info: Optional[Dict] = None,
        filename: str = "lab_report",
    ) -> str:
        patient_info = patient_info or {}
        now = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        summary = comparison_results.get("summary", {})
        results = comparison_results.get("results", [])
        overall = summary.get("overall_status", "Unknown")
        score = summary.get("severity_score", 0)
        sev_cfg = SEVERITY_CONFIG.get(overall, SEVERITY_CONFIG["Attention Needed"])

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MedInsight Health Report</title>
{self._styles()}
</head>
<body>
{self._header(patient_info, now, filename)}
{self._executive_summary(summary, score, overall, sev_cfg, ai_findings)}
{self._lab_results_table(results)}
{self._ai_findings_section(ai_findings)}
{self._patterns_section(ai_findings)}
{self._recommendations_section(ai_findings)}
{self._sources_section(ai_findings)}
{self._disclaimer_section(ai_findings)}
{self._footer(now)}
</body>
</html>"""
        return html

    # ─────────────────────────────────────────────
    # Sections
    # ─────────────────────────────────────────────

    def _header(self, patient_info: Dict, now: str, filename: str) -> str:
        name = patient_info.get("name", "Patient")
        age = patient_info.get("age", "")
        sex = patient_info.get("sex", "")
        meta = " · ".join(filter(None, [age and f"Age {age}", sex and sex.title()]))
        return f"""
<div class="report-header">
  <div class="header-left">
    <div class="logo">
      <span class="logo-icon">🔬</span>
      <span class="logo-text">MedInsight</span>
    </div>
    <div class="header-sub">AI-Powered Lab Report Analysis</div>
  </div>
  <div class="header-right">
    <div class="patient-name">{name}</div>
    <div class="patient-meta">{meta}</div>
    <div class="report-date">Generated {now}</div>
    <div class="report-file">Source: {filename}</div>
  </div>
</div>"""

    def _executive_summary(self, summary: Dict, score: int, overall: str, sev_cfg: Dict, ai_findings: Dict) -> str:
        counts = summary.get("counts", {})
        total = summary.get("total_tests", 0)
        abnormal = summary.get("abnormal_count", 0)
        critical = summary.get("critical_count", 0)
        patient_summary = ai_findings.get("patient_summary", "")

        score_color = sev_cfg["color"]
        gauge_deg = int((score / 100) * 180)

        stat_cards = ""
        for label, val, color in [
            ("Total Tests", total, "#60a5fa"),
            ("Normal", counts.get("NORMAL", 0), "#4ade80"),
            ("Abnormal", abnormal, "#fb923c"),
            ("Critical", critical, "#ef4444"),
        ]:
            stat_cards += f"""
            <div class="stat-card">
              <div class="stat-val" style="color:{color}">{val}</div>
              <div class="stat-label">{label}</div>
            </div>"""

        return f"""
<div class="section executive-summary" style="background:{sev_cfg['gradient']}">
  <div class="exec-left">
    <h2 class="section-title">Executive Summary</h2>
    <p class="patient-summary">{patient_summary}</p>
    <div class="stat-row">{stat_cards}</div>
  </div>
  <div class="exec-right">
    <div class="score-ring" style="--score:{gauge_deg}deg; --score-color:{score_color}">
      <div class="score-inner">
        <div class="score-num" style="color:{score_color}">{score}</div>
        <div class="score-label">/ 100</div>
        <div class="score-status" style="color:{score_color}">{overall}</div>
      </div>
    </div>
    <div class="score-desc">Health Risk Score</div>
  </div>
</div>"""

    def _lab_results_table(self, results: List[Dict]) -> str:
        if not results:
            return ""

        # Group by category
        by_cat: Dict[str, List] = {}
        for r in results:
            by_cat.setdefault(r.get("category", "Other"), []).append(r)

        tables_html = ""
        for category, cat_results in by_cat.items():
            icon = CATEGORY_ICONS.get(category, "🧪")
            rows = ""
            for r in cat_results:
                status = r.get("status", "NORMAL")
                colors = STATUS_COLORS.get(status, STATUS_COLORS["NORMAL"])
                ref_range = f"{r.get('ref_min', '–')} – {r.get('ref_max', '–')} {r.get('ref_unit', '')}".strip()
                arrow = {"HIGH": "↑", "CRITICAL HIGH": "↑↑", "LOW": "↓", "CRITICAL LOW": "↓↓",
                         "BORDERLINE": "~", "NORMAL": "✓"}.get(status, "")
                rows += f"""
              <tr style="background:{colors['bg']}; border-left: 3px solid {colors['border']}">
                <td class="test-name">{r.get('full_name', r.get('name', ''))}</td>
                <td class="test-value" style="color:{colors['text']}">{r.get('value', '')} {r.get('unit', '')}</td>
                <td class="ref-range">{ref_range}</td>
                <td><span class="status-badge" style="background:{colors['badge']}; color:{colors['text']}">{arrow} {status}</span></td>
              </tr>"""

            tables_html += f"""
          <div class="category-block">
            <h3 class="category-title">{icon} {category}</h3>
            <table class="results-table">
              <thead>
                <tr>
                  <th>Test</th><th>Your Value</th><th>Reference Range</th><th>Status</th>
                </tr>
              </thead>
              <tbody>{rows}</tbody>
            </table>
          </div>"""

        return f"""
<div class="section">
  <h2 class="section-title">📋 Lab Results</h2>
  {tables_html}
</div>"""

    def _ai_findings_section(self, ai_findings: Dict) -> str:
        findings = ai_findings.get("findings", [])
        if not findings:
            return ""

        cards_html = ""
        for f in findings:
            status = f.get("status", "NORMAL")
            colors = STATUS_COLORS.get(status, STATUS_COLORS["NORMAL"])
            causes = f.get("possible_causes", [])
            causes_html = "".join(f'<span class="cause-tag">{c}</span>' for c in causes[:4])
            severity = f.get("severity", "mild")
            sev_colors = {"mild": "#4ade80", "moderate": "#facc15", "severe": "#ef4444"}
            sev_color = sev_colors.get(severity, "#60a5fa")

            cards_html += f"""
          <div class="finding-card" style="border-color:{colors['border']}; background:{colors['bg']}">
            <div class="finding-header">
              <div class="finding-test">{f.get('test', '')}</div>
              <div class="finding-badges">
                <span class="status-badge" style="background:{colors['badge']}; color:{colors['text']}">{status}</span>
                <span class="severity-badge" style="color:{sev_color}">● {severity.title()}</span>
              </div>
            </div>
            <div class="finding-value" style="color:{colors['text']}">{f.get('value', '')}</div>
            <div class="finding-interp">{f.get('interpretation', '')}</div>
            {f'<div class="finding-causes"><strong>Possible causes:</strong><div class="causes-row">{causes_html}</div></div>' if causes else ''}
            <div class="finding-rec">💡 {f.get('recommendation', '')}</div>
          </div>"""

        return f"""
<div class="section">
  <h2 class="section-title">🤖 AI Diagnostic Findings</h2>
  <div class="findings-grid">{cards_html}</div>
</div>"""

    def _patterns_section(self, ai_findings: Dict) -> str:
        patterns = ai_findings.get("patterns_identified", [])
        if not patterns:
            return ""

        urgency_colors = {
            "routine": "#4ade80", "soon": "#facc15",
            "urgent": "#fb923c", "emergency": "#ef4444"
        }
        cards = ""
        for p in patterns:
            urgency = p.get("urgency", "routine")
            u_color = urgency_colors.get(urgency, "#60a5fa")
            tests = ", ".join(p.get("tests_involved", []))
            cards += f"""
          <div class="pattern-card">
            <div class="pattern-header">
              <div class="pattern-name">{p.get('pattern_name', '')}</div>
              <span class="urgency-badge" style="color:{u_color}; border-color:{u_color}">⏱ {urgency.upper()}</span>
            </div>
            <div class="pattern-tests">Tests: {tests}</div>
            <div class="pattern-significance">{p.get('clinical_significance', '')}</div>
          </div>"""

        return f"""
<div class="section">
  <h2 class="section-title">🔗 Clinical Patterns Identified</h2>
  <div class="patterns-grid">{cards}</div>
</div>"""

    def _recommendations_section(self, ai_findings: Dict) -> str:
        lifestyle = ai_findings.get("lifestyle_recommendations", [])
        follow_up = ai_findings.get("follow_up_recommendations", [])
        if not lifestyle and not follow_up:
            return ""

        lifestyle_html = "".join(f'<li class="rec-item lifestyle-item">🌱 {r}</li>' for r in lifestyle)
        followup_html = "".join(f'<li class="rec-item followup-item">🏥 {r}</li>' for r in follow_up)

        return f"""
<div class="section">
  <h2 class="section-title">📝 Recommendations</h2>
  <div class="rec-grid">
    {"<div class='rec-col'><h3 class='rec-subtitle'>Lifestyle</h3><ul class='rec-list'>" + lifestyle_html + "</ul></div>" if lifestyle else ""}
    {"<div class='rec-col'><h3 class='rec-subtitle'>Follow-Up Actions</h3><ul class='rec-list'>" + followup_html + "</ul></div>" if follow_up else ""}
  </div>
</div>"""

    def _sources_section(self, ai_findings: Dict) -> str:
        sources = ai_findings.get("searched_sources", [])
        if not sources:
            return ""
        items = "".join(f'<li class="source-item">🔗 {s}</li>' for s in sources)
        return f"""
<div class="section sources-section">
  <h2 class="section-title">📚 Clinical Sources Referenced</h2>
  <ul class="sources-list">{items}</ul>
</div>"""

    def _disclaimer_section(self, ai_findings: Dict) -> str:
        disclaimer = ai_findings.get("disclaimer", "This analysis is for informational purposes only and does not constitute medical advice. Always consult a qualified healthcare professional.")
        return f"""
<div class="disclaimer-box">
  <span class="disclaimer-icon">⚕️</span>
  <div>
    <strong>Medical Disclaimer</strong><br>
    {disclaimer}
  </div>
</div>"""

    def _footer(self, now: str) -> str:
        return f"""
<div class="report-footer">
  <span>MedInsight AI · Report generated {now}</span>
  <span>Powered by Gemini 2.0 Flash + Clinical Reference Database</span>
</div>"""

    # ─────────────────────────────────────────────
    # Styles
    # ─────────────────────────────────────────────

    def _styles(self) -> str:
        return """<style>
:root {
  --bg: #0a0a0f;
  --surface: #12121a;
  --surface2: #1a1a26;
  --border: #2a2a3d;
  --text: #e2e8f0;
  --text-muted: #94a3b8;
  --accent: #6366f1;
  --radius: 12px;
  --font: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--text); font-family: var(--font); line-height: 1.6; padding: 24px; font-size: 14px; }
/* Header */
.report-header { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #0f0f1a, #1a1a2e); border: 1px solid #2a2a4d; border-radius: var(--radius); padding: 24px 32px; margin-bottom: 20px; }
.logo { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
.logo-icon { font-size: 28px; }
.logo-text { font-size: 24px; font-weight: 800; background: linear-gradient(135deg, #6366f1, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.header-sub { color: var(--text-muted); font-size: 12px; }
.header-right { text-align: right; }
.patient-name { font-size: 20px; font-weight: 700; color: white; }
.patient-meta { color: #a78bfa; font-size: 13px; }
.report-date, .report-file { color: var(--text-muted); font-size: 12px; }
/* Sections */
.section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 28px 32px; margin-bottom: 20px; }
.section-title { font-size: 18px; font-weight: 700; color: white; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid var(--border); }
/* Executive Summary */
.executive-summary { display: flex; gap: 40px; align-items: center; border: none; }
.exec-left { flex: 1; }
.exec-right { flex: 0 0 160px; text-align: center; }
.patient-summary { color: var(--text); line-height: 1.8; margin-bottom: 20px; opacity: 0.9; }
.stat-row { display: flex; gap: 16px; flex-wrap: wrap; }
.stat-card { background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 14px 20px; text-align: center; min-width: 80px; }
.stat-val { font-size: 28px; font-weight: 800; }
.stat-label { font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }
/* Score Ring */
.score-ring { width: 130px; height: 130px; border-radius: 50%; background: conic-gradient(var(--score-color) var(--score), #1e1e2e 0deg); display: flex; align-items: center; justify-content: center; margin: 0 auto 12px; box-shadow: 0 0 30px rgba(0,0,0,0.5); }
.score-inner { width: 100px; height: 100px; border-radius: 50%; background: #0a0a14; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.score-num { font-size: 32px; font-weight: 900; line-height: 1; }
.score-label { font-size: 11px; color: var(--text-muted); }
.score-status { font-size: 10px; font-weight: 700; margin-top: 2px; }
.score-desc { font-size: 12px; color: var(--text-muted); }
/* Category blocks */
.category-block { margin-bottom: 28px; }
.category-title { font-size: 15px; font-weight: 600; color: #a78bfa; margin-bottom: 12px; }
/* Results Table */
.results-table { width: 100%; border-collapse: separate; border-spacing: 0 4px; }
.results-table thead tr { background: var(--surface2); }
.results-table th { padding: 10px 14px; text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; color: var(--text-muted); font-weight: 600; }
.results-table td { padding: 10px 14px; }
.results-table tr { border-radius: 8px; }
.test-name { font-weight: 500; color: var(--text); }
.test-value { font-weight: 700; font-size: 15px; }
.ref-range { color: var(--text-muted); font-size: 12px; }
/* Badges */
.status-badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; }
/* Findings Grid */
.findings-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.finding-card { border: 1px solid; border-radius: 10px; padding: 18px; }
.finding-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }
.finding-test { font-weight: 700; font-size: 15px; color: white; }
.finding-badges { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.severity-badge { font-size: 12px; font-weight: 600; }
.finding-value { font-size: 20px; font-weight: 800; margin-bottom: 10px; }
.finding-interp { color: var(--text); font-size: 13px; line-height: 1.7; margin-bottom: 10px; }
.finding-causes { margin-bottom: 10px; font-size: 12px; color: var(--text-muted); }
.causes-row { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 6px; }
.cause-tag { background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.12); border-radius: 20px; padding: 2px 10px; font-size: 11px; color: var(--text-muted); }
.finding-rec { background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.25); border-radius: 8px; padding: 10px 14px; font-size: 13px; color: #a5b4fc; }
/* Patterns */
.patterns-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
.pattern-card { background: var(--surface2); border: 1px solid var(--border); border-radius: 10px; padding: 16px; }
.pattern-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.pattern-name { font-weight: 700; color: white; font-size: 14px; }
.urgency-badge { border: 1px solid; border-radius: 20px; padding: 2px 10px; font-size: 10px; font-weight: 700; letter-spacing: 0.5px; }
.pattern-tests { font-size: 12px; color: var(--text-muted); margin-bottom: 8px; }
.pattern-significance { font-size: 13px; color: var(--text); line-height: 1.6; }
/* Recommendations */
.rec-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.rec-subtitle { font-size: 14px; font-weight: 600; color: #a78bfa; margin-bottom: 12px; }
.rec-list { list-style: none; display: flex; flex-direction: column; gap: 8px; }
.rec-item { background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; font-size: 13px; line-height: 1.5; }
/* Sources */
.sources-section { background: rgba(99,102,241,0.05); border-color: rgba(99,102,241,0.2); }
.sources-list { list-style: none; display: flex; flex-direction: column; gap: 6px; }
.source-item { font-size: 12px; color: var(--text-muted); padding: 4px 0; word-break: break-all; }
/* Disclaimer */
.disclaimer-box { display: flex; gap: 16px; align-items: flex-start; background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.25); border-radius: var(--radius); padding: 20px 24px; margin-bottom: 20px; font-size: 13px; color: #fca5a5; line-height: 1.7; }
.disclaimer-icon { font-size: 28px; flex-shrink: 0; }
/* Footer */
.report-footer { display: flex; justify-content: space-between; color: var(--text-muted); font-size: 11px; padding: 16px 0; border-top: 1px solid var(--border); }
@media (max-width: 700px) {
  .executive-summary { flex-direction: column; }
  .rec-grid { grid-template-columns: 1fr; }
  .report-header { flex-direction: column; gap: 16px; text-align: center; }
  .header-right { text-align: center; }
}
</style>"""
