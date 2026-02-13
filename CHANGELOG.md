# Changelog: PyFECONS Fork

**Fork**: [Tal-Rubin/PyFECONS](https://github.com/Tal-Rubin/PyFECONS)
**Upstream**: [Woodruff-Scientific-Ltd/PyFECONS](https://github.com/Woodruff-Scientific-Ltd/PyFECONS)

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
