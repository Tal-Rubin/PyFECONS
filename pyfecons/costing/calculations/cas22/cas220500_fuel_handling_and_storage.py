from pyfecons.costing.accounting.power_table import PowerTable
from pyfecons.costing.calculations.conversions import inflation_2010_2024
from pyfecons.costing.categories.cas220500 import CAS2205
from pyfecons.enums import FuelType
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.costing_constants import CostingConstants
from pyfecons.inputs.fuel_handling import FuelHandling
from pyfecons.units import M_USD


def cas_2205_fuel_handling_and_storage_costs(
    basic: Basic,
    fuel_handling: FuelHandling,
    power_table: PowerTable,
    constants: CostingConstants = None,
) -> CAS2205:
    # Cost Category 22.5 Fuel Handling and Storage
    cas2205 = CAS2205()
    cas2205 = compute_fuel_handling_and_storage_costs(fuel_handling, cas2205)
    cas2205 = compute_tritium_containment_costs(basic, power_table, cas2205)
    cas2205 = compute_pellet_injector_costs(basic, fuel_handling, constants, cas2205)
    return cas2205


def compute_fuel_handling_and_storage_costs(IN: FuelHandling, OUT: CAS2205) -> CAS2205:
    # ITER values from: Waganer, L., 2013. ARIES Cost Account Documentation. [pdf] San Diego: University of California,
    #   San Diego. Available at: https://cer.ucsd.edu/_files/publications/UCSD-CER-13-01.pdf  Pge 90.
    OUT.C2205010ITER = M_USD(20.465 * inflation_2010_2024)
    OUT.C2205020ITER = M_USD(7 * inflation_2010_2024)
    OUT.C2205030ITER = M_USD(22.511 * inflation_2010_2024)
    OUT.C2205040ITER = M_USD(9.76 * inflation_2010_2024)
    OUT.C2205050ITER = M_USD(22.826 * inflation_2010_2024)
    OUT.C2205060ITER = M_USD(47.542 * inflation_2010_2024)

    # ITER inflation cost
    OUT.C22050ITER = M_USD(
        OUT.C2205010ITER
        + OUT.C2205020ITER
        + OUT.C2205030ITER
        + OUT.C2205040ITER
        + OUT.C2205050ITER
        + OUT.C2205060ITER
    )
    OUT.C220501 = M_USD(OUT.C2205010ITER * IN.learning_tenth_of_a_kind)
    OUT.C220502 = M_USD(OUT.C2205020ITER * IN.learning_tenth_of_a_kind)
    OUT.C220503 = M_USD(OUT.C2205030ITER * IN.learning_tenth_of_a_kind)
    OUT.C220504 = M_USD(OUT.C2205040ITER * IN.learning_tenth_of_a_kind)
    OUT.C220505 = M_USD(OUT.C2205050ITER * IN.learning_tenth_of_a_kind)
    OUT.C220506 = M_USD(OUT.C2205060ITER * IN.learning_tenth_of_a_kind)
    # ITER inflation cost
    OUT.C220500 = M_USD(
        OUT.C220501
        + OUT.C220502
        + OUT.C220503
        + OUT.C220504
        + OUT.C220505
        + OUT.C220506
        # Note: C220507 (tritium containment) will be added separately
        # in compute_tritium_containment_costs() and aggregated there
    )
    return OUT


def compute_tritium_containment_costs(
    basic: Basic, power_table: PowerTable, OUT: CAS2205
) -> CAS2205:
    """Calculate tritium containment barrier costs (D-T primary, D-D secondary)

    Multiple confinement barriers are required for D-T and D-D fusion to prevent
    environmental tritium release. This is a major regulatory compliance requirement.

    Tritium permeation through hot steel structures is a significant challenge
    requiring specialized containment systems, seals, and membranes.

    Cost scaling:
    - D-T: $200M base for 1 GWe, scaling exponent 0.7 (full containment)
    - D-D: $20M base for 1 GWe, scaling exponent 0.7 (reduced, ~10% of D-T)
    - Other fuels: $0 (no tritium handling)

    Reference: Comprehensive Fusion Reactor Subsystems Framework (2026-02-08)
    """
    electric_gwe = power_table.p_net / 1000  # Convert MW to GWe

    if basic.fuel_type == FuelType.DT:
        # Full tritium containment for D-T fusion
        containment_base_cost = 200.0  # M_USD
        scaling_exponent = 0.7
        scaling_factor = (electric_gwe / 1.0) ** scaling_exponent
        OUT.C220507 = M_USD(containment_base_cost * scaling_factor)
    elif basic.fuel_type == FuelType.DD:
        # Reduced containment for in-situ bred tritium (~10% of D-T requirements)
        containment_base_cost = 20.0  # M_USD
        scaling_exponent = 0.7
        scaling_factor = (electric_gwe / 1.0) ** scaling_exponent
        OUT.C220507 = M_USD(containment_base_cost * scaling_factor)
    else:
        # No tritium containment needed for aneutronic fuels (p-B¹¹, D-He³)
        OUT.C220507 = M_USD(0.0)

    # Update total to include tritium containment costs
    OUT.C220500 = M_USD(
        OUT.C220501
        + OUT.C220502
        + OUT.C220503
        + OUT.C220504
        + OUT.C220505
        + OUT.C220506
        + OUT.C220507  # Tritium containment barriers
    )
    return OUT


def compute_pellet_injector_costs(
    basic: Basic,
    fuel_handling: FuelHandling,
    constants: CostingConstants,
    OUT: CAS2205,
) -> CAS2205:
    """Calculate pellet injection system costs (CAS 22.05.08).

    Pellet injectors provide plasma fueling and ELM pacing. Cost scales with
    fusion power (larger machines need higher fueling rate).

    Reference: ITER pellet injector ~$30M FOAK. NOAK with learning ~$15M at 2 GW.
    """
    if constants is None:
        OUT.C220508 = M_USD(0)
    else:
        OUT.C220508 = M_USD(
            float(constants.pellet_reference_cost)
            * (float(basic.p_nrl) / float(constants.pellet_reference_p_nrl))
            ** float(constants.pellet_scaling_exponent)
            * float(fuel_handling.learning_tenth_of_a_kind)
        )

    # Update total to include pellet injectors
    OUT.C220500 = M_USD(float(OUT.C220500) + float(OUT.C220508))
    return OUT
