import pyfecons


class TemplateException(Exception):
    """General template exception."""

    def __init__(self, message):
        self.message = message
        # pyfecons.logger.error(message) # if logger added
        super().__init__(self.message)


class FieldError:
    """A single field-level validation failure."""

    def __init__(self, dataclass_name: str, field_name: str, value, constraint: str):
        self.dataclass_name = dataclass_name
        self.field_name = field_name
        self.value = value
        self.constraint = constraint

    def __str__(self):
        return (
            f"{self.dataclass_name}.{self.field_name} = {self.value!r} "
            f"-- expected: {self.constraint}"
        )


class ValidationWarning:
    """A non-fatal validation concern."""

    def __init__(self, dataclass_name: str, field_name: str, value, message: str):
        self.dataclass_name = dataclass_name
        self.field_name = field_name
        self.value = value
        self.message = message

    def __str__(self):
        return (
            f"WARNING: {self.dataclass_name}.{self.field_name} = {self.value!r} "
            f"-- {self.message}"
        )


class ValidationError(Exception):
    """Raised when input validation fails with unrecoverable errors."""

    def __init__(self, errors: list[FieldError]):
        self.errors = errors
        msg = f"{len(errors)} validation error(s):\n"
        msg += "\n".join(f"  - {e}" for e in errors)
        super().__init__(msg)
