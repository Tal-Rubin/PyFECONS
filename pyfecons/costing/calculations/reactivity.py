"""
Minimal fusion reactivity data for 0D plasma sanity checks.

Stores peak thermal reactivity ⟨σv⟩ per fuel type and provides a function to
compute the minimum electron density required to achieve a given fusion power
in a given plasma volume, assuming best-case conditions (uniform plasma at
peak ⟨σv⟩ temperature with optimal reactant mix).

This is NOT a plasma physics model. It answers one question: "under the most
optimistic assumptions, what density does this power + volume combination
require?" If even that density is unreasonably high, the cost calculation
is meaningless.

Sources: NRL Plasma Formulary, Bosch & Hale (1992) Nuclear Fusion 32(4).
"""

import math

import scipy.constants as _sc

from pyfecons.costing.calculations.fuel_physics import (
    Q_DT,
    Q_PB11,
    Q_DD_nHe3,
    Q_DD_pT,
    Q_DHe3,
    compute_ash_neutron_split,
)
from pyfecons.enums import FuelType

_MeV_to_J = _sc.eV * 1e6

# ---------------------------------------------------------------------------
# Peak thermal reactivity ⟨σv⟩ [m³/s] at optimal ion temperature
#
# These are the maximum of ⟨σv⟩(T) for a Maxwellian plasma. Using peak
# values gives the most optimistic (lowest) density estimate.
# ---------------------------------------------------------------------------
PEAK_SIGMA_V = {
    FuelType.DT: 2.6e-22,  # @ T_i ~ 15 keV (Bosch & Hale)
    FuelType.DD: 3.3e-24,  # @ T_i ~ 50 keV (both branches combined)
    FuelType.DHE3: 5.0e-22,  # @ T_i ~ 200 keV
    FuelType.PB11: 3.4e-22,  # @ T_i ~ 300 keV
}

# ---------------------------------------------------------------------------
# Charge neutrality factors: n_e / n_ion for optimal reactant mix
#
# For A + B reaction with optimal 50:50 ion mix (n_A = n_B = n_ion):
#   n_e = (Z_A + Z_B) × n_ion
#
# DT:   Z_D=1, Z_T=1  → n_e = 2 × n_ion
# DD:   single species → n_e = n_D (Z_D=1)
# DHe3: Z_D=1, Z_He3=2 → n_e = 3 × n_ion (at 50:50 ion mix)
# PB11: Z_p=1, Z_B11=5 → n_e = 6 × n_ion (at 50:50 ion mix)
# ---------------------------------------------------------------------------
CHARGE_FACTOR = {
    FuelType.DT: 2,
    FuelType.DD: 1,  # single species: n_e = n_D
    FuelType.DHE3: 3,
    FuelType.PB11: 6,
}

# ---------------------------------------------------------------------------
# Species factor for reaction rate per unit n_ion²
#
# For A ≠ B: rate = n_A × n_B × ⟨σv⟩ = n_ion² × ⟨σv⟩ (at 50:50)
# For A = A: rate = n_A² × ⟨σv⟩ / 2 (identical particle correction)
# ---------------------------------------------------------------------------
SPECIES_FACTOR = {
    FuelType.DT: 1.0,
    FuelType.DD: 0.5,  # identical particles
    FuelType.DHE3: 1.0,
    FuelType.PB11: 1.0,
}

# ---------------------------------------------------------------------------
# Peak reactivity ion temperature [keV] per fuel type
#
# These are the T_i at which ⟨σv⟩(T) is maximized for a Maxwellian plasma.
# Used to compute plasma stored energy for the confinement time estimate.
# ---------------------------------------------------------------------------
PEAK_TEMPERATURE = {
    FuelType.DT: 15.0,  # keV (Bosch & Hale)
    FuelType.DD: 50.0,  # keV
    FuelType.DHE3: 200.0,  # keV
    FuelType.PB11: 300.0,  # keV
}

# ---------------------------------------------------------------------------
# Total particle factor: (n_e + n_ions_total) / n_e
#
# Used to compute total plasma thermal energy:
#   W = (3/2) × PARTICLE_FACTOR × n_e × kT × V
#
# DT:   n_e = 2×n_ion, n_ions = 2×n_ion → (2+2)/2 = 2
# DD:   n_e = n_D, n_ions = n_D → (1+1)/1 = 2
# DHe3: n_e = 3×n_ion, n_ions = 2×n_ion → (3+2)/3 = 5/3
# PB11: n_e = 6×n_ion, n_ions = 2×n_ion → (6+2)/6 = 4/3
# ---------------------------------------------------------------------------
PARTICLE_FACTOR = {
    FuelType.DT: 2.0,
    FuelType.DD: 2.0,
    FuelType.DHE3: 5.0 / 3.0,
    FuelType.PB11: 4.0 / 3.0,
}


