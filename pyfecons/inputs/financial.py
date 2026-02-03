from dataclasses import dataclass

from pyfecons.units import Ratio, Unknown, Years


@dataclass
class Financial:
    # TODO what are these?
    a_c_98: Unknown = Unknown(115)
    a_power: Unknown = Unknown(1000)
    # Financial parameters used to compute capital recovery factor
    # interest rate (decimal, e.g. 0.07 for 7%)
    interest_rate: Ratio = Ratio(0.07)
    # construction duration in years
    construction_years: Years = Years(5)
    # plant lifetime (years) used for annualization
    plant_lifetime_years: Years = Years(30)
    # legacy field (kept for backward compatibility) - will be updated by calculations
    capital_recovery_factor: Ratio = Ratio(0.09)
