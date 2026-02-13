from typing import TYPE_CHECKING, Optional, Union

from pyfecons.units import M_USD, MW, USD, W

if TYPE_CHECKING:
    from pyfecons.inputs.costing_constants import InflationFactors

# Unit conversions


def to_m_usd(dollars: Union[float, USD]) -> M_USD:
    return M_USD(dollars / 1e6)


def m_to_usd(dollars: Union[float, M_USD]) -> USD:
    return USD(dollars * 1e6)


# cost thousands to millions USD
def k_to_m_usd(thousands_dollars: Union[float, USD]) -> M_USD:
    return M_USD(thousands_dollars / 1e3)


def w_to_mw(watts: Union[float, W]) -> MW:
    return MW(watts / 1e6)


# EUR to USD conversion
# Default rate from Oct 20, 2024 - use InflationFactors for configurable rate
def eur_to_usd(
    amount_eur: float, inflation: Optional["InflationFactors"] = None
) -> float:
    if inflation is not None:
        return float(inflation.eur_to_usd_rate) * amount_eur
    return 0.920015 * amount_eur


# Inflation adjustment factors from https://www.usinflationcalculator.com/
# These are default values - use InflationFactors from CostingConstants for configurable values
inflation_1992_2024 = 2.26
inflation_2005_2024 = 1.58
inflation_2010_2024 = 1.43
inflation_factor_2019_2024 = 1.22


def get_inflation_factor(
    base_year: int, inflation: Optional["InflationFactors"] = None
) -> float:
    """Get inflation factor for a given base year.

    Args:
        base_year: The year of the original cost data
        inflation: Optional InflationFactors instance for configurable values

    Returns:
        Multiplier to convert base_year dollars to target year dollars
    """
    if inflation is not None:
        mapping = {
            1992: float(inflation.factor_1992),
            2005: float(inflation.factor_2005),
            2009: float(inflation.factor_2009),
            2010: float(inflation.factor_2009),
            2019: float(inflation.factor_2019),
        }
        return mapping.get(base_year, 1.0)

    # Default values for backward compatibility
    mapping = {
        1992: inflation_1992_2024,
        2005: inflation_2005_2024,
        2009: inflation_2010_2024,
        2010: inflation_2010_2024,
        2019: inflation_factor_2019_2024,
    }
    return mapping.get(base_year, 1.0)
