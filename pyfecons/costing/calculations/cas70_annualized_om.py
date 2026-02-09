from pyfecons.costing.accounting.power_table import PowerTable
from pyfecons.costing.calculations.conversions import to_m_usd
from pyfecons.costing.calculations.financials import (
    levelized_annual_cost,
    total_project_time,
)
from pyfecons.costing.categories.cas700000 import CAS70
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.costing_constants import CostingConstants
from pyfecons.inputs.financial import Financial


def cas70_annualized_om_costs(
    basic: Basic,
    financial: Financial,
    power_table: PowerTable,
    constants: CostingConstants,
) -> CAS70:
    # Cost Category  70 Annualized O&M Cost (AOC)
    cas70 = CAS70()

    c_om = constants.om_cost_per_mw_per_year * power_table.p_net * 1000

    # TODO what's this C750000? When do we include it?
    # C750000 = 0.1 * (C220000) scheduled replacement costs

    cas70.C700000 = levelized_annual_cost(
        annual_cost=to_m_usd(c_om),
        interest_rate=float(financial.interest_rate),
        inflation_rate=float(basic.yearly_inflation),
        plant_lifetime=float(basic.plant_lifetime),
        construction_time=total_project_time(
            basic.construction_time, basic.fuel_type, constants, noak=basic.noak
        ),
    )
    return cas70
