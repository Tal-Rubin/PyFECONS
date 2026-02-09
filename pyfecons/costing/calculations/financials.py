from pyfecons.enums import FuelType
from pyfecons.inputs.costing_constants import CostingConstants
from pyfecons.units import M_USD, Ratio


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


def compute_effective_crf(
    interest_rate: float,
    plant_lifetime: float,
    construction_time: float,
    fallback_crf: float | None = None,
) -> float:
    """CRF adjusted for construction time: effective_crf = CRF * (1+i)^Tc.

    Falls back to fallback_crf if interest_rate or plant_lifetime are invalid.
    """
    if interest_rate <= 0 or plant_lifetime <= 0:
        if fallback_crf is not None:
            return fallback_crf
        raise ValueError(
            f"Invalid financial parameters: interest_rate={interest_rate}, "
            f"plant_lifetime={plant_lifetime}"
        )
    crf = compute_crf(interest_rate, plant_lifetime)
    return crf * (1 + interest_rate) ** construction_time


def levelized_annual_cost(
    annual_cost: M_USD,
    interest_rate: float,
    inflation_rate: float,
    plant_lifetime: float,
    construction_time: float,
) -> M_USD:
    """Levelize an annual cost that grows with inflation over plant lifetime.

    Computes the present value of a growing OPEX annuity, then annualizes
    it using the effective CRF (adjusted for construction time).

    The annual_cost is treated as first-year-of-operation dollars
    (standard NREL/IEA convention).
    """
    i = interest_rate
    g = inflation_rate
    n = plant_lifetime

    # Present value of growing annuity
    if abs(i - g) < 1e-9:
        pv = annual_cost * n / (1 + i)
    else:
        pv = annual_cost * (1 - ((1 + g) / (1 + i)) ** n) / (i - g)

    # Annualize with construction-time-adjusted CRF
    if i <= 0 or n <= 0:
        return annual_cost  # fallback
    effective_crf = compute_effective_crf(i, n, construction_time)
    return M_USD(effective_crf * pv)
