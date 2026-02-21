from pyfecons.costing.categories.cas600000 import CAS60
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.costing_constants import CostingConstants
from pyfecons.inputs.financial import Financial
from pyfecons.units import M_USD


def cas60_capitalized_financial_costs(
    basic: Basic,
    financial: Financial,
    overnight_cost: M_USD,
    constants: CostingConstants,
) -> CAS60:
    """CAS60: Interest during construction (IDC).

    First-principles formula assuming uniform capital spending over
    the construction period:

        f_IDC = ((1+i)^T - 1) / (i*T) - 1
        CAS60 = f_IDC * overnight_cost

    where overnight_cost = CAS10 + CAS20 + CAS30 + CAS40 + CAS50.
    """
    cas60 = CAS60()

    i = float(financial.interest_rate)
    T = float(basic.construction_time)

    if i <= 0 or T <= 0:
        cas60.C600000 = M_USD(0)
        return cas60

    f_idc = ((1 + i) ** T - 1) / (i * T) - 1
    cas60.C600000 = M_USD(f_idc * float(overnight_cost))
    return cas60
