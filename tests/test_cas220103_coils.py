"""Tests for CAS 22.1.3 coil costing — legacy detailed and simplified models."""

import math

import pytest
import scipy.constants as sc

from pyfecons.costing.accounting.power_table import PowerTable
from pyfecons.costing.mfe.cas22.cas220103_coils import (
    cas_220103_coils,
    cas_220103_coils_simplified,
    compute_geometry_factor,
    compute_magnet_properties,
)
from pyfecons.enums import (
    CoilMaterial,
    ConfinementType,
    FusionMachineType,
    MagnetMaterialType,
    MagnetType,
)
from pyfecons.inputs.basic import Basic
from pyfecons.inputs.coils import Coils
from pyfecons.inputs.magnet import Magnet
from pyfecons.inputs.radial_build import RadialBuild
from pyfecons.units import Meters, Meters2, Ratio

# ── Helpers ──────────────────────────────────────────────────────────────


def _make_basic(confinement_type=ConfinementType.SPHERICAL_TOKAMAK):
    b = Basic()
    b.confinement_type = confinement_type
    b.fusion_machine_type = confinement_type.fusion_machine_type
    return b


def _make_coils_simplified(b_max=12.0, r_coil=4.0, **kwargs):
    c = Coils()
    c.b_max = b_max
    c.r_coil = r_coil
    for k, v in kwargs.items():
        setattr(c, k, v)
    return c


def _make_magnet(
    name="TF1",
    mtype=MagnetType.TF,
    material_type=MagnetMaterialType.HTS_CICC,
    coil_count=16,
    r_centre=4.0,
    z_centre=0.0,
    dr=0.4,
    dz=0.6,
    frac_in=0.1,
    coil_temp=20.0,
    mfr_factor=3,
    auto_cicc=True,
    auto_cicc_b=12.0,
    auto_cicc_r=4.0,
):
    return Magnet(
        name=name,
        type=mtype,
        material_type=material_type,
        coil_count=coil_count,
        r_centre=r_centre,
        z_centre=z_centre,
        dr=dr,
        dz=dz,
        frac_in=frac_in,
        coil_temp=coil_temp,
        mfr_factor=mfr_factor,
        auto_cicc=auto_cicc,
        auto_cicc_b=auto_cicc_b,
        auto_cicc_r=auto_cicc_r,
    )


def _make_radial_build():
    return RadialBuild(
        elon=Ratio(3),
        axis_t=Meters(3),
        plasma_t=Meters(1.1),
        vacuum_t=Meters(0.1),
        firstwall_t=Meters(0.2),
        blanket1_t=Meters(0.8),
        reflector_t=Meters(0.2),
        ht_shield_t=Meters(0.2),
        structure_t=Meters(0.2),
        gap1_t=Meters(0.5),
        vessel_t=Meters(0.2),
        coil_t=Meters(0.25),
        gap2_t=Meters(0.5),
        lt_shield_t=Meters(0.3),
        bioshield_t=Meters(1),
    )


# ── Simplified Model Tests ──────────────────────────────────────────────


