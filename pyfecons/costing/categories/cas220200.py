from dataclasses import dataclass

from pyfecons.units import M_USD


@dataclass
class CAS2202:
    """CAS 220200: Main & Secondary Coolant Systems

    Universal subsystem required for all fusion fuel types to prevent first wall meltdown
    and extract thermal energy for electricity generation.

    Subsystems:
    - C220201: Primary coolant loop (includes first wall + blanket cooling)
    - C220202: Intermediate coolant loop
    - C220203: Secondary coolant loop (to steam generator)

    First Wall Cooling Integration:
    First wall cooling is critical for all fuel types (D-T, D-D, D-He³, p-B¹¹) to prevent
    structural meltdown. The first wall cooling system is integrated into the primary coolant
    loop (C220201) and is not separately tracked as a cost line item.

    For p-B¹¹ fusion: X-ray bremsstrahlung radiation deposits energy on the first wall as
    thermal heat, requiring active cooling despite the aneutronic nature of the fuel.

    Cost breakdown between first wall cooling and blanket cooling is not explicitly tracked
    in separate subcosts, but the combined primary coolant system cost accounts for both
    heat removal requirements.

    Reference: Comprehensive Fusion Reactor Subsystems Framework (2026-02-08)
    """

    C220201: M_USD = None  # Primary coolant (includes first wall + blanket cooling)
    C220202: M_USD = None  # Intermediate coolant
    C220203: M_USD = None  # Secondary coolant
    C220200: M_USD = None  # Total main & secondary coolant cost
