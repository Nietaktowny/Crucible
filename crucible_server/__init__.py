"""
FastAPI server exposing Crucible workflows over HTTP.

This package wraps the `crucible` engine and `crucible_workspace` storage
layer behind a REST API so that user interfaces (such as `crucible_gui`) can
list, edit, run and inspect workflows without embedding the Python engine
directly.
"""

__version__ = "0.1.0"
