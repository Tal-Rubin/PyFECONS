from dataclasses import dataclass

from pyfecons.units import M_USD


@dataclass
class CAS21:
    """Cost Category 21: Buildings

    Building categories for fusion power plant infrastructure.
    Mapped to CAS 22 equipment subsystems they house.

    Nuclear Island (High Radiation/Containment):
        C210200: Fusion Heat Island - houses 22.01.01-06, 22.01.09
        C210700: Hot Cell Building - houses 22.04 (rad waste, remote handling)
        C211000: Tritium/Fuel Building - houses 22.05 (fuel handling & storage)

    Power Conversion Island:
        C210300: Turbine Building - houses 23.xx (turbines, generators)
        C210400: Heat Exchanger Building - houses 22.02, 22.03 (coolant systems)

    Electrical & Power Systems:
        C210500: Power Supply Building - houses 22.01.07 (magnet/laser power)
        C211200: Onsite AC Power Building - switchgear, transformers
        C211500: Cryogenics Building - houses 22.01.03 cooling (LN2/LHe plants)

    Support Buildings:
        C210600: Reactor Auxiliaries Building - houses 22.06
        C210800: Reactor Services Building - workshops, maintenance
        C210900: Service Water Building - cooling towers, pumps
        C211100: Control Building - houses 22.07 (I&C)

    Administrative & Site:
        C210100: Site Improvements - roads, fencing, grading
        C211300: Administration Building - offices, training
        C211400: Site Services Building - warehousing, storage
        C211600: Security Building - access control
        C211700: Ventilation Stack - filtered exhaust

    New Buildings (derived from CAS 22 subsystems):
        C211800: Isotope Separation Plant - houses 22.01.12 (D2O, Li-6, B-11)
        C211801: Target Factory (IFE only) - houses 22.01.08 (pellet fabrication)
        C211802: Direct Energy Converter Building - houses 22.01.09 (if separate)
        C211803: Magnet/Component Assembly Hall - houses 22.01.11 (large assembly)
    """

    # Site & Infrastructure
    C210100: M_USD = None  # Site improvements and facilities

    # Nuclear Island
    C210200: M_USD = None  # Fusion Heat Island Building (reactor, magnets, shielding)

    # Power Conversion
    C210300: M_USD = None  # Turbine Building
    C210400: M_USD = None  # Heat Exchanger Building

    # Electrical Systems
    C210500: M_USD = None  # Power Supply & Energy Storage Building

    # Support Systems
    C210600: M_USD = None  # Reactor Auxiliaries Building
    C210700: M_USD = None  # Hot Cell Building
    C210800: M_USD = None  # Reactor Services Building
    C210900: M_USD = None  # Service Water Building
    C211000: M_USD = None  # Fuel Storage Building

    # Control & Admin
    C211100: M_USD = None  # Control Room Building
    C211200: M_USD = None  # Onsite AC Power Building
    C211300: M_USD = None  # Administration Building
    C211400: M_USD = None  # Site Services Building
    C211500: M_USD = None  # Cryogenics Building
    C211600: M_USD = None  # Security Building
    C211700: M_USD = None  # Ventilation Stack

    # New Buildings (CAS 22 subsystem-derived)
    C211800: M_USD = None  # Isotope Separation Plant (22.01.12)
    C211801: M_USD = None  # Target Factory - IFE only (22.01.08)
    C211802: M_USD = None  # Direct Energy Converter Building (22.01.09)
    C211803: M_USD = None  # Magnet/Component Assembly Hall (22.01.11)

    # Contingency & Total
    C211900: M_USD = None  # Contingency
    C210000: M_USD = None  # Total Buildings Cost
