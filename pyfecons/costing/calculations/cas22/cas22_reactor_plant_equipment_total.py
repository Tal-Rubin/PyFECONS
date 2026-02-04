from pyfecons.costing.categories.cas220000 import CAS22
from pyfecons.units import M_USD, Count


def cas22_reactor_plant_equipment_total_costs(
    cas2201_total_cost: M_USD, cas2200_total_cost: M_USD, n_mod: Count
) -> CAS22:
    # Reactor Plant Equipment (RPE) total
    # Multiply by n_mod since each fusion module requires its own reactor equipment
    cas22 = CAS22()

    # Cost category 22.1 total (reactor equipment for all modules)
    cas22.C220100 = M_USD(cas2201_total_cost * float(n_mod))
    # Cost category 22.0 total (all reactor plant equipment for all modules)
    cas22.C220000 = M_USD(cas2200_total_cost * float(n_mod))
    return cas22
