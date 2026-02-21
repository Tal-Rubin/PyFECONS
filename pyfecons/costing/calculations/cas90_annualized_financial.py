from pyfecons.costing.calculations.financials import compute_crf
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
    """CAS90: Annualized financial (capital) costs.

    Plain CRF * total_capital. Construction-period financing is handled
    by CAS60 (IDC), so no effective CRF adjustment here.
    """
    cas90 = CAS90()
    cas90.C990000 = cas10_to_60_total_capital_cost

    i = float(financial.interest_rate)
    n = float(
        basic.plant_lifetime
        if basic and basic.plant_lifetime is not None
        else financial.plant_lifetime_years
    )

    if i <= 0 or n <= 0:
        crf = float(financial.capital_recovery_factor)
    else:
        crf = compute_crf(i, n)

    financial.capital_recovery_factor = Ratio(crf)
    cas90.C900000 = M_USD(crf * cas90.C990000)
    return cas90
