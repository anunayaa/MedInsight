"""
Medical Chat Engine — Interactive chatbot for discussing lab reports.

Uses Gemini 2.0 Flash with function calling (web_search, lookup_reference_range)
to answer medical queries in the context of analyzed lab reports.
Supports multi-turn conversation memory.
"""

import os
import json
import re
import logging
from typing import Dict, Any, List, Optional, Tuple

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
MODEL = "gemini-2.0-flash"

# ─────────────────────────────────────────────
# Groq Tool / Function Declarations & Conversion Helper
# ─────────────────────────────────────────────

GROQ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web for clinical guidelines, medical literature, "
                "normal reference ranges, drug interactions, or any medical information "
                "needed to answer the user's health question."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Medical search query",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results (1-5)",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_reference_range",
            "description": "Look up the clinical reference range for a specific lab test from the local database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "test_name": {
                        "type": "string",
                        "description": "Lab test name (e.g., 'Hemoglobin', 'TSH', 'LDL')",
                    },
                },
                "required": ["test_name"],
            },
        },
    }
]


def _convert_gemini_to_groq(contents_list: List, system_prompt: str) -> List[Dict]:
    groq_messages = [{"role": "system", "content": system_prompt}]
    call_id_map = {}
    
    for content in contents_list:
        role = "assistant" if content.role == "model" else "user"
        text_content = ""
        tool_calls = []
        is_tool_response = False
        tool_responses = []
        
        for part in content.parts:
            if hasattr(part, "text") and part.text:
                text_content += part.text
            elif hasattr(part, "function_call") and part.function_call:
                fc = part.function_call
                call_id = f"call_{fc.name}_{len(call_id_map)}"
                call_id_map[fc.name] = call_id
                tool_calls.append({
                    "id": call_id,
                    "type": "function",
                    "function": {
                        "name": fc.name,
                        "arguments": json.dumps(fc.args)
                    }
                })
            elif hasattr(part, "function_response") and part.function_response:
                fr = part.function_response
                is_tool_response = True
                call_id = call_id_map.get(fr.name, f"call_{fr.name}_default")
                tool_responses.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": fr.name,
                    "content": json.dumps(fr.response)
                })
                
        if is_tool_response:
            for tr in tool_responses:
                groq_messages.append(tr)
        else:
            msg = {"role": role}
            if text_content:
                msg["content"] = text_content
            if tool_calls:
                msg["tool_calls"] = tool_calls
            groq_messages.append(msg)
            
    return groq_messages

# ─────────────────────────────────────────────
# Tool / Function Declarations (shared with diagnostic_agent)
# ─────────────────────────────────────────────

CHAT_TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="web_search",
                description=(
                    "Search the web for clinical guidelines, medical literature, "
                    "normal reference ranges, drug interactions, or any medical information "
                    "needed to answer the user's health question."
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
                    required=["test_name"],  # fixed: was "query"
                ),
            ),
        ]
    )
]


