from pyfecons.costing.accounting.power_table import PowerTable
from pyfecons.costing.categories.cas220112 import CAS220112
from pyfecons.enums import FuelType
from pyfecons.inputs.basic import Basic
from pyfecons.units import M_USD


def cas_220112_isotope_separation_costs(
    basic: Basic, power_table: PowerTable
) -> CAS220112:
    """Calculate isotope separation plant costs (fuel-dependent)

    All fusion fuels require isotope separation infrastructure for fuel preparation.
    Costs are highly fuel-dependent based on required throughput and separation difficulty.

    Based on:
    - Fuel type (D-T, D-D, D-He³, p-B¹¹)
    - Plant capacity (GWe output)
    - Annual fuel throughput requirements

    Cost data from:
    - CANDU heavy water plants (D₂O extraction: $100M-500M)
    - Li-6 COLEX facilities (enrichment: $50M-150M)
    - B-11 laser separation (enrichment: $50M-200M)
    - H-1 purification systems (protium extraction: $10M-50M)

    Reference: Comprehensive Fusion Reactor Subsystems Framework (2026-02-08)
    """
    cas220112 = CAS220112()

    # D₂O extraction (D-T, D-D, D-He³)
    if basic.fuel_type in [FuelType.DT, FuelType.DD, FuelType.DHE3]:
        # Deuterium extraction plant (Girdler-Sulfide or distillation)
        # Scale: ~200-1000 kg D₂/GWe-yr depending on fuel
        # Natural abundance: ~0.015% D in seawater
        # Base cost: $300M for 1 GWe plant (mid-range estimate)
        # Scaling: Power law with exponent 0.6 (economies of scale)
        electric_gwe = power_table.p_net / 1000  # Convert MW to GWe
        throughput_scaling = (electric_gwe / 1.0) ** 0.6
        cas220112.C22011201 = M_USD(300.0 * throughput_scaling)
    else:
        cas220112.C22011201 = M_USD(0.0)

    # Li-6 enrichment (D-T only)
    if basic.fuel_type == FuelType.DT:
        # COLEX enrichment plant (Mercury amalgam process)
        # Scale: ~50-100 kg Li-6/GWe-yr for blanket inventory + makeup
        # Natural abundance: ~7.5% Li-6 in natural lithium
        # Target enrichment: 30-95% Li-6 for tritium breeding
        # Base cost: $100M for 1 GWe plant (mid-range estimate)
        # Note: Limited global capacity (~1-2 tonnes/yr) may add premium
        electric_gwe = power_table.p_net / 1000  # Convert MW to GWe
        throughput_scaling = (electric_gwe / 1.0) ** 0.6
        cas220112.C22011202 = M_USD(100.0 * throughput_scaling)
    else:
        cas220112.C22011202 = M_USD(0.0)

    # H-1 purification (p-B¹¹ only)
    if basic.fuel_type == FuelType.PB11:
        # Protium purification (remove trace D from natural H)
        # Scale: ~200 kg H/GWe-yr
        # Natural abundance: 99.985% H-1 in natural hydrogen
        # Process: Cryogenic distillation or chemical exchange
        # Base cost: $30M for 1 GWe plant (smaller than D₂O extraction)
        electric_gwe = power_table.p_net / 1000  # Convert MW to GWe
        throughput_scaling = (electric_gwe / 1.0) ** 0.6
        cas220112.C22011203 = M_USD(30.0 * throughput_scaling)
    else:
        cas220112.C22011203 = M_USD(0.0)

    # B-11 enrichment (p-B¹¹ only)
    if basic.fuel_type == FuelType.PB11:
        # Laser or chemical isotope separation
        # Scale: ~500-1000 kg B-11/GWe-yr
        # Natural abundance: ~80% B-11 in natural boron
        # Target enrichment: >99% B-11 to minimize neutron production from B-10(n,α)
        # Process: Laser isotope separation or chemical exchange
        # Base cost: $125M for 1 GWe plant (mid-range estimate)
        electric_gwe = power_table.p_net / 1000  # Convert MW to GWe
        throughput_scaling = (electric_gwe / 1.0) ** 0.6
        cas220112.C22011204 = M_USD(125.0 * throughput_scaling)
    else:
        cas220112.C22011204 = M_USD(0.0)

    # He-3 extraction (D-He³ only, future)
    if basic.fuel_type == FuelType.DHE3:
        # Placeholder: Lunar mining or T-decay infrastructure
        # Terrestrial He-3 production: ~15 kg/yr from T-decay (β⁻ decay, 12.3 yr half-life)
        # Required: ~50-100 kg/GWe-yr (terrestrial production << demand)
        # Status: NOT VIABLE without lunar mining technology
        # For now, set to zero pending lunar mining infrastructure
        cas220112.C22011205 = M_USD(0.0)
        # TODO: Add lunar extraction plant costs when technology matures
        # Estimated cost: $500M-2000M for lunar mining + Earth transport infrastructure
    else:
        cas220112.C22011205 = M_USD(0.0)

    # Total isotope separation costs
    cas220112.C220112 = M_USD(
        cas220112.C22011201  # D₂O extraction
        + cas220112.C22011202  # Li-6 enrichment
        + cas220112.C22011203  # H-1 purification
        + cas220112.C22011204  # B-11 enrichment
        + cas220112.C22011205  # He-3 extraction
    )

    return cas220112
