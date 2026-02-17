"""
Sensitivity analysis for PyFECONS: finite-difference LCOE elasticity computation.

Perturbs each scalar input parameter by a small fraction (default 1%),
re-runs the full costing pipeline, and computes the elasticity of LCOE
with respect to each parameter.
"""

import contextlib
import io
from copy import deepcopy
from dataclasses import dataclass, fields, is_dataclass
from typing import Dict, List, Optional, Tuple

from pyfecons.inputs.all_inputs import AllInputs


@dataclass
class SensitivityEntry:
    """A single parameter's sensitivity result."""

    parameter_path: str
    display_name: str
    baseline_value: float
    derivative: float
    elasticity: float


@dataclass
class SensitivityResult:
    """Complete sensitivity analysis results."""

    lcoe_baseline: float
    entries: List[SensitivityEntry]
    n_parameters_analyzed: int


# Human-readable display names for common input parameters.
# Keys are dataclass field paths; values are LaTeX-safe display names.
PARAMETER_DISPLAY_NAMES: Dict[str, str] = {
    # Basic
    "basic.p_nrl": "Fusion Power ($P_{NRL}$)",
    "basic.n_mod": "Number of Modules",
    "basic.plant_lifetime": "Plant Lifetime",
    "basic.plant_availability": "Plant Availability",
    "basic.yearly_inflation": "Yearly Inflation Rate",
    "basic.construction_time": "Construction Time",
    "basic.downtime": "Downtime",
    "basic.am": "Availability Multiplier",
    "basic.time_to_replace": "Component Replacement Time",
    "basic.implosion_frequency": "Implosion Frequency",
    # Power Input
    "power_input.eta_th": "Thermal Efficiency ($\\eta_{th}$)",
    "power_input.eta_p": "Pumping Efficiency ($\\eta_p$)",
    "power_input.eta_pin": "Input Power Efficiency ($\\eta_{pin}$)",
    "power_input.eta_pin1": "Input Power Efficiency 1 ($\\eta_{pin1}$)",
    "power_input.eta_pin2": "Input Power Efficiency 2 ($\\eta_{pin2}$)",
    "power_input.eta_de": "DEC Efficiency ($\\eta_{de}$)",
    "power_input.f_sub": "Subsystem Fraction ($f_{sub}$)",
    "power_input.f_dec": "DEC Capture Fraction ($f_{dec}$)",
    "power_input.mn": "Neutron Multiplier ($M_n$)",
    "power_input.p_input": "Input Power ($P_{input}$)",
    "power_input.p_pump": "Pump Power ($P_{pump}$)",
    "power_input.p_cryo": "Cryogenic Power ($P_{cryo}$)",
    "power_input.p_trit": "Tritium Systems Power ($P_{trit}$)",
    "power_input.p_house": "Housekeeping Power ($P_{house}$)",
    "power_input.p_cool": "Coil Cooling Power ($P_{cool}$)",
    "power_input.p_coils": "Coil Power ($P_{coils}$)",
    "power_input.p_implosion": "Implosion Power ($P_{imp}$)",
    "power_input.p_ignition": "Ignition Power ($P_{ign}$)",
    "power_input.p_target": "Target Power ($P_{tgt}$)",
    "power_input.dd_f_T": "DD Tritium Burn Fraction",
    "power_input.dd_f_He3": "DD He-3 Burn Fraction",
    "power_input.dhe3_dd_frac": "DHe3 DD Side-Reaction Fraction",
    "power_input.dhe3_f_T": "DHe3 Tritium Burn Fraction",
    # Radial Build
    "radial_build.elon": "Elongation",
    "radial_build.axis_t": "Axis Thickness",
    "radial_build.plasma_t": "Plasma Thickness",
    "radial_build.firstwall_t": "First Wall Thickness",
    "radial_build.blanket1_t": "Blanket Thickness",
    "radial_build.reflector_t": "Reflector Thickness",
    "radial_build.ht_shield_t": "HT Shield Thickness",
    "radial_build.structure_t": "Structure Thickness",
    "radial_build.vessel_t": "Vessel Thickness",
    "radial_build.coil_t": "Coil Thickness",
    "radial_build.lt_shield_t": "LT Shield Thickness",
    "radial_build.bioshield_t": "Bioshield Thickness",
    "radial_build.chamber_length": "Chamber Length",
    # Shield
    "shield.f_SiC": "SiC Fraction",
    "shield.FPCPPFbLi": "PbLi Fraction",
    "shield.f_W": "Tungsten Fraction",
    "shield.f_BFS": "Boron Steel Fraction",
    "shield.ife_shield_scaling": "IFE Shield Scaling",
    # Coils
    "coils.b_max": "Peak Magnetic Field ($B_{max}$)",
    "coils.r_coil": "Coil Radius ($r_{coil}$)",
    "coils.n_coils": "Number of Coils",
    "coils.cost_per_kAm": "Conductor Cost (\\$/kAm)",
    "coils.coil_markup": "Coil Markup Factor",
    "coils.path_factor": "Coil Path Factor",
    "coils.m_cost_ybco": "YBCO Cost (\\$/kAm)",
    "coils.m_cost_ss": "SS Cost (\\$/kg)",
    "coils.m_cost_cu": "Cu Cost (\\$/kg)",
    "coils.struct_factor": "Structure Factor",
    "coils.mfr_factor": "Manufacturing Factor",
    # Supplementary Heating
    "supplementary_heating.nbi_power": "NBI Power",
    "supplementary_heating.icrf_power": "ICRF Power",
    # Primary Structure
    "primary_structure.learning_credit": "Primary Struct. Learning Credit",
    "primary_structure.replacement_factor": "Replacement Factor",
    # Vacuum System
    "vacuum_system.learning_credit": "Vacuum Sys. Learning Credit",
    # Power Supplies
    "power_supplies.learning_credit": "Power Supply Learning Credit",
    "power_supplies.cost_per_watt": "Power Supply Cost (\\$/W)",
    # Installation
    "installation.labor_rate": "Installation Labor Rate (\\$/day)",
    # Fuel Handling
    "fuel_handling.learning_curve_credit": "Fuel Handling Learning Credit",
    # Financial
    "financial.interest_rate": "Interest Rate",
    "financial.a_power": "Reference Power",
    "financial.construction_years": "Financial Construction Years",
    "financial.plant_lifetime_years": "Financial Plant Lifetime",
    "financial.capital_recovery_factor": "Capital Recovery Factor",
    # Costing Constants
    "costing_constants.optimism": "Cost Optimism",
    "costing_constants.learning": "Cost Learning",
    # NPV
    "npv_input.discount_rate": "Discount Rate",
    # LSA
    "lsa_levels.lsa": "LSA Level",
}


