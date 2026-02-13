import scipy.constants as _sc

from pyfecons.enums import FuelType
from pyfecons.units import MW

# ---------------------------------------------------------------------------
# Particle masses (MeV/c^2) from CODATA via scipy
# ---------------------------------------------------------------------------
_m_d = _sc.physical_constants["deuteron mass energy equivalent in MeV"][0]
_m_t = _sc.physical_constants["triton mass energy equivalent in MeV"][0]
_m_n = _sc.physical_constants["neutron mass energy equivalent in MeV"][0]
_m_p = _sc.physical_constants["proton mass energy equivalent in MeV"][0]
_m_alpha = _sc.physical_constants["alpha particle mass energy equivalent in MeV"][0]
_m_he3 = _sc.physical_constants["helion mass energy equivalent in MeV"][0]

# ---------------------------------------------------------------------------
# Q-values from mass defect: Q = sum(reactant masses) - sum(product masses)
# ---------------------------------------------------------------------------
Q_DT = _m_d + _m_t - _m_alpha - _m_n  # D+T -> alpha + n
Q_DD_pT = 2 * _m_d - _m_t - _m_p  # D+D -> T + p
Q_DD_nHe3 = 2 * _m_d - _m_he3 - _m_n  # D+D -> He3 + n
Q_DHe3 = _m_d + _m_he3 - _m_alpha - _m_p  # D+He3 -> alpha + p
Q_PB11 = 8.68  # p+B11 -> 3 alpha; scipy lacks B-11 mass (NNDC/ENDF value)

# ---------------------------------------------------------------------------
# Product kinetic energies (two-body CoM kinematics)
# For A + B -> C + D:  KE_C = Q * m_D / (m_C + m_D)
# ---------------------------------------------------------------------------

# D+T -> alpha(E_alpha_DT) + n(E_n_DT)
E_alpha_DT = Q_DT * _m_n / (_m_alpha + _m_n)
E_n_DT = Q_DT * _m_alpha / (_m_alpha + _m_n)

# D+D -> T(E_T_DD) + p(E_p_DD)  [branch 1, 50%]
E_T_DD = Q_DD_pT * _m_p / (_m_t + _m_p)
E_p_DD = Q_DD_pT * _m_t / (_m_t + _m_p)

# D+D -> He3(E_He3_DD) + n(E_n_DD)  [branch 2, 50%]
E_He3_DD = Q_DD_nHe3 * _m_n / (_m_he3 + _m_n)
E_n_DD = Q_DD_nHe3 * _m_he3 / (_m_he3 + _m_n)

# D+He3 -> alpha(E_alpha_DHe3) + p(E_p_DHe3)
E_alpha_DHe3 = Q_DHe3 * _m_p / (_m_alpha + _m_p)
E_p_DHe3 = Q_DHe3 * _m_alpha / (_m_alpha + _m_p)

# ---------------------------------------------------------------------------
# Derived constants used in the semi-catalyzed DD model
# ---------------------------------------------------------------------------
# Per DD event (averaged over 50/50 branches), before secondary burns:
#   E_charged_primary = 0.5*(E_T_DD + E_p_DD) + 0.5*E_He3_DD
#   E_neutron_primary = 0.5*E_n_DD
#   E_total_primary   = 0.5*Q_DD_pT + 0.5*Q_DD_nHe3
_E_charged_primary_DD = 0.5 * (E_T_DD + E_p_DD) + 0.5 * E_He3_DD
_E_neutron_primary_DD = 0.5 * E_n_DD
_E_total_primary_DD = 0.5 * Q_DD_pT + 0.5 * Q_DD_nHe3


def compute_ash_neutron_split(
    p_nrl, fuel_type, dd_f_T=0.969, dd_f_He3=0.689, dhe3_dd_frac=0.07, dhe3_f_T=0.97
):
    """
    Compute charged-particle (ash) and neutron power from total fusion power.

    All reaction energetics derived from CODATA particle masses via scipy.constants.

    DT:   E_alpha / Q_DT ~ 20.0% charged (He4 alpha)
    DD:   Semi-catalyzed burn with secondary DT and DHe3 reactions.
          Products: protons, tritons, He-3, He-4 (not just alphas).
    DHe3: Primary 100% charged, with parameterized D-D side reactions.
    PB11: 100% charged (3 alphas, aneutronic).

    Args:
        p_nrl: Total fusion power [MW]
        fuel_type: FuelType enum
        dd_f_T: DD tritium burn fraction (0-1). Default 0.969 (T=50keV, tau_p=5s).
        dd_f_He3: DD He-3 burn fraction (0-1). Default 0.689 (T=50keV, tau_p=5s).
        dhe3_dd_frac: D-He3 energy fraction from D-D side reactions (0-1). Default 0.07.
        dhe3_f_T: D-He3 tritium burn fraction in D-D sides (0-1). Default 0.97.

    Returns:
        (p_ash, p_neutron) tuple in MW
    """
    if fuel_type == FuelType.DT:
        # D + T -> He4(E_alpha_DT) + n(E_n_DT), Q = Q_DT
        ash_frac = E_alpha_DT / Q_DT

    elif fuel_type == FuelType.DD:
        # Semi-catalyzed burn model (20260211-dd-steady-state-burn-analysis.md)
        #
        # Primary (50/50 branching):
        #   Branch 1: D+D -> T(E_T_DD) + p(E_p_DD),    Q = Q_DD_pT
        #   Branch 2: D+D -> He3(E_He3_DD) + n(E_n_DD), Q = Q_DD_nHe3
        #
        # Secondary:
        #   D+T -> He4(E_alpha_DT) + n(E_n_DT), Q = Q_DT, burn fraction f_T
        #   D+He3 -> He4(E_alpha_DHe3) + p(E_p_DHe3), Q = Q_DHe3, burn fraction f_He3
        #
        # Per DD event (averaged over branches):
        #   E_charged = E_charged_primary + 0.5*f_T*E_alpha_DT + 0.5*f_He3*Q_DHe3
        #   E_total   = E_total_primary   + 0.5*f_T*Q_DT       + 0.5*f_He3*Q_DHe3
        E_charged = (
            _E_charged_primary_DD + 0.5 * dd_f_T * E_alpha_DT + 0.5 * dd_f_He3 * Q_DHe3
        )
        E_total = _E_total_primary_DD + 0.5 * dd_f_T * Q_DT + 0.5 * dd_f_He3 * Q_DHe3
        ash_frac = E_charged / E_total

    elif fuel_type == FuelType.DHE3:
        # Primary: D+He3 -> He4(E_alpha_DHe3) + p(E_p_DHe3), Q = Q_DHe3, 100% charged
        # D-D side reactions produce neutrons (unavoidable at any D-He3 temperature)
        # He3 from D-D sides recycled as fuel (f_He3=0 in DD chain context)
        E_n_dd = _E_neutron_primary_DD + 0.5 * dhe3_f_T * E_n_DT
        E_c_dd = _E_charged_primary_DD + 0.5 * dhe3_f_T * E_alpha_DT
        ash_frac = (1 - dhe3_dd_frac) + dhe3_dd_frac * E_c_dd / (E_n_dd + E_c_dd)

    elif fuel_type == FuelType.PB11:
        # p + B11 -> 3 He4, Q = Q_PB11, fully aneutronic
        ash_frac = 1.0

    else:
        raise ValueError(f"Unknown fuel type: {fuel_type}")

    return MW(p_nrl * ash_frac), MW(p_nrl * (1 - ash_frac))
