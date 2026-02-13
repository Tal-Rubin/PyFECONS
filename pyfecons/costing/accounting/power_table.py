from dataclasses import dataclass

from pyfecons.units import MW, Ratio, Unknown


@dataclass
class PowerTable:
    """Power table data."""

    p_ash: MW = None  # Charged fusion product power (alphas, protons, tritons, He-3)
    p_neutron: MW = None  # Neutron power
    p_wall: MW = None  # Ash thermal power deposited on walls (-> thermal cycle)
    p_dec_waste: MW = None  # DEC waste heat (separately cooled, lost)
    p_cool: MW = None
    p_aux: MW = None  # Auxiliary systems
    p_coils: MW = None
    p_th: MW = None  # Thermal power
    p_the: MW = None  # Total thermal electric power
    p_dee: MW = None
    p_et: MW = None  # Total (Gross) Electric Power
    p_loss: MW = None  # Lost Power
    p_pump: MW = None  # Primary Coolant Pumping Power
    p_sub: MW = None  # Subsystem and Control Power
    q_sci: Unknown = None  # Scientific Q
    q_eng: Unknown = None  # Engineering Q
    rec_frac: Unknown = None  # Recirculating power fraction
    p_net: MW = None  # Output Power (Net Electric Power)
    gain_e: Ratio = None  # Gain in Electric Power
