from typing import TYPE_CHECKING, Optional

import numpy as np

from pyfecons.costing.accounting.power_table import PowerTable
from pyfecons.costing.calculations.conversions import inflation_2005_2024, to_m_usd
from pyfecons.costing.calculations.thermal import (
    compute_iter_cost_per_MW,
    compute_q_in_n_per_coil,
    compute_q_in_struct,
    k_steel,
)
from pyfecons.costing.categories.cas220101 import CAS220101
from pyfecons.costing.categories.cas220106 import CAS220106, VesselCost, VesselCosts
from pyfecons.inputs.coils import Coils
from pyfecons.inputs.radial_build import RadialBuild
from pyfecons.inputs.vacuum_system import VacuumSystem
from pyfecons.units import M_USD, USD, Kilograms, Meters3

if TYPE_CHECKING:
    from pyfecons.inputs.costing_constants import VacuumSystemConstants


# MFE vacuum system calculations
def cas_220106_vacuum_system_costs(
    vacuum_system: VacuumSystem,
    radial_build: RadialBuild,
    coils: Coils,
    power_table: PowerTable,
    cas220101: CAS220101,
    constants: Optional["VacuumSystemConstants"] = None,
) -> CAS220106:
    """Calculate CAS 22.01.06 Vacuum System costs.

    Args:
        vacuum_system: Vacuum system configuration
        radial_build: Radial build parameters
        coils: Coil configuration
        power_table: Power table data
        cas220101: Reactor equipment data
        constants: Optional configurable vacuum system parameters. Uses defaults if None.

    Returns:
        CAS220106 with calculated costs
    """
    # Use provided constants or default values for backward compatibility
    if constants is None:
        from pyfecons.inputs.costing_constants import VacuumSystemConstants

        constants = VacuumSystemConstants()
    # 22.1.6 Vacuum system
    cas220106 = CAS220106()
    build = cas220101

    # 22.1.6.1 Vacuum Vessel
    # from radial build
    syst_spool_ir = (
        build.axis_ir - (build.vessel_ir - build.axis_ir) * 0.5
    )  # Spool inner radius (goes around CS)
    syst_doors_ir = build.vessel_ir  # doors inner radius (goes within TF)
    syst_height = (
        radial_build.elon * build.vessel_vol / (np.pi * build.vessel_ir**2)
    )  # System height

    # Cost reference from: Lester M. Waganer et al., 2006, Fusion Engineering and Design. URL:
    #   http://qedfusion.org/LIB/REPORT/CONF/ACTsyscodedocs/ASC_FED2_Dragojlovic.pdf
    # TODO figure out why intellij is giving warnings for these assignments
    cas220106.vessel_costs = VesselCosts(
        spool_assembly=VesselCost(
            name="Spool assembly",
            total_mass=Kilograms(136043),
            material_cost=USD(49430),
            fabrication_cost=USD(2614897),
            total_cost=USD(2800370),
        ),
        removable_doors=VesselCost(
            name="Removable doors",
            total_mass=Kilograms(211328),
            material_cost=USD(859863),
            fabrication_cost=USD(6241880),
            total_cost=USD(7313071),
        ),
        door_frames=VesselCost(
            name="Doorframes",
            total_mass=Kilograms(53632),
            material_cost=USD(356555),
            fabrication_cost=USD(2736320),
            total_cost=USD(3146507),
        ),
        port_enclosures=VesselCost(
            name="Port enclosures",
            total_mass=Kilograms(712448),
            material_cost=USD(2020698),
            fabrication_cost=USD(14309096),
            total_cost=USD(17042242),
        ),
        total=VesselCost(name="Total"),
        contingency=VesselCost(name="Contingency (20%)"),
        prime_contractor_fee=VesselCost(name="Prime contractor fee (12%)"),
        total_subsystem_cost=VesselCost(name="Total subsystem cost"),
    )

    for cost in [
        cas220106.vessel_costs.spool_assembly,
        cas220106.vessel_costs.removable_doors,
        cas220106.vessel_costs.door_frames,
        cas220106.vessel_costs.port_enclosures,
    ]:
        geometry_factor = (
            (syst_spool_ir / constants.aries_spool_ir)
            * (syst_height / constants.aries_spool_height)
            if cost.name == "Spool assembly"
            else (syst_doors_ir / constants.aries_door_irb)
            * (syst_height / constants.aries_spool_height)
        )
        cost.total_mass = cost.total_mass * geometry_factor

        # Scaling costs based on new mass
        if cost.total_mass > 0:
            # New cost based on per kg rate, applying learning credit and inflation
            cost.material_cost = (
                cost.material_cost
                * geometry_factor
                * vacuum_system.learning_credit
                * inflation_2005_2024
            )
            cost.fabrication_cost = (
                cost.fabrication_cost
                * geometry_factor
                * vacuum_system.learning_credit
                * inflation_2005_2024
            )

        # Updating total cost after scaling other costs
        cost.total_cost = cost.material_cost + cost.fabrication_cost

        # Summing updated values to "Total"
        cas220106.vessel_costs.total.total_mass += cost.total_mass
        cas220106.vessel_costs.total.material_cost += cost.material_cost
        cas220106.vessel_costs.total.fabrication_cost += cost.fabrication_cost
        cas220106.vessel_costs.total.total_cost += cost.total_mass

    # Calculate new contingency and prime contractor fee based on updated total cost
    total_cost = cas220106.vessel_costs.total.total_cost
    cas220106.vessel_costs.contingency.total_cost = (
        total_cost * constants.contingency_rate
    )
    cas220106.vessel_costs.prime_contractor_fee.total_cost = (
        total_cost * constants.prime_contractor_fee
    )

    # Update the total subsystem cost
    cas220106.vessel_costs.total_subsystem_cost.total_cost = (
        total_cost
        + cas220106.vessel_costs.contingency.total_cost
        + cas220106.vessel_costs.prime_contractor_fee.total_cost
    )

    # Calculate mass and cost
    cas220106.mass_struct = cas220106.vessel_costs.total.total_mass
    cas220106.ves_vol = Meters3(
        np.pi * (syst_doors_ir**2 - syst_spool_ir**2) * syst_height
    )
    cas220106.C22010601 = to_m_usd(
        cas220106.vessel_costs.total_subsystem_cost.total_cost
    )

    # COOLING 22.1.3.2
    # Operating temperature of magnets and environment temperature from constants
    T_op = float(constants.t_magnet_operating)
    T_env = float(constants.t_environment)

    def calc_torus_sa(min_r: float, maj_r: float):
        return 4 * np.pi**2 * maj_r * min_r

    # Scaling cooling costs from ITER see Serio, L., ITER Organization and Domestic Agencies and Collaborators,
    #  2010, April. Challenges for cryogenics at ITER. In AIP Conference Proceedings (Vol. 1218, No. 1, pp. 651-662).
    #  American Institute of Physics.
    load_area_1 = calc_torus_sa((build.ht_shield_ir - build.axis_ir), build.axis_ir)
    load_area_2 = calc_torus_sa((build.lt_shield_ir - build.axis_ir), build.axis_ir)
    p_neutron = power_table.p_neutron
    # Neutron heat load on HT Shield
    q_in_n = compute_q_in_n_per_coil(
        load_area_1, p_neutron, build.coil_ir, build.axis_ir
    ) + 0.1 * compute_q_in_n_per_coil(
        load_area_2, p_neutron, build.coil_ir, build.axis_ir
    )
    q_in_struct = compute_q_in_struct(
        coils, k_steel((coils.t_env + coils.t_op) / 2), (coils.t_env + coils.t_op) / 2
    )
    q_in = q_in_struct + q_in_n  # total input heat for one coil

    cas220106.C22010602 = M_USD(q_in * compute_iter_cost_per_MW(coils))

    # VACUUM PUMPING 22.1.6.3
    # Number of vacuum pumps required to pump the full vacuum in 1 second
    no_vpumps = int(cas220106.ves_vol / vacuum_system.vpump_cap)
    cas220106.C22010603 = to_m_usd(no_vpumps * vacuum_system.cost_pump)

    # ROUGHING PUMP 22.1.6.4
    # from STARFIRE reference, only 1 needed
    cas220106.C22010604 = to_m_usd(
        constants.roughing_pump_base_cost * constants.roughing_pump_factor
    )

    cas220106.C220106 = M_USD(
        cas220106.C22010601
        + cas220106.C22010602
        + cas220106.C22010603
        + cas220106.C22010604
    )
    return cas220106
