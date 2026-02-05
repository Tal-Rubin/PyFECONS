from pyfecons.costing.accounting.power_table import PowerTable
from pyfecons.costing.calculations.conversions import m_to_usd
from pyfecons.costing.categories.cas700000 import CAS70
from pyfecons.costing.categories.cas800000 import CAS80
from pyfecons.costing.categories.cas900000 import CAS90
from pyfecons.costing.categories.lcoe import LCOE
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.financial import Financial
from pyfecons.units import M_USD


def lcoe_costs(
    basic: Basic,
    financial: Financial,
    power_table: PowerTable,
    cas70: CAS70,
    cas80: CAS80,
    cas90: CAS90,
) -> LCOE:
    # LCOE = Levelized Cost of Electricity
    # LCOE = (Annualized_CAPEX + Levelized_OPEX) / Annual_Energy
    #
    # Where:
    # - Annualized_CAPEX = CAS90 (already includes CRF * Total_CAPEX)
    # - Levelized_OPEX = CRF * PV(growing OPEX annuity)
    # - Annual_Energy = 8760 * p_net * n_mod * availability
    lcoe = LCOE()

    # Get financial parameters
    i = float(financial.interest_rate)  # discount rate
    g = float(basic.yearly_inflation)  # OPEX growth rate (inflation)
    n = float(basic.plant_lifetime)  # plant lifetime in years

    # Base annual OPEX (year 0 dollars)
    opex_base = m_to_usd(cas70.C700000) + m_to_usd(cas80.C800000)

    # Compute present value of growing OPEX annuity
    # OPEX in year k = opex_base * (1+g)^(k-1) for k = 1 to n
    # PV = opex_base * [1 - ((1+g)/(1+i))^n] / (i - g)  when i != g
    # PV = opex_base * n / (1+i)  when i == g (limit case)
    if abs(i - g) < 1e-9:
        # Special case: interest rate equals inflation rate
        pv_opex = opex_base * n / (1 + i)
    else:
        pv_opex = opex_base * (1 - ((1 + g) / (1 + i)) ** n) / (i - g)

    # Compute CRF to annualize the PV of OPEX
    # CRF = i*(1+i)^n / ((1+i)^n - 1)
    if i <= 0 or n <= 0:
        # Fallback: just use base OPEX if parameters invalid
        levelized_opex = opex_base
    else:
        crf = (i * (1 + i) ** n) / (((1 + i) ** n) - 1)
        levelized_opex = crf * pv_opex

    # Annual energy production (MWh)
    annual_energy_mwh = (
        8760 * power_table.p_net * float(basic.n_mod) * basic.plant_availability
    )

    # LCOE = (Annualized CAPEX + Levelized OPEX) / Annual Energy
    # CAS90.C900000 is already the annualized CAPEX
    lcoe.C1000000 = M_USD(
        (m_to_usd(cas90.C900000) + levelized_opex) / annual_energy_mwh
    )
    lcoe.C2000000 = M_USD(lcoe.C1000000 / 10)
    return lcoe
