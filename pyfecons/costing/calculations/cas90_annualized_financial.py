from pyfecons.costing.categories.cas900000 import CAS90
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.financial import Financial
from pyfecons.units import M_USD, Ratio


def cas90_annualized_financial_costs(
    basic: Basic, financial: Financial, cas10_to_60_total_capital_cost: M_USD
) -> CAS90:
    # Cost Category 90: Annualized Financial Costs (AFC)
    cas90 = CAS90()

    # Total Capital costs 99
    cas90.C990000 = cas10_to_60_total_capital_cost

    # Prefer construction and lifetime values from `Basic` inputs when available.
    # Compute capital recovery factor based on interest rate, plant lifetime,
    # and construction duration.
    # Standard capital recovery factor (CRF) for annuity over n years:
    # CRF = i*(1+i)^n / ((1+i)^n - 1)
    i = float(financial.interest_rate)
    # plant lifetime: prefer `basic.plant_lifetime` (years from end of construction)
    n = float(
        basic.plant_lifetime
        if basic and basic.plant_lifetime is not None
        else financial.plant_lifetime_years
    )
    # construction duration: prefer `basic.construction_time`
    Tc = float(
        basic.construction_time
        if basic and basic.construction_time is not None
        else financial.construction_years
    )

    if i <= 0 or n <= 0:
        # fallback to legacy value if parameters are invalid
        effective_crf = float(financial.capital_recovery_factor)
    else:
        crf = (i * (1 + i) ** n) / (((1 + i) ** n) - 1)
        # Adjust for construction time by capitalizing costs to commercial operation.
        # If costs are incurred before operation, their accumulated value at COD
        # is roughly multiplied by (1+i)^Tc. We apply that adjustment to the CRF.
        effective_crf = crf * (1 + i) ** Tc

    # Update legacy field for downstream code and set annualized cost
    financial.capital_recovery_factor = Ratio(effective_crf)
    cas90.C900000 = M_USD(effective_crf * cas90.C990000)
    return cas90
