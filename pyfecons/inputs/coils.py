from dataclasses import dataclass
from typing import Optional

from pyfecons.enums import CoilMaterial
from pyfecons.inputs.magnet import Magnet
from pyfecons.units import Amperes, AmperesMillimeters2, Count, Meters, Meters2


@dataclass
class Coils:
    magnets: list[Magnet] = None

    # Structural multiplication factor
    # This is multiplied by the magnet material cost (incl mfr factor) and added to the total
    struct_factor: float = 0.5

    # Constants
    tape_w: Meters = 0.004  # REBCO tape width in meters
    tape_t: Meters = 0.00013  # REBCO tape thickness in meters

    # Current density of the tape in A/mm^2, set in magnetsAll function
    # approximate critical current density of YBCO at 18T
    # https://www.sciencedirect.com/science/article/pii/S0011227516303812
    j_tape_ybco: AmperesMillimeters2 = 150

    m_cost_ybco: float = 50  # Material cost of YBCO tape in $/kAm
    m_cost_ss: float = 5  # Material cost of stainless steel in $/kg
    m_cost_cu: float = 10.3  # Material cost of copper in $/kg
    # see https://cds.cern.ch/record/2839592/files/2020_04_21_SHiP_SpectrometerMagnet_Bajas.pdf
    rebco_density: float = 6350  # Density of REBCO tape in kg/m^3
    cu_density: float = 7900  # Density of copper in kg/m^3
    ss_density: float = 7900  # Density of stainless steel in kg/m^3
    mfr_factor: int = 3  # Manufacturing factor

    # Yuhu CICC HTS cable specifications
    cable_w: Meters = Meters(0.014)  # Cable width in meters
    cable_h: Meters = Meters(0.017)  # Cable height in meters
    frac_cs_cu_yuhu: float = (
        0.307  # Fractional cross-sectional area of copper in Yuhu Zhai's cable design
    )
    frac_cs_ss_yuhu: float = (
        0.257  # Fractional cross-sectional area of stainless steel in Yuhu Zhai's cable design
    )
    frac_cs_sc_yuhu: float = (
        0.257  # Fractional cross-sectional area of REBCO in Yuhu Zhai's cable design
    )
    tot_cs_area_yuhu: Meters2 = (
        0.000238  # Total cross-sectional area of Yuhu Zhai's cable design in m^2
    )

    # HTS pancake constants
    m_cost_i: float = 20  # Material cost of insulator in $/kg
    i_density: float = 3000  # Density of insulator in kg/m^3
    turns_p: float = 18  # Turns of REBCO tape per pancake
    max_cu_current: Amperes = Amperes(20)  # max current for water cooled AWG 8
    # https://www.engineeringtoolbox.com/wire-gauges-d_419.html
    cu_wire_d: float = 3.3e-3  # copper wire diameter in meters AWG8

    # COOLING 22.1.3.6
    c_frac: float = 0.1
    no_beams: Count = Count(
        20
    )  # number of beams supporting each coil, from the coil to the vessel
    beam_length: Meters = Meters(1.5)  # total length of each beam
    beam_cs_area: Meters2 = Meters2(0.25)  # cross-sectional area of each support beam
    t_op: float = 4  # operating temperature of magnets
    t_env: float = 300  # temperature of environment (to be cooled from)

    # === Simplified model fields ===
    # When b_max and r_coil are set (and magnets is empty), the simplified
    # scaling model is used instead of the detailed per-magnet calculation.
    b_max: float = None  # Peak magnetic field at coil (Tesla)
    # r_coil is the major radius at the coil bore — encompasses the plasma,
    # vacuum vessel, blanket, and shield. For aneutronic fuels (pB11, DHe3)
    # without a breeding blanket, r_coil can be significantly smaller than
    # for DT, because the coils can be placed closer to the plasma.
    r_coil: Meters = None  # Major radius at coil bore (meters)
    n_coils: int = None  # Number of physical coils (default from ConfinementType)
    coil_material: Optional[CoilMaterial] = (
        None  # Conductor material (default REBCO_HTS)
    )
    cost_per_kAm: float = None  # Conductor cost in $/kAm (default from material)
    coil_markup: float = None  # Manufacturing markup (default from ConfinementType)
    path_factor: float = None  # Stellarator coil path length multiplier (default 2.0)

    def __post_init__(self):
        if self.magnets is None:
            self.magnets = []
