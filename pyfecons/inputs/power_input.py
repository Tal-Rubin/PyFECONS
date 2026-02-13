from dataclasses import dataclass

from pyfecons.units import MW, Percent, Ratio


@dataclass
class PowerInput:
    f_sub: Percent = None  # Subsystem and Control Fraction
    p_cryo: MW = None
    mn: Ratio = None  # Neutron energy multiplier
    eta_p: Percent = None  # Pumping power capture efficiency
    eta_th: Percent = None  # Thermal conversion efficiency
    p_trit: MW = None  # Tritium Systems
    p_house: MW = None  # Housekeeping power
    p_cool: MW = None  # Coil cooling power (TF + PF)
    p_coils: MW = None  # Power into coils (TF + PF)
    eta_pin: Percent = None  # Input power wall plug efficiency
    eta_pin1: Percent = None
    eta_pin2: Percent = None
    eta_de: Percent = None  # Direct energy conversion efficiency
    p_input: MW = None  # Input power
    p_implosion: MW = None  # Implosion laser power
    p_ignition: MW = None  # Ignition laser power
    p_target: MW = None  # Power into target factory
    p_pump: MW = None  # Primary coolant pumping power
    f_dec: Percent = (
        None  # DEC charged-particle capture fraction (0-1). Default 0 (no DEC).
    )
    dd_f_T: Percent = None  # DD tritium burn fraction (0-1). Default 0.969.
    dd_f_He3: Percent = None  # DD He-3 burn fraction (0-1). Default 0.689.
    dhe3_dd_frac: Percent = (
        None  # D-He3 energy fraction from D-D sides (0-1). Default 0.07.
    )
    dhe3_f_T: Percent = None  # D-He3 tritium burn in D-D sides (0-1). Default 0.97.
