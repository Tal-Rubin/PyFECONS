"""Tests for the input validation layer."""

import warnings

import pytest
from helpers import load_ife_inputs, load_mfe_inputs

from pyfecons.enums import FuelType, FusionMachineType, MagnetMaterialType, MagnetType
from pyfecons.exceptions import ValidationError
from pyfecons.inputs.all_inputs import AllInputs
from pyfecons.inputs.magnet import Magnet
from pyfecons.units import (
    HZ,
    MW,
    Count,
    Meters,
    Meters2,
    Meters3,
    Percent,
    Ratio,
    Years,
)
from pyfecons.validation import validate_inputs


def _make_test_magnet(**overrides):
    """Create a valid test magnet with optional overrides."""
    defaults = dict(
        name="TF",
        type=MagnetType.TF,
        material_type=MagnetMaterialType.HTS_CICC,
        coil_count=12,
        r_centre=Meters(0.18),
        z_centre=Meters(0),
        dr=Meters(0.25),
        dz=Meters(0.35),
        frac_in=Ratio(0),
        coil_temp=20,
        mfr_factor=5,
    )
    defaults.update(overrides)
    return Magnet(**defaults)


# ---------------------------------------------------------------------------
# Regression: existing customer configs must pass
# ---------------------------------------------------------------------------


class TestExistingInputsPass:
    def test_catf_mfe_passes(self):
        inputs = load_mfe_inputs()
        validate_inputs(inputs)  # should not raise

    def test_catf_ife_passes(self):
        inputs = load_ife_inputs()
        validate_inputs(inputs)  # should not raise


# ---------------------------------------------------------------------------
# Required field validation
# ---------------------------------------------------------------------------


class TestRequiredFields:
    def test_none_basic_rejected(self):
        inputs = AllInputs()
        inputs.basic = None
        with pytest.raises(ValidationError, match="basic"):
            validate_inputs(inputs)

    def test_none_power_input_rejected(self):
        inputs = load_mfe_inputs()
        inputs.power_input = None
        with pytest.raises(ValidationError, match="power_input"):
            validate_inputs(inputs)

    def test_none_coils_rejected_for_mfe(self):
        inputs = load_mfe_inputs()
        inputs.coils = None
        with pytest.raises(ValidationError, match="coils"):
            validate_inputs(inputs)

    def test_none_lasers_rejected_for_ife(self):
        inputs = load_ife_inputs()
        inputs.lasers = None
        with pytest.raises(ValidationError, match="lasers"):
            validate_inputs(inputs)

    def test_none_target_factory_rejected_for_ife(self):
        inputs = load_ife_inputs()
        inputs.target_factory = None
        with pytest.raises(ValidationError, match="target_factory"):
            validate_inputs(inputs)

    def test_none_p_nrl_rejected(self):
        inputs = load_mfe_inputs()
        inputs.basic.p_nrl = None
        with pytest.raises(ValidationError, match="p_nrl"):
            validate_inputs(inputs)

    def test_none_eta_th_rejected(self):
        inputs = load_mfe_inputs()
        inputs.power_input.eta_th = None
        with pytest.raises(ValidationError, match="eta_th"):
            validate_inputs(inputs)

    def test_none_eta_pin_rejected_for_mfe(self):
        inputs = load_mfe_inputs()
        inputs.power_input.eta_pin = None
        with pytest.raises(ValidationError, match="eta_pin"):
            validate_inputs(inputs)


# ---------------------------------------------------------------------------
# Field-level range checks
# ---------------------------------------------------------------------------


