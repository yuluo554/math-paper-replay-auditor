"""__init__.py for core module."""

from auditor.core.types import (
    Verdict,
    ClaimType,
    PaperStructure,
    ClaimResult,
    AuditResult,
)
from auditor.core.numerical_tolerance import NUMERICAL_TOLERANCE, tolerance_note

__all__ = [
    "Verdict",
    "ClaimType",
    "PaperStructure",
    "ClaimResult",
    "AuditResult",
    "NUMERICAL_TOLERANCE",
    "tolerance_note",
]
