"""Unit tests for fuel_physics.compute_ash_neutron_split().

Expected values are independently derived from CODATA particle masses via
scipy.constants, validating both the formula structure and the physics.
"""

import pytest
import scipy.constants as cs

from pyfecons.costing.calculations.fuel_physics import compute_ash_neutron_split
from pyfecons.enums import FuelType

# ---------------------------------------------------------------------------
# Reference values from scipy (independent of production code)
# ---------------------------------------------------------------------------

# Particle masses (MeV/c^2)
m_d = cs.physical_constants["deuteron mass energy equivalent in MeV"][0]
m_t = cs.physical_constants["triton mass energy equivalent in MeV"][0]
m_n = cs.physical_constants["neutron mass energy equivalent in MeV"][0]
m_p = cs.physical_constants["proton mass energy equivalent in MeV"][0]
m_alpha = cs.physical_constants["alpha particle mass energy equivalent in MeV"][0]
m_he3 = cs.physical_constants["helion mass energy equivalent in MeV"][0]

# Q-values
Q_DT = m_d + m_t - m_alpha - m_n
Q_DD_pT = 2 * m_d - m_t - m_p
Q_DD_nHe3 = 2 * m_d - m_he3 - m_n
Q_DHe3 = m_d + m_he3 - m_alpha - m_p

# Two-body CoM product energies
E_alpha_DT = Q_DT * m_n / (m_alpha + m_n)
E_n_DT = Q_DT * m_alpha / (m_alpha + m_n)

E_T_DD = Q_DD_pT * m_p / (m_t + m_p)
E_p_DD = Q_DD_pT * m_t / (m_t + m_p)
E_He3_DD = Q_DD_nHe3 * m_n / (m_he3 + m_n)
E_n_DD = Q_DD_nHe3 * m_he3 / (m_he3 + m_n)

E_alpha_DHe3 = Q_DHe3 * m_p / (m_alpha + m_p)
E_p_DHe3 = Q_DHe3 * m_alpha / (m_alpha + m_p)

# DD primary averages (before secondary burns)
E_charged_primary_DD = 0.5 * (E_T_DD + E_p_DD) + 0.5 * E_He3_DD
E_neutron_primary_DD = 0.5 * E_n_DD
E_total_primary_DD = 0.5 * Q_DD_pT + 0.5 * Q_DD_nHe3


# ---------------------------------------------------------------------------
# Q-value sanity checks (well-known literature values)
# ---------------------------------------------------------------------------


class TestQValueSanity:
    def test_q_dt_literature(self):
        """Q_DT should be ~17.59 MeV (well-known)."""
        assert Q_DT == pytest.approx(17.59, abs=0.02)

    def test_q_dd_pt_literature(self):
        """Q(D+D->T+p) should be ~4.03 MeV."""
        assert Q_DD_pT == pytest.approx(4.03, abs=0.01)

    def test_q_dd_nhe3_literature(self):
        """Q(D+D->He3+n) should be ~3.27 MeV."""
        assert Q_DD_nHe3 == pytest.approx(3.27, abs=0.01)

    def test_q_dhe3_literature(self):
        """Q(D+He3->alpha+p) should be ~18.35 MeV."""
        assert Q_DHe3 == pytest.approx(18.35, abs=0.02)

    def test_dt_product_sum(self):
        """DT product energies must sum to Q_DT."""
        assert E_alpha_DT + E_n_DT == pytest.approx(Q_DT, rel=1e-10)

    def test_dd_pt_product_sum(self):
        """DD(T+p) product energies must sum to Q_DD_pT."""
        assert E_T_DD + E_p_DD == pytest.approx(Q_DD_pT, rel=1e-10)

    def test_dd_nhe3_product_sum(self):
        """DD(He3+n) product energies must sum to Q_DD_nHe3."""
        assert E_He3_DD + E_n_DD == pytest.approx(Q_DD_nHe3, rel=1e-10)

    def test_dhe3_product_sum(self):
        """DHe3 product energies must sum to Q_DHe3."""
        assert E_alpha_DHe3 + E_p_DHe3 == pytest.approx(Q_DHe3, rel=1e-10)


