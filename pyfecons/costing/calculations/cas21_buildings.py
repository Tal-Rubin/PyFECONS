from pyfecons.costing.accounting.power_table import PowerTable
from pyfecons.costing.calculations.conversions import k_to_m_usd
from pyfecons.costing.categories.cas210000 import CAS21
from pyfecons.enums import FuelType, FusionMachineType
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.costing_constants import CostingConstants
from pyfecons.units import M_USD


def cas_21_building_costs(
    basic: Basic, power_table: PowerTable, constants: CostingConstants
) -> CAS21:
    """Calculate Cost Category 21: Buildings

    Buildings are mapped to CAS 22 equipment subsystems they house:
    - Nuclear Island: Fusion Heat Island (22.01.01-06), Hot Cell (22.04), Fuel Storage (22.05)
    - Power Conversion: Turbine (23.xx), Heat Exchanger (22.02-03)
    - Electrical: Power Supply (22.01.07), Cryogenics (22.01.03 cooling)
    - Support: Reactor Aux (22.06), Control (22.07)
    - New: Isotope Separation (22.01.12), Target Factory (22.01.08), DEC (22.01.09), Assembly Hall (22.01.11)

    References:
        [1] NETL reference case B12A
        [2] Waganer, L.M., 2013. ARIES cost account documentation. San Diego: University of California.
    """
    cas21 = CAS21()
    p_et = power_table.p_et

    # Fuel scaling: 0.5 for non-DT fuels (less tritium containment structure needed)
    fuel_scaling_factor = get_fuel_scaling_factor(
        basic.fusion_machine_type, basic.fuel_type
    )

    # Isotope separation scaling by fuel type
    isotope_scaling_factor = get_isotope_separation_scaling(basic.fuel_type)

    # =========================================================================
    # SITE & INFRASTRUCTURE
    # =========================================================================

    # 21.01.00 Site improvements and facilities. Source: [1] cost account 13, page 134
    cas21.C210100 = M_USD(
        k_to_m_usd(constants.site_improvements_per_kw) * p_et * fuel_scaling_factor
    )

    # =========================================================================
    # NUCLEAR ISLAND (houses CAS 22.01.01-06, 22.01.09)
    # =========================================================================

    # 21.02.00 Fusion Heat Island Building, Concrete & Steel. Source: [2], pg 11.
    # Houses: first wall, blanket, shield, magnets/lasers, vacuum vessel, primary structure
    cas21.C210200 = M_USD(
        k_to_m_usd(constants.fusion_heat_island_per_kw) * p_et * fuel_scaling_factor
    )

    # =========================================================================
    # POWER CONVERSION ISLAND (houses CAS 22.02, 22.03, 23.xx)
    # =========================================================================

    # 21.03.00 Turbine building, Steel. Source: [1] cost account 14.2, page 134
    cas21.C210300 = M_USD(k_to_m_usd(constants.turbine_building_per_kw) * p_et)

    # 21.04.00 Heat exchanger building, Concrete & Steel. Source: [1] cost account 14.2
    # Houses: primary/intermediate/secondary coolant loops (CAS 22.02), aux cooling (22.03)
    cas21.C210400 = M_USD(k_to_m_usd(constants.heat_exchanger_building_per_kw) * p_et)

    # =========================================================================
    # ELECTRICAL & POWER SYSTEMS (houses CAS 22.01.07)
    # =========================================================================

    # 21.05.00 Power supply & energy storage, Concrete & Steel. Source: scaled from [1]
    # Houses: magnet power supplies, capacitor banks, pulse power (CAS 22.01.07)
    cas21.C210500 = M_USD(
        k_to_m_usd(constants.power_supply_energy_storage_per_kw) * p_et
    )

    # 21.12.00 Onsite AC power, Steel frame
    cas21.C211200 = M_USD(k_to_m_usd(constants.onsite_ac_power_per_kw) * p_et)

    # 21.15.00 Cryogenics, Steel frame. Source: scaled from [1] cost account 14.4
    # Houses: LN2/LHe plants for superconducting magnets (supports CAS 22.01.03)
    # Zero for non-superconducting or IFE without SC magnets
    cryogenics_scaling = get_cryogenics_scaling(basic.fusion_machine_type)
    cas21.C211500 = M_USD(
        k_to_m_usd(constants.cryogenics_per_kw) * p_et * cryogenics_scaling
    )

    # =========================================================================
    # SUPPORT BUILDINGS (houses CAS 22.04, 22.05, 22.06, 22.07)
    # =========================================================================

    # 21.06.00 Reactor auxiliaries, Concrete & Steel. Source: [1] cost account 14.8
    # Houses: miscellaneous reactor plant equipment (CAS 22.06)
    cas21.C210600 = M_USD(k_to_m_usd(constants.reactor_auxiliaries_per_kw) * p_et)

    # 21.07.00 Hot cell, Concrete & Steel. Source: [1] cost account 14.1
    # Houses: remote handling, activated component repair, rad waste (CAS 22.04)
    cas21.C210700 = M_USD(
        k_to_m_usd(constants.hot_cell_per_kw) * p_et * fuel_scaling_factor
    )

    # 21.08.00 Reactor services, Steel frame. Source: scaled from [1] cost account 14.1
    cas21.C210800 = M_USD(k_to_m_usd(constants.reactor_services_per_kw) * p_et)

    # 21.09.00 Service water, Steel frame. Source: [1] cost account 14.4
    cas21.C210900 = M_USD(k_to_m_usd(constants.service_water_per_kw) * p_et)

    # 21.10.00 Fuel storage, Steel frame. Source: scaled from [1] cost account 14.1
    # Houses: tritium storage, pellet storage, fuel handling (CAS 22.05)
    cas21.C211000 = M_USD(
        k_to_m_usd(constants.fuel_storage_per_kw) * p_et * fuel_scaling_factor
    )

    # 21.11.00 Control room, Steel frame
    # Houses: instrumentation & control systems (CAS 22.07)
    cas21.C211100 = M_USD(k_to_m_usd(constants.control_room_per_kw) * p_et)

    # =========================================================================
    # ADMINISTRATIVE & SITE
    # =========================================================================

    # 21.13.00 Administration, Steel frame. Source: [1] cost account 14.3
    cas21.C211300 = M_USD(k_to_m_usd(constants.administration_per_kw) * p_et)

    # 21.14.00 Site services, Steel frame. Source: scaled from [1] cost account 14.6
    cas21.C211400 = M_USD(k_to_m_usd(constants.site_services_per_kw) * p_et)

    # 21.16.00 Security, Steel frame. Source: scaled from [1] cost account 14.8
    cas21.C211600 = M_USD(k_to_m_usd(constants.security_per_kw) * p_et)

    # 21.17.00 Ventilation stack, Steel cylinder & concrete foundation
    # Source: scaled from [1] cost account 14.3
    cas21.C211700 = M_USD(k_to_m_usd(constants.ventilation_stack_per_kw) * p_et)

    # =========================================================================
    # NEW BUILDINGS (derived from CAS 22 subsystems)
    # =========================================================================

    # 21.18.00 Isotope Separation Plant - houses CAS 22.01.12
    # D-T: D2O extraction + Li-6 enrichment
    # D-D: D2O extraction only
    # D-He3: D2O extraction + He-3 separation
    # p-B11: H-1 purification + B-11 enrichment
    # Scaled from CANDU heavy water plants (~$100-500M for 1GW)
    cas21.C211800 = M_USD(
        k_to_m_usd(constants.isotope_separation_per_kw) * p_et * isotope_scaling_factor
    )

    # 21.18.01 Target Factory (IFE only) - houses CAS 22.01.08
    # Clean room facility for pellet fabrication and cryogenic target handling
    # Only applicable to IFE reactor types
    if basic.fusion_machine_type == FusionMachineType.IFE:
        cas21.C211801 = M_USD(k_to_m_usd(constants.target_factory_per_kw) * p_et)
    else:
        cas21.C211801 = M_USD(0)

    # 21.18.02 Direct Energy Converter Building - houses CAS 22.01.09
    # Separate structure for charged particle recovery
    # More significant for aneutronic fuels (D-He3, p-B11) with higher alpha fractions
    dec_scaling = get_dec_building_scaling(basic.fuel_type)
    cas21.C211802 = M_USD(
        k_to_m_usd(constants.direct_energy_building_per_kw) * p_et * dec_scaling
    )

    # 21.18.03 Magnet/Component Assembly Hall - houses CAS 22.01.11
    # High-bay facility for large component assembly before installation
    # Scaled from ITER assembly hall estimates
    cas21.C211803 = M_USD(k_to_m_usd(constants.assembly_hall_per_kw) * p_et)

    # =========================================================================
    # TOTAL CALCULATION
    # =========================================================================

    # Sum all building costs (before contingency)
    cas21.C210000 = M_USD(
        cas21.C210100  # Site improvements
        + cas21.C210200  # Fusion Heat Island
        + cas21.C210300  # Turbine Building
        + cas21.C210400  # Heat Exchanger
        + cas21.C210500  # Power Supply
        + cas21.C210600  # Reactor Auxiliaries
        + cas21.C210700  # Hot Cell
        + cas21.C210800  # Reactor Services
        + cas21.C210900  # Service Water
        + cas21.C211000  # Fuel Storage
        + cas21.C211100  # Control Room
        + cas21.C211200  # Onsite AC Power
        + cas21.C211300  # Administration
        + cas21.C211400  # Site Services
        + cas21.C211500  # Cryogenics
        + cas21.C211600  # Security
        + cas21.C211700  # Ventilation Stack
        + cas21.C211800  # Isotope Separation Plant (NEW)
        + cas21.C211801  # Target Factory - IFE only (NEW)
        + cas21.C211802  # Direct Energy Converter Building (NEW)
        + cas21.C211803  # Magnet/Component Assembly Hall (NEW)
    )

    # Contingency: 10% for FOAK, 0% for NOAK
    if basic.noak:
        cas21.C211900 = M_USD(0)
    else:
        cas21.C211900 = M_USD(constants.contingency_rate * cas21.C210000)

    cas21.C210000 = M_USD(cas21.C210000 + cas21.C211900)

    return cas21


