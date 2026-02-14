# You must define an inputs object
from pyfecons.enums import *
from pyfecons.inputs.all_inputs import AllInputs
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.blanket import Blanket
from pyfecons.inputs.coils import Coils
from pyfecons.inputs.customer_info import CustomerInfo
from pyfecons.inputs.direct_energy_converter import DirectEnergyConverter
from pyfecons.inputs.fuel_handling import FuelHandling
from pyfecons.inputs.installation import Installation
from pyfecons.inputs.lsa_levels import LsaLevels
from pyfecons.inputs.npv_Input import NpvInput
from pyfecons.inputs.power_supplies import PowerSupplies
from pyfecons.inputs.power_input import PowerInput
from pyfecons.inputs.primary_structure import PrimaryStructure
from pyfecons.inputs.radial_build import RadialBuild
from pyfecons.inputs.shield import Shield
from pyfecons.inputs.vacuum_system import VacuumSystem
from pyfecons.units import *


def Generate() -> AllInputs:
    return AllInputs(
        customer_info=CustomerInfo(name="Clean Air Task Force"),
        basic=Basic(
            fusion_machine_type=FusionMachineType.MFE,
            confinement_type=ConfinementType.SPHERICAL_TOKAMAK,
            energy_conversion=EnergyConversion.TURBINE,
            fuel_type=FuelType.DT,
            p_nrl=MW(2600.0),
            n_mod=Count(1),
            am=Percent(0.99),
            downtime=Years(1),
            construction_time=Years(6),
            plant_lifetime=Years(30),
            plant_availability=Percent(0.85),
            noak=True,
            yearly_inflation=Percent(0.0245),
            time_to_replace=Years(10),
            region=Region.UNSPECIFIED,
        ),
        blanket=Blanket(
            first_wall=BlanketFirstWall.BERYLLIUM,
            blanket_type=BlanketType.SOLID_FIRST_WALL_WITH_A_SOLID_BREEDER_LI2TIO3,
            primary_coolant=BlanketPrimaryCoolant.LITHIUM_LI,
            secondary_coolant=BlanketSecondaryCoolant.LEAD_LITHIUM_PBLI,
            neutron_multiplier=BlanketNeutronMultiplier.BE12TI,
            structure=BlanketStructure.FERRITIC_MARTENSITIC_STEEL_FMS,
        ),
        power_input=PowerInput(
            f_sub=Percent(0.03),
            p_cryo=MW(0.5),
            mn=Ratio(1.1),
            eta_p=Percent(0.5),
            eta_th=Percent(0.46),
            p_trit=MW(10),
            p_house=MW(4),
            p_cool=MW(13.7),  # Coil cooling (TF 12.7 + PF 1.0)
            p_coils=MW(2),  # Power into coils (TF 1.0 + PF 1.0)
            eta_pin=Percent(0.5),
            eta_pin1=Percent(0.18),
            eta_pin2=Percent(0.82),
            f_dec=Percent(0),  # DEC capture fraction (0 = no DEC)
            eta_de=Percent(0.85),
            p_input=MW(50),
            p_pump=MW(1),
        ),
        radial_build=RadialBuild(
            elon=Ratio(3),
            axis_t=Meters(3),
            plasma_t=Meters(1.1),
            vacuum_t=Meters(0.1),
            firstwall_t=Meters(0.2),
            blanket1_t=Meters(0.8),
            reflector_t=Meters(0.2),
            ht_shield_t=Meters(0.2),
            structure_t=Meters(0.2),
            gap1_t=Meters(0.5),
            vessel_t=Meters(0.2),
            coil_t=Meters(0.25),
            gap2_t=Meters(0.5),
            lt_shield_t=Meters(0.3),
            bioshield_t=Meters(1),
        ),
        # TODO clarify where shield fractions come from
        shield=Shield(
            f_SiC=Ratio(0.00),
            FPCPPFbLi=Ratio(0.1),
            f_W=Ratio(0.00),
            f_BFS=Ratio(0.9),
        ),
        coils=Coils(
            b_max=18,
            r_coil=Meters(1.85),
            coil_material=CoilMaterial.REBCO_HTS,
        ),
        lsa_levels=LsaLevels(lsa=2),
        primary_structure=PrimaryStructure(
            syst_pga=StructurePga.PGA_03,
            learning_credit=Ratio(0.5),
            replacement_factor=Ratio(0.1),
        ),
        vacuum_system=VacuumSystem(
            learning_credit=Ratio(0.5),
            spool_ir=Meters(2.25),
            spool_or=Meters(3.15),
            door_irb=Meters(6),
            door_orb=Meters(6.25),
            door_irc=Meters(7.81),
            door_orc=Meters(8.06),
            spool_height=Meters(9),
            # assume 1 second vac rate
            # cost of 1 vacuum pump, scaled from 1985 dollars
            cost_pump=USD(40000),
            # 48 pumps needed for 200^3 system
            vpump_cap=Meters3(200 / 48),
        ),
        power_supplies=PowerSupplies(
            learning_credit=Ratio(0.5),
            # $1/W power supply industry rule of thumb
            cost_per_watt=USD_W(1),
        ),
        direct_energy_converter=DirectEnergyConverter(
            system_power=Unknown(1),
            flux_limit=Unknown(2),
        ),
        installation=Installation(labor_rate=USD(1600)),
        fuel_handling=FuelHandling(learning_curve_credit=Ratio(0.8)),
        npv_input=NpvInput(discount_rate=Percent(0.08)),
    )
