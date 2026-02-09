from dataclasses import dataclass

from pyfecons.units import M_USD


@dataclass
class CAS220112:
    """CAS 220112: Isotope Separation Systems

    Fuel-dependent isotope separation plant for fusion reactor fuel preparation.
    All fusion fuels require isotope separation infrastructure.

    Subsystems by fuel type:
    - D-T: D₂O extraction + Li-6 enrichment
    - D-D: D₂O extraction only
    - D-He³: D₂O extraction + He-3 separation (if available)
    - p-B¹¹: H-1 purification + B-11 enrichment

    Reference: Comprehensive Fusion Reactor Subsystems Framework (2026-02-08)
    Cost data from: CANDU heavy water plants, Li-6 COLEX facilities, B-11 laser separation
    """

    # D-T / D-D / D-He³: Deuterium extraction plant
    C22011201: M_USD = None  # Girdler-Sulfide or distillation ($100M-500M)

    # D-T only: Lithium-6 enrichment plant
    C22011202: M_USD = None  # COLEX process ($50M-150M)

    # p-B¹¹ only: Protium purification plant
    C22011203: M_USD = None  # Remove D from natural H ($10M-50M)

    # p-B¹¹ only: Boron-11 enrichment plant
    C22011204: M_USD = None  # Laser/chemical separation ($50M-200M)

    # D-He³ only: Helium-3 extraction system (future/lunar)
    C22011205: M_USD = None  # Lunar mining or T-decay infrastructure (TBD)

    # Total isotope separation costs
    C220112: M_USD = None
