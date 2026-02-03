from dataclasses import dataclass

from pyfecons.units import Ratio, Unknown


@dataclass
class Financial:
    # TODO what are these?
    a_c_98: Unknown = Unknown(115)
    a_power: Unknown = Unknown(1000)
    # Interest rate (effective cost of money) for capital recovery factor calculation
    # See https://netl.doe.gov/projects/files/CostAndPerformanceBaselineForFossilEnergyPlantsVolume1BituminousCoalAndNaturalGasToElectricity_101422.pdf
    interest_rate: Ratio = None
