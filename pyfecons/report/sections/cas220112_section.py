from dataclasses import dataclass

from pyfecons.costing.categories.cas220112 import CAS220112
from pyfecons.inputs.basic import Basic
from pyfecons.report.section import ReportSection


@dataclass
class CAS220112Section(ReportSection):
    def __init__(self, cas220112: CAS220112, basic: Basic):
        super().__init__()
        self.template_file = "CAS220112.tex"
        self.replacements = {
            "C220112": str(round(cas220112.C220112, 2)),
            "C22011201": str(round(cas220112.C22011201, 2)),
            "C22011202": str(round(cas220112.C22011202, 2)),
            "C22011203": str(round(cas220112.C22011203, 2)),
            "C22011204": str(round(cas220112.C22011204, 2)),
            "C22011205": str(round(cas220112.C22011205, 2)),
            "fuelType": basic.fuel_type.display_name,
        }
