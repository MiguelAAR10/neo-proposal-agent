"""
Compatibility ASGI entrypoint.

Some local scripts still run:
  uvicorn src.main:app

The canonical app module lives in:
  src.api.main:app
"""

from src.api.main import app

__all__ = ["app"]

