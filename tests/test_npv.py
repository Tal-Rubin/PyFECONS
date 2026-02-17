"""Tests for NPV (Net Present Value) calculation."""

import pytest

from pyfecons.costing.accounting.power_table import PowerTable
from pyfecons.costing.calculations.npv import calculate_npv
from pyfecons.costing.categories.cas100000 import CAS10
from pyfecons.costing.categories.cas220119 import CAS220119
from pyfecons.costing.categories.cas700000 import CAS70
from pyfecons.costing.categories.cas800000 import CAS80
from pyfecons.costing.categories.cas900000 import CAS90
from pyfecons.costing_data import CostingData
from pyfecons.enums import FusionMachineType
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.npv_Input import NpvInput


def _make_basic(plant_lifetime=30, plant_availability=0.85):
    b = Basic()
    b.plant_lifetime = plant_lifetime
    b.plant_availability = plant_availability
    return b


def _make_costing_data(
    p_net=1000.0,
    c100000=50.0,
    c220119=10.0,
    c700000=20.0,
    c800000=5.0,
    c900000=100.0,
):
    cd = CostingData(fusion_machine_type=FusionMachineType.MFE)
    cd.power_table = PowerTable(p_net=p_net)
    cd.cas10.C100000 = c100000
    cd.cas220119.C220119 = c220119
    cd.cas70.C700000 = c700000
    cd.cas80.C800000 = c800000
    cd.cas90.C900000 = c900000
    return cd


class TestNpvBasic:
    """Basic NPV calculation tests."""

    def test_zero_discount_rate(self):
        """With 0% discount rate, NPV = sum of annual cash flows."""
        basic = _make_basic(plant_lifetime=5, plant_availability=0.85)
        npv_input = NpvInput(discount_rate=0.0)
        cd = _make_costing_data()

        # Annual cash flow = cas90 + cas220119 + cas70 + cas80 - (cas10 + 0) * avail * pnet * 8760
        annual = (
            cd.cas90.C900000
            + cd.cas220119.C220119
            + cd.cas70.C700000
            + cd.cas80.C800000
            - (cd.cas10.C100000 + 0)
            * basic.plant_availability
            * cd.power_table.p_net
            * 8760
        )
        expected = annual * 5  # 5 years, no discounting

        result = calculate_npv(basic, npv_input, cd)
        assert float(result.npv) == pytest.approx(expected, rel=1e-10)

    def test_positive_discount_rate_reduces_npv(self):
        """Positive discount rate should yield NPV with smaller magnitude than zero-rate."""
        basic = _make_basic(plant_lifetime=10)
        cd = _make_costing_data()

        r_zero = calculate_npv(basic, NpvInput(discount_rate=0.0), cd)
        r_disc = calculate_npv(basic, NpvInput(discount_rate=0.08), cd)

        # Both should be large negative (revenue term dominates),
        # but discounted version should be closer to zero (smaller magnitude)
        assert abs(float(r_disc.npv)) < abs(float(r_zero.npv))

    def test_single_year(self):
        """Single year NPV should be the undiscounted annual cash flow (year 0)."""
        basic = _make_basic(plant_lifetime=1)
        npv_input = NpvInput(discount_rate=0.10)
        cd = _make_costing_data()

        annual = (
            cd.cas90.C900000
            + cd.cas220119.C220119
            + cd.cas70.C700000
            + cd.cas80.C800000
            - cd.cas10.C100000 * basic.plant_availability * cd.power_table.p_net * 8760
        )
        # Year 0: no discounting (1 + r)^0 = 1
        result = calculate_npv(basic, npv_input, cd)
        assert float(result.npv) == pytest.approx(annual, rel=1e-10)

    def test_zero_lifetime_gives_zero(self):
        """Zero plant lifetime should give NPV = 0."""
        basic = _make_basic(plant_lifetime=0)
        result = calculate_npv(
            basic, NpvInput(discount_rate=0.05), _make_costing_data()
        )
        assert float(result.npv) == pytest.approx(0.0, abs=1e-10)


class TestNpvSensitivity:
    """NPV sensitivity to input parameters."""

    def test_higher_p_net_increases_revenue(self):
        """More net power should increase revenue (make NPV more negative or less positive)."""
        basic = _make_basic(plant_lifetime=10)
        npv_input = NpvInput(discount_rate=0.05)

        r_low = calculate_npv(basic, npv_input, _make_costing_data(p_net=500))
        r_high = calculate_npv(basic, npv_input, _make_costing_data(p_net=1500))

        # Revenue term = cas10 * avail * pnet * 8760, so higher pnet -> more negative NPV
        assert float(r_high.npv) < float(r_low.npv)

    def test_higher_availability_increases_revenue(self):
        """Higher plant availability should increase revenue."""
        npv_input = NpvInput(discount_rate=0.05)
        cd = _make_costing_data()

        r_low = calculate_npv(_make_basic(plant_availability=0.5), npv_input, cd)
        r_high = calculate_npv(_make_basic(plant_availability=0.9), npv_input, cd)

        assert float(r_high.npv) < float(r_low.npv)

    def test_higher_discount_rate_attenuates(self):
        """Higher discount rate should move NPV closer to zero."""
        basic = _make_basic(plant_lifetime=30)
        cd = _make_costing_data()

        r_low = calculate_npv(basic, NpvInput(discount_rate=0.03), cd)
        r_high = calculate_npv(basic, NpvInput(discount_rate=0.15), cd)

        assert abs(float(r_high.npv)) < abs(float(r_low.npv))

    def test_longer_lifetime_accumulates(self):
        """Longer plant lifetime should accumulate more cash flow."""
        npv_input = NpvInput(discount_rate=0.05)
        cd = _make_costing_data()

        r_short = calculate_npv(_make_basic(plant_lifetime=10), npv_input, cd)
        r_long = calculate_npv(_make_basic(plant_lifetime=40), npv_input, cd)

        assert abs(float(r_long.npv)) > abs(float(r_short.npv))
