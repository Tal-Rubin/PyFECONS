from dataclasses import dataclass

from pyfecons.units import M_USD


@dataclass
class CAS220104SupplementaryHeating:
    # 22.1.4 Supplementary heating
    C22010401: M_USD = None  # NBI
    C22010402: M_USD = None  # ICRF
    C22010403: M_USD = None  # ECRH
    C22010404: M_USD = None  # LHCD
    C220104: M_USD = None
