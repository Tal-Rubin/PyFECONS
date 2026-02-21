from pyfecons.enums import FuelType
from pyfecons.inputs.costing_constants import CostingConstants
from pyfecons.units import M_USD


def get_licensing_time(fuel_type: FuelType, constants: CostingConstants) -> float:
    """Licensing timeline (years) by fuel type under NRC Part 30."""
    if fuel_type == FuelType.DT:
        return float(constants.licensing_time_dt)
    elif fuel_type == FuelType.DD:
        return float(constants.licensing_time_dd)
    elif fuel_type == FuelType.DHE3:
        return float(constants.licensing_time_dhe3)
    elif fuel_type == FuelType.PB11:
        return float(constants.licensing_time_pb11)
    return float(constants.licensing_time_dt)  # default to D-T (most conservative)


def total_project_time(
    construction_time: float,
    fuel_type: FuelType,
    constants: CostingConstants,
    noak: bool = False,
) -> float:
    """Total time from project start to commercial operation.

    Combines physical construction time with fuel-type-dependent licensing
    timeline. Used for financial calculations (IDC, CRF) where the total
    duration that capital is tied up before revenue matters.

    Licensing time is FOAK-only: NOAK plants reuse the approved design
    and need only site-specific permit review (included in construction_time).
    """
    if noak:
        return construction_time
    return construction_time + get_licensing_time(fuel_type, constants)


def compute_crf(interest_rate: float, plant_lifetime: float) -> float:
    """Capital Recovery Factor: CRF = i*(1+i)^n / ((1+i)^n - 1)."""
    i = interest_rate
    n = plant_lifetime
    return (i * (1 + i) ** n) / (((1 + i) ** n) - 1)


def levelized_annual_cost(
    annual_cost: M_USD,
    interest_rate: float,
    inflation_rate: float,
    plant_lifetime: float,
    construction_time: float,
) -> M_USD:
    """Levelized annual cost of a nominally-growing cost stream.

    Converts an annual cost (in today's dollars) into a level annual
    payment over the plant lifetime, accounting for:
    1. Inflation during construction (shifts to first-year-of-operation $)
    2. Continued inflation over the operating lifetime (growing annuity)
    3. Discounting at the nominal interest rate (time value of money)
    4. Annualization via CRF

    Formula:
      A_1 = annual_cost * (1 + g)^Tc          (first-year cost)
      PV  = A_1 * (1 - ((1+g)/(1+i))^n) / (i - g)  (growing annuity PV)
      levelized = CRF(i, n) * PV

    When i == g (L'Hopital limit): PV = A_1 * n / (1 + i)

    Uses plain CRF, not effective CRF — construction-period financing
    is handled by CAS60 (IDC).
    """
    i = interest_rate
    g = inflation_rate
    n = plant_lifetime

    if i <= 0 or n <= 0:
        return annual_cost  # fallback

    # Inflate to first-year-of-operation dollars
    a1 = float(annual_cost) * (1 + g) ** construction_time

    # PV of growing annuity discounted at nominal rate
    if abs(i - g) < 1e-9:
        pv = a1 * n / (1 + i)
    else:
        pv = a1 * (1 - ((1 + g) / (1 + i)) ** n) / (i - g)

    # Annualize with plain CRF
    crf = compute_crf(i, n)
    return M_USD(crf * pv)