def get_display_name(parameter_path: str) -> str:
    """Get human-readable name for a parameter path."""
    if parameter_path in PARAMETER_DISPLAY_NAMES:
        return PARAMETER_DISPLAY_NAMES[parameter_path]
    # Fallback: take the last segment, replace underscores, title-case
    parts = parameter_path.split(".")
    last = parts[-1]
    return last.replace("_", " ").title()


def get_scalar_leaves(obj, prefix: str = "") -> Dict[str, Tuple]:
    """
    Recursively extract all scalar (numeric, non-bool) leaf values
    from a nested dataclass.

    Returns a dict mapping 'parent.child.scalar' -> (parent_obj, field_name, value).
    """
    leaves = {}
    if obj is None:
        return leaves

    if is_dataclass(obj):
        for field in fields(obj):
            field_val = getattr(obj, field.name)
            full_path = f"{prefix}.{field.name}" if prefix else field.name

            if field_val is None:
                continue
            # Check bool BEFORE int (isinstance(True, int) is True in Python)
            elif isinstance(field_val, bool):
                continue
            elif isinstance(field_val, (int, float)):
                leaves[full_path] = (obj, field.name, field_val)
            elif is_dataclass(field_val):
                nested = get_scalar_leaves(field_val, full_path)
                leaves.update(nested)

    return leaves


def sensitivity_analysis(
    baseline_inputs: AllInputs,
    delta_frac: float = 0.01,
    quiet: bool = False,
) -> Optional[SensitivityResult]:
    """
    Compute LCOE sensitivity for all scalar inputs via finite differences.

    Args:
        baseline_inputs: The baseline AllInputs.
        delta_frac: Fractional perturbation (default 0.01 = 1%).
        quiet: If True, suppress all console output during perturbation runs.

    Returns:
        SensitivityResult, or None if baseline LCOE is invalid.
    """
    # Deferred import to avoid circular dependency
    from pyfecons.pyfecons import RunCosting

    # Run baseline
    if not quiet:
        print("Computing baseline LCOE...")
    baseline_costing = RunCosting(baseline_inputs)
    lcoe_baseline = float(baseline_costing.lcoe.C1000000)

    if lcoe_baseline is None or lcoe_baseline == 0:
        if not quiet:
            print("ERROR: Could not compute baseline LCOE.")
        return None

    if not quiet:
        print(f"Baseline LCOE: {lcoe_baseline:.4f} $/MWh")

    # Extract all scalar inputs
    scalar_leaves = get_scalar_leaves(baseline_inputs)
    n_params = len(scalar_leaves)
    if not quiet:
        print(f"Analyzing {n_params} scalar parameters...")

    entries = []
    for i, (path, (parent_obj, field_name, baseline_val)) in enumerate(
        sorted(scalar_leaves.items()), 1
    ):
        if baseline_val == 0:
            delta = 1.0
        else:
            delta = abs(baseline_val) * delta_frac

        # Perturbed inputs (forward difference)
        perturbed_inputs = deepcopy(baseline_inputs)
        perturbed_leaf = get_scalar_leaves(perturbed_inputs)
        if path not in perturbed_leaf:
            continue

        obj, field, _ = perturbed_leaf[path]
        setattr(obj, field, baseline_val + delta)

        try:
            if quiet:
                with contextlib.redirect_stdout(
                    io.StringIO()
                ), contextlib.redirect_stderr(io.StringIO()):
                    perturbed_costing = RunCosting(perturbed_inputs)
            else:
                perturbed_costing = RunCosting(perturbed_inputs)

            lcoe_perturbed = float(perturbed_costing.lcoe.C1000000)

            if lcoe_perturbed is not None:
                derivative = (lcoe_perturbed - lcoe_baseline) / delta
                elasticity = derivative * baseline_val / lcoe_baseline
                entries.append(
                    SensitivityEntry(
                        parameter_path=path,
                        display_name=get_display_name(path),
                        baseline_value=baseline_val,
                        derivative=derivative,
                        elasticity=elasticity,
                    )
                )
                if not quiet:
                    print(f"  [{i}/{n_params}] {path:50s} elasticity={elasticity:+.6f}")
        except Exception as e:
            if not quiet:
                print(f"  [{i}/{n_params}] {path:50s} ERROR: {e}")

    # Sort by |elasticity| descending
    entries.sort(key=lambda e: abs(e.elasticity), reverse=True)

    return SensitivityResult(
        lcoe_baseline=lcoe_baseline,
        entries=entries,
        n_parameters_analyzed=n_params,
    )
