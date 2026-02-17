from dataclasses import dataclass

from pyfecons.units import Ratio


@dataclass
class Shield:
    # fractions
    f_SiC: Ratio = None
    FPCPPFbLi: Ratio = None
    f_W: Ratio = None
    f_BFS: Ratio = None

    # IFE high-temperature shield cost multiplier relative to MFE (default 5.0).
    # Inherited from the original PyFECONS codebase; no published source identified.
    # Applied to HTS material cost (C22010201) for IFE machine types only.
    ife_shield_scaling: float = 5.0
