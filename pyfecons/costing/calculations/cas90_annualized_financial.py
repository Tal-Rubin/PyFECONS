from pyfecons.costing.categories.cas900000 import CAS90
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.financial import Financial
from pyfecons.units import M_USD


def calculate_capital_recovery_factor(interest_rate: float, n_years: float) -> float:
    """
    Calculate capital recovery factor (CRF) using the standard formula:
    CRF = x(1+x)^N / ((1+x)^N - 1)

    Where:
    - x = interest rate (effective cost of money)
    - N = plant lifetime + construction time (total project duration)
    """
    x = interest_rate
    n = n_years
    return (x * (1 + x) ** n) / ((1 + x) ** n - 1)


def cas90_annualized_financial_costs(
    financial: Financial, basic: Basic, cas10_to_60_total_capital_cost: M_USD
) -> CAS90:
    # Cost Category 90: Annualized Financial Costs (AFC)
    cas90 = CAS90()

    # Total Capital costs 99
    cas90.C990000 = cas10_to_60_total_capital_cost

    # Calculate capital recovery factor from interest rate and project duration
    n_years = basic.plant_lifetime + basic.construction_time
    capital_recovery_factor = calculate_capital_recovery_factor(
        financial.interest_rate, n_years
    )

    cas90.C900000 = M_USD(capital_recovery_factor * cas90.C990000)
    return cas90
