"""Tests for CAS30/CAS60/CAS90 financial fixes.

CAS30: indirect_fraction * CAS20 * (construction_time / reference_time)
CAS60: first-principles IDC via f_IDC = ((1+i)^T - 1) / (i*T) - 1
CAS90: plain CRF * total_capital (no effective CRF)
"""

import pytest

from pyfecons.costing.calculations.cas30_capitalized_indirect_service import (
    cas30_capitalized_indirect_service_costs,
)
from pyfecons.costing.calculations.cas60_capitalized_financial import (
    cas60_capitalized_financial_costs,
)
from pyfecons.costing.calculations.cas90_annualized_financial import (
    cas90_annualized_financial_costs,
)
from pyfecons.costing.calculations.financials import compute_crf
from pyfecons.costing.categories.cas200000 import CAS20
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.costing_constants import CostingConstants
from pyfecons.inputs.financial import Financial
from pyfecons.units import M_USD

# ---------------------------------------------------------------------------
# CAS30 — indirect_fraction * CAS20 * (t_con / t_ref)
# ---------------------------------------------------------------------------


class TestCAS30:
    def test_reference_case(self):
        """At reference construction time, CAS30 = indirect_fraction * CAS20."""
        constants = CostingConstants()
        cas20 = CAS20()
        cas20.C200000 = M_USD(5000)
        basic = Basic()
        basic.construction_time = constants.reference_construction_time

        cas30 = cas30_capitalized_indirect_service_costs(basic, cas20, constants)
        expected = constants.indirect_fraction * 5000
        assert float(cas30.C300000) == pytest.approx(expected, rel=1e-6)

    def test_scales_with_construction_time(self):
        """Doubling construction time doubles CAS30."""
        constants = CostingConstants()
        cas20 = CAS20()
        cas20.C200000 = M_USD(5000)

        basic_short = Basic()
        basic_short.construction_time = 3
        basic_long = Basic()
        basic_long.construction_time = 6

        cas30_short = cas30_capitalized_indirect_service_costs(
            basic_short, cas20, constants
        )
        cas30_long = cas30_capitalized_indirect_service_costs(
            basic_long, cas20, constants
        )
        assert float(cas30_long.C300000) / float(cas30_short.C300000) == pytest.approx(
            2.0, rel=1e-6
        )

    def test_scales_with_cas20(self):
        """Doubling CAS20 doubles CAS30."""
        constants = CostingConstants()
        basic = Basic()
        basic.construction_time = 6

        cas20_low = CAS20()
        cas20_low.C200000 = M_USD(3000)
        cas20_high = CAS20()
        cas20_high.C200000 = M_USD(6000)

        cas30_low = cas30_capitalized_indirect_service_costs(
            basic, cas20_low, constants
        )
        cas30_high = cas30_capitalized_indirect_service_costs(
            basic, cas20_high, constants
        )
        assert float(cas30_high.C300000) / float(cas30_low.C300000) == pytest.approx(
            2.0, rel=1e-6
        )

    def test_1gwe_reference(self):
        """At 1 GWe with CAS20=5000, 6yr construction: CAS30 ~ 1000M."""
        constants = CostingConstants()
        cas20 = CAS20()
        cas20.C200000 = M_USD(5000)
        basic = Basic()
        basic.construction_time = 6

        cas30 = cas30_capitalized_indirect_service_costs(basic, cas20, constants)
        # 0.20 * 5000 * (6/6) = 1000
        assert float(cas30.C300000) == pytest.approx(1000, rel=1e-6)


# ---------------------------------------------------------------------------
# CAS60 — first-principles IDC: f_IDC * overnight_cost
# ---------------------------------------------------------------------------


