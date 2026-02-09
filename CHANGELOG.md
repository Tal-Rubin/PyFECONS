# Changelog: PyFECONS Fork

**Fork**: [Tal-Rubin/PyFECONS](https://github.com/Tal-Rubin/PyFECONS)
**Upstream**: [Woodruff-Scientific-Ltd/PyFECONS](https://github.com/Woodruff-Scientific-Ltd/PyFECONS)

---

## CAS 10: Pre-Construction Costs Overhaul

### C110000 Land and Land Rights — land-intensity formula
- **Issue**: Legacy formula used opaque power-proportional scaling inherited from fission-era ARIES studies (1,000-acre assumption).
- **Fix**: Replaced with transparent land-intensity approach based on modern compact fusion project data. Site area = `land_intensity * P_NET * sqrt(N_mod)`, with `land_intensity = 0.25 acres/MWe` (from CFS ARC: 100 acres for 400 MWe). Land cost at $10,000/acre (USDA 2025 farmland average $4,350/acre with industrial-zone premium).
- **Files**: `cas10_pre_construction.py`, `costing_constants.py`

### C130000 Plant Licensing — fuel-type-specific costs under NRC Part 30
- **Issue**: Single $210M licensing constant was based on fission reactor licensing under NRC Part 50/52 (World Nuclear Org). Fusion is regulated under Part 30 (byproduct materials) per the ADVANCE Act of 2024.
- **Fix**: Replaced with per-fuel-type licensing constants: D-T $5M, D-D $3M, D-He3 $1M, p-B11 $0.1M. Calculation selects the correct cost based on `basic.fuel_type`. Removed `licensing_safety_addon` (double-counting). Deleted `costing/safety/licensing.py`.
- **Files**: `cas10_pre_construction.py`, `costing_constants.py`, `licensing.py` (deleted)

### C120000, C140000, C150000 — researched cost updates
- **Issue**: Placeholder values ($10M site permits, $5M plant permits, $5M plant studies) were unsourced and inconsistent with TeX narrative.
- **Fix**: Updated to research-backed estimates: C120000 $10M->$3M (EA under NEPA, not full EIS; GAO-14-369), C140000 $5M->$2M (standard industrial), C150000 $5M->$20M (FOAK; was below own stated $10-100M range).
- **Files**: `costing_constants.py`

### C150000 Plant Studies — FOAK/NOAK differentiation
- **Issue**: Flat $20M regardless of plant maturity. NOAK plants reuse established safety cases and engineering studies.
- **Fix**: Added `plant_studies_noak = $4M` constant. Calculation branches on `basic.noak` flag.
- **Files**: `cas10_pre_construction.py`, `costing_constants.py`

### Licensing timeline impact on project duration (FOAK only)
- **Issue**: `construction_time` did not account for NRC licensing duration, which varies by fuel type under Part 30. This understated interest during construction (CAS60) and the CRF adjustment (CAS90) for FOAK plants.
- **Fix**: Added per-fuel-type licensing time constants (D-T: 2.5yr, D-D: 1.5yr, D-He3: 0.75yr, p-B11: 0yr). `total_project_time()` adds licensing time to physical construction time for FOAK; returns just construction time for NOAK. Applied in CAS60 (IDC), CAS70 (levelized O&M), CAS80 (levelized fuel), and CAS90 (CRF).
- **Files**: `financials.py`, `costing_constants.py`, `cas60_capitalized_financial.py`, `cas70_annualized_om.py`, `cas90_annualized_financial.py`, `mfe/cas80_annualized_fuel.py`, `ife/cas80_annualized_fuel.py`, `mfe.py`, `ife.py`

### CAS10 TeX templates and bibliography
- Added 2025 update blocks for C110000 (fusion project land table, land-intensity formula), C120000 (EA vs EIS), C130000 (fuel-type licensing table), C140000, C150000 (FOAK/NOAK range).
- Added `\cite{}` references: `nrc10cfr30`, `advanceact2024`, `gao14369`, `usda2025farmland`, `nrc10cfr170`.
- Report values truncated to 2 decimal places.
- **Files**: `CAS100000.tex` (MFE + IFE), `additions.bib` (MFE + IFE), `cas100000_section.py`

---

## Bug Fixes

### LCOE levelization of annual costs (CAS70, CAS80, CAS90)
- **Issue**: O&M and fuel costs were not properly levelized. CAS70 used an inline growing-annuity formula but CAS80 (fuel) was not levelized at all — raw annual cost was fed directly into LCOE. CRF calculation was duplicated across CAS70 and CAS90. The original OPEX formula `(1 + inflation)^plant_lifetime` gave a future value rather than a discounted levelized cost.
- **Fix**: Created shared `financials.py` with `compute_crf`, `compute_effective_crf`, and `levelized_annual_cost`. CAS70, CAS80 (MFE + IFE), and CAS90 now use these shared functions. OPEX treated as first-year-of-operation dollars (NREL/IEA convention).
- **Files**: `financials.py` (new), `cas70_annualized_om.py`, `cas90_annualized_financial.py`, `mfe/cas80_annualized_fuel.py`, `ife/cas80_annualized_fuel.py`, `mfe.py`, `ife.py`

### `n_mod` scaling for reactor equipment (55e4f8e)
- **Issue**: CAS22 (reactor plant equipment) was not multiplied by `n_mod`, while CAS23-26 and LCOE denominator were. This caused LCOE to be underestimated for multi-module plants.
- **Fix**: Added `n_mod` parameter to `cas22_reactor_plant_equipment_total_costs()` and multiply `C220100` and `C220000` by `n_mod`.
- **Files**: `cas22_reactor_plant_equipment_total.py`, `mfe.py`, `ife.py`

---

## New Features

### Costing Constants (bceef77)
- Created `CostingConstants` dataclass to centralize ~40 cost parameters (building costs, equipment costs, contingency rates, etc.)
- **Files**: `costing_constants.py`, `all_inputs.py`, + 14 CAS calculation files

### Sensitivity Analysis Tool (bceef77, a3965bb)
- Computes d(LCOE)/d(input) for all scalar parameters using finite differences
- Outputs ranked elasticities to console and Excel
- **Files**: `sensitivity_analysis.py`

---

## Infrastructure

- CI configuration updates (84579be)
- Black formatting compliance (449ebfc, a0479e7)
- Test fixes (5d15099, 30d6586, 6b26660)
