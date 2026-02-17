"""Enhanced tests for CAS 22.1.1 reactor equipment — first wall, blanket, and neutron multiplier costs.

The existing test_cas220101_cost_functions.py covers total cost integration.
These tests exercise individual cost components, fuel type variations, and volume calculations.
"""

import pytest

from pyfecons.costing.calculations.cas22.cas220101_reactor_equipment import (
    compute_blanket_costs,
    compute_first_wall_costs,
    compute_inner_radii,
    compute_material_cost,
    compute_neutron_multiplier_costs,
    compute_outer_radii,
    compute_reactor_equipment_costs,
    compute_volume_ife,
    compute_volume_mfe_mirror,
    compute_volume_mfe_tokamak,
)
from pyfecons.costing.categories.cas220101 import CAS220101
from pyfecons.enums import (
    BlanketFirstWall,
    BlanketNeutronMultiplier,
    BlanketPrimaryCoolant,
    BlanketSecondaryCoolant,
    BlanketStructure,
    BlanketType,
    ConfinementType,
    FuelType,
    FusionMachineType,
)
from pyfecons.inputs.blanket import Blanket
from pyfecons.inputs.radial_build import RadialBuild
from pyfecons.materials import Materials
from pyfecons.units import M_USD, Meters, Meters3, Ratio

materials = Materials()


# ── Helpers ──────────────────────────────────────────────────────────────


def _make_blanket(
    first_wall=BlanketFirstWall.TUNGSTEN,
    blanket_type=BlanketType.SOLID_FIRST_WALL_WITH_A_LIQUID_BREEDER,
    neutron_multiplier=BlanketNeutronMultiplier.NONE,
):
    return Blanket(
        first_wall=first_wall,
        blanket_type=blanket_type,
        primary_coolant=BlanketPrimaryCoolant.DUAL_COOLANT_PBLI_AND_HE,
        secondary_coolant=BlanketSecondaryCoolant.LITHIUM_LI,
        neutron_multiplier=neutron_multiplier,
        structure=BlanketStructure.STAINLESS_STEEL_SS,
    )


def _make_radial_build_tokamak():
    return RadialBuild(
        elon=Ratio(3),
        axis_t=Meters(3),
        plasma_t=Meters(1.1),
        vacuum_t=Meters(0.1),
        firstwall_t=Meters(0.2),
        blanket1_t=Meters(0.8),
        reflector_t=Meters(0.2),
        ht_shield_t=Meters(0.2),
        structure_t=Meters(0.2),
        gap1_t=Meters(0.5),
        vessel_t=Meters(0.2),
        coil_t=Meters(0.25),
        gap2_t=Meters(0.5),
        lt_shield_t=Meters(0.3),
        bioshield_t=Meters(1),
    )


def _make_radial_build_mirror():
    return RadialBuild(
        chamber_length=Meters(12),
        axis_t=Meters(0),
        plasma_t=Meters(4.9),
        vacuum_t=Meters(0.1),
        firstwall_t=Meters(0.1),
        blanket1_t=Meters(1),
        reflector_t=Meters(0.1),
        ht_shield_t=Meters(0.25),
        structure_t=Meters(0.2),
        gap1_t=Meters(0.5),
        vessel_t=Meters(0.2),
        coil_t=Meters(1.76),
        gap2_t=Meters(1),
        lt_shield_t=Meters(0.3),
        bioshield_t=Meters(1),
    )


def _cas_with_volumes(firstwall_vol=10.0, blanket1_vol=50.0):
    """Create a CAS220101 with preset volumes for cost-function unit tests."""
    cas = CAS220101()
    cas.firstwall_vol = Meters3(firstwall_vol)
    cas.blanket1_vol = Meters3(blanket1_vol)
    return cas


# ── First Wall Cost Tests ────────────────────────────────────────────────


