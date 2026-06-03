"""
Report History Manager — Persists analyzed lab report data for future reference.

Storage: JSON file at data/report_history.json
Each report stores structured data (not the full HTML) for chatbot context.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

HISTORY_PATH = Path(__file__).parent.parent / "data" / "report_history.json"
MAX_REPORTS = 20


class ReportHistoryManager:
    """Manages persistent storage of analyzed lab report data."""

    def __init__(self):
        self._ensure_file()

    def _ensure_file(self):
        """Create the history file if it doesn't exist."""
        if not HISTORY_PATH.exists():
            HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(HISTORY_PATH, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _load(self) -> List[Dict]:
        """Load all reports from disk."""
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save(self, reports: List[Dict]):
        """Save all reports to disk."""
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(reports, f, indent=2, default=str)

    def save_report(
        self,
        filename: str,
        patient_info: Dict,
        ocr_text: str,
        comparison_results: Dict,
        ai_findings: Dict,
        location_data: Optional[Dict] = None,
        nearby_facilities: Optional[Dict] = None,
    ) -> str:
        """
        Save a new report to history.

        Returns the generated report ID.
        """
        reports = self._load()

        report_id = str(uuid.uuid4())[:8]
        summary = comparison_results.get("summary", {})

        record = {
            "id": report_id,
            "timestamp": datetime.now().isoformat(),
            "filename": filename,
            "patient_info": patient_info,
            "ocr_text": ocr_text[:3000],  # truncate for storage
            "comparison_summary": {
                "total_tests": summary.get("total_tests", 0),
                "abnormal_count": summary.get("abnormal_count", 0),
                "critical_count": summary.get("critical_count", 0),
                "severity_score": summary.get("severity_score", 0),
                "overall_status": summary.get("overall_status", "Unknown"),
            },
            "comparison_results_full": {
                "results": comparison_results.get("results", []),
                "summary": summary,
            },
            "ai_findings": {
                "patient_summary": ai_findings.get("patient_summary", ""),
                "overall_assessment": ai_findings.get("overall_assessment", ""),
                "findings": ai_findings.get("findings", []),
                "patterns_identified": ai_findings.get("patterns_identified", []),
                "lifestyle_recommendations": ai_findings.get("lifestyle_recommendations", []),
                "follow_up_recommendations": ai_findings.get("follow_up_recommendations", []),
            },
            "location_data": location_data,
            "nearby_facilities": nearby_facilities,
        }

        reports.insert(0, record)  # newest first

        # Enforce max reports limit
        if len(reports) > MAX_REPORTS:
            reports = reports[:MAX_REPORTS]

        self._save(reports)
        logger.info(f"Saved report {report_id} for '{filename}'")
        return report_id

    def list_reports(self) -> List[Dict]:
        """
        Return a summary list of all stored reports (newest first).

        Each item: {id, timestamp, filename, patient_info, comparison_summary}
        """
        reports = self._load()
        summaries = []
        for r in reports:
            summaries.append({
                "id": r["id"],
                "timestamp": r["timestamp"],
                "filename": r["filename"],
                "patient_info": r.get("patient_info", {}),
                "comparison_summary": r.get("comparison_summary", {}),
            })
        return summaries

    def load_report(self, report_id: str) -> Optional[Dict]:
        """
        Load a full report record by ID.

        Returns the full record dict, or None if not found.
        """
        reports = self._load()
        for r in reports:
            if r["id"] == report_id:
                return r
        return None

    def get_report_context(self, report_id: str) -> Optional[Dict]:
        """
        Load a report and return it in the format expected by MedicalChatEngine.

        Returns: {patient_info, comparison_results, ai_findings, ocr_text, location_data, nearby_facilities}
        """
        record = self.load_report(report_id)
        if not record:
            return None

        return {
            "patient_info": record.get("patient_info", {}),
            "comparison_results": record.get("comparison_results_full", {}),
            "ai_findings": record.get("ai_findings", {}),
            "ocr_text": record.get("ocr_text", ""),
            "location_data": record.get("location_data"),
            "nearby_facilities": record.get("nearby_facilities"),
        }

    def delete_report(self, report_id: str) -> bool:
        """Delete a report by ID. Returns True if found and deleted."""
        reports = self._load()
        original_len = len(reports)
        reports = [r for r in reports if r["id"] != report_id]
        if len(reports) < original_len:
            self._save(reports)
            logger.info(f"Deleted report {report_id}")
            return True
        return False