class TestSimplifiedCoils:
    """Tests for cas_220103_coils_simplified — conductor scaling law model."""

    def test_total_cost_positive(self):
        basic = _make_basic()
        coils = _make_coils_simplified()
        result = cas_220103_coils_simplified(coils, basic)
        assert float(result.C220103) > 0

    def test_cost_scales_with_b_max(self):
        """Higher B field requires more conductor → higher cost."""
        basic = _make_basic()
        r_low = cas_220103_coils_simplified(_make_coils_simplified(b_max=6.0), basic)
        r_high = cas_220103_coils_simplified(_make_coils_simplified(b_max=18.0), basic)
        assert float(r_high.C220103) > float(r_low.C220103)

    def test_cost_scales_with_r_coil_squared(self):
        """Cost scales with R^2 (via kA·m = G * B * R^2 / mu_0 / 1000)."""
        basic = _make_basic()
        r1 = cas_220103_coils_simplified(_make_coils_simplified(r_coil=2.0), basic)
        r2 = cas_220103_coils_simplified(_make_coils_simplified(r_coil=4.0), basic)
        ratio = float(r2.C220103) / float(r1.C220103)
        assert ratio == pytest.approx(4.0, rel=1e-6)

    def test_conductor_cost_before_markup(self):
        """conductor_cost * markup = C220103."""
        basic = _make_basic()
        coils = _make_coils_simplified()
        result = cas_220103_coils_simplified(coils, basic)
        assert float(result.C220103) == pytest.approx(
            float(result.conductor_cost) * result.markup, rel=1e-10
        )

    def test_cost_per_coil(self):
        basic = _make_basic()
        coils = _make_coils_simplified()
        result = cas_220103_coils_simplified(coils, basic)
        expected = float(result.C220103) / result.n_coils
        assert float(result.cost_per_coil) == pytest.approx(expected, rel=1e-10)

    def test_custom_markup_overrides_default(self):
        basic = _make_basic()
        coils = _make_coils_simplified(coil_markup=100.0)
        result = cas_220103_coils_simplified(coils, basic)
        assert result.markup == pytest.approx(100.0)

    def test_custom_n_coils(self):
        basic = _make_basic()
        coils = _make_coils_simplified(n_coils=10)
        result = cas_220103_coils_simplified(coils, basic)
        assert result.n_coils == 10

    def test_custom_cost_per_kAm(self):
        basic = _make_basic()
        c1 = cas_220103_coils_simplified(
            _make_coils_simplified(cost_per_kAm=50.0), basic
        )
        c2 = cas_220103_coils_simplified(
            _make_coils_simplified(cost_per_kAm=100.0), basic
        )
        assert float(c2.C220103) == pytest.approx(2.0 * float(c1.C220103), rel=1e-6)

    def test_default_material_is_rebco(self):
        basic = _make_basic()
        coils = _make_coils_simplified()
        result = cas_220103_coils_simplified(coils, basic)
        assert result.coil_material == CoilMaterial.REBCO_HTS


# ── Geometry Factor Tests ────────────────────────────────────────────────


class TestGeometryFactor:
    """Tests for compute_geometry_factor — topology-dependent scaling."""

    def test_tokamak_geometry(self):
        G = compute_geometry_factor(ConfinementType.SPHERICAL_TOKAMAK, 20, 1.0)
        assert G == pytest.approx(4 * math.pi**2, rel=1e-10)

    def test_conventional_tokamak_same_as_spherical(self):
        G_st = compute_geometry_factor(ConfinementType.SPHERICAL_TOKAMAK, 20, 1.0)
        G_ct = compute_geometry_factor(ConfinementType.CONVENTIONAL_TOKAMAK, 26, 1.0)
        assert G_st == pytest.approx(G_ct)

    def test_mirror_depends_on_n_coils(self):
        G4 = compute_geometry_factor(ConfinementType.MAGNETIC_MIRROR, 4, 1.0)
        G8 = compute_geometry_factor(ConfinementType.MAGNETIC_MIRROR, 8, 1.0)
        assert G8 == pytest.approx(2.0 * G4)

    def test_mirror_formula(self):
        n = 4
        G = compute_geometry_factor(ConfinementType.MAGNETIC_MIRROR, n, 1.0)
        assert G == pytest.approx(n * 4 * math.pi)

    def test_stellarator_uses_path_factor(self):
        G1 = compute_geometry_factor(ConfinementType.STELLARATOR, 50, 1.0)
        G2 = compute_geometry_factor(ConfinementType.STELLARATOR, 50, 2.0)
        assert G2 == pytest.approx(2.0 * G1)

    def test_stellarator_formula(self):
        pf = 2.0
        G = compute_geometry_factor(ConfinementType.STELLARATOR, 50, pf)
        assert G == pytest.approx(4 * math.pi**2 * pf)


# ── Confinement Defaults Tests ───────────────────────────────────────────


