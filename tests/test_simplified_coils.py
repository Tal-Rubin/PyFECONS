"""Tests for the simplified coil costing model (CAS220103).

Tests cover:
- Geometry factor computation per confinement type
- Conductor quantity scaling (total_kAm)
- Material cost defaults
- Manufacturing markup lookup
- Calibration against known fusion designs
- Validation rules for simplified mode
"""

import math
import warnings

import pytest
import scipy.constants as sc

from pyfecons.costing.mfe.cas22.cas220103_coils import (
    CONFINEMENT_DEFAULTS,
    cas_220103_coils_simplified,
    compute_geometry_factor,
)
from pyfecons.enums import CoilMaterial, ConfinementType, FuelType, FusionMachineType
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.coils import Coils


# ---------------------------------------------------------------------------
# Helper to create a Basic object with a given confinement type
# ---------------------------------------------------------------------------
def _basic(confinement_type=ConfinementType.SPHERICAL_TOKAMAK, **kwargs):
    defaults = dict(
        fusion_machine_type=FusionMachineType.MFE,
        confinement_type=confinement_type,
        fuel_type=FuelType.DT,
        p_nrl=1000,
        n_mod=1,
        construction_time=6,
        plant_lifetime=30,
        plant_availability=0.85,
        yearly_inflation=0.025,
        time_to_replace=10,
    )
    defaults.update(kwargs)
    return Basic(**defaults)


# ---------------------------------------------------------------------------
# Geometry factor tests
# ---------------------------------------------------------------------------
class TestGeometryFactor:
    def test_tokamak_g_equals_4pi_squared(self):
        G = compute_geometry_factor(ConfinementType.SPHERICAL_TOKAMAK, 20, 1.0)
        assert G == pytest.approx(4 * math.pi**2, rel=1e-10)

    def test_conventional_tokamak_same_as_spherical(self):
        G_st = compute_geometry_factor(ConfinementType.SPHERICAL_TOKAMAK, 20, 1.0)
        G_ct = compute_geometry_factor(ConfinementType.CONVENTIONAL_TOKAMAK, 26, 1.0)
        assert G_st == pytest.approx(G_ct)

    def test_tokamak_g_independent_of_n_coils(self):
        G1 = compute_geometry_factor(ConfinementType.SPHERICAL_TOKAMAK, 10, 1.0)
        G2 = compute_geometry_factor(ConfinementType.SPHERICAL_TOKAMAK, 50, 1.0)
        assert G1 == pytest.approx(G2)

    def test_mirror_g_scales_with_n_coils(self):
        G4 = compute_geometry_factor(ConfinementType.MAGNETIC_MIRROR, 4, 1.0)
        G20 = compute_geometry_factor(ConfinementType.MAGNETIC_MIRROR, 20, 1.0)
        assert G4 == pytest.approx(4 * 4 * math.pi)
        assert G20 == pytest.approx(20 * 4 * math.pi)
        assert G20 / G4 == pytest.approx(5.0)

    def test_stellarator_g_includes_path_factor(self):
        G = compute_geometry_factor(ConfinementType.STELLARATOR, 50, 2.0)
        assert G == pytest.approx(4 * math.pi**2 * 2.0, rel=1e-10)

    def test_stellarator_path_factor_1_equals_tokamak(self):
        G_tok = compute_geometry_factor(ConfinementType.SPHERICAL_TOKAMAK, 20, 1.0)
        G_stel = compute_geometry_factor(ConfinementType.STELLARATOR, 50, 1.0)
        assert G_tok == pytest.approx(G_stel)


# ---------------------------------------------------------------------------
# Conductor scaling tests
# ---------------------------------------------------------------------------
class TestConductorScaling:
    def test_doubling_b_doubles_conductor(self):
        coils = Coils(b_max=10, r_coil=1.0)
        basic = _basic()
        r1 = cas_220103_coils_simplified(coils, basic)

        coils2 = Coils(b_max=20, r_coil=1.0)
        r2 = cas_220103_coils_simplified(coils2, basic)

        assert r2.total_kAm == pytest.approx(2 * r1.total_kAm, rel=1e-10)
        assert r2.conductor_cost == pytest.approx(2 * r1.conductor_cost, rel=1e-10)

    def test_doubling_r_quadruples_conductor(self):
        coils = Coils(b_max=10, r_coil=1.0)
        basic = _basic()
        r1 = cas_220103_coils_simplified(coils, basic)

        coils2 = Coils(b_max=10, r_coil=2.0)
        r2 = cas_220103_coils_simplified(coils2, basic)

        assert r2.total_kAm == pytest.approx(4 * r1.total_kAm, rel=1e-10)

    def test_total_cost_equals_conductor_times_markup(self):
        coils = Coils(b_max=12, r_coil=3.0)
        basic = _basic()
        result = cas_220103_coils_simplified(coils, basic)
        assert result.C220103 == pytest.approx(
            result.conductor_cost * result.markup, rel=1e-10
        )


