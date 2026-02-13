from dataclasses import dataclass

from pyfecons.units import KG_M3, USD_KG, USD_M3, Megapascal


@dataclass
class Material:
    name: str = None
    rho: KG_M3 = None  # Density
    c: USD_M3 = None  # Cost per unit volume
    c_raw: USD_KG = None  # Cost per unit mass
    m: float = None  # Mass factor or multiplier (unitless) - TODO clarify this unit
    sigma: Megapascal = None


class Materials:
    def __init__(self):
        self.FS = Material(name="Ferritic Steel", rho=7470, c_raw=10, m=3, sigma=450)
        self.Pb = Material(name="Lead", rho=9400, c_raw=2.4, m=1.5)
        self.Li4SiO4 = Material(name="Lithium Silicate", rho=2390, c_raw=1, m=2)
        # FLiBe (2LiF-BeF₂): Molten salt coolant/breeder for fusion blankets
        # Cost dominated by Li-7 enrichment (99.99% Li-7 needed)
        # Density at ~700°C operating temperature
        self.FliBe = Material(
            name="Lithium Fluoride (LiF) and Beryllium Fluoride (BeF2) Mixture",
            rho=1940,
            c=40,
            c_raw=40,
            m=1.2,
        )
        self.W = Material(name="Tungsten", rho=19300, c_raw=100, m=3)
        self.Li = Material(name="Lithium", rho=534, c_raw=70, m=1.5)
        self.BFS = Material(name="BFS", rho=7800, c_raw=30, m=2)
        self.SiC = Material(name="Silicon Carbide", rho=3200, c_raw=14.49, m=3)
        self.Inconel = Material(name="Inconel", rho=8440, c_raw=46, m=3)
        self.Cu = Material(name="Copper", rho=7300, c_raw=10.2, m=3)
        self.Polyimide = Material(name="Polyimide", rho=1430, c_raw=100, m=3)
        self.YBCO = Material(
            name="Yttrium Barium Copper Oxide (YBa2Cu3O7)", rho=6200, c=55
        )
        self.Concrete = Material(name="Concrete", rho=2300, c_raw=13 / 25, m=2)
        self.SS316 = Material(
            name="Stainless Steel 316", rho=7860, c_raw=2, m=2, sigma=900
        )
        self.Nb3Sn = Material(name="Niobium-Tin (Nb3Sn)", c=5)
        self.Incoloy = Material(name="Incoloy", rho=8170, c_raw=4, m=2)
        # GdBCO: REBCO HTS tape, same material class as YBCO
        # Actual magnet costing uses m_cost_ybco ($/kAm) in Coils input, not Material.c
        # Tape pricing: current $150-300/kAm, target $50/kAm, long-term $10-20/kAm
        self.GdBCO = Material(
            name="Gadolinium Barium Copper Oxide (GdBa2Cu3O7)",
            rho=6350,
            c=55,
        )
        # He: Gas coolant for fusion blankets/first walls
        # Density at 8 MPa, 400°C from NIST — varies with T,P
        self.He = Material(
            name="Helium",
            rho=5.64,
            c_raw=24,
            m=1,
        )
        # NbTi: LTS superconductor, ITER PF coils
        # Wire cost ~$1/kAm at 4.2K — 50x cheaper than current REBCO tape
        # Uses CICC cable architecture (not tape) — different conductor model
        self.NbTi = Material(
            name="Niobium-Titanium (NbTi)",
            rho=6170,
            c=4,
        )

        # Beryllium: High-purity metal for first wall applications
        # Price: $800-1200/kg for high-purity ingots (2024-2025 market)
        # Sources:
        #   - Shanghai Metal Market: $1031-1035/kg (2025)
        #   - Accio market data: $600-1200/kg range
        #   - USGS Mineral Commodity Summaries 2024
        # Previous value ($5750/kg) was ~5-10x too high, likely confused with
        # aerospace-grade machined components or included excessive markup.
        # Note: ITER switched from Be to W first wall in 2023 due to melting concerns.
        self.Be = Material(name="Beryllium", rho=1850, c_raw=900, m=3)

        # Lithium Titanate (Li2TiO3): Solid tritium breeder ceramic
        # Price: $100-200/kg for ceramic-grade material
        # Sources:
        #   - MDPI review (2022): characterized as "low production cost"
        #   - Comparable to other technical ceramics ($50-200/kg range)
        #   - ResearchGate: "low-cost synthesis" methods actively researched
        # Previous value ($1297/kg) was undocumented and ~6-10x too high.
        # Li4SiO4 (alternate breeder) at $1/kg provides reasonable comparison.
        self.Li2TiO3 = Material(name="Lithium Titanate", rho=3430, c_raw=150, m=3)

        # Values to be calculated
        pblir = 10
        pbli_rho = (self.Pb.rho * pblir + self.Li.rho) / (pblir + 1)
        pbli_c = (self.Pb.c_raw * self.Pb.m * pblir + self.Li.c_raw * self.Li.m) / (
            pblir + 1
        )
        self.PbLi = Material(
            name="Lead (Pb) and Lithium (Li) Eutectic Alloy", rho=pbli_rho, c=pbli_c
        )
