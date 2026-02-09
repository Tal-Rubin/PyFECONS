from pyfecons.costing.calculations.financials import (
    levelized_annual_cost,
    total_project_time,
)
from pyfecons.costing.calculations.interpolation import (
    get_interpolated_value,
    interpolate_data,
)
from pyfecons.costing.categories.cas800000 import CAS80
from pyfecons.costing.ife.pfr_costs import yearlytcost_pfr_coords
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.costing_constants import CostingConstants
from pyfecons.inputs.financial import Financial
from pyfecons.units import M_USD


def cas80_annualized_fuel_costs(
    basic: Basic, financial: Financial, constants: CostingConstants
) -> CAS80:
    # Cost Category 80: Annualized Fuel Cost (AFC)
    cas80 = CAS80()

    # Simple interpolation of yearly total target cost from interpolated graph 2 below. See 22.1.8 for more.
    yearly_cost_interpolation = interpolate_data(yearlytcost_pfr_coords)
    annual_fuel_cost = M_USD(
        get_interpolated_value(yearly_cost_interpolation, basic.implosion_frequency)
    )

    cas80.C800000 = levelized_annual_cost(
        annual_cost=annual_fuel_cost,
        interest_rate=float(financial.interest_rate),
        inflation_rate=float(basic.yearly_inflation),
        plant_lifetime=float(basic.plant_lifetime),
        construction_time=total_project_time(
            basic.construction_time, basic.fuel_type, constants, noak=basic.noak
        ),
    )
    return cas80
