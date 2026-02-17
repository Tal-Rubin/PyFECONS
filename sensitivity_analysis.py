"""
Standalone sensitivity analysis CLI with Excel export.

This is a thin wrapper around pyfecons.sensitivity for interactive use.
The core logic lives in pyfecons/sensitivity.py and is also used by
RunCostingForCustomer.py for report integration.

Usage:
    python sensitivity_analysis.py mfe CATF
    python sensitivity_analysis.py ife CATF
"""

import argparse
import os
import sys
from dataclasses import fields, is_dataclass
from typing import Dict, List, Tuple

import pandas as pd

from pyfecons import RunCosting
from pyfecons.costing_data import CostingData
from pyfecons.inputs.all_inputs import AllInputs
from pyfecons.sensitivity import (
    SensitivityResult,
    get_scalar_leaves,
    sensitivity_analysis,
)

# Mapping of CAS category codes to human-readable names (for Excel export)
CAS_CATEGORY_NAMES = {
    # CAS 10 - Pre-construction
    "C100000": "CAS 10: Pre-construction Total",
    "C110000": "CAS 11: Land and Land Rights",
    "C120000": "CAS 12: Site Permits",
    "C130000": "CAS 13: Plant Licensing",
    "C140000": "CAS 14: Plant Permits",
    "C150000": "CAS 15: Plant Studies",
    "C160000": "CAS 16: Plant Reports",
    "C170000": "CAS 17: Other Pre-construction",
    # CAS 21 - Buildings
    "C210000": "CAS 21: Structures & Improvements Total",
    "C210100": "CAS 21.01: Site Improvements",
    "C210200": "CAS 21.02: Fusion Heat Island Building",
    "C210300": "CAS 21.03: Turbine Building",
    "C210400": "CAS 21.04: Heat Exchanger Building",
    "C210500": "CAS 21.05: Power Supply Building",
    "C210600": "CAS 21.06: Reactor Auxiliaries Building",
    "C210700": "CAS 21.07: Hot Cell Building",
    "C210800": "CAS 21.08: Reactor Services Building",
    "C210900": "CAS 21.09: Service Water Building",
    "C211000": "CAS 21.10: Fuel Storage Building",
    "C211100": "CAS 21.11: Control Room Building",
    "C211500": "CAS 21.15: Cryogenics Building",
    "C211800": "CAS 21.18: Isotope Separation Plant",
    # CAS 22 - Reactor Equipment
    "C220000": "CAS 22: Reactor Equipment Total",
    "C220100": "CAS 22.01: Reactor Equipment Subtotal",
    "C220101": "CAS 22.01.01: First Wall & Blanket",
    "C220102": "CAS 22.01.02: Shield",
    "C220103": "CAS 22.01.03: Coils/Lasers",
    "C220104": "CAS 22.01.04: Supplementary Heating",
    "C220105": "CAS 22.01.05: Primary Structure",
    "C220106": "CAS 22.01.06: Vacuum System",
    "C220107": "CAS 22.01.07: Power Supplies",
    "C220108": "CAS 22.01.08: Divertor/Target Factory",
    "C220109": "CAS 22.01.09: Direct Energy Converter",
    "C220111": "CAS 22.01.11: Installation",
    "C220112": "CAS 22.01.12: Isotope Separation",
    "C220119": "CAS 22.01.19: Replacement Equipment",
    "C220120": "CAS 22.01.20: Safety Systems",
    "C220200": "CAS 22.02: Heat Transport",
    "C220300": "CAS 22.03: Auxiliary Cooling",
    "C220400": "CAS 22.04: Radioactive Waste",
    "C220500": "CAS 22.05: Fuel Handling & Storage",
    "C220600": "CAS 22.06: Other Plant Equipment",
    "C220700": "CAS 22.07: Instrumentation & Control",
    # CAS 23-29
    "C230000": "CAS 23: Turbine Plant Equipment",
    "C240000": "CAS 24: Electric Plant Equipment",
    "C250000": "CAS 25: Miscellaneous Plant Equipment",
    "C260000": "CAS 26: Heat Rejection System",
    "C270000": "CAS 27: Special Materials",
    "C280000": "CAS 28: Digital Twin",
    "C290000": "CAS 29: Contingency",
    # CAS 20 Total
    "C200000": "CAS 20: Direct Costs Total",
    # CAS 30-90
    "C300000": "CAS 30: Indirect Service Costs",
    "C400000": "CAS 40: Capitalized Owner Costs",
    "C500000": "CAS 50: Supplementary Costs",
    "C600000": "CAS 60: Interest During Construction",
    "C700000": "CAS 70: O&M Costs (Annualized)",
    "C800000": "CAS 80: Annualized Fuel Cost",
    "C900000": "CAS 90: Total Capital Cost",
}