# ---------------------------------------------------------------------------
# Material defaults
# ---------------------------------------------------------------------------
class TestMaterialDefaults:
    def test_rebco_default_50(self):
        assert CoilMaterial.REBCO_HTS.default_cost_per_kAm == 50

    def test_nb3sn_default_7(self):
        assert CoilMaterial.NB3SN.default_cost_per_kAm == 7

    def test_nbti_default_7(self):
        assert CoilMaterial.NBTI.default_cost_per_kAm == 7

    def test_copper_default_1(self):
        assert CoilMaterial.COPPER.default_cost_per_kAm == 1

    def test_material_affects_conductor_cost(self):
        basic = _basic()
        r_rebco = cas_220103_coils_simplified(
            Coils(b_max=10, r_coil=1.0, coil_material=CoilMaterial.REBCO_HTS), basic
        )
        r_nbti = cas_220103_coils_simplified(
            Coils(b_max=10, r_coil=1.0, coil_material=CoilMaterial.NBTI), basic
        )
        # Same kAm, different $/kAm
        assert r_rebco.total_kAm == pytest.approx(r_nbti.total_kAm)
        assert r_rebco.conductor_cost / r_nbti.conductor_cost == pytest.approx(
            50 / 7, rel=1e-10
        )

    def test_custom_cost_per_kAm_overrides_material_default(self):
        basic = _basic()
        result = cas_220103_coils_simplified(
            Coils(
                b_max=10,
                r_coil=1.0,
                coil_material=CoilMaterial.REBCO_HTS,
                cost_per_kAm=25,
            ),
            basic,
        )
        # conductor cost should reflect $25/kAm, not $50/kAm
        expected_kAm = result.total_kAm
        assert result.conductor_cost == pytest.approx(
            expected_kAm * 25 / 1e6, rel=1e-10
        )


# ---------------------------------------------------------------------------
# Markup defaults per confinement type
# ---------------------------------------------------------------------------
class TestMarkupDefaults:
    @pytest.mark.parametrize(
        "ct, expected_markup",
        [
            (ConfinementType.MAGNETIC_MIRROR, 2.5),
            (ConfinementType.SPHERICAL_TOKAMAK, 6),
            (ConfinementType.CONVENTIONAL_TOKAMAK, 8),
            (ConfinementType.STELLARATOR, 12),
        ],
    )
    def test_default_markup(self, ct, expected_markup):
        coils = Coils(b_max=10, r_coil=1.0)
        basic = _basic(confinement_type=ct)
        result = cas_220103_coils_simplified(coils, basic)
        assert result.markup == expected_markup

    def test_custom_markup_overrides_default(self):
        coils = Coils(b_max=10, r_coil=1.0, coil_markup=3.0)
        basic = _basic()
        result = cas_220103_coils_simplified(coils, basic)
        assert result.markup == 3.0


# ---------------------------------------------------------------------------
# Calibration against known designs
# ---------------------------------------------------------------------------
class TestCalibration:
    """Verify conductor cost estimates match expectations from the plan.

    These are order-of-magnitude checks with 10% tolerance.
    Exact values depend on scipy.constants.mu_0.
    """

    def _conductor_cost(self, B, R, confinement_type, material, **kwargs):
        coils = Coils(b_max=B, r_coil=R, coil_material=material, **kwargs)
        basic = _basic(confinement_type=confinement_type)
        result = cas_220103_coils_simplified(coils, basic)
        return result.conductor_cost, result

    def test_sparc_conductor(self):
        """SPARC: B=20T, R=1.85m, REBCO → ~$107M conductor."""
        cost, _ = self._conductor_cost(
            20, 1.85, ConfinementType.SPHERICAL_TOKAMAK, CoilMaterial.REBCO_HTS
        )
        assert cost == pytest.approx(107, rel=0.1)

    def test_sparc_total(self):
        """SPARC: conductor ~$107M × markup 6 → ~$645M total."""
        _, result = self._conductor_cost(
            20, 1.85, ConfinementType.SPHERICAL_TOKAMAK, CoilMaterial.REBCO_HTS
        )
        assert result.C220103 == pytest.approx(645, rel=0.1)

    def test_iter_conductor(self):
        """ITER: B=13T, R=6.2m, Nb3Sn → ~$110M conductor."""
        cost, _ = self._conductor_cost(
            13, 6.2, ConfinementType.CONVENTIONAL_TOKAMAK, CoilMaterial.NB3SN
        )
        assert cost == pytest.approx(110, rel=0.1)

    def test_mirror_4_coils(self):
        """Small mirror: B=10T, R=1.0m, 4 coils, REBCO → ~$20M conductor."""
        cost, _ = self._conductor_cost(
            10,
            1.0,
            ConfinementType.MAGNETIC_MIRROR,
            CoilMaterial.REBCO_HTS,
            n_coils=4,
        )
        assert cost == pytest.approx(20, rel=0.1)

    def test_mirror_20_coils(self):
        """Long mirror: B=10T, R=1.0m, 20 coils → ~$100M conductor."""
        cost, _ = self._conductor_cost(
            10,
            1.0,
            ConfinementType.MAGNETIC_MIRROR,
            CoilMaterial.REBCO_HTS,
            n_coils=20,
        )
        assert cost == pytest.approx(100, rel=0.1)

    def test_w7x_conductor(self):
        """W7-X: B=5T, R=5.5m, NbTi, stellarator → ~$67M conductor."""
        cost, _ = self._conductor_cost(
            5, 5.5, ConfinementType.STELLARATOR, CoilMaterial.NBTI
        )
        assert cost == pytest.approx(67, rel=0.1)


