"""
Sensitivity analysis: hybrid approach using PyFECONS + finite differences.

This approach:
1. Uses PyFECONS for full non-differentiable calculations
2. Computes sensitivities via finite differences (simple, reliable)
3. Accurate and requires no code changes to PyFECONS

Usage:
    python sensitivity_analysis.py mfe CATF
    python sensitivity_analysis.py ife CATF
"""

import argparse
import os
import sys
from copy import deepcopy
from dataclasses import fields
from typing import Dict, Tuple

import pandas as pd

from pyfecons import RunCosting
from pyfecons.inputs.all_inputs import AllInputs


def get_scalar_leaves(obj, prefix: str = "") -> Dict[str, Tuple]:
    """
    Recursively extract all scalar (numeric/bool) leaf values from a nested dataclass.
    Returns a dict mapping 'parent.child.scalar' -> (parent_obj, field_name, value).
    """
    leaves = {}
    if obj is None:
        return leaves

    from dataclasses import is_dataclass

    if is_dataclass(obj):
        for field in fields(obj):
            field_val = getattr(obj, field.name)
            full_path = f"{prefix}.{field.name}" if prefix else field.name

            if field_val is None:
                continue
            elif isinstance(field_val, (int, float, bool)):
                leaves[full_path] = (obj, field.name, field_val)
            elif is_dataclass(field_val):
                # Recurse into nested dataclass
                nested = get_scalar_leaves(field_val, full_path)
                leaves.update(nested)

    return leaves


def sensitivity_analysis(baseline_inputs: AllInputs, delta_frac: float = 0.01) -> Dict:
    """
    Compute ∂(LCOE)/∂(input_i) for all scalar inputs using finite differences.

    Approach:
    - Run full PyFECONS costing for baseline and perturbed inputs
    - Use finite differences: (LCOE_perturbed - LCOE_baseline) / delta
    - Compute for all scalar input parameters

    Args:
        baseline_inputs: The baseline AllInputs instance.
        delta_frac: Fractional perturbation (0.01 = 1%).

    Returns:
        Dictionary with:
        - 'lcoe_baseline': baseline LCOE
        - 'derivatives': dict mapping input_path -> (derivative, baseline_value, elasticity)
        - 'sorted_by_elasticity': list sorted by |elasticity|
    """
    print("Computing baseline LCOE using PyFECONS...")
    baseline_costing = RunCosting(baseline_inputs)
    lcoe_baseline = float(baseline_costing.lcoe.C1000000)

    if lcoe_baseline is None or lcoe_baseline == 0:
        print("ERROR: Could not compute baseline LCOE.")
        return {}

    print(f"Baseline LCOE: {lcoe_baseline:.4f} M$/MWh")
    print()

    # Extract all scalar inputs
    scalar_leaves = get_scalar_leaves(baseline_inputs)
    print(f"Found {len(scalar_leaves)} scalar input parameters.")
    print()

    derivatives = {}
    for path, (parent_obj, field_name, baseline_val) in sorted(scalar_leaves.items()):
        if baseline_val is None or baseline_val == 0:
            delta = 1.0  # Use absolute delta if baseline is 0
        else:
            delta = abs(baseline_val) * delta_frac

        # Perturbed inputs (forward difference)
        perturbed_inputs = deepcopy(baseline_inputs)
        perturbed_leaf = get_scalar_leaves(perturbed_inputs)
        if path in perturbed_leaf:
            obj, field, _ = perturbed_leaf[path]
            setattr(obj, field, baseline_val + delta)

            try:
                perturbed_costing = RunCosting(perturbed_inputs)
                lcoe_perturbed = float(perturbed_costing.lcoe.C1000000)

                if lcoe_perturbed is not None:
                    # Partial derivative: ∂(LCOE)/∂(input_i)
                    derivative = (lcoe_perturbed - lcoe_baseline) / delta
                    elasticity = derivative * baseline_val / lcoe_baseline
                    derivatives[path] = (derivative, baseline_val, elasticity)
                    print(
                        f"{path:50s} = {baseline_val:15.4f}  →  ∂(LCOE)/∂ = {derivative:12.6f}"
                    )
                else:
                    print(
                        f"{path:50s} = {baseline_val:15.4f}  →  ERROR computing perturbed LCOE"
                    )
            except Exception as e:
                print(f"{path:50s} = {baseline_val:15.4f}  →  ERROR: {e}")

    print()
    print("=" * 110)
    print("SENSITIVITY RANKING (by absolute elasticity)")
    print("=" * 110)
    print(
        f"{'Rank':<5} {'Input Parameter':<50} {'Baseline':<15} {'∂(LCOE)/∂':<15} {'|Elasticity|':<15}"
    )
    print("-" * 110)

    sorted_derivs = sorted(
        derivatives.items(), key=lambda x: abs(x[1][2]), reverse=True
    )

    for rank, (path, (deriv, baseline_val, elasticity)) in enumerate(sorted_derivs, 1):
        print(
            f"{rank:<5} {path:<50} {baseline_val:<15.6f} {deriv:<15.6f} {abs(elasticity):<15.6f}"
        )

    return {
        "lcoe_baseline": lcoe_baseline,
        "derivatives": derivatives,
        "sorted_by_elasticity": sorted_derivs,
    }


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
    results: Dict, output_file: str = "lcoe_sensitivity_analysis.xlsx"
):
    """
    Save sensitivity analysis results to an Excel file with multiple sheets.

    Args:
        results: Dictionary returned by sensitivity_analysis()
        output_file: Output Excel filename
    """
    if not results:
        print("ERROR: No results to save.")
        return

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        # Sheet 1: Summary
        summary_data = {
            "Metric": ["Baseline LCOE (M$/MWh)", "Total Parameters Analyzed"],
            "Value": [f"{results['lcoe_baseline']:.6f}", len(results["derivatives"])],
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

        # Sheet 2: All derivatives ranked by absolute elasticity
        all_data = []
        for rank, (path, (deriv, baseline_val, elasticity)) in enumerate(
            results["sorted_by_elasticity"], 1
        ):
            all_data.append(
                {
                    "Rank": rank,
                    "Input Parameter": path,
                    "Baseline Value": baseline_val,
                    "∂(LCOE)/∂": deriv,
                    "Elasticity": elasticity,
                    "|Elasticity| (Ranking)": abs(elasticity),
                }
            )

        all_df = pd.DataFrame(all_data)
        all_df.to_excel(writer, sheet_name="All Derivatives", index=False)

        # Sheet 3: Top 20 most sensitive
        top20_data = all_data[:20]
        top20_df = pd.DataFrame(top20_data)
        top20_df.to_excel(writer, sheet_name="Top 20", index=False)

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

    results = sensitivity_analysis(baseline_inputs, delta_frac=args.delta)

    if results:
        print()
        print("=" * 90)
        print("TOP 5 MOST SENSITIVE PARAMETERS (ranked by |Elasticity|)")
        print("=" * 90)

        top_5 = results["sorted_by_elasticity"][:5]
        if top_5:
            for i, (path, (deriv, baseline_val, elasticity)) in enumerate(top_5, 1):
                print(
                    f"\n{i}. {path}\n"
                    f"   Baseline value:        {baseline_val:.6f}\n"
                    f"   ∂(LCOE)/∂:            {deriv:+.6f}\n"
                    f"   Elasticity:           {elasticity:+.4f}  ← RANKING METRIC\n"
                    f"   |Elasticity|:         {abs(elasticity):.4f}"
                )

        # Save to Excel
        output_file = os.path.join(output_dir, "lcoe_sensitivity_analysis.xlsx")
        save_results_to_excel(results, output_file)