class TestFirstWallCosts:
    """Tests for compute_first_wall_costs — material selection by fuel type."""

    def test_dt_tungsten_first_wall(self):
        blanket = _make_blanket(first_wall=BlanketFirstWall.TUNGSTEN)
        cas = _cas_with_volumes(firstwall_vol=10.0)
        cost = compute_first_wall_costs(FuelType.DT, blanket, cas)
        expected = compute_material_cost(cas.firstwall_vol, materials.W)
        assert float(cost) == pytest.approx(float(expected), rel=1e-10)

    def test_dt_beryllium_first_wall(self):
        blanket = _make_blanket(first_wall=BlanketFirstWall.BERYLLIUM)
        cas = _cas_with_volumes(firstwall_vol=10.0)
        cost = compute_first_wall_costs(FuelType.DT, blanket, cas)
        expected = compute_material_cost(cas.firstwall_vol, materials.Be)
        assert float(cost) == pytest.approx(float(expected), rel=1e-10)

    def test_dt_liquid_lithium_first_wall(self):
        blanket = _make_blanket(first_wall=BlanketFirstWall.LIQUID_LITHIUM)
        cas = _cas_with_volumes(firstwall_vol=10.0)
        cost = compute_first_wall_costs(FuelType.DT, blanket, cas)
        expected = compute_material_cost(cas.firstwall_vol, materials.Li)
        assert float(cost) == pytest.approx(float(expected), rel=1e-10)

    def test_dt_flibe_first_wall(self):
        blanket = _make_blanket(first_wall=BlanketFirstWall.FLIBE)
        cas = _cas_with_volumes(firstwall_vol=10.0)
        cost = compute_first_wall_costs(FuelType.DT, blanket, cas)
        expected = compute_material_cost(cas.firstwall_vol, materials.FliBe)
        assert float(cost) == pytest.approx(float(expected), rel=1e-10)

    def test_dd_uses_tungsten(self):
        """D-D always uses tungsten regardless of blanket.first_wall setting."""
        blanket = _make_blanket(first_wall=BlanketFirstWall.BERYLLIUM)
        cas = _cas_with_volumes(firstwall_vol=10.0)
        cost = compute_first_wall_costs(FuelType.DD, blanket, cas)
        expected = compute_material_cost(cas.firstwall_vol, materials.W)
        assert float(cost) == pytest.approx(float(expected), rel=1e-10)

    def test_dhe3_uses_ferritic_steel(self):
        """D-He3 uses ferritic steel (aneutronic)."""
        blanket = _make_blanket()
        cas = _cas_with_volumes(firstwall_vol=10.0)
        cost = compute_first_wall_costs(FuelType.DHE3, blanket, cas)
        expected = compute_material_cost(cas.firstwall_vol, materials.FS)
        assert float(cost) == pytest.approx(float(expected), rel=1e-10)

    def test_pb11_uses_ferritic_steel(self):
        """p-B11 uses ferritic steel (aneutronic)."""
        blanket = _make_blanket()
        cas = _cas_with_volumes(firstwall_vol=10.0)
        cost = compute_first_wall_costs(FuelType.PB11, blanket, cas)
        expected = compute_material_cost(cas.firstwall_vol, materials.FS)
        assert float(cost) == pytest.approx(float(expected), rel=1e-10)

    def test_aneutronic_cheaper_than_dt(self):
        """Aneutronic fuels should have cheaper first wall than D-T tungsten."""
        cas = _cas_with_volumes(firstwall_vol=10.0)
        blanket = _make_blanket(first_wall=BlanketFirstWall.TUNGSTEN)
        dt_cost = compute_first_wall_costs(FuelType.DT, blanket, cas)
        dhe3_cost = compute_first_wall_costs(FuelType.DHE3, blanket, cas)
        assert float(dhe3_cost) < float(dt_cost)

    def test_zero_volume_gives_zero_cost(self):
        cas = _cas_with_volumes(firstwall_vol=0.0)
        blanket = _make_blanket(first_wall=BlanketFirstWall.TUNGSTEN)
        cost = compute_first_wall_costs(FuelType.DT, blanket, cas)
        assert float(cost) == pytest.approx(0.0, abs=1e-10)

    def test_cost_scales_with_volume(self):
        blanket = _make_blanket(first_wall=BlanketFirstWall.TUNGSTEN)
        cas_small = _cas_with_volumes(firstwall_vol=5.0)
        cas_big = _cas_with_volumes(firstwall_vol=10.0)
        cost_small = compute_first_wall_costs(FuelType.DT, blanket, cas_small)
        cost_big = compute_first_wall_costs(FuelType.DT, blanket, cas_big)
        assert float(cost_big) == pytest.approx(2.0 * float(cost_small), rel=1e-10)