# ---------------------------------------------------------------------------
# Output fields
# ---------------------------------------------------------------------------
class TestOutputFields:
    def test_all_output_fields_populated(self):
        coils = Coils(b_max=12, r_coil=2.0)
        basic = _basic()
        result = cas_220103_coils_simplified(coils, basic)
        assert result.C220103 is not None and result.C220103 > 0
        assert result.conductor_cost is not None and result.conductor_cost > 0
        assert result.total_kAm is not None and result.total_kAm > 0
        assert result.geometry_factor is not None and result.geometry_factor > 0
        assert result.markup is not None and result.markup > 0
        assert result.n_coils is not None and result.n_coils > 0
        assert result.cost_per_coil is not None and result.cost_per_coil > 0
        assert result.coil_material is not None

    def test_cost_per_coil_equals_total_over_n(self):
        coils = Coils(b_max=12, r_coil=2.0)
        basic = _basic()
        result = cas_220103_coils_simplified(coils, basic)
        assert result.cost_per_coil == pytest.approx(
            result.C220103 / result.n_coils, rel=1e-10
        )

    def test_default_material_is_rebco(self):
        coils = Coils(b_max=12, r_coil=2.0)
        basic = _basic()
        result = cas_220103_coils_simplified(coils, basic)
        assert result.coil_material == CoilMaterial.REBCO_HTS


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------
class TestSimplifiedCoilsValidation:
    """Test validation rules for simplified coils mode."""

    def test_missing_both_modes_raises(self):
        """Must provide either magnets or b_max+r_coil."""
        from pyfecons.validation import ValidationResult, _validate_simplified_coils
        from tests.helpers import load_mfe_inputs

        inputs = load_mfe_inputs()
        inputs.coils = Coils()  # no magnets, no b_max/r_coil
        result = ValidationResult()
        _validate_simplified_coils(inputs, FusionMachineType.MFE, result)
        assert len(result.errors) >= 1
        assert any("magnets" in e.constraint for e in result.errors)

    def test_valid_simplified_no_errors(self):
        from pyfecons.validation import ValidationResult, _validate_simplified_coils
        from tests.helpers import load_mfe_inputs

        inputs = load_mfe_inputs()
        inputs.coils = Coils(b_max=18, r_coil=1.85)
        result = ValidationResult()
        _validate_simplified_coils(inputs, FusionMachineType.MFE, result)
        assert len(result.errors) == 0

    def test_negative_b_max_error(self):
        from pyfecons.validation import ValidationResult, _validate_simplified_coils
        from tests.helpers import load_mfe_inputs

        inputs = load_mfe_inputs()
        inputs.coils = Coils(b_max=-5, r_coil=1.85)
        result = ValidationResult()
        _validate_simplified_coils(inputs, FusionMachineType.MFE, result)
        assert any("b_max" in e.field_name for e in result.errors)

    def test_zero_r_coil_error(self):
        from pyfecons.validation import ValidationResult, _validate_simplified_coils
        from tests.helpers import load_mfe_inputs

        inputs = load_mfe_inputs()
        inputs.coils = Coils(b_max=10, r_coil=0)
        result = ValidationResult()
        _validate_simplified_coils(inputs, FusionMachineType.MFE, result)
        assert any("r_coil" in e.field_name for e in result.errors)

    def test_copper_without_p_coils_warns(self):
        from pyfecons.validation import ValidationResult, _validate_cross_field
        from tests.helpers import load_mfe_inputs

        inputs = load_mfe_inputs()
        inputs.coils = Coils(b_max=10, r_coil=1.0, coil_material=CoilMaterial.COPPER)
        inputs.power_input.p_coils = 0
        result = ValidationResult()
        _validate_cross_field(inputs, FusionMachineType.MFE, result)
        assert any("Copper" in w.message for w in result.warnings)