class TestCAS60:
    def test_reference_case_7pct_6yr(self):
        """f_IDC(0.07, 6) * 5000 — known value."""
        i, T = 0.07, 6
        f_idc = ((1 + i) ** T - 1) / (i * T) - 1
        expected = f_idc * 5000  # overnight cost

        basic = Basic()
        basic.construction_time = T
        basic.noak = True
        financial = Financial()
        financial.interest_rate = i
        constants = CostingConstants()

        cas60 = cas60_capitalized_financial_costs(
            basic, financial, M_USD(5000), constants
        )
        assert float(cas60.C600000) == pytest.approx(expected, rel=1e-6)

    def test_scales_with_overnight_cost(self):
        """Doubling overnight cost doubles IDC."""
        basic = Basic()
        basic.construction_time = 6
        basic.noak = True
        financial = Financial()
        financial.interest_rate = 0.07
        constants = CostingConstants()

        cas60_low = cas60_capitalized_financial_costs(
            basic, financial, M_USD(3000), constants
        )
        cas60_high = cas60_capitalized_financial_costs(
            basic, financial, M_USD(6000), constants
        )
        assert float(cas60_high.C600000) / float(cas60_low.C600000) == pytest.approx(
            2.0, rel=1e-6
        )

    def test_increases_with_construction_time(self):
        """Longer construction -> more IDC."""
        financial = Financial()
        financial.interest_rate = 0.07
        constants = CostingConstants()

        basic_short = Basic()
        basic_short.construction_time = 4
        basic_short.noak = True
        basic_long = Basic()
        basic_long.construction_time = 8
        basic_long.noak = True

        cas60_short = cas60_capitalized_financial_costs(
            basic_short, financial, M_USD(5000), constants
        )
        cas60_long = cas60_capitalized_financial_costs(
            basic_long, financial, M_USD(5000), constants
        )
        assert float(cas60_long.C600000) > float(cas60_short.C600000)

    def test_increases_with_interest_rate(self):
        """Higher interest -> more IDC."""
        basic = Basic()
        basic.construction_time = 6
        basic.noak = True
        constants = CostingConstants()

        fin_low = Financial()
        fin_low.interest_rate = 0.05
        fin_high = Financial()
        fin_high.interest_rate = 0.10

        cas60_low = cas60_capitalized_financial_costs(
            basic, fin_low, M_USD(5000), constants
        )
        cas60_high = cas60_capitalized_financial_costs(
            basic, fin_high, M_USD(5000), constants
        )
        assert float(cas60_high.C600000) > float(cas60_low.C600000)

    def test_5pct_6yr(self):
        """At 5%, 6yr: f_IDC ~ 0.1337."""
        i, T = 0.05, 6
        f_idc = ((1 + i) ** T - 1) / (i * T) - 1
        assert f_idc == pytest.approx(0.1337, abs=0.001)

        basic = Basic()
        basic.construction_time = T
        basic.noak = True
        financial = Financial()
        financial.interest_rate = i
        constants = CostingConstants()

        cas60 = cas60_capitalized_financial_costs(
            basic, financial, M_USD(1000), constants
        )
        assert float(cas60.C600000) == pytest.approx(f_idc * 1000, rel=1e-3)


# ---------------------------------------------------------------------------
# CAS90 — plain CRF * total_capital
# ---------------------------------------------------------------------------


class TestCAS90:
    def test_equals_crf_times_total_capital(self):
        """CAS90 = CRF(i, n) * total_capital. No construction-time adjustment."""
        basic = Basic()
        basic.plant_lifetime = 30
        basic.construction_time = 6
        basic.noak = True
        financial = Financial()
        financial.interest_rate = 0.07
        constants = CostingConstants()

        total_capital = M_USD(5500)
        cas90 = cas90_annualized_financial_costs(
            basic, financial, total_capital, constants
        )

        crf = compute_crf(0.07, 30)
        expected = crf * 5500
        assert float(cas90.C900000) == pytest.approx(expected, rel=1e-6)

    def test_no_construction_time_dependence(self):
        """CAS90 should not depend on construction_time (IDC is in CAS60)."""
        financial = Financial()
        financial.interest_rate = 0.07
        constants = CostingConstants()

        basic_short = Basic()
        basic_short.plant_lifetime = 30
        basic_short.construction_time = 4
        basic_short.noak = True
        basic_long = Basic()
        basic_long.plant_lifetime = 30
        basic_long.construction_time = 10
        basic_long.noak = True

        total_capital = M_USD(5500)
        cas90_short = cas90_annualized_financial_costs(
            basic_short, financial, total_capital, constants
        )
        cas90_long = cas90_annualized_financial_costs(
            basic_long, financial, total_capital, constants
        )
        assert float(cas90_short.C900000) == pytest.approx(
            float(cas90_long.C900000), rel=1e-10
        )

    def test_total_capital_stored(self):
        """C990000 should store the total capital input."""
        basic = Basic()
        basic.plant_lifetime = 30
        basic.construction_time = 6
        basic.noak = True
        financial = Financial()
        financial.interest_rate = 0.07
        constants = CostingConstants()

        cas90 = cas90_annualized_financial_costs(
            basic, financial, M_USD(5500), constants
        )
        assert float(cas90.C990000) == pytest.approx(5500, rel=1e-10)


# ---------------------------------------------------------------------------
# compute_effective_crf should no longer exist
# ---------------------------------------------------------------------------


class TestEffectiveCRFRemoved:
    def test_not_importable(self):
        """compute_effective_crf should no longer be in financials."""
        with pytest.raises(ImportError):
            from pyfecons.costing.calculations.financials import (  # noqa: F401
                compute_effective_crf,
            )