# ---------------------------------------------------------------------------
# DT fuel
# ---------------------------------------------------------------------------


class TestDT:
    def test_ash_fraction(self):
        expected_ash_frac = E_alpha_DT / Q_DT
        p_ash, p_neutron = compute_ash_neutron_split(1000, FuelType.DT)
        assert float(p_ash) == pytest.approx(1000 * expected_ash_frac, rel=1e-6)

    def test_neutron_fraction(self):
        expected_n_frac = E_n_DT / Q_DT
        p_ash, p_neutron = compute_ash_neutron_split(1000, FuelType.DT)
        assert float(p_neutron) == pytest.approx(1000 * expected_n_frac, rel=1e-6)

    def test_energy_conservation(self):
        p_ash, p_neutron = compute_ash_neutron_split(2600, FuelType.DT)
        assert float(p_ash) + float(p_neutron) == pytest.approx(2600, rel=1e-10)

    def test_ash_roughly_20_percent(self):
        """DT is well-known to be ~20% charged."""
        p_ash, _ = compute_ash_neutron_split(1000, FuelType.DT)
        assert 0.199 < float(p_ash) / 1000 < 0.203


# ---------------------------------------------------------------------------
# DD fuel (semi-catalyzed burn model)
# ---------------------------------------------------------------------------


class TestDD:
    def _expected_dd_ash_frac(self, dd_f_T=0.969, dd_f_He3=0.689):
        E_charged = (
            E_charged_primary_DD + 0.5 * dd_f_T * E_alpha_DT + 0.5 * dd_f_He3 * Q_DHe3
        )
        E_total = E_total_primary_DD + 0.5 * dd_f_T * Q_DT + 0.5 * dd_f_He3 * Q_DHe3
        return E_charged / E_total

    def test_default_burn_fractions(self):
        expected = self._expected_dd_ash_frac()
        p_ash, _ = compute_ash_neutron_split(1000, FuelType.DD)
        assert float(p_ash) / 1000 == pytest.approx(expected, rel=1e-6)

    def test_pure_dd_no_secondary(self):
        """dd_f_T=0, dd_f_He3=0: only primary DD, no secondary burns."""
        expected = self._expected_dd_ash_frac(dd_f_T=0, dd_f_He3=0)
        p_ash, _ = compute_ash_neutron_split(1000, FuelType.DD, dd_f_T=0, dd_f_He3=0)
        assert float(p_ash) / 1000 == pytest.approx(expected, rel=1e-6)
        # Primary DD is majority charged (protons, tritons, He3 > neutrons)
        assert float(p_ash) / 1000 > 0.5

    def test_fully_catalyzed(self):
        """dd_f_T=1, dd_f_He3=1: maximum secondary burns."""
        expected = self._expected_dd_ash_frac(dd_f_T=1, dd_f_He3=1)
        p_ash, _ = compute_ash_neutron_split(1000, FuelType.DD, dd_f_T=1, dd_f_He3=1)
        assert float(p_ash) / 1000 == pytest.approx(expected, rel=1e-6)

    def test_energy_conservation_defaults(self):
        p_ash, p_neutron = compute_ash_neutron_split(2600, FuelType.DD)
        assert float(p_ash) + float(p_neutron) == pytest.approx(2600, rel=1e-10)

    def test_energy_conservation_pure(self):
        p_ash, p_neutron = compute_ash_neutron_split(
            2600, FuelType.DD, dd_f_T=0, dd_f_He3=0
        )
        assert float(p_ash) + float(p_neutron) == pytest.approx(2600, rel=1e-10)

    def test_energy_conservation_catalyzed(self):
        p_ash, p_neutron = compute_ash_neutron_split(
            2600, FuelType.DD, dd_f_T=1, dd_f_He3=1
        )
        assert float(p_ash) + float(p_neutron) == pytest.approx(2600, rel=1e-10)

    def test_higher_burn_fraction_changes_split(self):
        """Higher burn fractions should change the ash fraction."""
        p_ash_low, _ = compute_ash_neutron_split(
            1000, FuelType.DD, dd_f_T=0.5, dd_f_He3=0.5
        )
        p_ash_high, _ = compute_ash_neutron_split(
            1000, FuelType.DD, dd_f_T=0.99, dd_f_He3=0.99
        )
        # With higher T burn fraction, more secondary DT neutrons are produced,
        # but also more He3 burns (all charged). The net effect depends on the
        # balance — just verify they differ.
        assert float(p_ash_low) != pytest.approx(float(p_ash_high), abs=1.0)


