"""Unit tests for lcoe.lcoe_costs().

Tests verify the LCOE formula: (annualized CAPEX + levelized OPEX + fuel) /
annual energy production, with synthetic inputs where the math is trivial.
"""

import pytest

from pyfecons.costing.accounting.power_table import PowerTable
from pyfecons.costing.calculations.lcoe import lcoe_costs
from pyfecons.costing.categories.cas700000 import CAS70
from pyfecons.costing.categories.cas800000 import CAS80
from pyfecons.costing.categories.cas900000 import CAS90
from pyfecons.inputs.basic import Basic
from pyfecons.units import M_USD, MW, Count, Percent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_lcoe(
    p_net=1000, n_mod=1, availability=0.85, c900000=500, c700000=50, c800000=10
):
    """Build minimal objects and compute LCOE."""
    basic = Basic(n_mod=Count(n_mod), plant_availability=Percent(availability))
    pt = PowerTable(p_net=MW(p_net))
    cas90 = CAS90(C900000=M_USD(c900000))
    cas70 = CAS70(C700000=M_USD(c700000))
    cas80 = CAS80(C800000=M_USD(c800000))
    return lcoe_costs(basic, pt, cas70, cas80, cas90)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestLCOE:
    def test_known_inputs(self):
        """LCOE = (C90 + C70 + C80) * 1e6 / (8760 * p_net * n_mod * avail)."""
        lcoe = _run_lcoe()
        annual_mwh = 8760 * 1000 * 1 * 0.85
        expected = (500e6 + 50e6 + 10e6) / annual_mwh
        assert float(lcoe.C1000000) == pytest.approx(expected, rel=1e-6)

    def test_c2000000_is_tenth(self):
        """C2000000 = C1000000 / 10."""
        lcoe = _run_lcoe()
        assert float(lcoe.C2000000) == pytest.approx(
            float(lcoe.C1000000) / 10, rel=1e-10
        )

    def test_multi_module(self):
        """n_mod=4: annual energy 4x, LCOE 1/4."""
        lcoe_1 = _run_lcoe(n_mod=1)
        lcoe_4 = _run_lcoe(n_mod=4)
        assert float(lcoe_4.C1000000) == pytest.approx(
            float(lcoe_1.C1000000) / 4, rel=1e-10
        )

    def test_higher_availability_lower_lcoe(self):
        lcoe_low = _run_lcoe(availability=0.7)
        lcoe_high = _run_lcoe(availability=0.9)
        assert float(lcoe_high.C1000000) < float(lcoe_low.C1000000)

    def test_availability_scaling(self):
        """LCOE is inversely proportional to availability."""
        lcoe_70 = _run_lcoe(availability=0.7)
        lcoe_85 = _run_lcoe(availability=0.85)
        ratio = float(lcoe_70.C1000000) / float(lcoe_85.C1000000)
        assert ratio == pytest.approx(0.85 / 0.7, rel=1e-6)

    def test_higher_p_net_lower_lcoe(self):
        lcoe_500 = _run_lcoe(p_net=500)
        lcoe_1000 = _run_lcoe(p_net=1000)
        assert float(lcoe_1000.C1000000) < float(lcoe_500.C1000000)

    def test_cas_component_contributions(self):
        """Each CAS component contributes proportionally to LCOE numerator."""
        annual_mwh = 8760 * 1000 * 1 * 0.85
        lcoe = _run_lcoe(c900000=500, c700000=50, c800000=10)
        capex_contrib = 500e6 / annual_mwh
        om_contrib = 50e6 / annual_mwh
        fuel_contrib = 10e6 / annual_mwh
        assert float(lcoe.C1000000) == pytest.approx(
            capex_contrib + om_contrib + fuel_contrib, rel=1e-6
        )

    def test_lcoe_positive(self):
        lcoe = _run_lcoe()
        assert float(lcoe.C1000000) > 0
        assert float(lcoe.C2000000) > 0
