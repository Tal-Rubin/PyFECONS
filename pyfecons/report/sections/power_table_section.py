from dataclasses import dataclass
from typing import Any, Dict

from pyfecons.costing.accounting.power_table import PowerTable
from pyfecons.enums import FuelType, FusionMachineType
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.power_input import PowerInput
from pyfecons.report.section import ReportSection


def _ash_split_text(fuel_type: FuelType) -> str:
    """Generate fuel-type-specific LaTeX text for the ash/neutron power split."""
    header = "\\subsubsection{Charged Particle (Ash) Power Split}\n"
    footer = "\n$P_{ash} = f_{ash} \\cdot P_{fusion}$, \\quad $P_{neutrons} = (1 - f_{ash}) \\cdot P_{fusion}$\n"

    if fuel_type == FuelType.DT:
        body = (
            "This plant uses D-T fuel. The D+T reaction produces a 3.52~MeV He-4 (alpha) "
            "and a 14.06~MeV neutron, totaling 17.58~MeV. The charged particle (ash) fraction is:\n\n"
            "$f_{ash} = 3.52 / 17.58 = 0.200$\n"
        )
    elif fuel_type == FuelType.DD:
        body = (
            "This plant uses D-D fuel with a semi-catalyzed burn model. "
            "The primary D-D reactions have two equally probable branches:\n\n"
            "\\begin{itemize}\n"
            "\\item D+D $\\to$ T(1.01~MeV) + p(3.02~MeV), $Q = 4.03$~MeV\n"
            "\\item D+D $\\to$ He-3(0.82~MeV) + n(2.45~MeV), $Q = 3.27$~MeV\n"
            "\\end{itemize}\n\n"
            "Tritium and He-3 ash undergo secondary burns with deuterium, parametrized by "
            "burn fractions $f_T$ and $f_{He3}$:\n\n"
            "\\begin{itemize}\n"
            "\\item D+T $\\to$ He-4(3.52~MeV) + n(14.06~MeV), burn fraction $f_T \\approx 0.97$\n"
            "\\item D+He-3 $\\to$ He-4(3.67~MeV) + p(14.68~MeV), burn fraction $f_{He3} \\approx 0.69$\n"
            "\\end{itemize}\n\n"
            "With these burn fractions: $f_{ash} \\approx 0.565$.\n"
        )
    elif fuel_type == FuelType.DHE3:
        body = (
            "This plant uses D-He3 fuel. The primary reaction is aneutronic: "
            "D+He3 $\\to$ He-4(3.67~MeV) + p(14.68~MeV), $Q = 18.35$~MeV, 100\\% charged particles. "
            "However, ${\\sim}7\\%$ of energy comes from unavoidable D-D side reactions "
            "which produce some neutrons. Tritium from D-D sides burns with $f_T \\approx 0.97$.\n\n"
            "With defaults: $f_{ash} \\approx 0.954$.\n"
        )
    elif fuel_type == FuelType.PB11:
        body = (
            "This plant uses p-B11 fuel. The p+B11 reaction produces three alpha particles "
            "(He-4) totaling 8.7~MeV. The reaction is fully aneutronic: $f_{ash} = 1.0$.\n"
        )
        footer = "\n$P_{ash} = P_{fusion}$, \\quad $P_{neutrons} = 0$\n"
    else:
        body = ""

    return header + body + footer


@dataclass
class PowerTableSection(ReportSection):
    """Report section for power table data."""

    def __init__(self, power_table: PowerTable, basic: Basic, power_input: PowerInput):
        super().__init__()

        if basic.fusion_machine_type == FusionMachineType.MFE:  # MFE
            self.template_file = "powerTableMFEDT.tex"
            self.replacements = {
                # Ordered by occurrence in template
                # 1. Output power
                "PNRL": basic.p_nrl,  # Fusion Power
                "PASH": power_table.p_ash,  # Charged particle (ash) power
                "PNEUTRON": power_table.p_neutron,  # Neutron Power
                "MN___": power_input.mn,  # Neutron Energy Multiplier
                "ETAP__": power_input.eta_p,  # Pumping power capture efficiency
                "PTH___": power_table.p_th,  # Thermal Power
                "ETATH": power_input.eta_th,  # Thermal conversion efficiency
                "PET___": power_table.p_et,  # Total (Gross) Electric Power
                # 2. Recirculating power
                "PLOSS": power_table.p_loss,  # Lost Power
                "PCOILS": power_table.p_coils,  # Power into coils
                "PPUMP": power_table.p_pump,  # Primary Coolant Pumping Power
                "FSUB": power_input.f_sub,  # Subsystem and Control Fraction
                "PSUB": power_table.p_sub,  # Subsystem and Control Power
                "PAUX": power_table.p_aux,  # Auxiliary systems
                "PTRIT": power_input.p_trit,  # Tritium Systems
                "PHOUSE": power_input.p_house,  # Housekeeping power
                "PCOOL": power_table.p_cool,  # Cooling systems
                "PCRYO": power_input.p_cryo,  # Cryo vacuum pumping
                "ETAPIN": power_input.eta_pin,  # Input power wall plug efficiency
                "PINPUT": power_input.p_input,  # Input power
                # 3. Outputs
                "QSCI": power_table.q_sci,  # Scientific Q
                "QENG": power_table.q_eng,  # Engineering Q
                "RECFRAC": round(
                    power_table.rec_frac, 3
                ),  # Recirculating power fraction
                "PNET": power_table.p_net,  # Output Power (Net Electric Power)
                # Fuel-type-specific ash/neutron split explanation
                "ASHSPLITTEXT": _ash_split_text(basic.fuel_type),
            }
        elif basic.fusion_machine_type == FusionMachineType.IFE:
            self.template_file = "powerTableIFEDT.tex"
            self.replacements = {
                "PNRL": round(basic.p_nrl, 1),
                "PASH": round(power_table.p_ash, 1),
                "PNEUTRON": round(power_table.p_neutron, 1),
                "MN": round(power_input.mn, 1),
                "FSUB": round(power_input.f_sub, 1),
                "PTRIT": round(power_input.p_trit, 1),
                "PHOUSE": round(power_input.p_house, 1),
                "PAUX": round(power_table.p_aux, 1),
                "PCRYO": round(power_input.p_cryo, 1),
                "ETAPIN1": round(power_input.eta_pin1, 1),
                "ETAPIN2": round(power_input.eta_pin2, 1),
                "ETAP": round(power_input.eta_p, 1),
                "ETATH": round(power_input.eta_th, 1),
                "PIMPLOSION": round(power_input.p_implosion, 1),
                "PIGNITION": round(power_input.p_ignition, 1),
                "PTH": round(power_table.p_th, 1),
                "PET": round(power_table.p_et, 1),
                "PLOSS": round(power_table.p_loss, 1),
                "GAINE": round(power_table.gain_e, 1),
                "PTARGET": round(power_input.p_target, 1),
                "PSUB": round(power_table.p_sub, 1),
                "QS": round(power_table.q_sci, 1),
                "QE": round(power_table.q_eng, 1),
                "EPSILON": round(power_table.rec_frac, 1),
                "PNET": round(power_table.p_net, 1),
                "PP": round(power_table.p_pump, 1),
                "PIN": round(power_input.p_input, 1),
                # Fuel-type-specific ash/neutron split explanation
                "ASHSPLITTEXT": _ash_split_text(basic.fuel_type),
            }
        else:
            raise ValueError(f"Unknown reactor type: {basic.fusion_machine_type}")
