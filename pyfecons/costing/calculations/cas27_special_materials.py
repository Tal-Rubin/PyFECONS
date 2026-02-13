from typing import TYPE_CHECKING, Optional

from pyfecons.costing.categories.cas220101 import CAS220101
from pyfecons.costing.categories.cas270000 import CAS27
from pyfecons.enums import BlanketPrimaryCoolant
from pyfecons.inputs.blanket import Blanket
from pyfecons.materials import Materials
from pyfecons.units import M_USD

if TYPE_CHECKING:
    from pyfecons.inputs.costing_constants import SpecialMaterialsConstants

materials = Materials()


def cas27_special_materials_costs(
    blanket: Blanket,
    cas220101: CAS220101,
    constants: Optional["SpecialMaterialsConstants"] = None,
) -> CAS27:
    """Calculate CAS 27 Special Materials costs.

    Args:
        blanket: Blanket configuration
        cas220101: Reactor equipment data (for volume calculations)
        constants: Optional configurable cost factors. Uses defaults if None.

    Returns:
        CAS27 cost category with calculated values
    """
    # Use provided constants or default values for backward compatibility
    if constants is None:
        from pyfecons.inputs.costing_constants import SpecialMaterialsConstants

        constants = SpecialMaterialsConstants()

    c = constants
    cas27 = CAS27()

    # Select the coolant and calculate C_27_1 based on primary coolant type
    if blanket.primary_coolant == BlanketPrimaryCoolant.FLIBE:
        # FliBe is a complex molten salt (LiF-BeF2) requiring enrichment
        cas27.C271000 = 1000 * c.flibe_cost_factor * materials.FliBe.c / 1e6
    elif blanket.primary_coolant == BlanketPrimaryCoolant.LEAD_LITHIUM_PBLI:
        # PbLi eutectic calculation using isotope fractions
        cas27.C271000 = M_USD(
            (
                materials.Pb.c_raw
                * materials.Pb.m
                * c.FPCPPFb
                * cas220101.firstwall_vol
                * materials.FliBe.rho
                * 1000
                + materials.Li.c_raw
                * materials.Li.m
                * c.f_6Li
                * cas220101.firstwall_vol
                * materials.FliBe.rho
                * 1000
            )
            / 1e6
        )
    elif blanket.primary_coolant == BlanketPrimaryCoolant.LITHIUM_LI:
        cas27.C271000 = M_USD(1000 * c.flibe_cost_factor * c.lithium_cost_factor / 1e6)
    elif blanket.primary_coolant == BlanketPrimaryCoolant.OTHER_EUTECTIC_SALT:
        cas27.C271000 = M_USD(1000 * c.flibe_cost_factor * c.lithium_cost_factor / 1e6)
    elif blanket.primary_coolant == BlanketPrimaryCoolant.HELIUM:
        # Helium is a commodity gas - much cheaper than molten salts
        cas27.C271000 = M_USD(1000 * c.helium_cost_factor * c.lithium_cost_factor / 1e6)
    elif blanket.primary_coolant == BlanketPrimaryCoolant.DUAL_COOLANT_PBLI_AND_HE:
        # Dual coolant uses helium pricing
        cas27.C271000 = M_USD(1000 * c.helium_cost_factor * c.lithium_cost_factor / 1e6)
    elif blanket.primary_coolant == BlanketPrimaryCoolant.WATER:
        # Water is very cheap
        cas27.C271000 = M_USD(1000 * 1000 * c.water_cost_factor / 1e6)

    # Additional materials calculations
    cas27.C274000 = M_USD(c.other_materials_factor * c.materials_adjustment)  # Other
    cas27.C275000 = M_USD(c.cover_gas_factor * c.materials_adjustment)  # Cover gas
    cas27.C270000 = M_USD(cas27.C271000 + cas27.C274000 + cas27.C275000)
    return cas27
