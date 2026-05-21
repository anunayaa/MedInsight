"""
Diagnostic Agent — Uses Google Gemini API (google-genai SDK) with function calling.

Free tier: 1,500 requests/day via Google AI Studio (aistudio.google.com)
Model: gemini-2.0-flash
"""

import os
import json
import re
import logging
from typing import Dict, Any, List, Optional

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
MODEL = "gemini-2.0-flash"

# ─────────────────────────────────────────────
# Tool / Function Declarations
# ─────────────────────────────────────────────

TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="web_search",
                description=(
                    "Search the web for clinical guidelines, medical literature, "
                    "normal reference ranges, drug interactions, or any medical information "
                    "needed to interpret lab results."
                ),
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "query": types.Schema(
                            type=types.Type.STRING,
                            description="Medical search query",
                        ),
                        "max_results": types.Schema(
                            type=types.Type.INTEGER,
                            description="Number of results (1-5)",
                        ),
                    },
                    required=["query"],
                ),
            ),
            types.FunctionDeclaration(
                name="lookup_reference_range",
                description="Look up the clinical reference range for a specific lab test from the local database.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "test_name": types.Schema(
                            type=types.Type.STRING,
                            description="Lab test name (e.g., 'Hemoglobin', 'TSH', 'LDL')",
                        ),
                    },
                    required=["test_name"],
                ),
            ),
        ]
    )
]

SYSTEM_PROMPT = """You are MedInsight, an expert AI medical diagnostic assistant reviewing a patient's laboratory test results.

Your role:
1. Identify all abnormal values and explain their clinical significance
2. Identify patterns across multiple abnormal values that suggest underlying conditions
3. Use web_search to look up relevant clinical guidelines for flagged values — limit to 1-2 searches total, only for the most clinically significant findings
4. Use lookup_reference_range to verify reference ranges when uncertain
5. Provide clear, evidence-based interpretations and actionable recommendations

GUIDELINES:
- Be thorough but clinically precise
- Group related findings (e.g., multiple CBC abnormalities may suggest one cause)
- Always recommend follow-up with a healthcare provider
- Use plain language with medical terms in parentheses
- Do NOT make definitive diagnoses — say "may suggest" or "is consistent with"

Your response MUST be valid JSON with this exact structure:
{
  "patient_summary": "Brief 2-3 sentence overview",
  "findings": [
    {
      "test": "Test name",
      "value": "Measured value with unit",
      "status": "HIGH/LOW/CRITICAL HIGH/CRITICAL LOW/BORDERLINE",
      "interpretation": "Clinical meaning in plain English",
      "possible_causes": ["cause1", "cause2"],
      "severity": "mild/moderate/severe",
      "recommendation": "Specific action"
    }
  ],
  "patterns_identified": [
    {
      "pattern_name": "Pattern name",
      "tests_involved": ["test1", "test2"],
      "clinical_significance": "Explanation",
      "urgency": "routine/soon/urgent/emergency"
    }
  ],
  "lifestyle_recommendations": ["rec1", "rec2"],
  "follow_up_recommendations": ["action1"],
  "searched_sources": ["source URL or title"],
  "overall_assessment": "Comprehensive 3-5 sentence summary",
  "disclaimer": "This analysis is for informational purposes only and does not constitute medical advice. Always consult a qualified healthcare provider."
}"""


