"""Unit tests for power_balance.power_balance().

Tests verify the power flow formulas by building minimal inputs with known
values and comparing outputs against independently computed expectations.
"""

import pytest

from pyfecons.costing.calculations.fuel_physics import Q_DT, E_alpha_DT, E_n_DT
from pyfecons.costing.calculations.power_balance import power_balance
from pyfecons.enums import FuelType, FusionMachineType
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.power_input import PowerInput
from pyfecons.units import MW, Count, Percent, Ratio, Unknown, Years

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mfe_basic(**overrides) -> Basic:
    """Minimal MFE Basic with reasonable DT defaults."""
    defaults = dict(
        fusion_machine_type=FusionMachineType.MFE,
        fuel_type=FuelType.DT,
        p_nrl=MW(2600),
        n_mod=Count(1),
        plant_availability=Percent(0.85),
        construction_time=Years(6),
        plant_lifetime=Years(30),
        noak=True,
        yearly_inflation=Percent(0.0245),
    )
    defaults.update(overrides)
    return Basic(**defaults)


def _make_mfe_power(**overrides) -> PowerInput:
    """Minimal MFE PowerInput matching CATF defaults."""
    defaults = dict(
        f_sub=Percent(0.03),
        p_cryo=MW(0.5),
        mn=Ratio(1.1),
        eta_p=Percent(0.5),
        eta_th=Percent(0.46),
        p_trit=MW(10),
        p_house=MW(4),
        p_cool=MW(13.7),
        p_coils=MW(2),
        eta_pin=Percent(0.5),
        f_dec=Percent(0),
        eta_de=Percent(0.85),
        p_input=MW(50),
        p_pump=MW(1),
    )
    defaults.update(overrides)
    return PowerInput(**defaults)


# ---------------------------------------------------------------------------
# MFE DT baseline (mirrors CATF MFE customer inputs)
# ---------------------------------------------------------------------------


class TestMFEDTBaseline:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.basic = _make_mfe_basic()
        self.pi = _make_mfe_power()
        self.pt = power_balance(self.basic, self.pi)

    def test_ash_fraction_matches_dt(self):
        """p_ash / p_nrl should equal DT charged fraction from CODATA."""
        expected_frac = E_alpha_DT / Q_DT
        assert float(self.pt.p_ash) / 2600 == pytest.approx(expected_frac, rel=1e-6)

    def test_neutron_fraction_matches_dt(self):
        expected_frac = E_n_DT / Q_DT
        assert float(self.pt.p_neutron) / 2600 == pytest.approx(expected_frac, rel=1e-6)

    def test_ash_plus_neutron_equals_p_nrl(self):
        assert float(self.pt.p_ash) + float(self.pt.p_neutron) == pytest.approx(
            2600, rel=1e-10
        )

    def test_p_aux(self):
        assert float(self.pt.p_aux) == pytest.approx(10 + 4, rel=1e-10)

    def test_no_dec(self):
        """f_dec=0: no direct energy conversion."""
        assert float(self.pt.p_dee) == pytest.approx(0, abs=1e-10)
        assert float(self.pt.p_dec_waste) == pytest.approx(0, abs=1e-10)

    def test_p_wall_equals_ash_thermal(self):
        """With no DEC, all ash goes to wall."""
        assert float(self.pt.p_wall) == pytest.approx(float(self.pt.p_ash), rel=1e-10)

    def test_p_th_formula(self):
        """p_th = mn*p_neutron + p_ash_thermal + p_input + eta_p*p_pump."""
        expected = (
            1.1 * float(self.pt.p_neutron)
            + float(self.pt.p_ash)  # no DEC: all ash thermal
            + 50  # p_input
            + 0.5 * 1  # eta_p * p_pump
        )
        assert float(self.pt.p_th) == pytest.approx(expected, rel=1e-10)

    def test_p_the_formula(self):
        assert float(self.pt.p_the) == pytest.approx(
            0.46 * float(self.pt.p_th), rel=1e-10
        )

    def test_p_et_equals_p_the_no_dec(self):
        """With no DEC, gross electric = thermal electric."""
        assert float(self.pt.p_et) == pytest.approx(float(self.pt.p_the), rel=1e-10)

    def test_p_loss(self):
        expected = (float(self.pt.p_th) - float(self.pt.p_the)) + float(
            self.pt.p_dec_waste
        )
        assert float(self.pt.p_loss) == pytest.approx(expected, rel=1e-10)

    def test_p_sub(self):
        assert float(self.pt.p_sub) == pytest.approx(
            0.03 * float(self.pt.p_et), rel=1e-10
        )

    def test_q_sci(self):
        assert float(self.pt.q_sci) == pytest.approx(2600 / 50, rel=1e-10)

    def test_q_eng_gt_1(self):
        """Plant must produce more than it recirculates."""
        assert float(self.pt.q_eng) > 1

    def test_rec_frac(self):
        assert float(self.pt.rec_frac) == pytest.approx(
            1 / float(self.pt.q_eng), rel=1e-10
        )

    def test_p_net_positive(self):
        assert float(self.pt.p_net) > 0

    def test_p_net_formula(self):
        expected = (1 - 1 / float(self.pt.q_eng)) * float(self.pt.p_et)
        assert float(self.pt.p_net) == pytest.approx(expected, rel=1e-10)

    def test_recirculating_power_mfe(self):
        """Verify MFE recirculating power sum."""
        recirculating = (
            float(self.pt.p_coils)
            + float(self.pt.p_pump)
            + float(self.pt.p_sub)
            + float(self.pt.p_aux)
            + float(self.pt.p_cool)
            + 0.5  # p_cryo
            + 50 / 0.5  # p_input / eta_pin
        )
        assert float(self.pt.q_eng) == pytest.approx(
            float(self.pt.p_et) / recirculating, rel=1e-10
        )


