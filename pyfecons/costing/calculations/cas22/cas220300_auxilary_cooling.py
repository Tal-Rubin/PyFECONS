from pyfecons.costing.accounting.power_table import PowerTable
from pyfecons.costing.calculations.conversions import inflation_1992_2024
from pyfecons.costing.categories.cas220300 import CAS2203
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.costing_constants import CostingConstants
from pyfecons.inputs.power_input import PowerInput
from pyfecons.units import M_USD, MW, Count


def cas_2203_auxilary_cooling_costs(
    basic: Basic,
    power_input: PowerInput,
    power_table: PowerTable,
    constants: CostingConstants,
) -> CAS2203:
    # Cost Category 22.3  Auxiliary cooling
    cas2203 = CAS2203()
    cas2203.C220301 = compute_auxilary_coolant_costs(basic.n_mod, power_table.p_th)
    cas2203.C220302 = compute_cryoplant_equipment_costs(power_input.p_cryo, constants)
    cas2203.C220300 = M_USD(cas2203.C220301 + cas2203.C220302)
    return cas2203


def compute_auxilary_coolant_costs(n_mod: Count, p_th: MW) -> M_USD:
    # Auxiliary cooling systems
    return M_USD(1.10 * 1e-3 * float(n_mod) * p_th * inflation_1992_2024)


def compute_cryoplant_equipment_costs(p_cryo: MW, constants: CostingConstants) -> M_USD:
    """Cryoplant capital equipment: compressors, liquefiers, cold-box, distribution piping.

    Scaled from ITER cryoplant (~$200M for 30 MW electrical load).
    Economy of scale exponent 0.7 (standard for industrial process plants).
    """
    if p_cryo is None or float(p_cryo) <= 0:
        return M_USD(0)
    return M_USD(
        float(constants.cryo_reference_cost)
        * (float(p_cryo) / float(constants.cryo_reference_p_cryo))
        ** float(constants.cryo_scaling_exponent)
    )
