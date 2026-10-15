class GeneratorError(Exception):
    """Base exception for Generator-related issues."""


class SpecNotFoundError(GeneratorError):
    """Raised when the specification file does not exist."""


class SpecFormatError(GeneratorError):
    """Raised when the YAML is malformed or invalid."""
