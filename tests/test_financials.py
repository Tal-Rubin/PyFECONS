"""Unit tests for financials module.

Tests CRF, effective CRF, levelized annual cost, licensing time, and
total project time with hand-computed expected values.
"""

import pytest

from pyfecons.costing.calculations.financials import (
    compute_crf,
    compute_effective_crf,
    get_licensing_time,
    levelized_annual_cost,
    total_project_time,
)
from pyfecons.enums import FuelType
from pyfecons.inputs.costing_constants import CostingConstants
from pyfecons.units import M_USD

# ---------------------------------------------------------------------------
# compute_crf
# ---------------------------------------------------------------------------


class TestComputeCRF:
    def test_known_value_8pct_30yr(self):
        """CRF(0.08, 30) = 0.08*1.08^30 / (1.08^30 - 1) ~ 0.08883."""
        crf = compute_crf(0.08, 30)
        assert crf == pytest.approx(0.08883, abs=0.0001)

    def test_known_value_5pct_20yr(self):
        """CRF(0.05, 20) ~ 0.08024."""
        crf = compute_crf(0.05, 20)
        assert crf == pytest.approx(0.08024, abs=0.0001)

    def test_known_value_10pct_10yr(self):
        """CRF(0.10, 10) ~ 0.16275."""
        crf = compute_crf(0.10, 10)
        assert crf == pytest.approx(0.16275, abs=0.0001)

    def test_high_rate_approaches_rate(self):
        """Very high interest -> CRF approaches interest_rate."""
        crf = compute_crf(0.50, 100)
        assert crf == pytest.approx(0.50, abs=0.001)

    def test_crf_gt_interest_rate(self):
        """CRF always exceeds the interest rate (must repay principal too)."""
        for i, n in [(0.05, 20), (0.08, 30), (0.10, 10)]:
            assert compute_crf(i, n) > i


# ---------------------------------------------------------------------------
# compute_effective_crf
# ---------------------------------------------------------------------------


class TestComputeEffectiveCRF:
    def test_basic(self):
        """effective_crf = CRF * (1+i)^Tc."""
        eff = compute_effective_crf(0.08, 30, 6)
        crf = compute_crf(0.08, 30)
        assert eff == pytest.approx(crf * 1.08**6, rel=1e-10)

    def test_zero_construction_time(self):
        """Tc=0: effective_crf = CRF."""
        eff = compute_effective_crf(0.08, 30, 0)
        assert eff == pytest.approx(compute_crf(0.08, 30), rel=1e-10)

    def test_fallback_on_zero_rate(self):
        """interest_rate=0 with fallback returns fallback."""
        assert compute_effective_crf(0, 30, 6, fallback_crf=0.1) == 0.1

    def test_fallback_on_zero_lifetime(self):
        assert compute_effective_crf(0.08, 0, 6, fallback_crf=0.1) == 0.1

    def test_raises_without_fallback(self):
        with pytest.raises(ValueError, match="Invalid financial parameters"):
            compute_effective_crf(0, 30, 6)


# ---------------------------------------------------------------------------
# levelized_annual_cost
# ---------------------------------------------------------------------------


class TestLevelizedAnnualCost:
    def test_known_value(self):
        """Verify with hand calculation: i=0.08, g=0.025, n=30, Tc=6."""
        annual = M_USD(100)
        result = levelized_annual_cost(annual, 0.08, 0.025, 30, 6)
        # PV of growing annuity: cost * (1 - ((1+g)/(1+i))^n) / (i - g)
        ratio = (1.025 / 1.08) ** 30
        pv = 100 * (1 - ratio) / (0.08 - 0.025)
        eff_crf = compute_crf(0.08, 30) * 1.08**6
        expected = eff_crf * pv
        assert float(result) == pytest.approx(expected, rel=1e-6)

    def test_equal_rates(self):
        """When i == g, uses pv = cost * n / (1+i)."""
        result = levelized_annual_cost(M_USD(100), 0.05, 0.05, 30, 6)
        pv = 100 * 30 / 1.05
        eff_crf = compute_crf(0.05, 30) * 1.05**6
        expected = eff_crf * pv
        assert float(result) == pytest.approx(expected, rel=1e-6)

    def test_zero_rate_fallback(self):
        """i=0: returns raw annual_cost."""
        result = levelized_annual_cost(M_USD(100), 0, 0.025, 30, 6)
        assert float(result) == pytest.approx(100, rel=1e-10)

    def test_positive(self):
        """Levelized cost should be positive for positive annual cost."""
        result = levelized_annual_cost(M_USD(50), 0.08, 0.025, 30, 6)
        assert float(result) > 0

    def test_higher_inflation_increases_cost(self):
        """Higher inflation -> higher levelized cost."""
        low = levelized_annual_cost(M_USD(100), 0.08, 0.01, 30, 6)
        high = levelized_annual_cost(M_USD(100), 0.08, 0.04, 30, 6)
        assert float(high) > float(low)


# ---------------------------------------------------------------------------
# get_licensing_time
# ---------------------------------------------------------------------------


class TestGetLicensingTime:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.constants = CostingConstants()

    def test_dt(self):
        assert get_licensing_time(FuelType.DT, self.constants) == 2.5

    def test_dd(self):
        assert get_licensing_time(FuelType.DD, self.constants) == 1.5

    def test_dhe3(self):
        assert get_licensing_time(FuelType.DHE3, self.constants) == 0.75

    def test_pb11(self):
        assert get_licensing_time(FuelType.PB11, self.constants) == 0.0

    def test_ordering(self):
        """More radioactive fuels -> longer licensing."""
        times = [
            get_licensing_time(f, self.constants)
            for f in [FuelType.PB11, FuelType.DHE3, FuelType.DD, FuelType.DT]
        ]
        assert times == sorted(times)


# ---------------------------------------------------------------------------
# total_project_time
# ---------------------------------------------------------------------------


class TestTotalProjectTime:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.constants = CostingConstants()

    def test_foak_dt(self):
        """FOAK DT: construction + licensing."""
        assert total_project_time(6, FuelType.DT, self.constants, noak=False) == 6 + 2.5

    def test_noak_dt(self):
        """NOAK: construction only."""
        assert total_project_time(6, FuelType.DT, self.constants, noak=True) == 6

    def test_foak_pb11(self):
        """FOAK PB11: licensing time is 0."""
        assert total_project_time(6, FuelType.PB11, self.constants, noak=False) == 6

    def test_foak_longer_than_noak(self):
        """FOAK always >= NOAK for fuels with licensing."""
        for fuel in [FuelType.DT, FuelType.DD, FuelType.DHE3]:
            foak = total_project_time(6, fuel, self.constants, noak=False)
            noak = total_project_time(6, fuel, self.constants, noak=True)
            assert foak >= noak
