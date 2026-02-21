"""Unit tests for financials module.

Tests CRF, levelized annual cost, licensing time, and total project time
with hand-computed expected values.
"""

import pytest

from pyfecons.costing.calculations.financials import (
    compute_crf,
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
# compute_effective_crf — REMOVED
# IDC is now handled in CAS60 via f_IDC formula. CAS90 uses plain CRF.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# levelized_annual_cost — uses plain CRF (not effective CRF)
# ---------------------------------------------------------------------------


class TestLevelizedAnnualCost:
    def test_zero_inflation_equals_annual_cost(self):
        """With zero inflation, levelized cost equals the annual cost.

        PV of flat annuity at rate i = A/CRF, so CRF * PV = A.
        """
        result = levelized_annual_cost(M_USD(10.0), 0.07, 0.0, 30, 6)
        assert float(result) == pytest.approx(10.0, abs=0.01)

    def test_reference_case(self):
        """At 7% nominal, 2% inflation, 30yr life, 6yr construction.

        A_1 = 100 * 1.02^6 = 112.616
        PV = 112.616 * (1 - (1.02/1.07)^30) / (0.07 - 0.02) = 1716.5
        CRF(0.07, 30) = 0.08059
        levelized = 0.08059 * 1716.5 = 138.35
        """
        result = levelized_annual_cost(M_USD(100), 0.07, 0.02, 30, 6)
        assert float(result) == pytest.approx(138.35, abs=1.0)

    def test_higher_than_simple_inflation(self):
        """Proper levelization should exceed the old cost * (1+g)^Tc approach.

        The growing annuity over 30 years adds ~23% vs just inflating to year 1.
        """
        simple = 100.0 * (1.02**6)  # old approach: ~112.6
        levelized = levelized_annual_cost(M_USD(100), 0.07, 0.02, 30, 6)
        assert float(levelized) > simple

    def test_equal_rates(self):
        """When i == g, uses pv = A_1 * n / (1+i). Should not crash."""
        result = levelized_annual_cost(M_USD(100), 0.05, 0.05, 30, 6)
        # PV = 100 * 1.05^6 * 30 / 1.05
        a1 = 100 * 1.05**6
        pv = a1 * 30 / 1.05
        crf = compute_crf(0.05, 30)
        expected = crf * pv
        assert float(result) == pytest.approx(expected, rel=1e-6)

    def test_positive(self):
        """Levelized cost should be positive for positive annual cost."""
        result = levelized_annual_cost(M_USD(50), 0.08, 0.025, 30, 6)
        assert float(result) > 0

    def test_higher_inflation_increases_cost(self):
        """Higher inflation -> higher levelized cost."""
        low = levelized_annual_cost(M_USD(100), 0.08, 0.01, 30, 6)
        high = levelized_annual_cost(M_USD(100), 0.08, 0.04, 30, 6)
        assert float(high) > float(low)

    def test_scales_linearly(self):
        """Doubling annual cost should double the levelized result."""
        low = levelized_annual_cost(M_USD(50), 0.07, 0.02, 30, 6)
        high = levelized_annual_cost(M_USD(100), 0.07, 0.02, 30, 6)
        assert float(high) / float(low) == pytest.approx(2.0, rel=1e-10)

    def test_zero_rate_fallback(self):
        """i=0: returns raw annual_cost."""
        result = levelized_annual_cost(M_USD(100), 0, 0.025, 30, 6)
        assert float(result) == pytest.approx(100, rel=1e-10)


# ---------------------------------------------------------------------------
# get_licensing_time
# ---------------------------------------------------------------------------


class TestGetLicensingTime:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.constants = CostingConstants()

    def test_dt(self):
        assert get_licensing_time(FuelType.DT, self.constants) == 2.0

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
        assert total_project_time(6, FuelType.DT, self.constants, noak=False) == 6 + 2.0

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
