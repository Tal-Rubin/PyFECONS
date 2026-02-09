from pyfecons.costing.calculations.conversions import to_m_usd
from pyfecons.costing.calculations.financials import (
    levelized_annual_cost,
    total_project_time,
)
from pyfecons.costing.categories.cas800000 import CAS80
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.costing_constants import CostingConstants
from pyfecons.inputs.financial import Financial
from pyfecons.units import Kilograms


def cas80_annualized_fuel_costs(
    basic: Basic, financial: Financial, constants: CostingConstants
) -> CAS80:
    # Cost Category 80: Annualized Fuel Cost (AFC)
    cas80 = CAS80()

    # TODO - why are there three calculations of c_f here?
    # c_f = 0.03 * (8760 * PNET*NMOD * p_a) / (1 + yinflation )**lifeY #hours * power = MWh
    # c_f = 50

    # the mass of deuterium https://physics.nist.gov/cgi-bin/cuu/Value?md
    m_D = Kilograms(3.342 * 10 ** (-27))

    # u_D ($/kg) = 2175 ($/kg) from STARFIRE * 1.12345/0.42273 [GDP IPD ratio for 2019/1980]
    u_D = 2175
    c_f = (
        float(basic.n_mod)
        * basic.p_nrl
        * 1e6
        * 3600
        * 8760
        * u_D
        * m_D
        * basic.plant_availability
        / (17.58 * 1.6021e-13)
    )

    cas80.C800000 = levelized_annual_cost(
        annual_cost=to_m_usd(c_f),
        interest_rate=float(financial.interest_rate),
        inflation_rate=float(basic.yearly_inflation),
        plant_lifetime=float(basic.plant_lifetime),
        construction_time=total_project_time(
            basic.construction_time, basic.fuel_type, constants, noak=basic.noak
        ),
    )
    return cas80
