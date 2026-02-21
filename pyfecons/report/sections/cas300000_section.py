from dataclasses import dataclass

from pyfecons.costing.categories.cas300000 import CAS30
from pyfecons.inputs.basic import Basic
from pyfecons.report.section import ReportSection


@dataclass
class CAS30Section(ReportSection):
    def __init__(self, cas30: CAS30, basic: Basic):
        super().__init__()
        self.template_file = "CAS300000.tex"
        self.replacements = {
            "constructionTime": str(round(basic.construction_time)),
            "C300000": str(round(cas30.C300000)),
        }