def get_capital_cost_categories(costing: CostingData) -> List[Tuple[str, str, float]]:
    """
    Extract all capital cost categories from CostingData.

    Returns:
        List of tuples: (category_code, category_name, cost_value_m_usd)
        sorted by cost value descending.
    """
    costs = []

    def extract_costs(obj, prefix: str = ""):
        """Recursively extract cost fields from dataclasses."""
        if obj is None:
            return

        if is_dataclass(obj):
            for fld in fields(obj):
                field_val = getattr(obj, fld.name)
                if field_val is None:
                    continue

                # Check if this is a cost field (starts with 'C' followed by digits)
                if fld.name.startswith("C") and fld.name[1:].isdigit():
                    if isinstance(field_val, (int, float)) and field_val > 0:
                        category_name = CAS_CATEGORY_NAMES.get(
                            fld.name, f"CAS {fld.name}"
                        )
                        costs.append((fld.name, category_name, float(field_val)))
                elif is_dataclass(field_val) and fld.name.startswith("cas"):
                    # Recurse into CAS category dataclasses
                    extract_costs(field_val, fld.name)

    # Extract from all CAS categories in CostingData
    extract_costs(costing)

    # Sort by cost value descending
    costs.sort(key=lambda x: x[2], reverse=True)

    return costs


def autofit_columns(worksheet):
    """Auto-fit column widths based on content."""
    for column_cells in worksheet.columns:
        max_length = 0
        column_letter = column_cells[0].column_letter
        for cell in column_cells:
            try:
                cell_length = len(str(cell.value)) if cell.value else 0
                max_length = max(max_length, cell_length)
            except (TypeError, AttributeError):
                pass
        worksheet.column_dimensions[column_letter].width = max_length + 2