def _build_system_prompt(report_context: Optional[Dict] = None) -> str:
    """Build system prompt with optional report context injected.

    Token-efficiency rules applied here:
    - ocr_text is NOT included (redundant with AI assessment; saves ~500-2000 tokens/msg)
    - Only non-borderline abnormals are listed (skips noise)
    - AI assessment capped at 300 chars (was 500)
    """
    base = """You are MedInsight Chat, a friendly and knowledgeable AI medical assistant.

Your role:
- Answer the user's health and medical questions clearly and accurately
- If a lab report has been analyzed, reference the specific results to give personalized context
- Use web_search to look up clinical guidelines, drug interactions, or medical information when needed
- Use lookup_reference_range to check reference ranges for specific lab tests
- Be empathetic, thorough, and clear — use plain language with medical terms in parentheses
- Always recommend consulting a healthcare provider for definitive medical advice
- Never make definitive diagnoses — say "may suggest" or "is consistent with"

IMPORTANT:
- Keep responses concise but informative (2-4 paragraphs max unless the user asks for detail)
- Use markdown formatting: **bold** for emphasis, bullet points for lists
- If no lab report context is available, you can still answer general medical questions
- Reference specific test values from the report when relevant to the question

DISCLAIMER: Always remind users that your responses are informational and not a substitute for professional medical advice when discussing specific health concerns."""

    if report_context:
        context_parts = []

        # Patient info
        patient = report_context.get("patient_info", {})
        if patient:
            parts = [f"{k.title()}: {v}" for k, v in patient.items() if v]
            if parts:
                context_parts.append(f"**Patient:** {' | '.join(parts)}")

        # Report summary
        comparison = report_context.get("comparison_results", {})
        summary = comparison.get("summary", {})
        if summary:
            context_parts.append(
                f"**Report Summary:** {summary.get('total_tests', 0)} tests analyzed, "
                f"{summary.get('abnormal_count', 0)} abnormal, "
                f"severity score {summary.get('severity_score', 0)}/100 "
                f"({summary.get('overall_status', 'Unknown')})"
            )

        # Only actionable abnormals (exclude NORMAL and BORDERLINE to cut tokens)
        results = comparison.get("results", [])
        abnormal = [
            r for r in results
            if r.get("status", "NORMAL") not in ("NORMAL", "BORDERLINE")
        ]
        if abnormal:
            abnormal_lines = []
            for r in abnormal:
                abnormal_lines.append(
                    f"- {r.get('full_name', r.get('name', ''))}: {r.get('value', '')} {r.get('unit', '')} "
                    f"[{r.get('status', '')}] (ref: {r.get('ref_min', '–')}–{r.get('ref_max', '–')})"
                )
            context_parts.append("**Flagged Values:**\n" + "\n".join(abnormal_lines))

        # AI assessment — capped at 300 chars (was 500)
        ai_findings = report_context.get("ai_findings", {})
        if ai_findings.get("overall_assessment"):
            context_parts.append(
                f"**AI Assessment:** {ai_findings['overall_assessment'][:300]}"
            )

        # ocr_text intentionally excluded — saves ~500-2000 tokens per message

        if context_parts:
            base += "\n\n--- CURRENT LAB REPORT CONTEXT ---\n\n" + "\n\n".join(context_parts)

    return base