class TestFieldRangeChecks:
    def test_negative_power_rejected(self):
        inputs = load_mfe_inputs()
        inputs.basic.p_nrl = MW(-100)
        with pytest.raises(ValidationError, match="p_nrl"):
            validate_inputs(inputs)

    def test_zero_power_rejected(self):
        inputs = load_mfe_inputs()
        inputs.basic.p_nrl = MW(0)
        with pytest.raises(ValidationError, match="p_nrl"):
            validate_inputs(inputs)

    def test_efficiency_over_one_rejected(self):
        inputs = load_mfe_inputs()
        inputs.power_input.eta_th = Percent(1.5)
        with pytest.raises(ValidationError, match="eta_th"):
            validate_inputs(inputs)

    def test_zero_efficiency_rejected(self):
        inputs = load_mfe_inputs()
        inputs.power_input.eta_th = Percent(0)
        with pytest.raises(ValidationError, match="eta_th"):
            validate_inputs(inputs)

    def test_negative_efficiency_rejected(self):
        inputs = load_mfe_inputs()
        inputs.power_input.eta_p = Percent(-0.1)
        with pytest.raises(ValidationError, match="eta_p"):
            validate_inputs(inputs)

    def test_f_sub_over_one_rejected(self):
        inputs = load_mfe_inputs()
        inputs.power_input.f_sub = Percent(1.5)
        with pytest.raises(ValidationError, match="f_sub"):
            validate_inputs(inputs)

    def test_negative_f_sub_rejected(self):
        inputs = load_mfe_inputs()
        inputs.power_input.f_sub = Percent(-0.1)
        with pytest.raises(ValidationError, match="f_sub"):
            validate_inputs(inputs)

    def test_mn_below_one_rejected(self):
        inputs = load_mfe_inputs()
        inputs.power_input.mn = Ratio(0.5)
        with pytest.raises(ValidationError, match="mn"):
            validate_inputs(inputs)

    def test_negative_plant_availability_rejected(self):
        inputs = load_mfe_inputs()
        inputs.basic.plant_availability = Percent(-0.1)
        with pytest.raises(ValidationError, match="plant_availability"):
            validate_inputs(inputs)

    def test_plant_availability_over_one_rejected(self):
        inputs = load_mfe_inputs()
        inputs.basic.plant_availability = Percent(1.5)
        with pytest.raises(ValidationError, match="plant_availability"):
            validate_inputs(inputs)

    def test_negative_downtime_rejected(self):
        inputs = load_mfe_inputs()
        inputs.basic.downtime = Years(-1)
        with pytest.raises(ValidationError, match="downtime"):
            validate_inputs(inputs)

    def test_zero_plant_lifetime_rejected(self):
        inputs = load_mfe_inputs()
        inputs.basic.plant_lifetime = Years(0)
        with pytest.raises(ValidationError, match="plant_lifetime"):
            validate_inputs(inputs)

    def test_negative_inflation_rejected(self):
        inputs = load_mfe_inputs()
        inputs.basic.yearly_inflation = Percent(-0.01)
        with pytest.raises(ValidationError, match="yearly_inflation"):
            validate_inputs(inputs)

    def test_negative_interest_rate_rejected(self):
        inputs = load_mfe_inputs()
        inputs.financial.interest_rate = Ratio(-0.01)
        with pytest.raises(ValidationError, match="interest_rate"):
            validate_inputs(inputs)

    def test_shield_fraction_over_one_rejected(self):
        inputs = load_mfe_inputs()
        inputs.shield.f_SiC = Ratio(1.5)
        with pytest.raises(ValidationError, match="f_SiC"):
            validate_inputs(inputs)

    def test_negative_plasma_thickness_rejected(self):
        inputs = load_mfe_inputs()
        inputs.radial_build.plasma_t = Meters(-0.1)
        with pytest.raises(ValidationError, match="plasma_t"):
            validate_inputs(inputs)

    def test_zero_plasma_thickness_rejected(self):
        inputs = load_mfe_inputs()
        inputs.radial_build.plasma_t = Meters(0)
        with pytest.raises(ValidationError, match="plasma_t"):
            validate_inputs(inputs)

    def test_zero_elon_rejected(self):
        inputs = load_mfe_inputs()
        inputs.radial_build.elon = Ratio(0)
        with pytest.raises(ValidationError, match="elon"):
            validate_inputs(inputs)

    def test_burn_fraction_over_one_rejected(self):
        inputs = load_mfe_inputs()
        inputs.power_input.dd_f_T = Percent(1.5)
        with pytest.raises(ValidationError, match="dd_f_T"):
            validate_inputs(inputs)

    def test_f_dec_over_one_rejected(self):
        inputs = load_mfe_inputs()
        inputs.power_input.f_dec = Percent(1.5)
        with pytest.raises(ValidationError, match="f_dec"):
            validate_inputs(inputs)


