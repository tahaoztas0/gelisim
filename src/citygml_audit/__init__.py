"""Lightweight CityGML structural and geometry auditing."""
from .validator import audit_file, audit_text

__all__ = ["audit_file", "audit_text"]
__version__ = "0.1.0"