def _effective_q_mev(fuel_type, dd_f_T=0.969, dd_f_He3=0.689):
    """
    Effective energy release per primary reaction [MeV], including
    secondary burns for DD.

    For DT, DHe3, PB11: just the primary Q-value.
    For DD: includes energy from semi-catalyzed secondary DT and DHe3 reactions.
    """
    if fuel_type == FuelType.DT:
        return Q_DT
    elif fuel_type == FuelType.DD:
        # Per DD primary event (averaged over 50/50 branches):
        #   E = E_primary + 0.5 * f_T * Q_DT + 0.5 * f_He3 * Q_DHe3
        E_primary = 0.5 * Q_DD_pT + 0.5 * Q_DD_nHe3
        return E_primary + 0.5 * dd_f_T * Q_DT + 0.5 * dd_f_He3 * Q_DHe3
    elif fuel_type == FuelType.DHE3:
        return Q_DHe3
    elif fuel_type == FuelType.PB11:
        return Q_PB11
    else:
        raise ValueError(f"Unknown fuel type: {fuel_type}")


def min_density_for_power(
    p_fusion_mw,
    volume_m3,
    fuel_type,
    dd_f_T=0.969,
    dd_f_He3=0.689,
):
    """
    Compute minimum electron density [m⁻³] to achieve p_fusion in the given
    volume, assuming uniform plasma at peak ⟨σv⟩ with optimal reactant mix.

    This is the most optimistic estimate. Actual required density is higher due
    to non-uniform profiles, sub-optimal temperature, impurities, and radiation.

    Formula:
        P/V = n_ion² × ⟨σv⟩_peak × Q_eff × species_factor
        n_ion = sqrt(P / (V × ⟨σv⟩_peak × Q_eff × species_factor))
        n_e = charge_factor × n_ion

    Args:
        p_fusion_mw: Total fusion power [MW]
        volume_m3: Plasma volume [m³]
        fuel_type: FuelType enum
        dd_f_T: DD tritium burn fraction (only used for DD fuel)
        dd_f_He3: DD He-3 burn fraction (only used for DD fuel)

    Returns:
        Minimum electron density [m⁻³]
    """
    p_watts = p_fusion_mw * 1e6
    sigma_v = PEAK_SIGMA_V[fuel_type]
    q_joules = _effective_q_mev(fuel_type, dd_f_T, dd_f_He3) * _MeV_to_J
    species = SPECIES_FACTOR[fuel_type]
    charge = CHARGE_FACTOR[fuel_type]

    # P/V = n_ion² × σv × Q × species_factor
    # n_ion = sqrt(P / (V × σv × Q × species_factor))
    n_ion = math.sqrt(p_watts / (volume_m3 * sigma_v * q_joules * species))
    n_e = charge * n_ion

    return n_e


def required_confinement_time(
    p_fusion_mw,
    volume_m3,
    fuel_type,
    p_input_mw,
    dd_f_T=0.969,
    dd_f_He3=0.689,
    dhe3_dd_frac=0.07,
    dhe3_f_T=0.97,
):
    """
    Compute minimum required energy confinement time [seconds] assuming
    best-case 0D conditions (uniform plasma at peak ⟨σv⟩, zero radiation).

    Steady-state energy balance (ignoring radiation):
        τ_E = W_plasma / (P_ash + P_external)

    where W_plasma = (3/2) × particle_factor × n_e × kT × V, with n_e from
    min_density_for_power() (same optimistic assumptions).

    This is the absolute minimum confinement time needed. Real devices need
    longer τ_E due to radiation losses (bremsstrahlung, synchrotron, line).

    Args:
        p_fusion_mw: Total fusion power [MW]
        volume_m3: Plasma volume [m³]
        fuel_type: FuelType enum
        p_input_mw: External heating power [MW]
        dd_f_T: DD tritium burn fraction
        dd_f_He3: DD He-3 burn fraction
        dhe3_dd_frac: DHe3 energy fraction from DD side reactions
        dhe3_f_T: DHe3 tritium burn fraction in DD sides

    Returns:
        Minimum confinement time τ_E [seconds]
    """
    keV_to_J = _sc.eV * 1e3

    # Reuse min_density under the same best-case assumptions
    n_e = min_density_for_power(
        p_fusion_mw, volume_m3, fuel_type, dd_f_T=dd_f_T, dd_f_He3=dd_f_He3
    )

    # Plasma thermal energy: W = (3/2) × particle_factor × n_e × kT × V
    kT = PEAK_TEMPERATURE[fuel_type] * keV_to_J
    W_plasma = 1.5 * PARTICLE_FACTOR[fuel_type] * n_e * kT * volume_m3

    # Charged-particle self-heating power
    p_ash_mw, _ = compute_ash_neutron_split(
        p_fusion_mw,
        fuel_type,
        dd_f_T=dd_f_T,
        dd_f_He3=dd_f_He3,
        dhe3_dd_frac=dhe3_dd_frac,
        dhe3_f_T=dhe3_f_T,
    )

    # τ_E = W / (P_ash + P_external)
    p_heating_watts = (float(p_ash_mw) + p_input_mw) * 1e6
    return W_plasma / p_heating_watts
