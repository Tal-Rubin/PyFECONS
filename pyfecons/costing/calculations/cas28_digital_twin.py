from pyfecons.costing.categories.cas280000 import CAS28
from pyfecons.inputs.costing_constants import CostingConstants
from pyfecons.units import M_USD


def cas28_digital_twin_costs(constants: CostingConstants) -> CAS28:
    # cost category 28 Digital Twin
    cas28 = CAS28()
    # In-house cost estimate provided by NtTau Digital LTD
    cas28.C280000 = constants.digital_twin
    return cas28
