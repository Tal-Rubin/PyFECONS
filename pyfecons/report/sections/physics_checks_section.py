"""Report section for physics feasibility checks."""

from dataclasses import dataclass

from pyfecons.costing.calculations.fuel_physics import compute_ash_neutron_split
from pyfecons.costing.calculations.power_balance import power_balance
from pyfecons.costing.calculations.reactivity import (
    min_density_for_power,
    required_confinement_time,
)
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.power_input import PowerInput
from pyfecons.inputs.radial_build import RadialBuild
from pyfecons.report.section import ReportSection


def _status(value, threshold, above=True):
    """Return 'OK' or WARNING LaTeX string based on threshold comparison."""
    exceeded = value > threshold if above else value < threshold
    if exceeded:
        return "\\textbf{WARNING}"
    return "OK"


def _build_checks_table(
    basic: Basic, power_input: PowerInput, radial_build: RadialBuild
) -> str:
    """Build a LaTeX table of physics feasibility check results."""
    rows = []

    p_nrl = float(basic.p_nrl)
    p_input = float(power_input.p_input)
    fuel_type = basic.fuel_type

    # Gather burn fraction kwargs
    burn_kw = {}
    for attr in ("dd_f_T", "dd_f_He3", "dhe3_dd_frac", "dhe3_f_T"):
        val = getattr(power_input, attr, None)
        if val is not None:
            burn_kw[attr] = val

    # Q_sci (always available)
    q_sci = p_nrl / p_input
    rows.append(
        (
            "$Q_{sci}$",
            "$P_{fusion} / P_{input}$",
            f"{q_sci:.2f}",
            "",
            _status(q_sci, 1.0, above=False),
        )
    )

    # p_net (always available)
    try:
        pt = power_balance(basic, power_input)
        p_net = float(pt.p_net)
        rows.append(
            (
                "$P_{net}$",
                "Net electric power",
                f"{p_net:.1f}",
                "MW",
                _status(p_net, 0, above=False),
            )
        )
    except Exception:
        pass

    # Compute ash/neutron split (needed for wall loading and heat flux)
    try:
        p_ash, p_neutron = compute_ash_neutron_split(p_nrl, fuel_type, **burn_kw)
    except Exception:
        p_ash, p_neutron = None, None

    # Density check (requires plasma_volume)
    if radial_build.plasma_volume is not None:
        try:
            density_kw = {
                k: v for k, v in burn_kw.items() if k in ("dd_f_T", "dd_f_He3")
            }
            n_e = min_density_for_power(
                p_nrl, float(radial_build.plasma_volume), fuel_type, **density_kw
            )
            rows.append(
                (
                    "$n_e$ (min)",
                    "Best-case electron density",
                    f"{n_e:.2e}",
                    "m$^{-3}$",
                    _status(n_e, 5e20),
                )
            )
        except Exception:
            pass

    # Confinement time (requires plasma_volume)
    if radial_build.plasma_volume is not None:
        try:
            tau_e = required_confinement_time(
                p_nrl, float(radial_build.plasma_volume), fuel_type, p_input, **burn_kw
            )
            rows.append(
                (
                    "$\\tau_E$ (min)",
                    "Best-case confinement time",
                    f"{tau_e:.3f}",
                    "s",
                    _status(tau_e, 30.0),
                )
            )
        except Exception:
            pass

    # Wall loading (requires first_wall_area)
    if radial_build.first_wall_area is not None and p_neutron is not None:
        wall_loading = float(p_neutron) / float(radial_build.first_wall_area)
        rows.append(
            (
                "$\\Gamma_n$",
                "Neutron wall loading",
                f"{wall_loading:.2f}",
                "MW/m$^2$",
                _status(wall_loading, 5.0),
            )
        )

    # Divertor heat flux (requires divertor_area)
    if radial_build.divertor_area is not None and p_ash is not None:
        f_dec = float(power_input.f_dec) if power_input.f_dec else 0.0
        p_exhaust = float(p_ash) * (1 - f_dec) + p_input
        heat_flux = p_exhaust / float(radial_build.divertor_area)
        rows.append(
            (
                "$q_{div}$",
                "Divertor heat flux",
                f"{heat_flux:.1f}",
                "MW/m$^2$",
                _status(heat_flux, 15.0),
            )
        )

    # Build LaTeX table
    lines = [
        "\\begin{table}[ht!]",
        "\\centering",
        "\\begin{tabular}{|l|p{5cm}|r|l|l|}",
        "\\hline",
        "\\textbf{Parameter} & \\textbf{Description} & \\textbf{Value} & "
        "\\textbf{Units} & \\textbf{Status} \\\\",
        "\\hline",
    ]
    for param, desc, val, unit, status in rows:
        lines.append(f"{param} & {desc} & {val} & {unit} & {status} \\\\")
        lines.append("\\hline")
    lines.extend(
        [
            "\\end{tabular}",
            "\\caption{Physics feasibility checks. Best-case assumptions: "
            "uniform plasma at peak reactivity temperature, zero radiation losses.}",
            "\\label{tab:physicschecks}",
            "\\end{table}",
        ]
    )

    return "\n".join(lines)


@dataclass
class PhysicsChecksSection(ReportSection):
    """Report section for physics feasibility check results."""

    def __init__(
        self, basic: Basic, power_input: PowerInput, radial_build: RadialBuild
    ):
        super().__init__()
        self.template_file = "PhysicsChecks.tex"
        self.replacements = {
            "PHYSICSCHECKSCONTENT": _build_checks_table(
                basic, power_input, radial_build
            ),
        }
