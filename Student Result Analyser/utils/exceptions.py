"""Application-specific exception hierarchy."""


class ValidationError(Exception):
    """Raised when user-supplied input fails any validation rule."""


class DuplicateRollError(Exception):
    """Raised when a student with the same roll number already exists."""


class StudentNotFoundError(Exception):
    """Raised when a student with the given roll number cannot be found."""


class NoStudentsError(Exception):
    """Raised when a statistics operation is requested with no students."""


class NoSubjectsError(Exception):
    """Raised when a student is added before subjects have been configured."""
