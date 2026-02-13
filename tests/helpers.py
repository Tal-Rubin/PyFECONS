"""Shared helpers for PyFECONS tests.

Standalone functions that can be imported by any test module.
For pytest fixtures, see conftest.py.
"""

import importlib
import os
import sys

from pyfecons.inputs.all_inputs import AllInputs


def _load_customer_inputs(reactor_type: str) -> AllInputs:
    """Load customer inputs from DefineInputs.py for the given reactor type."""
    customer_dir = os.path.join(
        os.path.dirname(__file__), "..", "customers", "CATF", reactor_type
    )
    customer_dir = os.path.abspath(customer_dir)
    sys.path.insert(0, customer_dir)
    try:
        if "DefineInputs" in sys.modules:
            importlib.reload(sys.modules["DefineInputs"])
        else:
            import DefineInputs
        return DefineInputs.Generate()
    finally:
        if customer_dir in sys.path:
            sys.path.remove(customer_dir)
        if "DefineInputs" in sys.modules:
            del sys.modules["DefineInputs"]


def load_mfe_inputs() -> AllInputs:
    """Load fresh CATF MFE inputs (call each time you need a mutable copy)."""
    return _load_customer_inputs("mfe")


def load_ife_inputs() -> AllInputs:
    """Load fresh CATF IFE inputs (call each time you need a mutable copy)."""
    return _load_customer_inputs("ife")
