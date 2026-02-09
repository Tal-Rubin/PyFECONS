from pyfecons.costing.calculations.cas22.cas220101_reactor_equipment import (
    compute_reactor_equipment_costs,
)
from pyfecons.enums import ConfinementType, FuelType, FusionMachineType
from pyfecons.inputs.blanket import Blanket
from pyfecons.inputs.radial_build import RadialBuild
from pyfecons.units import M_USD


def compute_cas22_reactor_equipment_total_cost(
    fusion_machine_type: FusionMachineType,
    confinement_type: ConfinementType,
    fuel_type: FuelType,
    blanket: Blanket,
    radial_build: RadialBuild,
) -> M_USD:
    result = compute_reactor_equipment_costs(
        fusion_machine_type, confinement_type, fuel_type, blanket, radial_build
    )
    return result.C220101