# ── Blanket Cost Tests ───────────────────────────────────────────────────


class TestBlanketCosts:
    """Tests for compute_blanket_costs — tritium breeding blanket (DT only)."""

    def test_non_dt_blanket_is_zero(self):
        """All non-DT fuels have zero blanket cost."""
        cas = _cas_with_volumes(blanket1_vol=50.0)
        blanket = _make_blanket()
        for fuel in (FuelType.DD, FuelType.DHE3, FuelType.PB11):
            cost = compute_blanket_costs(fuel, blanket, cas)
            assert float(cost) == pytest.approx(
                0.0, abs=1e-10
            ), f"Expected zero for {fuel}"

    def test_dt_liquid_breeder_uses_lithium(self):
        blanket = _make_blanket(
            blanket_type=BlanketType.SOLID_FIRST_WALL_WITH_A_LIQUID_BREEDER
        )
        cas = _cas_with_volumes(blanket1_vol=50.0)
        cost = compute_blanket_costs(FuelType.DT, blanket, cas)
        expected = compute_material_cost(cas.blanket1_vol, materials.Li)
        assert float(cost) == pytest.approx(float(expected), rel=1e-10)

    def test_dt_flowing_liquid_uses_lithium(self):
        blanket = _make_blanket(blanket_type=BlanketType.FLOWING_LIQUID_FIRST_WALL)
        cas = _cas_with_volumes(blanket1_vol=50.0)
        cost = compute_blanket_costs(FuelType.DT, blanket, cas)
        expected = compute_material_cost(cas.blanket1_vol, materials.Li)
        assert float(cost) == pytest.approx(float(expected), rel=1e-10)

    def test_dt_solid_breeder_li4sio4(self):
        blanket = _make_blanket(
            blanket_type=BlanketType.SOLID_FIRST_WALL_WITH_A_SOLID_BREEDER_LI4SIO4,
        )
        cas = _cas_with_volumes(blanket1_vol=50.0)
        cost = compute_blanket_costs(FuelType.DT, blanket, cas)
        expected = compute_material_cost(cas.blanket1_vol, materials.Li4SiO4)
        assert float(cost) == pytest.approx(float(expected), rel=1e-10)

    def test_dt_solid_breeder_li2tio3(self):
        blanket = _make_blanket(
            blanket_type=BlanketType.SOLID_FIRST_WALL_WITH_A_SOLID_BREEDER_LI2TIO3,
        )
        cas = _cas_with_volumes(blanket1_vol=50.0)
        cost = compute_blanket_costs(FuelType.DT, blanket, cas)
        expected = compute_material_cost(cas.blanket1_vol, materials.Li2TiO3)
        assert float(cost) == pytest.approx(float(expected), rel=1e-10)

    def test_dt_aneutronic_blanket_is_zero(self):
        """SOLID_FIRST_WALL_NO_BREEDER is allowed for DT and returns zero."""
        blanket = _make_blanket(
            blanket_type=BlanketType.SOLID_FIRST_WALL_NO_BREEDER_ANEUTRONIC_FUEL,
        )
        cas = _cas_with_volumes(blanket1_vol=50.0)
        cost = compute_blanket_costs(FuelType.DT, blanket, cas)
        assert float(cost) == pytest.approx(0.0, abs=1e-10)


# ── Neutron Multiplier Cost Tests ────────────────────────────────────────


