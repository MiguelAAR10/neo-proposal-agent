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

