from dataclasses import dataclass

from pyfecons.costing.categories.cas600000 import CAS60
from pyfecons.report.section import ReportSection


@dataclass
class CAS60Section(ReportSection):
    def __init__(self, cas60: CAS60):
        super().__init__()
        self.template_file = "CAS600000.tex"
        self.replacements = {
            "C600000": str(round(cas60.C600000)),
        }
