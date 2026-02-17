from pyfecons.costing.accounting.power_table import PowerTable
from pyfecons.costing.categories.cas220700 import CAS2207
from pyfecons.inputs.costing_constants import CostingConstants
from pyfecons.units import M_USD


def cas_2207_instrumentation_and_control_costs(
    power_table: PowerTable = None, constants: CostingConstants = None
) -> CAS2207:
    # Cost Category 22.7 Instrumentation and Control
    cas2207 = CAS2207()
    cas2207.C220700 = compute_instrumentation_and_control_costs(power_table, constants)
    return cas2207


def compute_instrumentation_and_control_costs(
    power_table: PowerTable = None, constants: CostingConstants = None
) -> M_USD:
    # Source: page 576, account 12,
    # https://netl.doe.gov/projects/files/CostAndPerformanceBaselineForFossilEnergyPlantsVolume1BituminousCoalAndNaturalGasToElectricity_101422.pdf
    # Scaled with plant thermal power using economy-of-scale exponent.
    if constants is None or power_table is None:
        return M_USD(85)

    p_th = float(power_table.p_th)
    ref_cost = float(constants.ic_reference_cost)
    ref_p_th = float(constants.ic_reference_p_th)
    exponent = float(constants.ic_scaling_exponent)

    if ref_p_th <= 0 or p_th <= 0:
        return M_USD(ref_cost)

    return M_USD(ref_cost * (p_th / ref_p_th) ** exponent)
