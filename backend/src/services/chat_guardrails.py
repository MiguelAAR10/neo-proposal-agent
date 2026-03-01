from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class GuardrailResult:
    allowed: bool
    code: str
    reason: str
    sanitized_message: str


_MAX_CHAT_MESSAGE_LEN = 700
_MIN_CHAT_MESSAGE_LEN = 2

_BLOCK_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"(?i)\b(ignore|ignora)\b.{0,40}\b(instruction|instruccion|prompt|regla)\b", "PROMPT_INJECTION"),
    (r"(?i)\b(api[_ -]?key|token|password|contrase(?:n|ñ)a|secret)\b", "SENSITIVE_DATA_REQUEST"),
    (r"(?i)\b(rm\s+-rf|drop\s+table|truncate\s+table|delete\s+from)\b", "DESTRUCTIVE_INTENT"),
)


def evaluate_chat_message(message: str) -> GuardrailResult:
    sanitized = " ".join((message or "").strip().split())
    if len(sanitized) < _MIN_CHAT_MESSAGE_LEN:
        return GuardrailResult(
            allowed=False,
            code="EMPTY_OR_TOO_SHORT",
            reason="Mensaje vacio o demasiado corto.",
            sanitized_message=sanitized,
        )
    if len(sanitized) > _MAX_CHAT_MESSAGE_LEN:
        return GuardrailResult(
            allowed=False,
            code="TOO_LONG",
            reason=f"Mensaje excede {_MAX_CHAT_MESSAGE_LEN} caracteres.",
            sanitized_message=sanitized[:_MAX_CHAT_MESSAGE_LEN],
        )

    for pattern, code in _BLOCK_PATTERNS:
        if re.search(pattern, sanitized):
            return GuardrailResult(
                allowed=False,
                code=code,
                reason="Mensaje bloqueado por policy de seguridad conversacional.",
                sanitized_message=sanitized,
            )

    return GuardrailResult(
        allowed=True,
        code="ALLOWED",
        reason="OK",
        sanitized_message=sanitized,
    )
