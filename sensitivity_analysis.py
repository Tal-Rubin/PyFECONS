"""
Sensitivity analysis: hybrid approach using PyFECONS + finite differences.

This approach:
1. Uses PyFECONS for full non-differentiable calculations
2. Computes sensitivities via finite differences (simple, reliable)
3. Accurate and requires no code changes to PyFECONS
"""

import os
import sys
from copy import deepcopy
from dataclasses import fields
from typing import Dict, List, Tuple

import pandas as pd
from pyfecons import RunCosting
from pyfecons.inputs.all_inputs import AllInputs

# Add the customer directory to the path
customer_dir = os.path.join(
    os.path.dirname(__file__), "customers", "CATF", "mfe"
)
customer_dir = os.path.abspath(customer_dir)
output_dir = os.path.join(customer_dir, "output")
os.makedirs(output_dir, exist_ok=True)
sys.path.insert(0, customer_dir)

try:
    import importlib
    import DefineInputs as customer_inputs_module

    importlib.reload(customer_inputs_module)
    baseline_inputs = customer_inputs_module.Generate()
except (ImportError, AttributeError) as e:
    print(f"Warning: Could not load customer inputs from {customer_dir}: {e}")
    print("Using fallback minimal MFE inputs.")
    # Minimal fallback inputs
    from pyfecons.inputs.basic import Basic
    from pyfecons.inputs.power_input import PowerInput
    from pyfecons.enums import FusionMachineType, ConfinementType, EnergyConversion, FuelType

    baseline_inputs = AllInputs(
        basic=Basic(
            fusion_machine_type=FusionMachineType.MFE,
            confinement_type=ConfinementType.SPHERICAL_TOKAMAK,
            energy_conversion=EnergyConversion.TURBINE,
            fuel_type=FuelType.DT,
            p_nrl=1000.0,  # MW
            n_mod=1,
            am=0.85,
            downtime=0.1,
            construction_time=5.0,
            plant_lifetime=30.0,
            plant_availability=0.75,
            yearly_inflation=0.03,
        ),
        power_input=PowerInput(
            p_th=3000.0,  # MW thermal
        ),
    )


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
                    print(f"{path:50s} = {baseline_val:15.4f}  →  ∂(LCOE)/∂ = {derivative:12.6f}")
                else:
                    print(f"{path:50s} = {baseline_val:15.4f}  →  ERROR computing perturbed LCOE")
            except Exception as e:
                print(f"{path:50s} = {baseline_val:15.4f}  →  ERROR: {e}")

    print()
    print("=" * 110)
    print("SENSITIVITY RANKING (by absolute elasticity)")
    print("=" * 110)
    print(f"{'Rank':<5} {'Input Parameter':<50} {'Baseline':<15} {'∂(LCOE)/∂':<15} {'|Elasticity|':<15}")
    print("-" * 110)

    sorted_derivs = sorted(
        derivatives.items(),
        key=lambda x: abs(x[1][2]),
        reverse=True
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


def save_results_to_excel(results: Dict, output_file: str = "lcoe_sensitivity_analysis.xlsx"):
    """
    Save sensitivity analysis results to an Excel file with multiple sheets.
    
    Args:
        results: Dictionary returned by sensitivity_analysis()
        output_file: Output Excel filename
    """
    if not results:
        print("ERROR: No results to save.")
        return

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Sheet 1: Summary
        summary_data = {
            'Metric': ['Baseline LCOE (M$/MWh)', 'Total Parameters Analyzed'],
            'Value': [
                f"{results['lcoe_baseline']:.6f}",
                len(results['derivatives'])
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

        # Sheet 2: All derivatives ranked by absolute elasticity
        all_data = []
        for rank, (path, (deriv, baseline_val, elasticity)) in enumerate(results['sorted_by_elasticity'], 1):
            all_data.append({
                'Rank': rank,
                'Input Parameter': path,
                'Baseline Value': baseline_val,
                '∂(LCOE)/∂': deriv,
                'Elasticity': elasticity,
                '|Elasticity| (Ranking)': abs(elasticity),
            })
        
        all_df = pd.DataFrame(all_data)
        all_df.to_excel(writer, sheet_name='All Derivatives', index=False)

        # Sheet 3: Top 20 most sensitive
        top20_data = all_data[:20]
        top20_df = pd.DataFrame(top20_data)
        top20_df.to_excel(writer, sheet_name='Top 20', index=False)

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    print("=" * 90)
    print("LCOE SENSITIVITY ANALYSIS (Finite Differences + PyFECONS)")
    print("=" * 90)
    print()

    results = sensitivity_analysis(baseline_inputs, delta_frac=0.01)

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