# ---------------------------------------------------------------------------
# MFE with DEC
# ---------------------------------------------------------------------------


class TestMFEWithDEC:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.basic = _make_mfe_basic()
        self.pi = _make_mfe_power(f_dec=Percent(0.5))
        self.pt = power_balance(self.basic, self.pi)

    def test_p_dee(self):
        expected = 0.5 * 0.85 * float(self.pt.p_ash)
        assert float(self.pt.p_dee) == pytest.approx(expected, rel=1e-10)

    def test_p_dec_waste(self):
        expected = 0.5 * (1 - 0.85) * float(self.pt.p_ash)
        assert float(self.pt.p_dec_waste) == pytest.approx(expected, rel=1e-10)

    def test_p_wall_reduced(self):
        """Only half the ash goes to walls (other half to DEC)."""
        expected = 0.5 * float(self.pt.p_ash)
        assert float(self.pt.p_wall) == pytest.approx(expected, rel=1e-10)

    def test_p_et_includes_dee(self):
        assert float(self.pt.p_et) == pytest.approx(
            float(self.pt.p_dee) + float(self.pt.p_the), rel=1e-10
        )

    def test_dec_energy_conservation(self):
        """DEC-captured ash = p_dee + p_dec_waste (all accounted for)."""
        dec_total = float(self.pt.p_dee) + float(self.pt.p_dec_waste)
        expected = 0.5 * float(self.pt.p_ash)
        assert dec_total == pytest.approx(expected, rel=1e-10)


# ---------------------------------------------------------------------------
# IFE baseline (uses CATF IFE fixture from conftest)
# ---------------------------------------------------------------------------


class TestIFE:
    def test_ife_p_net_positive(self, ife_inputs):
        pt = power_balance(ife_inputs.basic, ife_inputs.power_input)
        assert float(pt.p_net) > 0

    def test_ife_no_dec(self, ife_inputs):
        """IFE path: no DEC, all ash thermalizes."""
        pt = power_balance(ife_inputs.basic, ife_inputs.power_input)
        assert float(pt.p_dee) == pytest.approx(0, abs=1e-10)
        assert float(pt.p_dec_waste) == pytest.approx(0, abs=1e-10)

    def test_ife_gain_e(self, ife_inputs):
        """IFE sets gain_e = p_et / p_input."""
        pt = power_balance(ife_inputs.basic, ife_inputs.power_input)
        assert float(pt.gain_e) == pytest.approx(
            float(pt.p_et) / float(ife_inputs.power_input.p_input), rel=1e-10
        )

    def test_ife_energy_conservation(self, ife_inputs):
        pt = power_balance(ife_inputs.basic, ife_inputs.power_input)
        assert float(pt.p_ash) + float(pt.p_neutron) == pytest.approx(
            float(ife_inputs.basic.p_nrl), rel=1e-10
        )


# ---------------------------------------------------------------------------
# Different fuel types
# ---------------------------------------------------------------------------


class TestFuelTypes:
    def test_dd_more_charged(self):
        """DD has higher charged fraction than DT."""
        basic_dt = _make_mfe_basic(fuel_type=FuelType.DT)
        basic_dd = _make_mfe_basic(fuel_type=FuelType.DD)
        pi = _make_mfe_power()
        pt_dt = power_balance(basic_dt, pi)
        pt_dd = power_balance(basic_dd, pi)
        assert float(pt_dd.p_ash) > float(pt_dt.p_ash)

    def test_pb11_no_neutrons(self):
        """PB11 should have zero neutron power."""
        basic = _make_mfe_basic(fuel_type=FuelType.PB11)
        pi = _make_mfe_power()
        pt = power_balance(basic, pi)
        assert float(pt.p_neutron) == pytest.approx(0, abs=1e-10)
        assert float(pt.p_ash) == pytest.approx(2600, rel=1e-10)

    def test_pb11_p_th_no_neutron_blanket(self):
        """With no neutrons, p_th has no blanket multiplication term."""
        basic = _make_mfe_basic(fuel_type=FuelType.PB11)
        pi = _make_mfe_power()
        pt = power_balance(basic, pi)
        # p_th = mn*0 + 2600 + 50 + 0.5*1 = 2650.5
        assert float(pt.p_th) == pytest.approx(2600 + 50 + 0.5 * 1, rel=1e-10)

    def test_dhe3_mostly_charged(self):
        """DHe3 should be >93% charged (7% DD sides)."""
        basic = _make_mfe_basic(fuel_type=FuelType.DHE3)
        pi = _make_mfe_power()
        pt = power_balance(basic, pi)
        assert float(pt.p_ash) / 2600 > 0.93


# ---------------------------------------------------------------------------
# Parametrized: energy conservation across fuels
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fuel_type", [FuelType.DT, FuelType.DD, FuelType.DHE3, FuelType.PB11]
)
def test_ash_neutron_conservation(fuel_type):
    basic = _make_mfe_basic(fuel_type=fuel_type)
    pi = _make_mfe_power()
    pt = power_balance(basic, pi)
    assert float(pt.p_ash) + float(pt.p_neutron) == pytest.approx(2600, rel=1e-10)
