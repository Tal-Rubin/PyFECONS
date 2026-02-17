"""Tests for the reactivity module (peak cross-sections and min_density_for_power)."""

import pytest

from pyfecons.costing.calculations.reactivity import (
    CHARGE_FACTOR,
    PARTICLE_FACTOR,
    PEAK_SIGMA_V,
    PEAK_TEMPERATURE,
    SPECIES_FACTOR,
    min_density_for_power,
    required_confinement_time,
)
from pyfecons.enums import FuelType


class TestPeakSigmaV:
    """Sanity checks on stored ⟨σv⟩ values."""

    def test_all_fuel_types_present(self):
        for ft in (FuelType.DT, FuelType.DD, FuelType.DHE3, FuelType.PB11):
            assert ft in PEAK_SIGMA_V

    def test_dt_is_highest(self):
        # DT has the highest peak ⟨σv⟩ among all fuels (easiest to ignite)
        # except DHe3 which is slightly lower but same order
        assert PEAK_SIGMA_V[FuelType.DT] > PEAK_SIGMA_V[FuelType.DD]

    def test_dd_is_lowest(self):
        # DD has the lowest peak ⟨σv⟩ — hardest plasma physics
        assert PEAK_SIGMA_V[FuelType.DD] < PEAK_SIGMA_V[FuelType.DT]
        assert PEAK_SIGMA_V[FuelType.DD] < PEAK_SIGMA_V[FuelType.DHE3]
        assert PEAK_SIGMA_V[FuelType.DD] < PEAK_SIGMA_V[FuelType.PB11]

    def test_values_positive(self):
        for ft, sv in PEAK_SIGMA_V.items():
            assert sv > 0, f"⟨σv⟩ must be positive for {ft}"


class TestMinDensityForPower:
    """Test the density calculation for known cases."""

    def test_dt_iter_like(self):
        # ITER-like: 500 MW in ~830 m³ → should give n_e ~ 1e20 m⁻³
        n_e = min_density_for_power(500, 830, FuelType.DT)
        assert (
            5e19 < n_e < 5e20
        ), f"ITER-like DT density {n_e:.2e} outside expected range"

    def test_dt_catf(self):
        # CATF: 2600 MW in 215 m³ → should give n_e ~ 2.6e20 m⁻³
        n_e = min_density_for_power(2600, 215, FuelType.DT)
        assert 1e20 < n_e < 5e20, f"CATF DT density {n_e:.2e} outside expected range"

    def test_dd_requires_higher_density_than_dt(self):
        # DD has much lower ⟨σv⟩, so needs higher density for same power/volume
        n_e_dt = min_density_for_power(1000, 500, FuelType.DT)
        n_e_dd = min_density_for_power(1000, 500, FuelType.DD)
        assert n_e_dd > n_e_dt

    def test_larger_volume_lower_density(self):
        # More volume → lower required density
        n_e_small = min_density_for_power(1000, 100, FuelType.DT)
        n_e_large = min_density_for_power(1000, 1000, FuelType.DT)
        assert n_e_large < n_e_small

    def test_higher_power_higher_density(self):
        # More power → higher required density
        n_e_low = min_density_for_power(100, 500, FuelType.DT)
        n_e_high = min_density_for_power(5000, 500, FuelType.DT)
        assert n_e_high > n_e_low

    def test_all_fuel_types_return_positive(self):
        for ft in (FuelType.DT, FuelType.DD, FuelType.DHE3, FuelType.PB11):
            n_e = min_density_for_power(1000, 500, ft)
            assert n_e > 0, f"Density must be positive for {ft}"

    def test_charge_factor_applied(self):
        # For PB11 with Z_B11=5, charge_factor=6, so n_e should be much
        # higher relative to n_ion than for DT (charge_factor=2)
        n_e_dt = min_density_for_power(1000, 500, FuelType.DT)
        n_e_pb11 = min_density_for_power(1000, 500, FuelType.PB11)
        # PB11 has similar peak ⟨σv⟩ to DT but charge_factor 6 vs 2
        # and similar Q per reaction, so the 3x charge factor ratio
        # should push PB11 density much higher
        assert n_e_pb11 > n_e_dt

    def test_unknown_fuel_type_raises(self):
        with pytest.raises((ValueError, KeyError)):
            min_density_for_power(1000, 500, "INVALID")