class MedicalChatEngine:
    """Interactive medical chatbot using Gemini 2.0 Flash with function calling."""

    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY not set. Get a free key at aistudio.google.com"
            )
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def chat(
        self,
        user_message: str,
        report_context: Optional[Dict] = None,
        chat_history: Optional[List] = None,
    ) -> Tuple[str, List]:
        chat_history = chat_history or []

        system_prompt = _build_system_prompt(report_context)

        user_content = types.Content(
            role="user", parts=[types.Part(text=user_message)]
        )
        contents = chat_history + [user_content]

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=CHAT_TOOLS,
        )

        try:
            # Capped at 3 rounds (was 6)
            for _ in range(3):
                response = self.client.models.generate_content(
                    model=MODEL,
                    contents=contents,
                    config=config,
                )

                model_content = types.Content(
                    role="model", parts=response.candidates[0].content.parts
                )
                contents.append(model_content)

                fn_calls = [
                    p for p in response.candidates[0].content.parts
                    if p.function_call is not None
                ]

                if not fn_calls:
                    final_text = "".join(
                        p.text for p in response.candidates[0].content.parts
                        if hasattr(p, "text") and p.text
                    )
                    # Keep last 20 items (10 turns) — was 40
                    trimmed = contents[-20:] if len(contents) > 20 else contents
                    return final_text, trimmed

                fn_response_parts = []
                for part in fn_calls:
                    fc = part.function_call
                    result = self._execute_function(fc.name, dict(fc.args))
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

            return "I'm sorry, I couldn't complete my analysis. Please try rephrasing your question.", contents

        except Exception as e:
            logger.exception("Chat engine error")
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                groq_key = os.getenv("GROQ_API_KEY", "")
                if groq_key:
                    logger.warning("Gemini rate limit exceeded. Failing over to Groq...")
                    try:
                        return self._chat_with_groq(
                            user_message=user_message,
                            system_prompt=system_prompt,
                            chat_history=chat_history,
                        )
                    except Exception as groq_err:
                        logger.exception("Groq fallback failed")
                        return (
                            f"⚠️ **Rate Limit Exceeded & Fallback Failed**:\n\n"
                            f"Gemini API rate limit was hit, and the Groq fallback failed with error: {str(groq_err)}",
                            chat_history
                        )

                user_msg = (
                    "⚠️ **API Rate Limit Exceeded (429 Resource Exhausted)**:\n\n"
                    "You have hit the Google Gemini Free Tier rate limit (15 requests per minute).\n\n"
                    "Because MedInsight uses **Function Calling** (such as looking up medical databases and searching the web) "
                    "to provide precise, context-aware answers, a single user message can trigger multiple API requests in rapid succession under the hood.\n\n"
                    "**Please wait 30–60 seconds and try again.**\n\n"
                    "*Tip: To lift this rate limit completely, you can enable Pay-As-You-Go billing in your Google AI Studio dashboard, or add a `GROQ_API_KEY` to your `.env` file to instantly use Groq's high-limit free tier!*"
                )
                return user_msg, chat_history
            return f"I encountered an error: {str(e)}. Please try again.", chat_history

    def _chat_with_groq(
        self,
        user_message: str,
        system_prompt: str,
        chat_history: List,
    ) -> Tuple[str, List]:
        """Fallback chat implementation using Groq's Llama 3.3 model."""
        groq_key = os.getenv("GROQ_API_KEY", "")
        if not groq_key:
            raise ValueError("GROQ_API_KEY not configured in environment.")

        from groq import Groq
        groq_client = Groq(api_key=groq_key)

        user_content = types.Content(
            role="user", parts=[types.Part(text=user_message)]
        )
        gemini_contents = chat_history + [user_content]

        messages = _convert_gemini_to_groq(gemini_contents, system_prompt)

        try:
            # Capped at 3 rounds (was 6)
            for _ in range(3):
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    tools=GROQ_TOOLS,
                    tool_choice="auto",
                )

                response_message = response.choices[0].message
                messages.append(response_message)

                gemini_parts = []
                if response_message.content:
                    gemini_parts.append(types.Part(text=response_message.content))

                if response_message.tool_calls:
                    for tc in response_message.tool_calls:
                        gemini_parts.append(
                            types.Part(
                                function_call=types.FunctionCall(
                                    name=tc.function.name,
                                    args=json.loads(tc.function.arguments),
                                )
                            )
                        )

                gemini_contents.append(
                    types.Content(role="model", parts=gemini_parts)
                )

                if not response_message.tool_calls:
                    final_text = response_message.content or ""
                    trimmed = gemini_contents[-20:] if len(gemini_contents) > 20 else gemini_contents
                    return final_text, trimmed

                tool_responses_gemini_parts = []
                for tc in response_message.tool_calls:
                    result = self._execute_function(tc.function.name, json.loads(tc.function.arguments))
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tc.function.name,
                        "content": json.dumps({"result": result}),
                    })
                    tool_responses_gemini_parts.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=tc.function.name,
                                response={"result": result},
                            )
                        )
                    )

                gemini_contents.append(
                    types.Content(role="user", parts=tool_responses_gemini_parts)
                )

            return "I'm sorry, I couldn't complete my analysis using Groq. Please try rephrasing your question.", gemini_contents

        except Exception as e:
            logger.exception("Groq failover error")
            raise e

    # ─────────────────────────────────────────────
    # Function Execution
    # ─────────────────────────────────────────────

    def _execute_function(self, name: str, args: Dict) -> str:
        try:
            if name == "web_search":
                return self._web_search(args.get("query", ""), int(args.get("max_results", 3)))
            elif name == "lookup_reference_range":
                return self._lookup_reference(args.get("test_name", ""))
            return f"Unknown function: {name}"
        except Exception as e:
            return f"Function error: {str(e)}"

    def _web_search(self, query: str, max_results: int = 3) -> str:
        if not TAVILY_API_KEY:
            return "Web search unavailable (no Tavily API key configured)."
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=TAVILY_API_KEY)
            response = client.search(query=query, max_results=max_results, search_depth="advanced")
            results_text = f"Search results for '{query}':\n\n"
            for r in response.get("results", []):
                # Cap each result body at 400 chars
                content_snippet = (r.get("content") or "")[:400]
                results_text += f"**{r.get('title', '')}**\n{content_snippet}\n\n"
            return results_text.strip()
        except Exception as e:
            return f"Web search failed: {str(e)}"

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