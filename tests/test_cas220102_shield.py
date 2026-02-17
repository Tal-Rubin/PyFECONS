"""Tests for CAS 220102: Shield costs."""

import pytest

from pyfecons.costing.calculations.cas22.cas220102_shield import cas_220102_shield_costs
from pyfecons.costing.categories.cas220101 import CAS220101
from pyfecons.enums import FusionMachineType
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.blanket import Blanket
from pyfecons.inputs.shield import Shield


def _make_basic(machine_type=FusionMachineType.MFE):
    b = Basic()
    b.fusion_machine_type = machine_type
    return b


def _make_shield(f_SiC=0.3, f_W=0.2, f_BFS=0.3, FPCPPFbLi=0.2):
    return Shield(f_SiC=f_SiC, FPCPPFbLi=FPCPPFbLi, f_W=f_W, f_BFS=f_BFS)


def _make_cas220101(ht_shield_vol=100.0, lt_shield_vol=200.0, bioshield_vol=500.0):
    out = CAS220101()
    out.ht_shield_vol = ht_shield_vol
    out.lt_shield_vol = lt_shield_vol
    out.bioshield_vol = bioshield_vol
    return out


class TestShieldCostsMFE:
    """MFE shield cost calculations (no IFE scaling)."""

    def test_total_is_sum_of_components(self):
        result = cas_220102_shield_costs(
            _make_basic(), _make_shield(), Blanket(), _make_cas220101()
        )
        expected = (
            result.C22010201 + result.C22010202 + result.C22010203 + result.C22010204
        )
        assert float(result.C220102) == pytest.approx(float(expected), rel=1e-10)

    def test_misc_is_10pct_of_bioshield(self):
        result = cas_220102_shield_costs(
            _make_basic(), _make_shield(), Blanket(), _make_cas220101()
        )
        assert float(result.C22010204) == pytest.approx(
            float(result.C22010203) * 0.1, rel=1e-10
        )

    def test_hts_volume_stored(self):
        result = cas_220102_shield_costs(
            _make_basic(),
            _make_shield(),
            Blanket(),
            _make_cas220101(ht_shield_vol=42.0),
        )
        assert result.V_HTS == pytest.approx(42.0, rel=1e-10)

    def test_zero_volumes_give_zero_cost(self):
        result = cas_220102_shield_costs(
            _make_basic(),
            _make_shield(),
            Blanket(),
            _make_cas220101(ht_shield_vol=0, lt_shield_vol=0, bioshield_vol=0),
        )
        assert float(result.C220102) == pytest.approx(0.0, abs=1e-10)

    def test_mfe_no_ife_scaling(self):
        """MFE should apply scaling factor of 1.0 (no change)."""
        shield = _make_shield()
        shield.ife_shield_scaling = 99.0  # should be ignored for MFE
        result = cas_220102_shield_costs(
            _make_basic(FusionMachineType.MFE), shield, Blanket(), _make_cas220101()
        )
        # Compare with default shield (ife_shield_scaling doesn't matter for MFE)
        result_default = cas_220102_shield_costs(
            _make_basic(FusionMachineType.MFE),
            _make_shield(),
            Blanket(),
            _make_cas220101(),
        )
        assert float(result.C22010201) == pytest.approx(
            float(result_default.C22010201), rel=1e-10
        )

    def test_cost_scales_with_volume(self):
        r1 = cas_220102_shield_costs(
            _make_basic(), _make_shield(), Blanket(), _make_cas220101(ht_shield_vol=100)
        )
        r2 = cas_220102_shield_costs(
            _make_basic(), _make_shield(), Blanket(), _make_cas220101(ht_shield_vol=200)
        )
        # HTS cost should roughly double (rounding may introduce small error)
        assert float(r2.C22010201) == pytest.approx(
            float(r1.C22010201) * 2, abs=0.2  # rounding tolerance
        )


class TestShieldCostsIFE:
    """IFE shield cost calculations (with configurable scaling)."""

    def test_ife_applies_default_scaling(self):
        """IFE should apply default 5.0x scaling to HTS cost."""
        mfe = cas_220102_shield_costs(
            _make_basic(FusionMachineType.MFE),
            _make_shield(),
            Blanket(),
            _make_cas220101(),
        )
        ife = cas_220102_shield_costs(
            _make_basic(FusionMachineType.IFE),
            _make_shield(),
            Blanket(),
            _make_cas220101(),
        )
        assert float(ife.C22010201) == pytest.approx(
            float(mfe.C22010201) * 5.0, abs=0.2
        )

    def test_ife_custom_scaling(self):
        """Custom ife_shield_scaling should override the default."""
        shield = _make_shield()
        shield.ife_shield_scaling = 3.0
        result = cas_220102_shield_costs(
            _make_basic(FusionMachineType.IFE), shield, Blanket(), _make_cas220101()
        )
        mfe = cas_220102_shield_costs(
            _make_basic(FusionMachineType.MFE),
            _make_shield(),
            Blanket(),
            _make_cas220101(),
        )
        assert float(result.C22010201) == pytest.approx(
            float(mfe.C22010201) * 3.0, abs=0.2
        )

    def test_ife_scaling_only_affects_hts(self):
        """IFE scaling should only affect C22010201 (HTS), not LTS or bioshield."""
        mfe = cas_220102_shield_costs(
            _make_basic(FusionMachineType.MFE),
            _make_shield(),
            Blanket(),
            _make_cas220101(),
        )
        ife = cas_220102_shield_costs(
            _make_basic(FusionMachineType.IFE),
            _make_shield(),
            Blanket(),
            _make_cas220101(),
        )
        assert float(ife.C22010202) == pytest.approx(float(mfe.C22010202), rel=1e-10)
        assert float(ife.C22010203) == pytest.approx(float(mfe.C22010203), rel=1e-10)


class TestShieldMaterialFractions:
    """Tests for material fraction sensitivity."""

    def test_all_sic_vs_all_w(self):
        """Tungsten-heavy shield should cost more than SiC-heavy shield."""
        sic_shield = _make_shield(f_SiC=0.8, f_W=0.0, f_BFS=0.1, FPCPPFbLi=0.1)
        w_shield = _make_shield(f_SiC=0.0, f_W=0.8, f_BFS=0.1, FPCPPFbLi=0.1)
        r_sic = cas_220102_shield_costs(
            _make_basic(), sic_shield, Blanket(), _make_cas220101()
        )
        r_w = cas_220102_shield_costs(
            _make_basic(), w_shield, Blanket(), _make_cas220101()
        )
        # W: rho=19300, c_raw=100, m=3 vs SiC: rho=3200, c_raw=14.49, m=3
        assert float(r_w.C22010201) > float(r_sic.C22010201)

    def test_zero_fractions_give_zero_hts(self):
        zero_shield = _make_shield(f_SiC=0, f_W=0, f_BFS=0, FPCPPFbLi=0)
        result = cas_220102_shield_costs(
            _make_basic(), zero_shield, Blanket(), _make_cas220101()
        )
        assert float(result.C22010201) == pytest.approx(0.0, abs=1e-10)