# ---------------------------------------------------------------------------
# DHe3 fuel
# ---------------------------------------------------------------------------


class TestDHe3:
    def _expected_dhe3_ash_frac(self, dhe3_dd_frac=0.07, dhe3_f_T=0.97):
        E_n_dd = E_neutron_primary_DD + 0.5 * dhe3_f_T * E_n_DT
        E_c_dd = E_charged_primary_DD + 0.5 * dhe3_f_T * E_alpha_DT
        return (1 - dhe3_dd_frac) + dhe3_dd_frac * E_c_dd / (E_n_dd + E_c_dd)

    def test_default_fractions(self):
        expected = self._expected_dhe3_ash_frac()
        p_ash, _ = compute_ash_neutron_split(1000, FuelType.DHE3)
        assert float(p_ash) / 1000 == pytest.approx(expected, rel=1e-6)

    def test_pure_aneutronic(self):
        """dhe3_dd_frac=0: no DD side reactions, 100% charged."""
        p_ash, p_neutron = compute_ash_neutron_split(
            1000, FuelType.DHE3, dhe3_dd_frac=0
        )
        assert float(p_ash) == pytest.approx(1000, rel=1e-10)
        assert float(p_neutron) == pytest.approx(0, abs=1e-10)

    def test_mostly_charged(self):
        """With default 7% DD sides, ash fraction should be >93%."""
        p_ash, _ = compute_ash_neutron_split(1000, FuelType.DHE3)
        assert float(p_ash) / 1000 > 0.93

    def test_energy_conservation(self):
        p_ash, p_neutron = compute_ash_neutron_split(2600, FuelType.DHE3)
        assert float(p_ash) + float(p_neutron) == pytest.approx(2600, rel=1e-10)


# ---------------------------------------------------------------------------
# p-B11 fuel
# ---------------------------------------------------------------------------


class TestPB11:
    def test_fully_aneutronic(self):
        p_ash, p_neutron = compute_ash_neutron_split(1000, FuelType.PB11)
        assert float(p_ash) == pytest.approx(1000, rel=1e-10)
        assert float(p_neutron) == pytest.approx(0, abs=1e-10)

    def test_energy_conservation(self):
        p_ash, p_neutron = compute_ash_neutron_split(2600, FuelType.PB11)
        assert float(p_ash) + float(p_neutron) == pytest.approx(2600, rel=1e-10)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_unknown_fuel_type_raises(self):
        with pytest.raises(ValueError, match="Unknown fuel type"):
            compute_ash_neutron_split(1000, "invalid_fuel")


# ---------------------------------------------------------------------------
# Parametrized energy conservation across all fuels and power levels
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fuel_type", [FuelType.DT, FuelType.DD, FuelType.DHE3, FuelType.PB11]
)
@pytest.mark.parametrize("p_nrl", [100, 1000, 5000])
def test_energy_conservation_parametrized(fuel_type, p_nrl):
    p_ash, p_neutron = compute_ash_neutron_split(p_nrl, fuel_type)
    assert float(p_ash) + float(p_neutron) == pytest.approx(p_nrl, rel=1e-10)
