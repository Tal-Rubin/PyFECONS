from pyfecons.costing.accounting.power_table import PowerTable
from pyfecons.costing.calculations.conversions import to_m_usd
from pyfecons.costing.categories.cas700000 import CAS70
from pyfecons.inputs.costing_constants import CostingConstants


def cas70_annualized_om_costs(
    power_table: PowerTable, constants: CostingConstants
) -> CAS70:
    # Cost Category  70 Annualized O&M Cost (AOC)
    cas70 = CAS70()

    c_om = constants.om_cost_per_mw_per_year * power_table.p_net * 1000

    # TODO what's this C750000? When do we include it?
    # C750000 = 0.1 * (C220000) scheduled replacement costs

    cas70.C700000 = to_m_usd(c_om)  # + C750000
    return cas70
