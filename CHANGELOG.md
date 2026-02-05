# Changelog: PyFECONS Fork

**Fork**: [Tal-Rubin/PyFECONS](https://github.com/Tal-Rubin/PyFECONS)
**Upstream**: [Woodruff-Scientific-Ltd/PyFECONS](https://github.com/Woodruff-Scientific-Ltd/PyFECONS)

---

## Bug Fixes

### `n_mod` scaling for reactor equipment (55e4f8e)
- **Issue**: CAS22 (reactor plant equipment) was not multiplied by `n_mod`, while CAS23-26 and LCOE denominator were. This caused LCOE to be underestimated for multi-module plants.
- **Fix**: Added `n_mod` parameter to `cas22_reactor_plant_equipment_total_costs()` and multiply `C220100` and `C220000` by `n_mod`
- **Files**: `cas22_reactor_plant_equipment_total.py`, `mfe.py`, `ife.py`

### LCOE inflation handling for OPEX
- **Issue**: O&M and fuel costs (CAS70 + CAS80) were multiplied by `(1 + inflation)^plant_lifetime`, which gave a future value rather than a properly discounted levelized cost. This caused LCOE to increase with longer plant lifetimes.
- **Fix**: Replaced with correct growing annuity formula:
  - Compute present value of OPEX stream: `PV = OPEX × [1 - ((1+g)/(1+i))^n] / (i-g)`
  - Annualize using CRF: `Levelized_OPEX = CRF × PV`
  - Where `g` = inflation rate, `i` = interest rate, `n` = plant lifetime
- **Convention**: OPEX is treated as first-year-of-operation dollars (standard NREL/IEA convention)
- **Files**: `lcoe.py`, `mfe.py`, `ife.py`

---

## New Features

### Capital Recovery Factor calculation (774d250)
- Computes CRF dynamically from interest rate and plant lifetime instead of using a fixed value
- Formula: `CRF = i*(1+i)^n / ((1+i)^n - 1)`
- Adjusts for construction time by capitalizing costs: `effective_crf = crf * (1+i)^Tc`
- Falls back to legacy `financial.capital_recovery_factor` if parameters invalid
- **Files**: `cas90_annualized_financial.py`, `financial.py`

### Sensitivity Analysis Tool (bceef77, a3965bb)
- Added `sensitivity_analysis.py` - computes d(LCOE)/d(input) for all scalar parameters
- Uses finite differences with PyFECONS full calculations
- Outputs ranked elasticities to console and Excel
- **Files**: `sensitivity_analysis.py`

### Costing Constants Refactor (bceef77)
- Created `CostingConstants` dataclass to centralize magic numbers
- Consolidates ~40 cost parameters (building costs, equipment costs, contingency rates, etc.)
- Makes assumptions explicit and editable
- **Files**: `costing_constants.py`, `all_inputs.py`, + 14 CAS calculation files

---

## Infrastructure

- CI configuration updates (84579be)
- Black formatting compliance (449ebfc, a0479e7)
- Test fixes (5d15099, 30d6586, 6b26660)

