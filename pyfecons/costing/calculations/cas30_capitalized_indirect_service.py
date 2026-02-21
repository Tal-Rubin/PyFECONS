from pyfecons.costing.categories.cas200000 import CAS20
from pyfecons.costing.categories.cas300000 import CAS30
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.costing_constants import CostingConstants
from pyfecons.units import M_USD


def cas30_capitalized_indirect_service_costs(
    basic: Basic,
    cas20: CAS20,
    constants: CostingConstants,
) -> CAS30:
    """CAS30: Indirect service costs.

    Computed as a fraction of total direct cost (CAS20), scaled by
    construction time relative to a reference duration:

        CAS30 = indirect_fraction * CAS20 * (t_con / t_ref)

    Default: 20% of CAS20 at 6-year reference construction time.
    """
    cas30 = CAS30()
    cas30.C300000 = M_USD(
        constants.indirect_fraction
        * cas20.C200000
        * (basic.construction_time / constants.reference_construction_time)
    )
    return cas30