# ---------------------------------------------------------------------------
# Magnet validation
# ---------------------------------------------------------------------------


class TestMagnetValidation:
    def test_zero_coil_count_rejected(self):
        inputs = load_mfe_inputs()
        inputs.coils.magnets = [_make_test_magnet(coil_count=0)]
        with pytest.raises(ValidationError, match="coil_count"):
            validate_inputs(inputs)

    def test_negative_radius_rejected(self):
        inputs = load_mfe_inputs()
        inputs.coils.magnets = [_make_test_magnet(r_centre=Meters(-1))]
        with pytest.raises(ValidationError, match="r_centre"):
            validate_inputs(inputs)

    def test_zero_dr_rejected(self):
        inputs = load_mfe_inputs()
        inputs.coils.magnets = [_make_test_magnet(dr=Meters(0))]
        with pytest.raises(ValidationError, match="dr"):
            validate_inputs(inputs)

    def test_frac_in_over_one_rejected(self):
        inputs = load_mfe_inputs()
        inputs.coils.magnets = [_make_test_magnet(frac_in=Ratio(1.5))]
        with pytest.raises(ValidationError, match="frac_in"):
            validate_inputs(inputs)

    def test_zero_mfr_factor_rejected(self):
        inputs = load_mfe_inputs()
        inputs.coils.magnets = [_make_test_magnet(mfr_factor=0)]
        with pytest.raises(ValidationError, match="mfr_factor"):
            validate_inputs(inputs)


# ---------------------------------------------------------------------------
# Cross-field validation
# ---------------------------------------------------------------------------


class TestCrossFieldValidation:
    def test_time_to_replace_exceeds_lifetime(self):
        inputs = load_mfe_inputs()
        inputs.basic.time_to_replace = Years(50)
        inputs.basic.plant_lifetime = Years(30)
        with pytest.raises(ValidationError, match="time_to_replace"):
            validate_inputs(inputs)

    def test_eta_pin_zero_division_by_zero(self):
        inputs = load_mfe_inputs()
        inputs.power_input.eta_pin = Percent(0)
        with pytest.raises(ValidationError, match="eta_pin"):
            validate_inputs(inputs)

    def test_shield_fractions_sum_warning(self):
        inputs = load_mfe_inputs()
        # Set fractions that don't sum to 1
        inputs.shield.f_SiC = Ratio(0.1)
        inputs.shield.FPCPPFbLi = Ratio(0.1)
        inputs.shield.f_W = Ratio(0.1)
        inputs.shield.f_BFS = Ratio(0.1)
        with pytest.warns(UserWarning, match="shield fractions"):
            validate_inputs(inputs)

    def test_dd_fuel_warns_on_missing_burn_fractions(self):
        inputs = load_mfe_inputs()
        inputs.basic.fuel_type = FuelType.DD
        inputs.power_input.dd_f_T = None
        inputs.power_input.dd_f_He3 = None
        with pytest.warns(UserWarning) as record:
            validate_inputs(inputs)
        messages = [str(w.message) for w in record]
        assert any("dd_f_T" in m for m in messages)
        assert any("dd_f_He3" in m for m in messages)

    def test_dhe3_fuel_warns_on_missing_fractions(self):
        inputs = load_mfe_inputs()
        inputs.basic.fuel_type = FuelType.DHE3
        inputs.power_input.dhe3_dd_frac = None
        inputs.power_input.dhe3_f_T = None
        with pytest.warns(UserWarning) as record:
            validate_inputs(inputs)
        messages = [str(w.message) for w in record]
        assert any("dhe3_dd_frac" in m for m in messages)
        assert any("dhe3_f_T" in m for m in messages)


# ---------------------------------------------------------------------------
# Multi-error accumulation
# ---------------------------------------------------------------------------