class TestNeutronMultiplierCosts:
    """Tests for compute_neutron_multiplier_costs — 7.5% of blanket cost, DT only."""

    def test_dt_with_be_multiplier(self):
        blanket_cost = M_USD(100.0)
        blanket = _make_blanket(neutron_multiplier=BlanketNeutronMultiplier.BE)
        cost = compute_neutron_multiplier_costs(FuelType.DT, blanket, blanket_cost)
        assert float(cost) == pytest.approx(7.5, rel=1e-10)

    def test_dt_with_pb_multiplier(self):
        blanket_cost = M_USD(100.0)
        blanket = _make_blanket(neutron_multiplier=BlanketNeutronMultiplier.PB)
        cost = compute_neutron_multiplier_costs(FuelType.DT, blanket, blanket_cost)
        assert float(cost) == pytest.approx(7.5, rel=1e-10)

    def test_dt_with_none_multiplier_is_zero(self):
        blanket_cost = M_USD(100.0)
        blanket = _make_blanket(neutron_multiplier=BlanketNeutronMultiplier.NONE)
        cost = compute_neutron_multiplier_costs(FuelType.DT, blanket, blanket_cost)
        assert float(cost) == pytest.approx(0.0, abs=1e-10)

    def test_non_dt_always_zero(self):
        blanket_cost = M_USD(100.0)
        blanket = _make_blanket(neutron_multiplier=BlanketNeutronMultiplier.BE)
        for fuel in (FuelType.DD, FuelType.DHE3, FuelType.PB11):
            cost = compute_neutron_multiplier_costs(fuel, blanket, blanket_cost)
            assert float(cost) == pytest.approx(
                0.0, abs=1e-10
            ), f"Expected zero for {fuel}"

    def test_multiplier_scales_with_blanket_cost(self):
        blanket = _make_blanket(neutron_multiplier=BlanketNeutronMultiplier.PB)
        c1 = compute_neutron_multiplier_costs(FuelType.DT, blanket, M_USD(200.0))
        c2 = compute_neutron_multiplier_costs(FuelType.DT, blanket, M_USD(100.0))
        assert float(c1) == pytest.approx(2.0 * float(c2), rel=1e-10)


# ── Radial Build / Volume Tests ──────────────────────────────────────────


class TestRadialBuild:
    """Tests for compute_inner_radii, compute_outer_radii, and volume computations."""

    def test_inner_radii_cumulative(self):
        """Inner radii should be cumulative sums of thicknesses."""
        rb = _make_radial_build_tokamak()
        cas = CAS220101()
        cas = compute_inner_radii(FusionMachineType.MFE, rb, cas)
        # plasma_ir = axis_t = 3
        assert cas.plasma_ir == pytest.approx(3.0)
        # vacuum_ir = plasma_t + plasma_ir = 1.1 + 3 = 4.1
        assert cas.vacuum_ir == pytest.approx(4.1)
        # firstwall_ir = vacuum_t + vacuum_ir = 0.1 + 4.1 = 4.2
        assert cas.firstwall_ir == pytest.approx(4.2)
        # blanket1_ir = firstwall_ir + firstwall_t = 4.2 + 0.2 = 4.4
        assert cas.blanket1_ir == pytest.approx(4.4)

    def test_outer_radii_equals_ir_plus_thickness(self):
        """Each outer radius should equal its inner radius + thickness."""
        rb = _make_radial_build_tokamak()
        cas = CAS220101()
        cas = compute_inner_radii(FusionMachineType.MFE, rb, cas)
        cas = compute_outer_radii(FusionMachineType.MFE, rb, cas)
        assert cas.firstwall_or == pytest.approx(cas.firstwall_ir + rb.firstwall_t)
        assert cas.blanket1_or == pytest.approx(cas.blanket1_ir + rb.blanket1_t)
        assert cas.vessel_or == pytest.approx(cas.vessel_ir + rb.vessel_t)

    def test_tokamak_volumes_positive(self):
        """All tokamak component volumes should be non-negative."""
        rb = _make_radial_build_tokamak()
        cas = CAS220101()
        cas = compute_inner_radii(FusionMachineType.MFE, rb, cas)
        cas = compute_outer_radii(FusionMachineType.MFE, rb, cas)
        cas = compute_volume_mfe_tokamak(rb, cas)
        assert cas.firstwall_vol >= 0
        assert cas.blanket1_vol >= 0
        assert cas.ht_shield_vol >= 0
        assert cas.vessel_vol >= 0

    def test_mirror_volumes_positive(self):
        """All mirror component volumes should be non-negative."""
        rb = _make_radial_build_mirror()
        cas = CAS220101()
        cas = compute_inner_radii(FusionMachineType.MFE, rb, cas)
        cas = compute_outer_radii(FusionMachineType.MFE, rb, cas)
        cas = compute_volume_mfe_mirror(rb, cas)
        assert cas.firstwall_vol >= 0
        assert cas.blanket1_vol >= 0
        assert cas.ht_shield_vol >= 0
        assert cas.vessel_vol >= 0

    def test_mfe_has_coil_ir(self):
        """MFE radial build should set coil_ir between lt_shield and gap2."""
        rb = _make_radial_build_tokamak()
        cas = CAS220101()
        cas = compute_inner_radii(FusionMachineType.MFE, rb, cas)
        assert cas.coil_ir == pytest.approx(cas.lt_shield_ir + rb.lt_shield_t)
        assert cas.gap2_ir == pytest.approx(cas.coil_ir + rb.coil_t)

    def test_ife_no_coil_ir(self):
        """IFE radial build should skip coil_ir (gap2 follows lt_shield directly)."""
        rb = _make_radial_build_tokamak()  # reusing; IFE just needs the thicknesses
        cas = CAS220101()
        cas = compute_inner_radii(FusionMachineType.IFE, rb, cas)
        assert cas.gap2_ir == pytest.approx(cas.lt_shield_ir + rb.lt_shield_t)


