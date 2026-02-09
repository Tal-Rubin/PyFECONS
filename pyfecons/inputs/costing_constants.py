from dataclasses import dataclass

from pyfecons.units import M_USD, MW, Ratio, Unknown


@dataclass
class CostingConstants:
    # CAS 10: Pre-construction fixed costs (M USD)
    # Site permits: EA under NEPA (~$0.2-1M), site characterization ($0.5-2M),
    # state/local construction permits ($0.1-0.5M). Fusion under Part 30
    # requires EA not full EIS (avg $6M for DOE projects per GAO-14-369).
    site_permits: M_USD = M_USD(3)
    # Plant licensing costs under NRC Part 30 (byproduct materials) framework.
    # Covers NRC application, safety analysis, radiation protection, emergency
    # planning, and waste management. Varies by fuel type due to differing
    # tritium inventories and neutron activation levels.
    licensing_dt: M_USD = M_USD(5)  # D-T: full Part 30 ($1-10M range)
    licensing_dd: M_USD = M_USD(
        3
    )  # D-D: reduced Part 30, no breeding blankets ($0.5-5M)
    licensing_dhe3: M_USD = M_USD(
        1
    )  # D-He3: minimal Part 30, mostly aneutronic ($0.2-2M)
    licensing_pb11: M_USD = M_USD(
        0.1
    )  # p-B11: likely no NRC, general industrial only (~$0)
    # Licensing timeline (years) by fuel type under NRC Part 30.
    # Added to physical construction time for financial calculations (IDC, CRF).
    # D-T: full Part 30 review with tritium and activation analysis.
    # D-D: reduced scope, no breeding blanket review.
    # D-He3: minimal Part 30, mostly aneutronic.
    # p-B11: likely exempt from NRC, standard industrial permits only.
    licensing_time_dt: Unknown = Unknown(2.5)
    licensing_time_dd: Unknown = Unknown(1.5)
    licensing_time_dhe3: Unknown = Unknown(0.75)
    licensing_time_pb11: Unknown = Unknown(0.0)
    # Plant permits: building codes, electrical, fire, air quality, discharge.
    # Standard industrial permits, not nuclear-specific ($1-3M typical).
    plant_permits: M_USD = M_USD(2)
    # Plant studies: engineering feasibility, safety case, technology qualification.
    # FOAK: $10-100M+ for novel designs (safety case, technology qualification).
    # NOAK: $3-5M for site-specific adaptation of established designs.
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