class TestMultiErrorAccumulation:
    def test_multiple_errors_reported_at_once(self):
        inputs = load_mfe_inputs()
        inputs.basic.p_nrl = MW(-100)
        inputs.basic.plant_lifetime = Years(-5)
        inputs.power_input.eta_th = Percent(2.0)
        with pytest.raises(ValidationError) as exc_info:
            validate_inputs(inputs)
        error = exc_info.value
        assert len(error.errors) >= 3
        field_names = [e.field_name for e in error.errors]
        assert "p_nrl" in field_names
        assert "plant_lifetime" in field_names
        assert "eta_th" in field_names

    def test_error_message_is_readable(self):
        inputs = load_mfe_inputs()
        inputs.basic.p_nrl = MW(-100)
        with pytest.raises(ValidationError) as exc_info:
            validate_inputs(inputs)
        msg = str(exc_info.value)
        assert "p_nrl" in msg
        assert "-100" in msg
        assert "> 0" in msg


# ---------------------------------------------------------------------------
# Warning for unusually high efficiency
# ---------------------------------------------------------------------------


class TestWarnings:
    def test_high_eta_th_warns(self):
        inputs = load_mfe_inputs()
        inputs.power_input.eta_th = Percent(0.70)
        with pytest.warns(UserWarning, match="thermal efficiency"):
            validate_inputs(inputs)

    def test_normal_eta_th_no_warning(self):
        inputs = load_mfe_inputs()
        inputs.power_input.eta_th = Percent(0.46)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            validate_inputs(inputs)  # should not warn


# ---------------------------------------------------------------------------
# Costing sanity checks (Q_sci, p_net, heating mismatch)
# ---------------------------------------------------------------------------


class TestCostingSanityChecks:
    def test_q_sci_below_one_warns(self):
        inputs = load_mfe_inputs()
        # p_nrl < p_input → Q_sci < 1
        inputs.basic.p_nrl = MW(30)
        inputs.power_input.p_input = MW(50)
        with pytest.warns(UserWarning, match="Q_sci.*< 1"):
            validate_inputs(inputs)

    def test_q_sci_above_one_no_warning(self):
        inputs = load_mfe_inputs()
        # Q_sci = 2600/50 = 52 >> 1
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            validate_inputs(inputs)

    def test_p_net_nonpositive_warns(self):
        inputs = load_mfe_inputs()
        # Very low fusion power with high recirculating → p_net <= 0
        inputs.basic.p_nrl = MW(100)
        inputs.power_input.p_input = MW(50)
        with pytest.warns(UserWarning, match="p_net.*non-positive"):
            validate_inputs(inputs)

    def test_p_net_positive_no_warning(self):
        inputs = load_mfe_inputs()
        # CATF defaults: p_nrl=2600, p_input=50 → large positive p_net
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            validate_inputs(inputs)

    def test_heating_mismatch_warns(self):
        inputs = load_mfe_inputs()
        from pyfecons.inputs.supplementary_heating import SupplementaryHeating

        inputs.supplementary_heating = SupplementaryHeating(
            nbi_power=MW(30), icrf_power=MW(10)
        )
        # Total heating = 40 MW, p_input = 50 MW → mismatch of 10 MW
        with pytest.warns(UserWarning, match="differs from p_input"):
            validate_inputs(inputs)

    def test_heating_match_no_warning(self):
        inputs = load_mfe_inputs()
        from pyfecons.inputs.supplementary_heating import SupplementaryHeating

        inputs.supplementary_heating = SupplementaryHeating(
            nbi_power=MW(40), icrf_power=MW(10)
        )
        # Total = 50 MW = p_input → no mismatch
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            validate_inputs(inputs)

    def test_no_supplementary_heating_no_mismatch_warning(self):
        inputs = load_mfe_inputs()
        inputs.supplementary_heating = None
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            validate_inputs(inputs)


# ---------------------------------------------------------------------------
# Physics feasibility checks (density, wall loading, heat flux)
# ---------------------------------------------------------------------------