class DiagnosticAgent:
    """Gemini 2.0 Flash diagnostic agent with function calling."""

    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY not set. Get a free key at aistudio.google.com"
            )
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def analyze(
        self,
        ocr_text: str,
        comparison_results: Dict[str, Any],
        patient_info: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        patient_info = patient_info or {}
        user_message = self._build_user_message(ocr_text, comparison_results, patient_info)
        searched_sources: List[str] = []

        contents: List[types.Content] = [
            types.Content(role="user", parts=[types.Part(text=user_message)])
        ]

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=TOOLS,
        )

        try:
            # Capped at 4 rounds (was 10) — reduces worst-case token usage by ~60%
            for _ in range(4):
                response = self.client.models.generate_content(
                    model=MODEL,
                    contents=contents,
                    config=config,
                )

                contents.append(
                    types.Content(role="model", parts=response.candidates[0].content.parts)
                )

                fn_calls = [
                    p for p in response.candidates[0].content.parts
                    if p.function_call is not None
                ]

                if not fn_calls:
                    final_text = "".join(
                        p.text for p in response.candidates[0].content.parts
                        if hasattr(p, "text") and p.text
                    )
                    return self._parse_response(final_text, searched_sources)

                fn_response_parts = []
                for part in fn_calls:
                    fc = part.function_call
                    result, sources = self._execute_function(fc.name, dict(fc.args))
                    searched_sources.extend(sources)
                    fn_response_parts.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=fc.name,
                                response={"result": result},
                            )
                        )
                    )

                contents.append(
                    types.Content(role="user", parts=fn_response_parts)
                )

            return self._error_response("Agent did not complete within iteration limit")

        except Exception as e:
            logger.exception("Gemini diagnostic agent failed")
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                msg = (
                    "API Rate Limit Exceeded (429 Resource Exhausted): "
                    "You have hit the Gemini Free Tier rate limit (15 requests per minute). "
                    "Since our AI agent performs multiple database and clinical web search iterations to generate a premium diagnostic report, "
                    "it is very easy to exceed this rate limit window.\n\n"
                    "Please wait 30–60 seconds and try again. Alternatively, switch to a Pay-As-You-Go plan in Google AI Studio to lift this limit completely."
                )
                return self._error_response(msg)
            return self._error_response(str(e))

    # ─────────────────────────────────────────────
    # Function Execution
    # ─────────────────────────────────────────────

    def _execute_function(self, name: str, args: Dict):
        try:
            if name == "web_search":
                return self._web_search(args.get("query", ""), int(args.get("max_results", 3)))
            elif name == "lookup_reference_range":
                return self._lookup_reference(args.get("test_name", "")), []
            return f"Unknown function: {name}", []
        except Exception as e:
            return f"Function error: {str(e)}", []

    def _web_search(self, query: str, max_results: int = 3):
        if not TAVILY_API_KEY:
            return "Web search unavailable (no Tavily API key configured).", []
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=TAVILY_API_KEY)
            response = client.search(query=query, max_results=max_results, search_depth="advanced")
            results_text = f"Search results for '{query}':\n\n"
            sources = []
            for r in response.get("results", []):
                # Cap each result body at 400 chars (was uncapped — saves ~300-600 tokens/search)
                content_snippet = (r.get("content") or "")[:400]
                results_text += f"**{r.get('title', '')}**\n{content_snippet}\n\n"
                if r.get("url"):
                    sources.append(f"{r.get('title', '')} — {r.get('url', '')}")
            return results_text.strip(), sources
        except Exception as e:
            return f"Web search failed: {str(e)}", []

    @staticmethod
    def _lookup_reference(test_name: str) -> str:
        from pathlib import Path
        ref_path = Path(__file__).parent.parent / "data" / "reference_ranges.json"
        with open(ref_path) as f:
            ranges = json.load(f)
        test_lower = test_name.lower().strip()
        for category, tests in ranges.items():
            for name, data in tests.items():
                if (name.lower() == test_lower
                        or data.get("full_name", "").lower() == test_lower
                        or test_lower in name.lower()):
                    return json.dumps({"test": name, "category": category, **data}, indent=2)
        return f"Reference range not found for: {test_name}"

    # ─────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────

    @staticmethod
    def _build_user_message(ocr_text: str, comparison_results: Dict, patient_info: Dict) -> str:
        patient_str = ""
        if patient_info:
            parts = [f"{k.title()}: {v}" for k, v in patient_info.items() if v]
            if parts:
                patient_str = "**Patient:** " + " | ".join(parts) + "\n\n"

        summary = comparison_results.get("summary", {})

        # Only include actionable abnormals (exclude BORDERLINE) to reduce prompt size
        abnormal_only = [
            r for r in comparison_results.get("results", [])
            if r.get("status", "NORMAL") not in ("NORMAL", "BORDERLINE")
        ]
        abnormal_str = ""
        if abnormal_only:
            abnormal_str = "\n**Flagged Values:**\n"
            for r in abnormal_only:
                abnormal_str += (
                    f"- {r['full_name']}: {r['value']} {r['unit']} "
                    f"[{r['status']}] (ref: {r['ref_min']}-{r['ref_max']})\n"
                )

        return (
            f"{patient_str}"
            # OCR text capped at 1,500 chars (was 3,000) — abnormals list above gives
            # the model the key data; raw text is a fallback for context only
            f"**Lab Report (OCR Extracted):**\n```\n{ocr_text[:1500]}\n```\n\n"
            f"{abnormal_str}\n"
            f"**Severity Score:** {summary.get('severity_score', 'N/A')}/100 "
            f"- {summary.get('overall_status', 'Unknown')}\n\n"
            "Analyze this lab report thoroughly. Use web_search only for the most significant "
            "abnormal findings (1-2 searches max). Return your analysis as the specified JSON format."
        )

    @staticmethod
    def _parse_response(text: str, sources: List[str]) -> Dict[str, Any]:
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        json_str = json_match.group(1) if json_match else text.strip()
        start = json_str.find("{")
        end = json_str.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = json_str[start:end]
        try:
            parsed = json.loads(json_str)
            if sources:
                parsed.setdefault("searched_sources", []).extend(sources)
            return parsed
        except json.JSONDecodeError:
            return {
                "patient_summary": "Analysis completed.",
                "findings": [], "patterns_identified": [],
                "lifestyle_recommendations": [], "follow_up_recommendations": [],
                "searched_sources": sources, "overall_assessment": text[:1500],
                "disclaimer": "For informational purposes only.",
            }

    @staticmethod
    def _error_response(message: str) -> Dict[str, Any]:
        return {
            "patient_summary": "Analysis failed.",
            "findings": [], "patterns_identified": [],
            "lifestyle_recommendations": [], "follow_up_recommendations": [],
            "searched_sources": [], "overall_assessment": message,
            "disclaimer": "For informational purposes only.",
        }