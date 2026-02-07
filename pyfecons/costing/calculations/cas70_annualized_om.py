from pyfecons.costing.accounting.power_table import PowerTable
from pyfecons.costing.calculations.conversions import to_m_usd
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

    # Get financial parameters
    i = float(financial.interest_rate)  # discount rate
    g = float(basic.yearly_inflation)  # OPEX growth rate (inflation)
    n = float(basic.plant_lifetime)  # plant lifetime in years
    Tc = float(basic.construction_time)  # construction duration in years

    # Compute present value of growing OPEX annuity
    # OPEX in year k = opex_base * (1+g)^(k-1) for k = 1 to n
    # PV = opex_base * [1 - ((1+g)/(1+i))^n] / (i - g)  when i != g
    # PV = opex_base * n / (1+i)  when i == g (limit case)
    if abs(i - g) < 1e-9:
        # Special case: interest rate equals inflation rate
        pv_opex = to_m_usd(c_om) * n / (1 + i)
    else:
        pv_opex = to_m_usd(c_om) * (1 - ((1 + g) / (1 + i)) ** n) / (i - g)

    # Compute CRF to annualize the PV of OPEX
    # CRF = i*(1+i)^n / ((1+i)^n - 1)
    if i <= 0 or n <= 0:
        # Fallback: just use base OPEX if parameters invalid
        levelized_cas70 = to_m_usd(c_om)
    else:
        crf = (i * (1 + i) ** n) / (((1 + i) ** n) - 1)
        effective_crf = crf * (1 + i) ** Tc
        levelized_cas70 = effective_crf * pv_opex

    cas70.C700000 = levelized_cas70  # + C750000
    return cas70