def save_results_to_excel(
    result: SensitivityResult,
    baseline_costing: CostingData,
    output_file: str = "lcoe_sensitivity_analysis.xlsx",
):
    """
    Save sensitivity analysis results to an Excel file with multiple sheets.
    """
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        # Sheet 1: Summary
        summary_data = {
            "Metric": ["Baseline LCOE ($/MWh)", "Total Parameters Analyzed"],
            "Value": [
                f"{result.lcoe_baseline:.6f}",
                result.n_parameters_analyzed,
            ],
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

        # Sheet 2: All derivatives ranked by absolute elasticity
        all_data = []
        for rank, entry in enumerate(result.entries, 1):
            all_data.append(
                {
                    "Rank": rank,
                    "Input Parameter": entry.parameter_path,
                    "Display Name": entry.display_name,
                    "Baseline Value": entry.baseline_value,
                    "∂(LCOE)/∂": entry.derivative,
                    "Elasticity": entry.elasticity,
                    "|Elasticity|": abs(entry.elasticity),
                }
            )

        all_df = pd.DataFrame(all_data)
        all_df.to_excel(writer, sheet_name="All Derivatives", index=False)

        # Sheet 3: Top 20 most sensitive
        top20_df = pd.DataFrame(all_data[:20])
        top20_df.to_excel(writer, sheet_name="Top 20 Sensitive", index=False)

        # Sheet 4: Top 20 Capital Expenses
        if baseline_costing is not None:
            capital_costs = get_capital_cost_categories(baseline_costing)
            top20_capital = capital_costs[:20]

            capital_data = []
            for rank, (code, name, value) in enumerate(top20_capital, 1):
                capital_data.append(
                    {
                        "Rank": rank,
                        "Category Code": code,
                        "Category Name": name,
                        "Cost (M$)": value,
                    }
                )

            capital_df = pd.DataFrame(capital_data)
            capital_df.to_excel(writer, sheet_name="Top 20 Capital Costs", index=False)

        # Auto-fit columns for all sheets
        for sheet_name in writer.sheets:
            autofit_columns(writer.sheets[sheet_name])

    print(f"\nResults saved to: {output_file}")


def load_customer_inputs(
    fusion_machine_type: str, customer_name: str
) -> Tuple[AllInputs, str]:
    """
    Load customer inputs from the customer directory.

    Args:
        fusion_machine_type: 'mfe', 'ife', or 'mif'
        customer_name: Customer folder name (e.g., 'CATF')

    Returns:
        Tuple of (AllInputs instance, output_dir path)
    """
    customer_dir = os.path.join(
        os.path.dirname(__file__), "customers", customer_name, fusion_machine_type
    )
    customer_dir = os.path.abspath(customer_dir)
    output_dir = os.path.join(customer_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    sys.path.insert(0, customer_dir)

    try:
        import importlib

        DefineInputs = __import__("DefineInputs")
        importlib.reload(DefineInputs)

        if "Generate" not in dir(DefineInputs):
            raise AttributeError("Generate function is missing in DefineInputs.py.")

        inputs = DefineInputs.Generate()
        if not isinstance(inputs, AllInputs):
            raise TypeError("Generate function must return an instance of AllInputs.")

        return inputs, output_dir

    except ImportError as e:
        print(f"ERROR: Could not import DefineInputs from {customer_dir}: {e}")
        sys.exit(1)
    except AttributeError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except TypeError as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Run LCOE sensitivity analysis for a customer"
    )
    parser.add_argument(
        "fusion_machine_type",
        type=str,
        choices=["mfe", "ife", "mif"],
        help="Fusion machine type: mfe, ife, or mif",
    )
    parser.add_argument("customer_name", type=str, help="Customer name (e.g., CATF)")
    parser.add_argument(
        "--delta",
        type=float,
        default=0.01,
        help="Fractional perturbation for finite differences (default: 0.01 = 1%%)",
    )
    args = parser.parse_args()

    if args.fusion_machine_type == "mif":
        print("FUSION_MACHINE_TYPE mif not yet implemented...")
        sys.exit(1)

    # Load customer inputs
    baseline_inputs, output_dir = load_customer_inputs(
        args.fusion_machine_type, args.customer_name
    )

    print("=" * 90)
    print(
        f"LCOE SENSITIVITY ANALYSIS: {args.customer_name} ({args.fusion_machine_type})"
    )
    print("=" * 90)
    print()

    # Run sensitivity analysis (verbose mode for standalone CLI)
    result = sensitivity_analysis(baseline_inputs, delta_frac=args.delta, quiet=False)

    if result:
        print()
        print("=" * 90)
        print("TOP 5 MOST SENSITIVE PARAMETERS (ranked by |Elasticity|)")
        print("=" * 90)

        for i, entry in enumerate(result.entries[:5], 1):
            print(
                f"\n{i}. {entry.parameter_path} ({entry.display_name})\n"
                f"   Baseline value:        {entry.baseline_value:.6f}\n"
                f"   ∂(LCOE)/∂:            {entry.derivative:+.6f}\n"
                f"   Elasticity:           {entry.elasticity:+.4f}\n"
                f"   |Elasticity|:         {abs(entry.elasticity):.4f}"
            )

        # Run baseline costing for capital cost export
        baseline_costing = RunCosting(baseline_inputs)

        # Save to Excel
        output_file = os.path.join(output_dir, "lcoe_sensitivity_analysis.xlsx")
        save_results_to_excel(result, baseline_costing, output_file)
