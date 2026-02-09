from pyfecons.costing.calculations.financials import (
    compute_effective_crf,
    total_project_time,
)
from pyfecons.costing.categories.cas900000 import CAS90
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.costing_constants import CostingConstants
from pyfecons.inputs.financial import Financial
from pyfecons.units import M_USD, Ratio


def cas90_annualized_financial_costs(
    basic: Basic,
    financial: Financial,
    cas10_to_60_total_capital_cost: M_USD,
    constants: CostingConstants,
) -> CAS90:
    # Cost Category 90: Annualized Financial Costs (AFC)
    cas90 = CAS90()

    # Total Capital costs 99
    cas90.C990000 = cas10_to_60_total_capital_cost

    i = float(financial.interest_rate)
    n = float(
        basic.plant_lifetime
        if basic and basic.plant_lifetime is not None
        else financial.plant_lifetime_years
    )
    # CRF adjustment uses total project time (licensing + construction).
    Tc = total_project_time(
        float(
            basic.construction_time
            if basic and basic.construction_time is not None
            else financial.construction_years
        ),
        basic.fuel_type,
        constants,
        noak=basic.noak,
    )

    effective_crf = compute_effective_crf(
        interest_rate=i,
        plant_lifetime=n,
        construction_time=Tc,
        fallback_crf=float(financial.capital_recovery_factor),
    )

    # Update legacy field for downstream code and set annualized cost
    financial.capital_recovery_factor = Ratio(effective_crf)
    cas90.C900000 = M_USD(effective_crf * cas90.C990000)
    return cas90
