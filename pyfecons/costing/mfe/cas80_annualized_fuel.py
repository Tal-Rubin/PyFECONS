import scipy.constants as _sc

from pyfecons.costing.calculations.conversions import to_m_usd
from pyfecons.costing.calculations.financials import (
    levelized_annual_cost,
    total_project_time,
)
from pyfecons.costing.calculations.fuel_physics import (
    Q_DT,
    Q_PB11,
    Q_DD_nHe3,
    Q_DD_pT,
    Q_DHe3,
)
from pyfecons.costing.categories.cas800000 import CAS80
from pyfecons.enums import FuelType
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.costing_constants import CostingConstants
from pyfecons.inputs.financial import Financial

# Particle masses in kg (CODATA via scipy, except Li-6 and B-11)
_M_DEUTERIUM_KG = _sc.physical_constants["deuteron mass"][0]
_M_PROTON_KG = _sc.physical_constants["proton mass"][0]
_M_HE3_KG = _sc.physical_constants["helion mass"][0]  # helion = He-3 nucleus
_M_LI6_KG = 6.015122795 * _sc.atomic_mass  # not in scipy CODATA
_M_B11_KG = 11.0093054 * _sc.atomic_mass  # not in scipy CODATA
_MEV_TO_JOULES = _sc.eV * 1e6

# Fuel isotope unit costs ($/kg) — TODO: move to CostingConstants
_U_DEUTERIUM = 2175.0  # STARFIRE (1980) inflation-adjusted via GDP IPD
_U_LI6 = 1000.0  # enriched Li-6 (90%) for breeding blanket
_U_HE3 = 2_000_000.0  # He-3 ($2,000/g — optimistic self-production)
_U_PROTIUM = 5.0  # commodity H2
_U_B11 = 10_000.0  # enriched B-11 (>95%, $10/g, tails from B-10)

# DD burn fraction defaults (T=50 keV, tau_p=5 s)
_DD_F_T = 0.969
_DD_F_HE3 = 0.689


def cas80_annualized_fuel_costs(
    basic: Basic, financial: Financial, constants: CostingConstants
) -> CAS80:
    """CAS80: Annualized fuel cost — fuel-specific consumable costs.

    Each fuel cycle has different consumables, Q-values, and costs per reaction.
    The 1e6 (MW->W) and /1e6 ($->M$) cancel, giving a clean formula.
    """
    cas80 = CAS80()

    SECONDS_PER_YR = 3600.0 * 8760.0

    fuel = basic.fuel_type
    if fuel == FuelType.DT:
        cost_per_rxn = _M_DEUTERIUM_KG * _U_DEUTERIUM + _M_LI6_KG * _U_LI6
        q_eff = Q_DT
    elif fuel == FuelType.DD:
        q_eff = (
            0.5 * Q_DD_pT
            + 0.5 * Q_DD_nHe3
            + 0.5 * _DD_F_T * Q_DT
            + 0.5 * _DD_F_HE3 * Q_DHe3
        )
        d_per_event = 2 + 0.5 * _DD_F_T + 0.5 * _DD_F_HE3
        cost_per_rxn = d_per_event * _M_DEUTERIUM_KG * _U_DEUTERIUM
    elif fuel == FuelType.DHE3:
        cost_per_rxn = _M_DEUTERIUM_KG * _U_DEUTERIUM + _M_HE3_KG * _U_HE3
        q_eff = Q_DHe3
    elif fuel == FuelType.PB11:
        cost_per_rxn = _M_PROTON_KG * _U_PROTIUM + _M_B11_KG * _U_B11
        q_eff = Q_PB11
    else:
        cost_per_rxn = 0.0
        q_eff = Q_DT

    c_f = (
        float(basic.n_mod)
        * basic.p_nrl
        * SECONDS_PER_YR
        * basic.plant_availability
        * cost_per_rxn
        / (q_eff * _MEV_TO_JOULES)
    )

    cas80.C800000 = levelized_annual_cost(
        annual_cost=to_m_usd(c_f),
        interest_rate=float(financial.interest_rate),
        inflation_rate=float(basic.yearly_inflation),
        plant_lifetime=float(basic.plant_lifetime),
        construction_time=total_project_time(
            basic.construction_time, basic.fuel_type, constants, noak=basic.noak
        ),
    )
    return cas80
