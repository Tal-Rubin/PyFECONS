from pyfecons.costing.categories.cas100000 import CAS10
from pyfecons.inputs.basic import Basic
from pyfecons.report import ReportSection


class CAS10Section(ReportSection):
    def __init__(self, cas10: CAS10, basic: Basic):
        super().__init__()
        self.template_file = "CAS100000.tex"
        self.replacements = {
            "Nmod": str(basic.n_mod),
            "C100000": str(round(cas10.C100000, 2)),
            "C110100": str(round(cas10.C110100, 2)),
            "C110200": str(round(cas10.C110200, 2)),
            "C110000": str(round(cas10.C110000, 2)),
            "C120000": str(round(cas10.C120000, 2)),
            "C130000": str(round(cas10.C130000, 2)),
            "C140000": str(round(cas10.C140000, 2)),
            "C150000": str(round(cas10.C150000, 2)),
            "C160000": str(round(cas10.C160000, 2)),
            "C170000": str(round(cas10.C170000, 2)),
            "C190000": str(round(cas10.C190000, 2)),
        }
