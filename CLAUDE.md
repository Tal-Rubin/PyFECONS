# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PyFECONS (Python Fusion Economics) is a fusion reactor costing analysis library. It performs cost calculations for MFE (Magnetic Fusion Energy) and IFE (Inertial Fusion Energy) reactor types and generates PDF reports using LaTeX.

## Commands

### Running Costing
```bash
# Full report
python3 RunCostingForCustomer.py mfe CATF
python3 RunCostingForCustomer.py ife CATF

# Lite report (summary only)
python3 RunCostingForCustomer.py mfe CATF --lite

# Safety analysis enabled
python3 RunCostingForCustomer.py mfe CATF --safety
```

### Testing
```bash
pytest tests/                          # Run all tests
pytest tests/test_mfe.py               # Run specific test file
pytest tests/test_mfe.py::test_name    # Run single test
```

### Linting and Formatting
```bash
./format.sh                            # Format all files
pre-commit run --all-files             # Run all pre-commit hooks
```

### Setup
```bash
./setup-dev.sh                         # New developer setup
pip install pre-commit && pre-commit install  # Existing developers
```

## Architecture

### Core Pipeline
```
AllInputs → RunCosting() → CostingData → CreateReportContent() → ReportContent → RenderFinalReport() → PDF
```

1. **Inputs** (`pyfecons/inputs/`): `AllInputs` container holds 20+ domain-specific input classes (Basic, PowerInput, RadialBuild, Blanket, Coils, Lasers, etc.)

2. **Costing Engine** (`pyfecons/costing/`): Hierarchical Cost Accounting Structure (CAS) system
   - CAS10: Pre-construction costs
   - CAS20: Direct costs (buildings, reactor equipment)
   - CAS22: Reactor plant equipment (largest, most complex)
   - CAS23-29: Turbine, electrical, misc equipment
   - CAS30-60: Indirect and capitalized costs
   - CAS70-90: Annualized costs
   - LCOE/NPV: Final economic analysis

3. **Report Generation** (`pyfecons/report/`): LaTeX template hydration system with template files in `pyfecons/costing/{mfe,ife}/templates/`

### MFE vs IFE Differences
Several CAS categories have reactor-type-specific implementations:
- **CAS220103**: Coils (MFE) vs Lasers (IFE)
- **CAS220104**: Supplementary Heating (MFE) vs Ignition Lasers (IFE)
- **CAS220108**: Divertor (MFE) vs Target Factory (IFE)

### Key Data Types
- `CostingData` (`pyfecons/costing_data.py`): Main output container with all CAS results
- `ReportSection`: Base class for cost category outputs (template_file, replacements, figures)
- Custom units in `pyfecons/units.py`: `M_USD`, `MW`, `Meters`, `Percent`, etc. (floats with semantic meaning)

### Cost Calculation Pattern
Each cost category follows this pattern:
```python
def cas_xx(inputs: AllInputs, data: CostingData) -> ReportSection:
    OUT = data.casXX
    # ... calculations ...
    OUT.C_XXXXX = M_USD(calculated_value)
    OUT.template_file = 'CASXXXXXX.tex'
    OUT.replacements = {'C_XXXXX': round(OUT.C_XXXXX), ...}
    return OUT
```

### Customer Configuration
- Customer folders: `customers/{CUSTOMER_NAME}/{mfe,ife}/`
- `DefineInputs.py`: Must export `Generate() -> AllInputs`
- `DefineInputsSafety.py`: Optional safety-specific inputs
- Custom templates override library templates when placed in `customers/.../templates/`

## Code Style

- Black formatter (88 char lines, double quotes)
- isort for imports (black profile)
- Flake8 for linting
- Pre-commit hooks run automatically on commit

## External Dependencies

LaTeX is required for PDF generation:
- Mac: `brew install --cask mactex`
- Linux: `sudo apt install texlive-latex-extra texlive-font-utils`
