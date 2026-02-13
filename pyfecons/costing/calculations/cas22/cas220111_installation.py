from typing import TYPE_CHECKING, Optional

from pyfecons.costing.calculations.conversions import to_m_usd
from pyfecons.costing.categories.cas220101 import CAS220101
from pyfecons.costing.categories.cas220111 import CAS220111
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.installation import Installation
from pyfecons.units import M_USD, USD, Count, Meters, Years

if TYPE_CHECKING:
    from pyfecons.inputs.costing_constants import InstallationConstants


def cas_220111_installation_costs(
    basic: Basic,
    installation: Installation,
    cas220101: CAS220101,
    constants: Optional["InstallationConstants"] = None,
) -> CAS220111:
    # Cost Category 22.1.11 Installation costs
    cas220111 = CAS220111()

    cas220111.C220111 = compute_installation_costs(
        installation.labor_rate,
        basic.construction_time,
        basic.n_mod,
        cas220101.axis_ir,
        constants,
    )
    return cas220111


def compute_installation_costs(
    labor_rate: USD,
    construction_time: Years,
    n_mod: Count,
    axis_ir: Meters,
    constants: Optional["InstallationConstants"] = None,
) -> M_USD:
    # Use provided constants or default values for backward compatibility
    if constants is None:
        from pyfecons.inputs.costing_constants import InstallationConstants

        constants = InstallationConstants()

    c = constants
    labor_rate_m_usd = to_m_usd(labor_rate)

    # Construction worker calculation
    construction_worker = (
        c.construction_worker_base * axis_ir / c.construction_worker_divisor
    )

    costs = {
        # Base installation work
        "C_22_1_11_in": float(n_mod)
        * construction_time
        * (labor_rate_m_usd * c.construction_worker_base * c.base_multiplier),
        # CAS 22.01.01 First wall and blanket
        "C_22_1_11_1_in": float(n_mod)
        * (labor_rate_m_usd * c.first_wall_blanket_multiplier * construction_worker),
        # CAS 22.01.02 Shield
        "C_22_1_11_2_in": float(n_mod)
        * (labor_rate_m_usd * c.shield_multiplier * construction_worker),
        # CAS 22.01.03 Coils
        "C_22_1_11_3_in": float(n_mod)
        * (labor_rate_m_usd * c.coils_multiplier * construction_worker),
        # CAS 22.01.04 Supplementary heating
        "C_22_1_11_4_in": float(n_mod)
        * (labor_rate_m_usd * c.supplementary_heating_multiplier * construction_worker),
        # CAS 22.01.05 Primary structure
        "C_22_1_11_5_in": float(n_mod)
        * (labor_rate_m_usd * c.primary_structure_multiplier * construction_worker),
        # CAS 22.01.06 Vacuum system
        "C_22_1_11_6_in": float(n_mod)
        * (labor_rate_m_usd * c.vacuum_system_multiplier * construction_worker),
        # CAS 22.01.07 Power supplies
        "C_22_1_11_7_in": float(n_mod)
        * (labor_rate_m_usd * c.power_supplies_multiplier * construction_worker),
        # CAS 22.01.08 Guns or divertor (not included in labor calculation)
        "C_22_1_11_8_in": 0,
        # CAS 22.01.09 Direct energy converter
        "C_22_1_11_9_in": float(n_mod)
        * (
            labor_rate_m_usd
            * c.direct_energy_converter_multiplier
            * construction_worker
        ),
        # CAS 22.01.10 ECRH (not included in labor calculation)
        "C_22_1_11_10_in": 0,
    }
    # Total cost calculations
    return M_USD(sum(costs.values()))
