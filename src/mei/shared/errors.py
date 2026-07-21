class MeiError(Exception):
    """Base class for all application-raised errors.

    `problem_type` and `status_code` map directly onto an RFC 9457
    problem-details response so every domain error renders consistently
    at the API boundary.
    """

    problem_type: str = "about:blank"
    status_code: int = 500
    title: str = "Internal Server Error"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.title
        super().__init__(self.detail)


class NotFoundError(MeiError):
    problem_type = "https://mei.dev/errors/not-found"
    status_code = 404
    title = "Resource Not Found"


class ValidationError(MeiError):
    problem_type = "https://mei.dev/errors/validation"
    status_code = 422
    title = "Validation Failed"


class ConflictError(MeiError):
    problem_type = "https://mei.dev/errors/conflict"
    status_code = 409
    title = "Conflict"


class UnauthorizedError(MeiError):
    problem_type = "https://mei.dev/errors/unauthorized"
    status_code = 401
    title = "Unauthorized"


class ForbiddenError(MeiError):
    problem_type = "https://mei.dev/errors/forbidden"
    status_code = 403
    title = "Forbidden"


class UnsupportedURLError(MeiError):
    """Raised when the collector rejects a URL on security grounds (SSRF policy)."""

    problem_type = "https://mei.dev/errors/unsupported-url"
    status_code = 422
    title = "Unsupported URL"


class FetchError(MeiError):
    """Raised when a source URL cannot be retrieved or archived."""

    problem_type = "https://mei.dev/errors/fetch-failed"
    status_code = 502
    title = "Fetch Failed"


class LLMConfigurationError(MeiError):
    """Raised when a real LLM adapter is invoked without the required provider config."""

    problem_type = "https://mei.dev/errors/llm-configuration"
    status_code = 500
    title = "LLM Not Configured"


class LLMOutputError(MeiError):
    """Raised when an LLM's structured output fails to validate after retries."""

    problem_type = "https://mei.dev/errors/llm-output"
    status_code = 502
    title = "LLM Output Invalid"