class TestPhysicsFeasibilityChecks:
    def test_catf_defaults_with_areas_no_warning(self):
        """CATF MFE with plausible areas/volume should pass all physics checks."""
        inputs = load_mfe_inputs()
        # CATF now includes plasma_volume=215, first_wall_area=426, divertor_area=50
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            validate_inputs(inputs)

    def test_density_warning_tiny_volume(self):
        """Tiny plasma volume with high power → unreasonable density."""
        inputs = load_mfe_inputs()
        inputs.radial_build.plasma_volume = Meters3(1)  # 1 m³ for 2600 MW
        with pytest.warns(UserWarning, match="electron_density.*exceeds"):
            validate_inputs(inputs)

    def test_density_no_warning_without_volume(self):
        """When plasma_volume is None, density check is skipped."""
        inputs = load_mfe_inputs()
        inputs.radial_build.plasma_volume = None
        inputs.radial_build.first_wall_area = None
        inputs.radial_build.divertor_area = None
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            validate_inputs(inputs)

    def test_wall_loading_warning_small_area(self):
        """Small first wall area with high power → excessive wall loading."""
        inputs = load_mfe_inputs()
        inputs.radial_build.first_wall_area = Meters2(10)  # 10 m² for 2600 MW
        inputs.radial_build.plasma_volume = None  # avoid density warning
        inputs.radial_build.divertor_area = None
        with pytest.warns(UserWarning, match="wall_loading.*exceeds"):
            validate_inputs(inputs)

    def test_wall_loading_no_warning_without_area(self):
        """When first_wall_area is None, wall loading check is skipped."""
        inputs = load_mfe_inputs()
        inputs.radial_build.first_wall_area = None
        inputs.radial_build.plasma_volume = None
        inputs.radial_build.divertor_area = None
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            validate_inputs(inputs)

    def test_heat_flux_warning_small_divertor(self):
        """Small divertor area with high power → excessive heat flux."""
        inputs = load_mfe_inputs()
        inputs.radial_build.divertor_area = Meters2(1)  # 1 m² for 2600 MW
        inputs.radial_build.plasma_volume = None  # avoid density warning
        inputs.radial_build.first_wall_area = None
        with pytest.warns(UserWarning, match="divertor_heat_flux.*exceeds"):
            validate_inputs(inputs)

    def test_heat_flux_no_warning_without_area(self):
        """When divertor_area is None, heat flux check is skipped."""
        inputs = load_mfe_inputs()
        inputs.radial_build.divertor_area = None
        inputs.radial_build.plasma_volume = None
        inputs.radial_build.first_wall_area = None
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            validate_inputs(inputs)

    def test_pb11_no_wall_loading_warning(self):
        """PB11 is aneutronic — wall loading should be ~0 regardless of area."""
        inputs = load_mfe_inputs()
        inputs.basic.fuel_type = FuelType.PB11
        inputs.radial_build.first_wall_area = Meters2(10)  # tiny area
        inputs.radial_build.plasma_volume = None
        inputs.radial_build.divertor_area = None
        # PB11 has zero neutrons → wall loading = 0 → no warning
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            validate_inputs(inputs)

    def test_confinement_time_no_warning_catf(self):
        """CATF DT baseline: τ_E ≈ 0.7 s, well under 30s threshold."""
        inputs = load_mfe_inputs()
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            validate_inputs(inputs)

    def test_confinement_time_warning_extreme(self):
        """PB11 at 300 keV stores 20x more energy per particle than DT at 15 keV.
        Large volume + high T → τ_E > 30 s.
        PB11, 2600 MW, 10000 m³ → τ_E ≈ 51 s > 30 s threshold.
        """
        inputs = load_mfe_inputs()
        inputs.basic.fuel_type = FuelType.PB11
        inputs.radial_build.plasma_volume = Meters3(10000)
        inputs.radial_build.first_wall_area = None
        inputs.radial_build.divertor_area = None
        with pytest.warns(UserWarning, match="confinement_time.*exceeds"):
            validate_inputs(inputs)

    def test_confinement_time_no_warning_without_volume(self):
        """When plasma_volume is None, confinement time check is skipped."""
        inputs = load_mfe_inputs()
        inputs.radial_build.plasma_volume = None
        inputs.radial_build.first_wall_area = None
        inputs.radial_build.divertor_area = None
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            validate_inputs(inputs)