class TestConfinementDefaults:
    """Simplified model uses correct defaults per confinement type."""

    def test_mirror_defaults(self):
        basic = _make_basic(ConfinementType.MAGNETIC_MIRROR)
        coils = _make_coils_simplified()
        result = cas_220103_coils_simplified(coils, basic)
        assert result.n_coils == 4
        assert result.markup == pytest.approx(2.5)

    def test_spherical_tokamak_defaults(self):
        basic = _make_basic(ConfinementType.SPHERICAL_TOKAMAK)
        coils = _make_coils_simplified()
        result = cas_220103_coils_simplified(coils, basic)
        assert result.n_coils == 20
        assert result.markup == pytest.approx(6)

    def test_conventional_tokamak_defaults(self):
        basic = _make_basic(ConfinementType.CONVENTIONAL_TOKAMAK)
        coils = _make_coils_simplified()
        result = cas_220103_coils_simplified(coils, basic)
        assert result.n_coils == 26
        assert result.markup == pytest.approx(8)

    def test_stellarator_defaults(self):
        basic = _make_basic(ConfinementType.STELLARATOR)
        coils = _make_coils_simplified()
        result = cas_220103_coils_simplified(coils, basic)
        assert result.n_coils == 50
        assert result.markup == pytest.approx(12)

    def test_stellarator_more_expensive_than_tokamak(self):
        """Stellarators should be more expensive due to higher markup and path_factor."""
        coils = _make_coils_simplified()
        r_tok = cas_220103_coils_simplified(
            coils, _make_basic(ConfinementType.SPHERICAL_TOKAMAK)
        )
        r_stel = cas_220103_coils_simplified(
            coils, _make_basic(ConfinementType.STELLARATOR)
        )
        assert float(r_stel.C220103) > float(r_tok.C220103)


# ── Legacy Detailed Model Tests ──────────────────────────────────────────


class TestLegacyDetailedCoils:
    """Tests for cas_220103_coils — detailed per-magnet costing."""

    def _run_legacy(self, magnets, p_net=1000.0, p_neutron=400.0):
        coils = Coils()
        coils.magnets = magnets
        rb = _make_radial_build()
        pt = PowerTable(p_net=p_net, p_neutron=p_neutron)
        return cas_220103_coils(coils, rb, pt)

    def test_shim_coil_is_5_percent(self):
        """Shim coils (C22010304) should be 5% of TF + CS + PF total."""
        mag_tf = _make_magnet(name="TF", mtype=MagnetType.TF, coil_count=16)
        mag_pf = _make_magnet(
            name="PF", mtype=MagnetType.PF, coil_count=6, r_centre=6.0
        )
        result = self._run_legacy([mag_tf, mag_pf])
        primary_total = (
            float(result.C22010301) + float(result.C22010302) + float(result.C22010303)
        )
        assert float(result.C22010304) == pytest.approx(0.05 * primary_total, rel=1e-10)

    def test_total_is_sum_of_all_subcategories(self):
        mag = _make_magnet(name="TF", mtype=MagnetType.TF, coil_count=8)
        result = self._run_legacy([mag])
        total = (
            float(result.C22010301)
            + float(result.C22010302)
            + float(result.C22010303)
            + float(result.C22010304)
            + float(result.C22010305)
            + float(result.C22010306)
        )
        assert float(result.C220103) == pytest.approx(total, rel=1e-10)

    def test_tf_only_coils_sorted_correctly(self):
        """A single TF magnet should show up in C22010301, not CS or PF."""
        mag = _make_magnet(name="TF", mtype=MagnetType.TF, coil_count=8)
        result = self._run_legacy([mag])
        assert float(result.C22010301) > 0
        assert float(result.C22010302) == pytest.approx(0.0, abs=1e-10)
        assert float(result.C22010303) == pytest.approx(0.0, abs=1e-10)

    def test_more_coils_higher_cost(self):
        """More coils should yield higher TF cost."""
        mag8 = _make_magnet(name="TF", mtype=MagnetType.TF, coil_count=8)
        mag16 = _make_magnet(name="TF", mtype=MagnetType.TF, coil_count=16)
        r8 = self._run_legacy([mag8])
        r16 = self._run_legacy([mag16])
        assert float(r16.C22010301) > float(r8.C22010301)

    def test_pf_coil_count(self):
        mag_pf = _make_magnet(
            name="PF", mtype=MagnetType.PF, coil_count=6, r_centre=6.0
        )
        result = self._run_legacy([mag_pf])
        assert float(result.no_pf_coils) == 6
        assert float(result.no_pf_pairs) == 3
