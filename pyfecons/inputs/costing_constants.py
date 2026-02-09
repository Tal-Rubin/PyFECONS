from dataclasses import dataclass

from pyfecons.units import M_USD, MW, Ratio, Unknown


@dataclass
class CostingConstants:
    # CAS 10: Pre-construction fixed costs (M USD)
    site_permits: M_USD = M_USD(3)
    licensing_dt: M_USD = M_USD(5)
    licensing_dd: M_USD = M_USD(3)
    licensing_dhe3: M_USD = M_USD(1)
    licensing_pb11: M_USD = M_USD(0.1)
    licensing_time_dt: Unknown = Unknown(2.5)
    licensing_time_dd: Unknown = Unknown(1.5)
    licensing_time_dhe3: Unknown = Unknown(0.75)
    licensing_time_pb11: Unknown = Unknown(0.0)
    plant_permits: M_USD = M_USD(2)
    plant_studies_foak: M_USD = M_USD(20)
    plant_studies_noak: M_USD = M_USD(4)
    plant_reports: M_USD = M_USD(2)
    other_pre_construction: M_USD = M_USD(1)

    # CAS 10: Land cost calibration
    land_intensity_acres_per_mwe: Ratio = Ratio(0.25)
    land_cost_usd_per_acre: Unknown = Unknown(10000.0)
    us_farm_real_estate_value_usd_per_acre: Unknown = Unknown(4350.0)
    stack_release_fraction: Ratio = Ratio(0.10)

    # CAS 21: Building costs ($/kW)
    # Original buildings (sources: NETL B12A, ARIES cost documentation)
    site_improvements_per_kw: Unknown = Unknown(268)
    fusion_heat_island_per_kw: Unknown = Unknown(186.8)
    turbine_building_per_kw: Unknown = Unknown(54.0)
    heat_exchanger_building_per_kw: Unknown = Unknown(37.8)
    power_supply_energy_storage_per_kw: Unknown = Unknown(10.8)
    reactor_auxiliaries_per_kw: Unknown = Unknown(5.4)
    hot_cell_per_kw: Unknown = Unknown(93.4)
    reactor_services_per_kw: Unknown = Unknown(18.7)
    service_water_per_kw: Unknown = Unknown(0.3)
    fuel_storage_per_kw: Unknown = Unknown(1.1)
    control_room_per_kw: Unknown = Unknown(0.9)
    onsite_ac_power_per_kw: Unknown = Unknown(0.8)
    administration_per_kw: Unknown = Unknown(4.4)
    site_services_per_kw: Unknown = Unknown(1.6)
    cryogenics_per_kw: Unknown = Unknown(2.4)
    security_per_kw: Unknown = Unknown(0.9)
    ventilation_stack_per_kw: Unknown = Unknown(27.0)

    # CAS 21: New buildings derived from CAS 22 subsystems
    # 21.18 Isotope Separation Plant - houses CAS 22.01.12
    # Scaled from CANDU heavy water plants (~$100-500M for 1GW)
    # Includes D2O extraction, Li-6 enrichment (D-T), B-11 enrichment (p-B11)
    isotope_separation_per_kw: Unknown = Unknown(150.0)

    # 21.1801 Target Factory (IFE only) - houses CAS 22.01.08
    # Clean room facility for pellet fabrication and cryogenic handling
    # Scaled from NIF target production estimates
    target_factory_per_kw: Unknown = Unknown(50.0)

    # 21.1802 Direct Energy Converter Building - houses CAS 22.01.09
    # Separate structure for charged particle recovery (aneutronic fuels)
    # Only needed if DEC is external to main reactor building
    direct_energy_building_per_kw: Unknown = Unknown(25.0)

    # 21.1803 Magnet/Component Assembly Hall - houses CAS 22.01.11
    # High-bay facility for large component assembly before installation
    # Scaled from ITER assembly hall estimates
    assembly_hall_per_kw: Unknown = Unknown(15.0)

    # CAS 23-26: Equipment costs (M USD / MW)
    turbine_plant_per_mw: Unknown = Unknown(0.219)
    electric_plant_per_mw: Unknown = Unknown(0.054)
    misc_plant_per_mw: Unknown = Unknown(0.038)
    heat_rejection_per_mw: Unknown = Unknown(0.107)

    # CAS 28: Digital twin (M USD)
    digital_twin: M_USD = M_USD(5)

    # CAS 29: Contingency rate (fraction, applied across CAS 10/21/29/50)
    contingency_rate: Ratio = Ratio(0.1)

    # CAS 30: Indirect service cost coefficients (M USD / MW / year)
    field_indirect_cost_coeff: Unknown = Unknown(0.02)
    construction_supervision_coeff: Unknown = Unknown(0.05)
    design_services_coeff: Unknown = Unknown(0.03)
    indirect_reference_power_mw: MW = MW(150)

    # CAS 50: Supplementary costs
    shipping: M_USD = M_USD(8)
    spare_parts_fraction: Ratio = Ratio(0.1)
    taxes: M_USD = M_USD(100)
    insurance: M_USD = M_USD(1)
    fuel_load_reference_cost_musd: M_USD = M_USD(34)
    fuel_load_reference_power_mw: MW = MW(150)
    decommissioning: M_USD = M_USD(200)

    # CAS 60: Interest during construction coefficient (M USD / MW / year)
    idc_coeff: Unknown = Unknown(0.099)

    # CAS 70: O&M cost ($/MW/year)
    om_cost_per_mw_per_year: Unknown = Unknown(60)
