"""Domain exceptions: raised by services, translated to HTTP responses only in the API layer."""


class AppError(Exception):
    """Base class for expected business errors; `code` is a stable machine-readable identifier."""

    code = "app_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    code = "not_found"

    def __init__(self, entity: str, entity_id: int) -> None:
        super().__init__(f"{entity} з id={entity_id} не знайдено")


class ConflictError(AppError):
    """The operation contradicts the current data: a duplicate value or an entity still in use."""

    code = "conflict"


class BusinessRuleError(AppError):
    """The request is well-formed but breaks a business rule."""

    code = "business_rule_violation"
