# placeholder file to test the testing capability

import pytest

from pyfecons import compute_cas22_reactor_equipment_total_cost
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
from pyfecons.units import Meters, Ratio


def test_mfe_tokamak_cas220101_total_cost():
    blanket = Blanket(
        BlanketFirstWall.BERYLLIUM,
        BlanketType.SOLID_FIRST_WALL_WITH_A_SOLID_BREEDER_LI4SIO4,
        BlanketPrimaryCoolant.DUAL_COOLANT_PBLI_AND_HE,
        BlanketSecondaryCoolant.LITHIUM_LI,
        BlanketNeutronMultiplier.NONE,
        BlanketStructure.STAINLESS_STEEL_SS,
    )
    radial_build = RadialBuild(
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
    result_cost = compute_cas22_reactor_equipment_total_cost(
        fusion_machine_type=FusionMachineType.MFE,
        confinement_type=ConfinementType.SPHERICAL_TOKAMAK,
        fuel_type=FuelType.DT,
        radial_build=radial_build,
        blanket=blanket,
    )
    # Expected value updated 2026-02-09 after Beryllium cost correction
    # (c_raw changed from $5,750 to $900/kg per market research)
    expected_result_cost = 463.88
    assert pytest.approx(result_cost, rel=1e-2) == expected_result_cost


def test_mfe_mirror_cas220101_total_cost():
    blanket = Blanket(
        BlanketFirstWall.BERYLLIUM,
        BlanketType.SOLID_FIRST_WALL_WITH_A_SOLID_BREEDER_LI4SIO4,
        BlanketPrimaryCoolant.DUAL_COOLANT_PBLI_AND_HE,
        BlanketSecondaryCoolant.LITHIUM_LI,
        BlanketNeutronMultiplier.NONE,
        BlanketStructure.STAINLESS_STEEL_SS,
    )
    radial_build = RadialBuild(
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
    result_cost = compute_cas22_reactor_equipment_total_cost(
        FusionMachineType.MFE,
        ConfinementType.MAGNETIC_MIRROR,
        FuelType.DT,
        blanket,
        radial_build,
    )
    # Expected value updated 2026-02-09 after Beryllium cost correction
    # (c_raw changed from $5,750 to $900/kg per market research)
    expected_result_cost = 192.21
    assert pytest.approx(result_cost, rel=1e-2) == expected_result_cost


def test_mfe_mirror_minimal_cas220101_total_cost():
    blanket = Blanket(
        BlanketFirstWall.BERYLLIUM,
        BlanketType.SOLID_FIRST_WALL_NO_BREEDER_ANEUTRONIC_FUEL,
        BlanketPrimaryCoolant.FLIBE,
        BlanketSecondaryCoolant.WATER,
        BlanketNeutronMultiplier.PB,
        BlanketStructure.OXIDE_DISPERSION_STRENGTHENED_ODS_STEEL,
    )
    radial_build = RadialBuild(
        chamber_length=Meters(10),
        axis_t=Meters(1),
        plasma_t=Meters(3),
        vacuum_t=Meters(0.2),
        firstwall_t=Meters(0.01),
        blanket1_t=Meters(1),
        reflector_t=Meters(0),
        ht_shield_t=Meters(0),
        structure_t=Meters(0),
        gap1_t=Meters(0),
        vessel_t=Meters(0),
        coil_t=Meters(0),
        gap2_t=Meters(0),
        lt_shield_t=Meters(0),
        bioshield_t=Meters(0),
    )
    result_cost = compute_cas22_reactor_equipment_total_cost(
        FusionMachineType.MFE,
        ConfinementType.MAGNETIC_MIRROR,
        FuelType.DT,
        blanket,
        radial_build,
    )
    # Expected value updated 2026-02-09 after Beryllium cost correction
    # (c_raw changed from $5,750 to $900/kg per market research)
    expected_result_cost = 13.20
    assert pytest.approx(result_cost, rel=1e-2) == expected_result_cost