class TestPeakTemperature:
    """Sanity checks on stored peak temperatures."""

    def test_all_fuel_types_present(self):
        for ft in (FuelType.DT, FuelType.DD, FuelType.DHE3, FuelType.PB11):
            assert ft in PEAK_TEMPERATURE

    def test_values_positive(self):
        for ft, t in PEAK_TEMPERATURE.items():
            assert t > 0, f"Peak temperature must be positive for {ft}"

    def test_dt_lowest(self):
        # DT has the lowest peak ⟨σv⟩ temperature (easiest to ignite)
        assert PEAK_TEMPERATURE[FuelType.DT] < PEAK_TEMPERATURE[FuelType.DD]
        assert PEAK_TEMPERATURE[FuelType.DT] < PEAK_TEMPERATURE[FuelType.DHE3]
        assert PEAK_TEMPERATURE[FuelType.DT] < PEAK_TEMPERATURE[FuelType.PB11]


class TestParticleFactor:
    """Sanity checks on particle factors."""

    def test_all_fuel_types_present(self):
        for ft in (FuelType.DT, FuelType.DD, FuelType.DHE3, FuelType.PB11):
            assert ft in PARTICLE_FACTOR

    def test_values_positive(self):
        for ft, pf in PARTICLE_FACTOR.items():
            assert pf > 0, f"Particle factor must be positive for {ft}"

    def test_dt_equals_dd(self):
        # Both DT and DD have particle_factor = 2
        assert PARTICLE_FACTOR[FuelType.DT] == PARTICLE_FACTOR[FuelType.DD]


class TestRequiredConfinementTime:
    """Test the confinement time calculation."""

    def test_dt_catf(self):
        # CATF: 2600 MW, 215 m³, 50 MW input → τ_E ≈ 0.695 s
        tau_e = required_confinement_time(2600, 215, FuelType.DT, 50)
        assert 0.3 < tau_e < 2.0, f"CATF DT τ_E = {tau_e:.3f} outside expected range"

    def test_dt_iter_like(self):
        # ITER-like: 500 MW, 830 m³, 50 MW heating → τ_E ~ few seconds
        tau_e = required_confinement_time(500, 830, FuelType.DT, 50)
        assert 0.5 < tau_e < 10.0, f"ITER-like τ_E = {tau_e:.3f} outside expected range"

    def test_dd_longer_than_dt(self):
        # DD requires much longer confinement than DT for same power/volume
        tau_dt = required_confinement_time(1000, 500, FuelType.DT, 50)
        tau_dd = required_confinement_time(1000, 500, FuelType.DD, 50)
        assert tau_dd > tau_dt

    def test_more_heating_shorter_tau(self):
        # More external heating → shorter required τ_E
        tau_low = required_confinement_time(1000, 500, FuelType.DT, 50)
        tau_high = required_confinement_time(1000, 500, FuelType.DT, 200)
        assert tau_high < tau_low

    def test_larger_volume_longer_tau(self):
        # Larger volume at same power → more energy to confine, longer τ_E
        # (n_e drops as 1/sqrt(V) but W = n_e*kT*V grows as sqrt(V))
        tau_small = required_confinement_time(1000, 100, FuelType.DT, 50)
        tau_large = required_confinement_time(1000, 1000, FuelType.DT, 50)
        assert tau_large > tau_small

    def test_all_fuel_types_return_positive(self):
        for ft in (FuelType.DT, FuelType.DD, FuelType.DHE3, FuelType.PB11):
            tau_e = required_confinement_time(1000, 500, ft, 50)
            assert tau_e > 0, f"τ_E must be positive for {ft}"

    def test_unknown_fuel_type_raises(self):
        with pytest.raises((ValueError, KeyError)):
            required_confinement_time(1000, 500, "INVALID", 50)
