from pyfecons.enums import FuelType
from pyfecons.units import MW


def compute_ash_neutron_split(
    p_nrl, fuel_type, dd_f_T=0.969, dd_f_He3=0.689, dhe3_dd_frac=0.07, dhe3_f_T=0.97
):
    """
    Compute charged-particle (ash) and neutron power from total fusion power.

    DT:   3.52 / 17.58 = 20.0% charged (He4 alpha)
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
        # D + T -> He4(3.52 MeV) + n(14.06 MeV), Q = 17.58 MeV
        ash_frac = 3.52 / 17.58

    elif fuel_type == FuelType.DD:
        # Semi-catalyzed burn model (20260211-dd-steady-state-burn-analysis.md)
        #
        # Primary (50/50 branching):
        #   Branch 1: D+D -> T(1.01) + p(3.02),  Q = 4.03 MeV
        #   Branch 2: D+D -> He3(0.82) + n(2.45), Q = 3.27 MeV
        #
        # Secondary:
        #   D+T -> He4(3.52) + n(14.06), Q = 17.58 MeV, burn fraction f_T
        #   D+He3 -> He4(3.67) + p(14.68), Q = 18.35 MeV, burn fraction f_He3
        #
        # Per DD event (averaged over branches):
        #   E_charged = 2.425 + 0.5*f_T*3.52 + 0.5*f_He3*18.35
        #   E_total   = 3.65  + 0.5*f_T*17.58 + 0.5*f_He3*18.35
        #   (equivalently: E_neutron = 1.225 + 0.5*f_T*14.06, E_charged = E_total - E_neutron)
        E_charged = 2.425 + 0.5 * dd_f_T * 3.52 + 0.5 * dd_f_He3 * 18.35
        E_total = 3.65 + 0.5 * dd_f_T * 17.58 + 0.5 * dd_f_He3 * 18.35
        ash_frac = E_charged / E_total

    elif fuel_type == FuelType.DHE3:
        # Primary: D+He3 -> He4(3.67) + p(14.68) = 18.35 MeV, 100% charged
        # D-D side reactions produce neutrons (unavoidable at any D-He3 temperature)
        # He3 from D-D sides recycled as fuel (f_He3=0 in DD chain context)
        E_n_dd = 1.225 + 0.5 * dhe3_f_T * 14.06
        E_c_dd = 2.425 + 0.5 * dhe3_f_T * 3.52
        ash_frac = (1 - dhe3_dd_frac) + dhe3_dd_frac * E_c_dd / (E_n_dd + E_c_dd)

    elif fuel_type == FuelType.PB11:
        # p + B11 -> 3 He4, Q = 8.7 MeV, fully aneutronic
        ash_frac = 1.0

    else:
        raise ValueError(f"Unknown fuel type: {fuel_type}")

    return MW(p_nrl * ash_frac), MW(p_nrl * (1 - ash_frac))
