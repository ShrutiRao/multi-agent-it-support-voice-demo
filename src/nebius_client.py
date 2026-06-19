from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib import error, request


@dataclass
class NebiusResult:
    text: str
    data: dict[str, Any] | None = None


class NebiusClient:
    """
    Minimal OpenAI-compatible Nebius helper.

    The client is optional. If no API key or model is configured, callers should
    fall back to deterministic local logic.
    """

    def __init__(self) -> None:
        self.api_key = os.environ.get("NEBIUS_API_KEY", "").strip()
        self.model = os.environ.get("NEBIUS_MODEL", "").strip()
        self.base_url = os.environ.get(
            "NEBIUS_BASE_URL",
            "https://api.tokenfactory.nebius.com/v1",
        ).rstrip("/")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.model)

    def suggest_route(self, transcript_text: str, fallback: str) -> str:
        result = self._chat_json(
            system_prompt=(
                "You classify IT support calls into one category only. "
                "Return JSON with a single key named issue_category."
            ),
            user_prompt=(
                f"Classify this support request into one of: vpn, mfa, password_reset, email, billing, unknown.\n"
                f"Transcript:\n{transcript_text}\n\n"
                f"Fallback category: {fallback}"
            ),
        )
        category = self._extract_category(result.data or {}, fallback)
        return category

    def summarize_transcript(self, transcript_text: str, fallback: str) -> str:
        result = self._chat_json(
            system_prompt=(
                "Summarize employee support calls for a helpdesk review panel. "
                "Return JSON with summary and bullets."
            ),
            user_prompt=(
                f"Write a concise summary of this support call.\n\nTranscript:\n{transcript_text}\n\n"
                f"Fallback summary: {fallback}"
            ),
        )
        data = result.data or {}
        summary = str(data.get("summary") or result.text or fallback).strip()
        bullets = data.get("bullets")
        if isinstance(bullets, list) and bullets:
            summary = summary + "\n" + "\n".join(f"- {str(item).strip()}" for item in bullets if str(item).strip())
        return summary

    def review_call(self, transcript_text: str, state: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
        result = self._chat_json(
            system_prompt=(
                "You are a QA reviewer for employee IT support calls. "
                "Return JSON with keys: resolved, verified, correct_process_followed, "
                "follow_up_required, qa_notes (array of strings), summary."
            ),
            user_prompt=(
                "Review this support call and output a structured QA assessment.\n\n"
                f"Transcript:\n{transcript_text}\n\n"
                f"Final state:\n{json.dumps(state, ensure_ascii=True)}\n\n"
                f"Fallback review:\n{json.dumps(fallback, ensure_ascii=True)}"
            ),
        )
        data = result.data or {}
        review = dict(fallback)
        review.update(
            {
                "resolved": bool(data.get("resolved", review.get("resolved"))),
                "employee_verified": bool(data.get("verified", review.get("employee_verified"))),
                "correct_process_followed": bool(
                    data.get("correct_process_followed", review.get("correct_process_followed"))
                ),
                "follow_up_required": bool(data.get("follow_up_required", review.get("follow_up_required"))),
                "qa_notes": self._ensure_list(data.get("qa_notes")) or review.get("qa_notes", []),
                "summary": str(data.get("summary") or review.get("summary") or "").strip(),
            }
        )
        return review

    def draft_escalation(self, transcript_text: str, state: dict[str, Any], fallback: str) -> str:
        result = self._chat_json(
            system_prompt=(
                "You draft escalation notes for IT helpdesk tickets. "
                "Return JSON with one key named ticket_summary."
            ),
            user_prompt=(
                "Draft a concise escalation summary for the ticket.\n\n"
                f"Transcript:\n{transcript_text}\n\n"
                f"State:\n{json.dumps(state, ensure_ascii=True)}\n\n"
                f"Fallback summary: {fallback}"
            ),
        )
        data = result.data or {}
        return str(data.get("ticket_summary") or result.text or fallback).strip()

    def _chat_json(self, system_prompt: str, user_prompt: str) -> NebiusResult:
        if not self.enabled:
            return NebiusResult(text="", data=None)

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8")
        except error.URLError:
            return NebiusResult(text="", data=None)

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return NebiusResult(text=raw, data=None)

        content = (
            parsed.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        return NebiusResult(text=str(content), data=self._parse_json_like(str(content)))

    @staticmethod
    def _parse_json_like(text: str) -> dict[str, Any] | None:
        stripped = text.strip()
        if not stripped:
            return None
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass
        match = re.search(r"\{.*\}", stripped, re.S)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _extract_category(data: dict[str, Any], fallback: str) -> str:
        candidate = str(data.get("issue_category") or data.get("category") or fallback).strip().lower()
        if candidate in {"vpn", "mfa", "password_reset", "email", "billing"}:
            return candidate
        return fallback

    @staticmethod
    def _ensure_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []
