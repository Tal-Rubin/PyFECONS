# Changelog: PyFECONS Fork

**Fork**: [Tal-Rubin/PyFECONS](https://github.com/Tal-Rubin/PyFECONS)
**Upstream**: [Woodruff-Scientific-Ltd/PyFECONS](https://github.com/Woodruff-Scientific-Ltd/PyFECONS)

---

## Sensitivity Analysis in Report (2026-02-17)

### New Feature: LCOE Sensitivity Table in PDF Report
- **Issue**: Sensitivity analysis existed only as a standalone CLI script (`sensitivity_analysis.py`) with Excel export. Users had no way to see which input parameters most affect LCOE directly in the generated report.
- **Fix**: Integrated sensitivity analysis into the standard report pipeline. When `RunCostingForCustomer.py` runs, it automatically perturbs every scalar input by 1%, re-runs costing, and computes elasticity (ε = % change in LCOE per % change in parameter). The top 15 most sensitive parameters appear in a LaTeX table in the PDF report, with colored direction indicators (red +, green −).
- **CLI flags**: `--no-sensitivity` skips analysis; `--lite` reports also skip it automatically.
- **Performance**: ~100-150 RunCosting calls with suppressed stdout/stderr via `contextlib.redirect_stdout`. Typically 10-75 seconds depending on parameter count.

### New Files
- `pyfecons/sensitivity.py` — Core library module: `SensitivityEntry`/`SensitivityResult` dataclasses, `PARAMETER_DISPLAY_NAMES` dict (~100 human-readable LaTeX names), `get_scalar_leaves()` with bool exclusion fix, `sensitivity_analysis()` function
- `pyfecons/report/sections/sensitivity_section.py` — `SensitivitySection(ReportSection)` generating dynamic table rows with `_escape_latex()` helper
- `pyfecons/costing/shared/templates/SensitivityAnalysis.tex` — Shared LaTeX template with elasticity equation, 5-column table (Rank, Parameter, Baseline, |ε|, Dir.), used by both MFE and IFE

### Modified Files
- `pyfecons/report/utils.py` — `get_report_sections()` accepts optional `SensitivityResult`, appends `SensitivitySection` after NPV
- `pyfecons/pyfecons.py` — `CreateReportContent()` threads `sensitivity_result` to MFE/IFE report builders
- `pyfecons/__init__.py` — Exports `SensitivityResult` and `sensitivity_analysis`
- `pyfecons/report/mfe_report.py` — Accepts `sensitivity_result`, sets `%sensitivity_flag%` in document template
- `pyfecons/report/ife_report.py` — Same changes as MFE
- `pyfecons/costing/mfe/templates/Costing_ARPA-E_MFE_Modified.tex` — Added `\ifsensitivity` conditional block
- `pyfecons/costing/ife/templates/Costing_ARPA-E_IFE_Modified.tex` — Same changes as MFE
- `RunCostingForCustomer.py` — Added `--no-sensitivity` flag, runs analysis after costing, passes result to report, suppressed pdflatex output
- `sensitivity_analysis.py` — Refactored to import from `pyfecons.sensitivity` instead of duplicating logic

---

## Test Coverage Expansion & Template Fixes (2026-02-17)

### New Unit Tests for Previously Untested Modules
- **Issue**: Four core calculation modules had no unit tests: reactor equipment cost components, shield costs, NPV, and legacy detailed coil costing.
- **Fix**: Created 4 new test files (~73 tests):
  - `test_cas220101_enhanced.py` — 30 tests: first wall material selection by fuel type (DT W/Be/Li/FLiBe, DD→W, DHe3/PB11→FS), blanket costs for all BlanketType variants, neutron multiplier (7.5% of blanket, DT-only), radial build geometry (cumulative radii, MFE vs IFE), volume positivity, integration (sum-of-components, aneutronic zero blanket/multiplier)
  - `test_npv.py` — 8 tests: zero discount rate identity, positive discount attenuation, single-year undiscounted, zero lifetime, sensitivity monotonicity for p_net/availability/discount rate/lifetime
  - `test_cas220102_shield.py` — 13 tests: MFE total equals sum, misc 10% of bioshield, volume storage, IFE default 5x and custom scaling, material fraction comparisons
  - `test_cas220103_coils.py` — 22 tests: simplified model (positive cost, B-field scaling, R² scaling, conductor×markup identity, custom overrides, REBCO default), geometry factor formulas (tokamak/mirror/stellarator), confinement defaults (all 4 types), legacy detailed (shim 5%, total summation, magnet type sorting, coil count, PF pair counting)
- **Files**: `tests/test_cas220101_enhanced.py`, `tests/test_npv.py`, `tests/test_cas220102_shield.py`, `tests/test_cas220103_coils.py`

### pytest-cov Integration
- Added `pytest-cov==6.0.0` to `requirements.txt`
- Configured in `pyproject.toml`: `--cov=pyfecons --cov-report=term-missing --cov-fail-under=40`
- Every `pytest` run now shows line-level coverage and fails if overall coverage drops below 40%

### Magic Multipliers Documented/Configurable
- **IFE 5x shield scaling** (`cas220102_shield.py`): Made configurable as `Shield.ife_shield_scaling` (default 5.0). No published source identified; documented as inherited from original codebase.
- **7.5% neutron multiplier** (`cas220101_reactor_equipment.py`): Already well-documented with source reference. No change needed.
- **5% shim coil** (`cas220103_coils.py`): Documented inline per ARIES methodology (Waganer 2006), consistent with ITER correction coils at ~3-5%.
- **Files**: `pyfecons/inputs/shield.py`, `pyfecons/costing/calculations/cas22/cas220102_shield.py`, `pyfecons/costing/mfe/cas22/cas220103_coils.py`

### LaTeX Template Fixes
- **DEC rows in MFE power table**: Added f_dec, eta_de, P_dee, P_wall, P_the rows; updated P_TH and P_ET equations; fixed section numbering (2.5.3→2.6, 2.6.→2.7, 2.6.1→2.7.1)
- **IFE power table numbering**: Fixed gap 2.5.3→2.5
- **CAS 22.1.19 in CASstructure.tex**: Added Scheduled Replacement row with M220119 ARIES placeholder
- **LCOE C_SCR**: Fixed stale reference in shared, MFE lite, and IFE lite LCOE templates — clarifies that scheduled component replacement is now capitalized under CAS 22.01.19 within C_AC
- **Foreword citation**: Added `\cite{Woodruff2026CostingFrameworkFusion}` to both MFE and IFE forewords
- **C220112 bug fix**: Added missing C220112 (Isotope Separation) mapping in `cost_table_builder.py` with None guard; added `M220112: "-"` to MFE and IFE comparison tables
- **DEC placeholders**: Added FDEC__, ETADE_, PDEE__, PWALL_, PTHEL_ to `power_table_section.py`
- **Files**: `powerTableMFEDT.tex`, `powerTableIFEDT.tex`, `power_table_section.py`, `CASstructure.tex`, `LCOE.tex` (×3), `foreword.tex` (×2), `cost_table_builder.py`, `cost_table_mfe.py`, `cost_table_ife.py`

---

## Simplified Coil Costing Model (2026-02-13)

### New Feature: Conductor Scaling Mode for CAS 220103
- **Issue**: The existing coils model requires 10+ individually-specified `Magnet` objects (TF, CS, PF1-PF8) with per-coil geometry — ~140 input values. Too detailed for a TEA tool comparing confinement concepts. Also tokamak-centric with no differentiation by confinement type.
- **Fix**: Added a simplified scaling mode alongside the existing detailed model. When `b_max` and `r_coil` are provided (instead of a `magnets` list), uses conductor scaling law:
  ```
  total_kAm = G × B_max × R_coil² / (μ₀ × 1000)
  total_cost = total_kAm × cost_per_kAm × manufacturing_markup
  ```
- **Geometry factor G** accounts for coil topology:
  - **Tokamak** (ST/CT): G = 4π² ≈ 39.5 — empirical total-system scaling for TF+CS+PF combined
  - **Magnetic mirror**: G = n_coils × 4π — each solenoid independently produces field (N does NOT cancel)
  - **Stellarator**: G = 4π² × path_factor — cooperative field like tokamak, but 3D coil paths ~2× longer
- **`r_coil` encompasses plasma + vessel + blanket + shield**. Aneutronic fuels without a breeding blanket get smaller r_coil → less conductor → cheaper magnets.
- **Coil material selection**: New `CoilMaterial` enum with default $/kAm:
  - REBCO_HTS: $50/kAm (GdBCO/YBCO tape, CFS/SPARC)
  - NB3SN: $7/kAm (ITER TF/CS, LTS CICC)
  - NBTI: $7/kAm (ITER PF, workhorse LTS)
  - COPPER: $1/kAm (resistive, requires large p_coils input)
- **Manufacturing markup** per confinement type: Mirror 2.5×, ST 6×, CT 8×, Stellarator 12×
- **Calibrated** against known designs:
  - SPARC (B=20T, R=1.85m): conductor $107M × 6 = $645M (CFS est. $400-800M)
  - ITER (B=13T, R=6.2m): conductor $110M (Nb₃Sn at $7/kAm)
  - W7-X (B=5T, R=5.5m): conductor $67M × 15 = $1B (~€1B actual)
  - Mirror (4 coils, B=10T, R=1m): conductor $20M × 2.5 = $50M
- **Backward compatible**: If `magnets` list is provided, the legacy detailed model runs unchanged.
- **Validation**: Simplified mode validates b_max > 0, r_coil > 0, and warns if copper coils + no p_coils.
- **Files**:
  - `pyfecons/enums.py` — Added `CoilMaterial` enum; uncommented `STELLARATOR`, `CONVENTIONAL_TOKAMAK` in `ConfinementType`
  - `pyfecons/inputs/coils.py` — Added 7 simplified fields (b_max, r_coil, n_coils, coil_material, cost_per_kAm, coil_markup, path_factor)
  - `pyfecons/costing/mfe/cas22/cas220103_coils.py` — Added `compute_geometry_factor()` + `cas_220103_coils_simplified()`
  - `pyfecons/costing/categories/cas220103_coils.py` — Added 7 output fields
  - `pyfecons/costing/mfe/mfe.py` — Dispatch: `magnets` → legacy, else → simplified
  - `pyfecons/report/sections/cas220103_section.py` — Split into simplified/detailed branches
  - `pyfecons/costing/mfe/templates/CAS220103_MFE_simplified.tex` — New LaTeX template
  - `pyfecons/validation.py` — Added simplified coils + copper p_coils validation
  - `customers/CATF/mfe/DefineInputs.py` — Switched to `Coils(b_max=18, r_coil=1.85, coil_material=CoilMaterial.REBCO_HTS)`
  - `tests/test_simplified_coils.py` — 30 new tests (geometry factors, scaling, materials, calibration, validation)
  - `tests/test_validation.py` — Updated magnet tests to create own magnets (CATF config no longer has magnets list)

---

## Unit Tests for Core Calculation Modules (2026-02-12 – 2026-02-13)

### New Test Suite
- **Issue**: Zero unit tests for calculation modules. Bugs in power balance and fuel physics went undetected.
- **Fix**: Created 4 new test files (~100 tests) covering the highest-risk modules:
  - `test_fuel_physics.py` — 20 tests: Q-value sanity, DT/DD/DHe3/PB11 ash splits, energy conservation, scipy-derived expected values
  - `test_power_balance.py` — 25 tests: MFE DT baseline formulas, DEC routing, IFE via fixture, fuel type comparisons, parametrized conservation
  - `test_financials.py` — 20 tests: CRF, effective CRF, levelized annual cost, licensing time, total project time
  - `test_lcoe.py` — 8 tests: LCOE formula, multi-module scaling, availability proportionality
- **Infrastructure**:
  - `tests/helpers.py` — shared `load_mfe_inputs()`/`load_ife_inputs()` (eliminated ~120 lines of duplication)
  - `tests/conftest.py` — session-scoped fixtures for read-only use
  - `pythonpath` added to `pyproject.toml` so `tests/` modules are importable
- **Refactored**: `fuel_physics.py` now derives all MeV constants from CODATA particle masses via `scipy.constants` (replacing hardcoded approximations)
- **Files**: `tests/test_fuel_physics.py`, `tests/test_power_balance.py`, `tests/test_financials.py`, `tests/test_lcoe.py`, `tests/helpers.py`, `tests/conftest.py`, `pyfecons/costing/calculations/fuel_physics.py`

---

## Material Properties Completion (2026-02-13)

### Completed Four Undefined Materials
- **Issue**: Four materials in `materials.py` had placeholder or incorrect values (zero density, placeholder costs), causing incorrect cost calculations for any design using them.
- **Fix**: Researched and completed all four:
  - **GdBCO** (REBCO HTS tape): rho=6350 kg/m³, c=55. Same class as YBCO; used in CFS/SPARC magnets.
  - **He** (blanket coolant): rho=5.64 kg/m³ (at 8 MPa, 400°C from NIST), c_raw=$24/kg. Chemically/neutronically inert gas coolant for DEMO blanket concepts.
  - **NbTi** (LTS superconductor): rho=6170 kg/m³, c=4. ITER PF coils, workhorse LTS. CICC architecture differs from REBCO tape.
  - **FLiBe** (molten salt): rho 1900→1940 kg/m³ (700°C ref), c_raw 1000→40 $/kg (aligned with c, removed unjustified 25× discrepancy), m 1→1.2.
- **Research doc**: `fusion-tea/knowledge/research/approved/20260213-superconductor-and-coolant-materials.md`
- **Files**: `pyfecons/materials.py`

---

## Input Validation Layer (2026-02-12)

### Centralized Validation Module
- **Issue**: 22 input dataclasses with ~200 fields and zero validation. Users could input negative power, efficiency > 1, or None for required fields and get either a confusing crash deep in the calculation pipeline or a confident-looking PDF with meaningless numbers.
- **Fix**: Created `validation.py` with `validate_inputs()` called from `RunCosting()` before dispatch. Three-tier validation:
  - **Tier 1 — Required fields**: Machine-type-dependent (MFE requires coils/eta_pin/elon/coil_t; IFE requires lasers/eta_pin1/eta_pin2/implosion_frequency). Checks both top-level dataclasses and critical fields within them.
  - **Tier 2 — Field-level range checks**: Data-driven `FIELD_RULES` table (~50 rules) covering power values, efficiencies, fractions, radial build thicknesses, financial parameters, and shield fractions.
  - **Tier 3 — Cross-field checks**: Shield fractions sum ≈ 1.0 (warning), time_to_replace ≤ plant_lifetime, division-by-zero prevention (eta_pin, eta_pin1/2), fuel-type burn fraction defaults (DD/DHe3).
- **Design decisions**:
  - Centralized module (not `__post_init__`) to avoid touching 22 stable dataclass files and to support cross-field checks
  - Multi-error accumulation: all errors reported at once via `ValidationError` (not fail-fast)
  - Warnings suppressed when hard errors exist (no noise)
  - Per-magnet validation: coil_count, r_centre, dr, dz, frac_in, mfr_factor
- **Files**: `pyfecons/validation.py` (new), `pyfecons/exceptions.py` (added FieldError, ValidationWarning, ValidationError), `pyfecons/pyfecons.py` (2-line integration), `tests/test_validation.py` (new, 44 tests)

### Runtime Crash Bug Fixes
- **Issue**: Two `raise f"string"` statements threw `TypeError` instead of the intended error message.
- **Fix**: Changed to `raise ValueError(f"string")`.
- **Files**: `pyfecons/costing/calculations/cas22/cas220101_reactor_equipment.py:405`, `pyfecons/costing/mfe/cas22/cas220103_coils.py:423`

### Customer File Updates
- **CATF MFE/IFE**: Added `p_pump=MW(1)` (was unset, now required by validation)

---

## Power Balance Rework (2026-02-11 – 2026-02-12)

### Thermal Power Model Fix
- **Issue**: `p_th` only counted neutron blanket heating (`mn * p_nrl`), completely missing charged particle wall heating, input heating, and pump heat recovery. This underestimated thermal power for ALL fuels: DT by ~19%, DD/DHe3 significantly, and p-B11 was completely broken (100% charged particles, zero thermal power).
- **Fix**: Corrected formula to `p_th = mn * p_neutron + p_ash_thermal + p_input + eta_p * p_pump`. Each term: neutron blanket multiplication, charged particle wall deposition, plasma heating power, and recovered pump heat.

### Fuel-Dependent Ash/Neutron Split
- **Issue**: `compute_p_alpha` treated DD as pure DD (ignoring secondary DT/DHe3 burns from ash). Real DD plasmas are naturally semi-catalyzed — tritium ash burns with D (~97% burn fraction), He-3 ash burns with D (~69% burn fraction).
- **Fix**: Created `fuel_physics.py` with `compute_ash_neutron_split()`. Renamed p_alpha → p_ash throughout. Fuel models:
  - **DT**: 3.52/17.58 = 20.02% charged
  - **DD**: Semi-catalyzed model parametrized by `dd_f_T` (~0.969) and `dd_f_He3` (~0.689). With defaults: ~56.5% charged.
  - **DHe3**: Primary D-He3 is 100% charged, but ~7% of energy comes from unavoidable D-D side reactions producing some neutrons. Parametrized by `dhe3_dd_frac` (~0.07), `dhe3_f_T` (~0.97). With defaults: ~95.4% charged.
  - **p-B11**: 100% charged (aneutronic)
- **Default burn fractions**: Single source of truth in `fuel_physics.py` function parameter defaults. `power_balance.py` passes through only non-None customer overrides via `**kwargs`.
- **Reference**: `20260211-dd-steady-state-burn-analysis.md`

### Direct Energy Conversion (DEC) Support
- **Feature**: Added DEC routing for MFE: `f_dec` fraction of ash power goes to direct energy converter. `eta_de` fraction becomes electricity (`p_dee`), remainder is waste heat (`p_dec_waste`). Remaining `(1 - f_dec)` ash thermalizes on the wall.
- **Impact**: When `f_dec = 0` (default), all ash thermalizes through thermal cycle — backward compatible.
- **Fields**: `f_dec` (capture fraction), `eta_de` (conversion efficiency), `p_dee` (DEC electric), `p_dec_waste` (DEC waste heat)

### p_sub Formula Fix
- **Issue**: `p_sub = f_sub * p_the` (thermal electric only). Templates documented `f_sub * P_ET` (gross electric). These differ when DEC is enabled.
- **Fix**: Changed to `p_sub = f_sub * p_et` to match template documentation.

### p_loss Formula Fix
- **Issue**: `p_loss = p_th - p_the` only counted thermal cycle rejection, missing DEC waste heat.
- **Fix**: Changed to `p_loss = (p_th - p_the) + p_dec_waste`.

### PowerInput Cleanup
- **Removed fields**: `fpcppf` (orphaned after p_pump became direct MW input), `p_machinery` (never used in calculations), `p_tf`/`p_pf` (always summed to p_coils), `p_tfcool`/`p_pfcool` (always summed to p_cool)
- **Added fields**: `p_coils` (was p_tf + p_pf), `p_cool` (was p_tfcool + p_pfcool), `p_pump` (direct MW input), `f_dec`, `dd_f_T`, `dd_f_He3`, `dhe3_dd_frac`, `dhe3_f_T`
- **Deleted files**: MFE/IFE `PowerBalance.py` wrappers (unified into single `power_balance.py`)

### LaTeX Template Updates
- **MFE templates** (standard + lite): Fixed `M_N` display (was incorrectly showing `M_N = P_TH/P_fusion`), added explicit p_th formula, removed stale per-coil breakdown rows
- **IFE non-lite template**: Converted from hardcoded values to placeholder tokens (was non-functional for replacements), removed stale Machinery and fpcppf rows
- **IFE lite template**: Fixed `M_N` display, added pump capture efficiency row, fixed numbering gap
- **Fuel-dependent ash split text**: All 4 templates now use an `ASHSPLITTEXT` placeholder that generates a fuel-type-specific subsection explaining the charged particle / neutron power split (reaction channels, burn fractions, ash fraction) for the selected fuel only
- **Report section** (`power_table_section.py`): Updated replacement keys to match new templates, added `_ash_split_text()` function generating fuel-specific LaTeX for DT, DD, DHe3, and p-B11

### Customer File Updates
- **CATF MFE**: Consolidated `p_tf + p_pf → p_coils=MW(2)`, `p_tfcool + p_pfcool → p_cool=MW(13.7)`, removed `fpcppf`, added `f_dec=Percent(0)`
- **CATF IFE**: Removed `fpcppf`, `p_machinery`

### Files Changed
- `pyfecons/costing/calculations/fuel_physics.py` (new)
- `pyfecons/costing/calculations/power_balance.py` (rewritten)
- `pyfecons/inputs/power_input.py`
- `pyfecons/costing/accounting/power_table.py`
- `pyfecons/report/sections/power_table_section.py`
- `pyfecons/costing/mfe/templates/powerTableMFEDT.tex`
- `pyfecons/costing/mfe/templates/lite/powerTableMFEDT.tex`
- `pyfecons/costing/ife/templates/powerTableIFEDT.tex`
- `pyfecons/costing/ife/templates/lite/powerTableIFEDT.tex`
- `customers/CATF/mfe/DefineInputs.py`
- `customers/CATF/ife/DefineInputs.py`
- Deleted: `pyfecons/costing/mfe/PowerBalance.py`, `pyfecons/costing/ife/PowerBalance.py`

---

## CAS 220101: Fuel-Type-Aware First Wall Material Selection (2026-02-09)

### First Wall Material Automatically Chosen Based on Fuel Type
- **Issue**: First wall material was always taken from `blanket.first_wall` configuration, even though non-D-T fuels have different requirements and don't need expensive neutron-resistant materials.
- **Physics**:
  - **D-T**: 14.1 MeV neutrons cause severe radiation damage → Requires Be, W, or liquid walls
  - **D-D**: 2.45 MeV neutrons (lower energy) → Tungsten provides adequate protection
  - **D-He3**: Aneutronic → Only thermal handling needed, Ferritic Steel is adequate
  - **p-B11**: Fully aneutronic → Only thermal handling needed, Ferritic Steel is adequate
- **Fix**: Modified `compute_first_wall_costs()` to take `fuel_type` parameter:
  - D-T: Uses configured `blanket.first_wall` material
  - D-D: Automatically uses Tungsten ($535M)
  - D-He3/p-B11: Automatically uses Ferritic Steel ($21M)
- **Cost Impact**: Aneutronic first wall cost reduced from $461M (Be) to $21M (FS) = 22x reduction
- **Files**: `cas220101_reactor_equipment.py`

---

## CAS 220101: Fuel-Type-Aware Blanket Costs (2026-02-09)

### Blanket Cost Automatically Set to Zero for Non-D-T Fuels
- **Issue**: Tritium breeding blanket costs (C22010102) were being calculated for all fuel types, even though only D-T fusion requires tritium breeding. This caused p-B11, D-D, and D-He3 plants to incorrectly include ~$790M in blanket costs.
- **Physics**:
  - **D-T**: Requires lithium-based breeding blanket (TBR > 1.0) to produce tritium
  - **D-D**: Produces tritium as byproduct, no breeding blanket needed
  - **D-He3**: No tritium involved, no breeding blanket needed
  - **p-B11**: Fully aneutronic, no tritium, no breeding blanket needed
- **Fix**: Modified `compute_blanket_costs()` to take `fuel_type` parameter and return $0 for non-D-T fuels, regardless of `blanket_type` setting in inputs.
- **Cost Impact**: Non-D-T plants now correctly show $0 blanket cost instead of ~$790M
- **Files**: `cas220101_reactor_equipment.py`

---

## Material Cost Corrections: Beryllium and Lithium Titanate (2026-02-09)

### Beryllium (Be) First Wall Material — c_raw corrected from $5,750/kg to $900/kg
- **Issue**: Beryllium cost was set at $5,750/kg with no source documentation. This value was ~5-10x higher than market prices, causing first wall costs to be massively overestimated.
- **Research**:
  - Shanghai Metal Market (2025): $1,031-1,035/kg
  - Accio market data: $600-1,200/kg for high-purity ingots
  - USGS Mineral Commodity Summaries 2024: confirms sub-$1,000/kg range
- **Fix**: Updated `c_raw` from $5,750 to $900/kg (mid-range of market data)
- **Cost Impact**: First wall cost reduced by ~6.4x (e.g., $2,948M → $461M for 92 m³ Be first wall)
- **Note**: ITER switched from Be to W first wall in 2023 due to melting/dust concerns
- **Files**: `materials.py`, `pycosting_arpa_e_mfe.py`, `pycosting_arpa_e_ife2.py`, customer input files

### Lithium Titanate (Li2TiO3) Breeder Material — c_raw corrected from $1,297/kg to $150/kg
- **Issue**: Li2TiO3 cost was set at $1,297.05/kg with no source documentation. This value was ~6-10x higher than typical ceramic pricing, causing blanket costs to be massively overestimated.
- **Research**:
  - MDPI review (2022): Li2TiO3 characterized as having "low production cost"
  - ResearchGate: "low-cost synthesis" methods actively researched
  - Comparable technical ceramics: $50-200/kg range
  - Li4SiO4 (alternate breeder) in codebase: $1/kg
- **Fix**: Updated `c_raw` from $1,297.05 to $150/kg (mid-range of ceramic pricing)
- **Cost Impact**: Blanket cost reduced by ~8.6x (e.g., $6,829M → $789M for 512 m³ Li2TiO3 blanket)
- **Files**: `materials.py`, `pycosting_arpa_e_mfe.py`, `pycosting_arpa_e_ife2.py`, customer input files

### Total CAS 220101 Impact
| Component | Previous | Corrected | Reduction |
|-----------|----------|-----------|-----------|
| First Wall (Be) | $2,948M | $461M | 6.4x |
| Blanket (Li2TiO3) | $6,829M | $789M | 8.6x |
| Neutron Multiplier | $512M | $59M | 8.7x |
| **Total C220101** | **$10,289M** | **$1,309M** | **7.9x** |

### Sources Added
- Shanghai Metal Market: https://www.metal.com/Other-Minor-Metals/201102250108
- Accio market data: https://www.accio.com/plp/beryllium-metal-price
- USGS MCS 2024: https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-beryllium.pdf
- MDPI Li2TiO3 review: https://www.mdpi.com/2079-6412/12/8/1053
- ITER Be→W decision: https://www.iter.org/machine/blanket

---

## CAS 22: Reactor Plant Equipment — Fuel-Dependent Subsystems (2026-02-09)

### New CAS 220112: Isotope Separation Systems
- **Issue**: PyFECONS lacked fuel-dependent isotope separation infrastructure costs. All fusion fuels require isotope separation (D₂O extraction, Li-6 enrichment, B-11 enrichment, H-1 purification), representing $155M-400M in missing capex per GWe depending on fuel type.
- **Fix**: Added CAS 220112 with five fuel-dependent subcosts:
  - **C22011201**: Deuterium extraction plant (D-T, D-D, D-He³) — $300M base @ 1 GWe, scaling exponent 0.6
  - **C22011202**: Lithium-6 enrichment (D-T only) — $100M base @ 1 GWe, COLEX process
  - **C22011203**: Protium purification (p-B¹¹ only) — $30M base @ 1 GWe
  - **C22011204**: Boron-11 enrichment (p-B¹¹ only) — $125M base @ 1 GWe
  - **C22011205**: Helium-3 extraction (D-He³ placeholder) — $0 (lunar mining not viable)
- **Cost Impact by Fuel**:
  - D-T: $400M ($300M D₂O + $100M Li-6)
  - D-D: $300M (D₂O only)
  - p-B¹¹: $155M ($30M H-1 + $125M B-11)
  - D-He³: $300M+ (pending He-3 availability)
- **Files**: `cas220112.py`, `cas220112_isotope_separation.py`, `cas220112_section.py`, `CAS220112.tex` (MFE + IFE), `costing_data.py`, `mfe.py`, `ife.py`, `utils.py`
- **Reference**: Comprehensive Fusion Reactor Subsystems Framework (2026-02-08), CANDU D₂O plants, Li-6 COLEX facilities, B-11 laser separation studies

### New CAS 220101.C22010103: Neutron Multiplier (D-T)
- **Issue**: Neutron multipliers (Be/Pb layers) required for D-T tritium breeding (TBR > 1.05-1.2) were not explicitly costed, representing ~5-10% of blanket cost ($50-200M).
- **Fix**: Added C22010103 subcost to CAS220101. Calculates as 7.5% of blanket cost (C22010102) for D-T fuel when `blanket.neutron_multiplier != NONE`. Zero cost for other fuels.
- **Cost Impact**: $50-200M for D-T plants (7.5% of blanket)
- **Files**: `cas220101.py`, `cas220101_reactor_equipment.py`

### New CAS 220500.C220507: Tritium Containment Barriers
- **Issue**: Regulatory tritium containment barriers (permeation prevention, seals, membranes) were not modeled, missing ~$100M-300M in D-T compliance costs.
- **Fix**: Added C220507 subcost to CAS220500. Fuel-dependent calculation:
  - **D-T**: $200M base @ 1 GWe, scaling exponent 0.7 (full containment)
  - **D-D**: $20M base @ 1 GWe, scaling exponent 0.7 (reduced, ~10% of D-T)
  - **Other fuels**: $0 (no tritium handling)
- **Cost Impact**: D-T $200M, D-D $20M
- **Files**: `cas220500.py`, `cas220500_fuel_handling_and_storage.py`

### CAS 220200 Documentation: First Wall Cooling Integration
- **Issue**: First wall cooling integration was not clearly documented. All fuels require first wall cooling (including p-B¹¹ X-ray bremsstrahlung heat), but cost breakdown was unclear.
- **Fix**: Added comprehensive docstring to `CAS2202` dataclass explaining that first wall cooling is integrated into primary coolant loop (C220201) and not separately tracked. Clarifies p-B¹¹ thermal heat deposition.
- **Files**: `cas220200.py`

### Total Cost Impact Summary (1 GWe plant)
| Fuel Type | CAS 220112 | C22010103 | C220507 | **Total Added** | **% Increase CAS22** |
|-----------|------------|-----------|---------|-----------------|----------------------|
| **D-T**   | $400M      | $50-200M  | $200M   | **$650-800M**   | **~10-15%**          |
| **D-D**   | $300M      | $0        | $20M    | **$320M**       | **~5-8%**            |
| **p-B¹¹** | $155M      | $0        | $0      | **$155M**       | **~3-5%**            |
| **D-He³** | $300M+     | $0        | $0      | **$300M+**      | **~5-7%**            |

### LaTeX Templates and Report Integration
- Created `CAS220112.tex` for MFE and IFE with fuel-dependent subsystem documentation
- Created `CAS220112Section` report section class with variable substitutions
- Integrated into report generation pipeline via `utils.py`
- Added `\input{Modified/CAS220112.tex}` to both MFE and IFE document templates (between CAS220111 and CAS220119)
- Replaced plain-text references with proper `\cite{}` commands (CANDU D₂O, COLEX Li-6, laser isotope separation, framework document)
- Added placeholder BibTeX entries to `additions.bib` (MFE + IFE) - **TODO: Replace with actual peer-reviewed sources**
- **Files**: `mfe/templates/CAS220112.tex`, `ife/templates/CAS220112.tex`, `cas220112_section.py`, `utils.py`, `Costing_ARPA-E_MFE_Modified.tex`, `Costing_ARPA-E_IFE_Modified.tex`, `additions.bib` (MFE + IFE)

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
- Added 2026 update blocks for C110000 (fusion project land table, land-intensity formula), C120000 (EA vs EIS), C130000 (fuel-type licensing table), C140000, C150000 (FOAK/NOAK range).
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
