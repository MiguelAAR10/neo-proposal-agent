from __future__ import annotations


class BackendDomainError(Exception):
    """Base error for controlled backend failures."""

    status_code: int = 500
    code: str = "BACKEND_ERROR"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ValidationDomainError(BackendDomainError):
    status_code = 400
    code = "VALIDATION_ERROR"


class SessionNotFoundError(BackendDomainError):
    status_code = 404
    code = "SESSION_NOT_FOUND"


class BusinessRuleError(BackendDomainError):
    status_code = 400
    code = "BUSINESS_RULE_ERROR"


class ExternalDependencyTimeout(BackendDomainError):
    status_code = 504
    code = "EXTERNAL_TIMEOUT"

    def __init__(self, dependency: str, timeout_seconds: float):
        super().__init__(f"{dependency} timeout > {timeout_seconds}s")
        self.dependency = dependency
        self.timeout_seconds = timeout_seconds


class InsightParseError(BackendDomainError):
    status_code = 422
    code = "INSIGHT_PARSE_FAILED"


class IntelStorageError(BackendDomainError):
    status_code = 500
    code = "INTEL_STORAGE_ERROR"


class RadarToolTimeoutError(BackendDomainError):
    status_code = 504
    code = "RADAR_TOOL_TIMEOUT"


class RadarToolUnavailableError(BackendDomainError):
    status_code = 503
    code = "RADAR_TOOL_UNAVAILABLE"


class RadarTriggerParseError(BackendDomainError):
    status_code = 422
    code = "RADAR_TRIGGER_PARSE_FAILED"


class RadarStorageError(BackendDomainError):
    status_code = 500
    code = "RADAR_STORAGE_ERROR"
