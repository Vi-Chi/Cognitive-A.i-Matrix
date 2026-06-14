"""A.i Core P0 reality loop.

This package is the reconciled local core: it uses the existing MΣBUS package
and the existing Urbi bridge instead of carrying a parallel bus schema.
"""
from ._paths import ensure_dependency_paths

ensure_dependency_paths()

__all__ = ["ensure_dependency_paths"]