# ── Integration: Total Cost ─────────────────────────────────────────────


class TestReactorEquipmentIntegration:
    """Integration tests for compute_reactor_equipment_costs: total = fw + blanket + nm."""

    def test_total_equals_sum_of_components(self):
        rb = _make_radial_build_tokamak()
        blanket = _make_blanket(
            first_wall=BlanketFirstWall.TUNGSTEN,
            blanket_type=BlanketType.SOLID_FIRST_WALL_WITH_A_LIQUID_BREEDER,
            neutron_multiplier=BlanketNeutronMultiplier.BE,
        )
        cas = compute_reactor_equipment_costs(
            FusionMachineType.MFE,
            ConfinementType.SPHERICAL_TOKAMAK,
            FuelType.DT,
            blanket,
            rb,
        )
        total = float(cas.C22010101) + float(cas.C22010102) + float(cas.C22010103)
        assert float(cas.C220101) == pytest.approx(total, rel=1e-10)

    def test_aneutronic_no_blanket_no_multiplier(self):
        """D-He3 should have zero blanket and neutron multiplier costs."""
        rb = _make_radial_build_tokamak()
        blanket = _make_blanket(neutron_multiplier=BlanketNeutronMultiplier.BE)
        cas = compute_reactor_equipment_costs(
            FusionMachineType.MFE,
            ConfinementType.SPHERICAL_TOKAMAK,
            FuelType.DHE3,
            blanket,
            rb,
        )
        assert float(cas.C22010102) == pytest.approx(0.0, abs=1e-10)
        assert float(cas.C22010103) == pytest.approx(0.0, abs=1e-10)
        # Total should equal first wall only
        assert float(cas.C220101) == pytest.approx(float(cas.C22010101), rel=1e-10)

    def test_mirror_vs_tokamak_different_costs(self):
        """Mirror and tokamak geometries produce different total costs."""
        blanket = _make_blanket()
        rb_tok = _make_radial_build_tokamak()
        rb_mir = _make_radial_build_mirror()
        cas_tok = compute_reactor_equipment_costs(
            FusionMachineType.MFE,
            ConfinementType.SPHERICAL_TOKAMAK,
            FuelType.DT,
            blanket,
            rb_tok,
        )
        cas_mir = compute_reactor_equipment_costs(
            FusionMachineType.MFE,
            ConfinementType.MAGNETIC_MIRROR,
            FuelType.DT,
            blanket,
            rb_mir,
        )
        assert float(cas_tok.C220101) != pytest.approx(float(cas_mir.C220101), rel=0.01)

    def test_unsupported_machine_type_raises(self):
        rb = _make_radial_build_tokamak()
        blanket = _make_blanket()
        with pytest.raises(ValueError, match="Unsupported reactor type"):
            compute_reactor_equipment_costs(
                FusionMachineType.MIF,
                ConfinementType.SPHERICAL_TOKAMAK,
                FuelType.DT,
                blanket,
                rb,
            )
