from dataclasses import dataclass

from pyfecons.report.section import ReportSection
from pyfecons.sensitivity import SensitivityResult


def _escape_latex(text: str) -> str:
    """Escape special LaTeX characters, preserving math mode ($...$)."""
    result = []
    in_math = False
    for char in text:
        if char == "$":
            in_math = not in_math
            result.append(char)
        elif char == "_" and not in_math:
            result.append("\\_")
        elif char == "&" and not in_math:
            result.append("\\&")
        elif char == "%" and not in_math:
            result.append("\\%")
        elif char == "#" and not in_math:
            result.append("\\#")
        else:
            result.append(char)
    return "".join(result)


@dataclass
class SensitivitySection(ReportSection):
    def __init__(self, sensitivity_result: SensitivityResult, top_n: int = 15):
        super().__init__()
        self.template_file = "SensitivityAnalysis.tex"

        # Build dynamic table rows for top N parameters
        top_entries = sensitivity_result.entries[:top_n]
        rows = []
        for rank, entry in enumerate(top_entries, 1):
            direction = (
                "\\textcolor{red}{+}"
                if entry.elasticity >= 0
                else "\\textcolor{green!60!black}{$-$}"
            )
            display = _escape_latex(entry.display_name)
            rows.append(
                f"{rank} & {display} & "
                f"{entry.baseline_value:.4g} & "
                f"{abs(entry.elasticity):.4f} & "
                f"{direction}"
            )
        table_rows = " \\\\\n".join(rows)

        self.replacements = {
            "sensitivity_lcoe_baseline": f"{sensitivity_result.lcoe_baseline:.2f}",
            "sensitivity_n_params": str(sensitivity_result.n_parameters_analyzed),
            "sensitivity_table_rows": table_rows,
            "sensitivity_top_n": str(len(top_entries)),
        }
