"""
Comparison Engine — Parses lab values from OCR text and compares to clinical reference ranges.

Pipeline:
  raw_text → parse_lab_values → compare_to_reference → severity scoring
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Load reference ranges database
_REF_PATH = Path(__file__).parent.parent / "data" / "reference_ranges.json"
with open(_REF_PATH, encoding="utf-8") as f:
    REFERENCE_RANGES: Dict = json.load(f)

# Build a flat lookup: test_name_lower → {range_data, category}
_FLAT_REFS: Dict[str, Dict] = {}
for category, tests in REFERENCE_RANGES.items():
    for test_name, range_data in tests.items():
        _FLAT_REFS[test_name.lower()] = {**range_data, "category": category, "name": test_name}
        # Also index by full_name
        if "full_name" in range_data:
            _FLAT_REFS[range_data["full_name"].lower()] = {**range_data, "category": category, "name": test_name}


# Regex patterns to extract lab values
# Matches: "Hemoglobin: 11.2 g/dL" or "WBC   4.5   x10³/µL" etc.
_LAB_PATTERN = re.compile(
    r"(?P<name>[A-Za-z][A-Za-z0-9\s\-\(\)\/\.]+?)"   # test name
    r"[\s:=]+?"
    r"(?P<value>\d+\.?\d*)"                             # numeric value
    r"\s*"
    r"(?P<unit>[A-Za-zµ%\³\⁶\/\.\s]{0,20})?",          # optional unit
    re.MULTILINE,
)

# Status labels
STATUS_NORMAL = "NORMAL"
STATUS_LOW = "LOW"
STATUS_HIGH = "HIGH"
STATUS_CRITICAL_LOW = "CRITICAL LOW"
STATUS_CRITICAL_HIGH = "CRITICAL HIGH"
STATUS_BORDERLINE = "BORDERLINE"

# Severity weights
SEVERITY_WEIGHTS = {
    STATUS_NORMAL: 0,
    STATUS_BORDERLINE: 10,
    STATUS_LOW: 25,
    STATUS_HIGH: 25,
    STATUS_CRITICAL_LOW: 60,
    STATUS_CRITICAL_HIGH: 60,
}


class ComparisonEngine:
    """Parses lab values from OCR text and compares them to clinical reference ranges."""

    def analyze(self, raw_text: str, sex: str = "unknown") -> Dict[str, Any]:
        """
        Full pipeline: parse → compare → score.

        Args:
            raw_text: OCR-extracted text
            sex: "male", "female", or "unknown"

        Returns:
            {
                lab_values: [...],
                results: [...],         # comparison results
                severity_score: int,    # 0-100
                summary: {...},
                unrecognized: [...]     # extracted but not in reference DB
            }
        """
        lab_values = self.parse_lab_values(raw_text)
        results, unrecognized = self.compare_to_reference(lab_values, sex)
        severity_score = self.calculate_severity_score(results)
        summary = self._build_summary(results, severity_score)

        return {
            "lab_values": lab_values,
            "results": results,
            "severity_score": severity_score,
            "summary": summary,
            "unrecognized": unrecognized,
        }

    # ─────────────────────────────────────────────
    # Step 1: Parse lab values from text
    # ─────────────────────────────────────────────

    def parse_lab_values(self, raw_text: str) -> List[Dict[str, Any]]:
        """
        Extract lab test name/value/unit triplets from raw OCR text.

        Returns list of dicts: {name, value, unit, raw_line}
        """
        lab_values = []
        seen_names = set()

        # Process line by line for better accuracy
        lines = raw_text.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            for match in _LAB_PATTERN.finditer(line):
                name = match.group("name").strip().rstrip(":= ")
                value_str = match.group("value").strip()
                unit = (match.group("unit") or "").strip()

                # Filter out noise
                if len(name) < 2 or len(name) > 60:
                    continue
                if not value_str:
                    continue
                try:
                    value = float(value_str)
                except ValueError:
                    continue

                # Deduplicate
                name_key = name.lower().strip()
                if name_key in seen_names:
                    continue
                seen_names.add(name_key)

                lab_values.append({
                    "name": name,
                    "value": value,
                    "unit": unit,
                    "raw_line": line,
                })

        logger.info(f"Parsed {len(lab_values)} lab values from text")
        return lab_values

    # ─────────────────────────────────────────────
    # Step 2: Compare to reference ranges
    # ─────────────────────────────────────────────

    def compare_to_reference(
        self, lab_values: List[Dict], sex: str = "unknown"
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Compare each parsed lab value to the reference database.

        Returns:
            (results, unrecognized)
        """
        results = []
        unrecognized = []

        for lv in lab_values:
            ref = self._find_reference(lv["name"])
            if ref is None:
                unrecognized.append(lv)
                continue

            # Apply sex-specific ranges if available
            effective_ref = self._apply_sex_specific(ref, sex)
            status = self._classify(lv["value"], effective_ref)

            results.append({
                "name": ref["name"],
                "full_name": ref.get("full_name", ref["name"]),
                "category": ref["category"],
                "value": lv["value"],
                "unit": lv.get("unit") or ref.get("unit", ""),
                "ref_min": effective_ref.get("min"),
                "ref_max": effective_ref.get("max"),
                "ref_unit": ref.get("unit", ""),
                "status": status,
                "severity": SEVERITY_WEIGHTS[status],
                "critical_low": ref.get("critical_low"),
                "critical_high": ref.get("critical_high"),
            })

        logger.info(f"Compared {len(results)} values; {len(unrecognized)} unrecognized")
        return results, unrecognized

    # ─────────────────────────────────────────────
    # Step 3: Severity scoring
    # ─────────────────────────────────────────────

    def calculate_severity_score(self, results: List[Dict]) -> int:
        """
        Compute an overall health severity score from 0 (perfect) to 100 (critical).

        Algorithm: weighted sum, capped at 100, normalized per test count.
        """
        if not results:
            return 0

        total_severity = sum(r["severity"] for r in results)
        max_possible = len(results) * SEVERITY_WEIGHTS[STATUS_CRITICAL_HIGH]
        raw_score = (total_severity / max_possible) * 100 if max_possible > 0 else 0

        # Boost for any critical values
        critical_count = sum(
            1 for r in results
            if r["status"] in (STATUS_CRITICAL_LOW, STATUS_CRITICAL_HIGH)
        )
        boost = min(critical_count * 15, 40)

        return min(100, round(raw_score + boost))

    # ─────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────

    def _find_reference(self, name: str) -> Optional[Dict]:
        """Fuzzy-ish lookup: exact match first, then partial match."""
        key = name.lower().strip()
        if key in _FLAT_REFS:
            return _FLAT_REFS[key]

        # Partial match — find first ref whose key is contained in the name or vice versa
        for ref_key, ref_data in _FLAT_REFS.items():
            if ref_key in key or key in ref_key:
                return ref_data

        return None

    @staticmethod
    def _apply_sex_specific(ref: Dict, sex: str) -> Dict:
        """Return sex-adjusted reference if available."""
        if sex in ("female", "male") and "sex_specific" in ref:
            sex_ref = ref["sex_specific"].get(sex)
            if sex_ref:
                merged = {**ref, **sex_ref}
                return merged
        return ref

    @staticmethod
    def _classify(value: float, ref: Dict) -> str:
        """Classify a value as NORMAL / LOW / HIGH / CRITICAL LOW / CRITICAL HIGH / BORDERLINE."""
        lo = ref.get("min")
        hi = ref.get("max")
        crit_lo = ref.get("critical_low")
        crit_hi = ref.get("critical_high")

        if crit_lo is not None and value < crit_lo:
            return STATUS_CRITICAL_LOW
        if crit_hi is not None and value > crit_hi:
            return STATUS_CRITICAL_HIGH
        if lo is not None and value < lo:
            # Check if borderline (within 10% of lower bound)
            if lo > 0 and value >= lo * 0.90:
                return STATUS_BORDERLINE
            return STATUS_LOW
        if hi is not None and value > hi:
            # Check if borderline (within 10% of upper bound)
            if hi > 0 and value <= hi * 1.10:
                return STATUS_BORDERLINE
            return STATUS_HIGH
        return STATUS_NORMAL

    @staticmethod
    def _build_summary(results: List[Dict], severity_score: int) -> Dict:
        """Build a structured summary of findings."""
        counts = {
            STATUS_NORMAL: 0,
            STATUS_BORDERLINE: 0,
            STATUS_LOW: 0,
            STATUS_HIGH: 0,
            STATUS_CRITICAL_LOW: 0,
            STATUS_CRITICAL_HIGH: 0,
        }
        for r in results:
            if r["status"] in counts:
                counts[r["status"]] += 1

        abnormal = [r for r in results if r["status"] != STATUS_NORMAL]
        critical = [r for r in results if r["status"] in (STATUS_CRITICAL_LOW, STATUS_CRITICAL_HIGH)]

        if severity_score == 0:
            overall = "Excellent"
        elif severity_score <= 15:
            overall = "Good"
        elif severity_score <= 35:
            overall = "Attention Needed"
        elif severity_score <= 60:
            overall = "Concerning"
        else:
            overall = "Critical"

        return {
            "total_tests": len(results),
            "counts": counts,
            "abnormal_count": len(abnormal),
            "critical_count": len(critical),
            "abnormal_tests": abnormal,
            "critical_tests": critical,
            "overall_status": overall,
            "severity_score": severity_score,
        }
