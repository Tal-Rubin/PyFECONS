"""Shared fixtures for PyFECONS tests.

For standalone helper functions (load_mfe_inputs, load_ife_inputs),
see helpers.py.
"""

import pytest
from helpers import _load_customer_inputs

# ---------------------------------------------------------------------------
# Session-scoped fixtures (immutable, shared across all tests in a session)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def mfe_inputs():
    """CATF MFE inputs (session-scoped, do not mutate)."""
    return _load_customer_inputs("mfe")


@pytest.fixture(scope="session")
def ife_inputs():
    """CATF IFE inputs (session-scoped, do not mutate)."""
    return _load_customer_inputs("ife")