def get_fuel_scaling_factor(
    fusion_machine_type: FusionMachineType, fuel_type: FuelType
) -> float:
    """Scale containment buildings based on tritium handling requirements.

    D-T fuel requires full tritium containment infrastructure.
    Other fuels require less containment structure (0.5x).
    """
    if fusion_machine_type != FusionMachineType.MFE:
        return 1.0
    if fuel_type == FuelType.DT:
        return 1.0
    return 0.5


def get_isotope_separation_scaling(fuel_type: FuelType) -> float:
    """Scale isotope separation plant based on fuel type complexity.

    D-T: Full scale (D2O + Li-6 enrichment) = 1.0
    D-D: D2O extraction only = 0.6
    D-He3: D2O + He-3 (limited availability) = 0.8
    p-B11: H-1 purification + B-11 enrichment = 1.2 (more complex)
    """
    scaling = {
        FuelType.DT: 1.0,
        FuelType.DD: 0.6,
        FuelType.DHE3: 0.8,
        FuelType.PB11: 1.2,
    }
    return scaling.get(fuel_type, 1.0)


def get_cryogenics_scaling(fusion_machine_type: FusionMachineType) -> float:
    """Scale cryogenics building based on superconducting magnet requirements.

    MFE: Full cryogenics for superconducting TF/CS/PF coils = 1.0
    IFE: Minimal cryogenics (target handling only) = 0.3
    MIF: Varies by design = 0.5
    """
    scaling = {
        FusionMachineType.MFE: 1.0,
        FusionMachineType.IFE: 0.3,
        FusionMachineType.MIF: 0.5,
    }
    return scaling.get(fusion_machine_type, 1.0)


def get_dec_building_scaling(fuel_type: FuelType) -> float:
    """Scale Direct Energy Converter building based on charged particle output.

    Aneutronic fuels (D-He3, p-B11) produce more charged particles,
    requiring larger DEC infrastructure.

    D-T: Minimal DEC (most energy in neutrons) = 0.2
    D-D: Some DEC potential = 0.4
    D-He3: Significant DEC (high alpha fraction) = 1.0
    p-B11: Maximum DEC (fully aneutronic) = 1.5
    """
    scaling = {
        FuelType.DT: 0.2,
        FuelType.DD: 0.4,
        FuelType.DHE3: 1.0,
        FuelType.PB11: 1.5,
    }
    return scaling.get(fuel_type, 1.0)
