from pyfecons.costing.accounting.power_table import PowerTable
from pyfecons.costing.calculations.fuel_physics import compute_ash_neutron_split
from pyfecons.enums import FusionMachineType
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.power_input import PowerInput
from pyfecons.units import MW, Ratio, Unknown


def power_balance(basic: Basic, power_input: PowerInput) -> PowerTable:
    power_table = PowerTable()

    # Ash / neutron split (fuel-type dependent)
    # Only pass non-None overrides; defaults live in fuel_physics.py
    fuel_kwargs = {
        k: v
        for k, v in {
            "dd_f_T": power_input.dd_f_T,
            "dd_f_He3": power_input.dd_f_He3,
            "dhe3_dd_frac": power_input.dhe3_dd_frac,
            "dhe3_f_T": power_input.dhe3_f_T,
        }.items()
        if v is not None
    }
    power_table.p_ash, power_table.p_neutron = compute_ash_neutron_split(
        basic.p_nrl, basic.fuel_type, **fuel_kwargs
    )

    power_table.p_aux = MW(power_input.p_trit + power_input.p_house)

    # Charged-particle routing (MFE only: DEC captures f_dec fraction)
    if basic.fusion_machine_type == FusionMachineType.MFE:
        f_dec = power_input.f_dec if power_input.f_dec is not None else 0.0
        power_table.p_dee = MW(f_dec * power_input.eta_de * power_table.p_ash)
        power_table.p_dec_waste = MW(
            f_dec * (1 - power_input.eta_de) * power_table.p_ash
        )
        p_ash_thermal = (1 - f_dec) * power_table.p_ash
        power_table.p_cool = (
            MW(power_input.p_cool) if power_input.p_cool is not None else MW(0)
        )
        power_table.p_coils = (
            MW(power_input.p_coils) if power_input.p_coils is not None else MW(0)
        )
    else:
        # IFE: no DEC, all ash thermalizes
        power_table.p_dee = MW(0)
        power_table.p_dec_waste = MW(0)
        p_ash_thermal = power_table.p_ash

    power_table.p_wall = MW(p_ash_thermal)

    # Pumping power (direct input)
    power_table.p_pump = MW(power_input.p_pump if power_input.p_pump is not None else 0)

    # Thermal power to turbine:
    #   neutron blanket heating (x mn) + ash wall heat + auxiliary heating + pump heat recovery
    power_table.p_th = MW(
        power_input.mn * power_table.p_neutron
        + p_ash_thermal
        + power_input.p_input
        + power_input.eta_p * power_table.p_pump
    )

    power_table.p_the = MW(power_input.eta_th * power_table.p_th)
    power_table.p_et = MW(power_table.p_dee + power_table.p_the)
    power_table.p_loss = MW(
        (power_table.p_th - power_table.p_the)  # thermal cycle rejection
        + power_table.p_dec_waste  # DEC conversion waste (0 if no DEC)
    )
    power_table.p_sub = MW(power_input.f_sub * power_table.p_et)
    power_table.q_sci = Unknown(basic.p_nrl / power_input.p_input)

    # Engineering Q: gross electric / total recirculating power
    if basic.fusion_machine_type == FusionMachineType.MFE:
        recirculating = (
            power_table.p_coils
            + power_table.p_pump
            + power_table.p_sub
            + power_table.p_aux
            + power_table.p_cool
            + power_input.p_cryo
            + power_input.p_input / power_input.eta_pin
        )
    else:
        # IFE: target factory + driver power
        recirculating = (
            power_input.p_target
            + power_table.p_pump
            + power_table.p_sub
            + power_table.p_aux
            + power_input.p_cryo
            + power_input.p_implosion / power_input.eta_pin1
            + power_input.p_ignition / power_input.eta_pin2
        )
        power_table.gain_e = Ratio(power_table.p_et / power_input.p_input)

    power_table.q_eng = Unknown(power_table.p_et / recirculating)
    power_table.rec_frac = 1 / power_table.q_eng
    power_table.p_net = MW((1 - 1 / power_table.q_eng) * power_table.p_et)

    return power_table
