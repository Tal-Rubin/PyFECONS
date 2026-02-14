"""
Input validation for PyFECONS costing engine.

Layered validation:
  1. Required fields: ensure non-None for the given machine type
  2. Field-level: range checks per individual field
  3. Cross-field: physics consistency across multiple fields/dataclasses

Usage:
    from pyfecons.validation import validate_inputs
    validate_inputs(inputs)  # raises ValidationError or emits warnings
"""

import warnings

from pyfecons.enums import CoilMaterial, FuelType, FusionMachineType
from pyfecons.exceptions import FieldError, ValidationError, ValidationWarning
from pyfecons.inputs.all_inputs import AllInputs


class ValidationResult:
    """Accumulates errors and warnings during validation."""

    def __init__(self):
        self.errors: list[FieldError] = []
        self.warnings: list[ValidationWarning] = []

    def error(self, dc_name, field, value, constraint):
        self.errors.append(FieldError(dc_name, field, value, constraint))

    def warn(self, dc_name, field, value, message):
        self.warnings.append(ValidationWarning(dc_name, field, value, message))

    def raise_if_errors(self):
        if self.errors:
            raise ValidationError(self.errors)
        # Only emit warnings when there are no hard errors -- warnings are
        # noise when the user already has errors to fix first.
        for w in self.warnings:
            warnings.warn(str(w), stacklevel=3)


# ---------------------------------------------------------------------------
# Required top-level dataclasses per machine type
# ---------------------------------------------------------------------------

# Both MFE and IFE share these
_COMMON_REQUIRED = [
    "basic",
    "power_input",
    "radial_build",
    "shield",
    "blanket",
    "primary_structure",
    "vacuum_system",
    "power_supplies",
    "installation",
    "fuel_handling",
    "lsa_levels",
    "financial",
]

_MFE_REQUIRED = _COMMON_REQUIRED + ["coils"]
_IFE_REQUIRED = _COMMON_REQUIRED + ["lasers", "target_factory"]

# ---------------------------------------------------------------------------
# Required non-None fields within each dataclass, per machine type
# ---------------------------------------------------------------------------

_COMMON_BASIC_FIELDS = [
    "fusion_machine_type",
    "confinement_type",
    "energy_conversion",
    "fuel_type",
    "p_nrl",
    "n_mod",
    "construction_time",
    "plant_lifetime",
    "plant_availability",
    "yearly_inflation",
    "time_to_replace",
]

_COMMON_POWER_INPUT_FIELDS = [
    "f_sub",
    "mn",
    "eta_p",
    "eta_th",
    "p_trit",
    "p_house",
    "p_input",
    "p_cryo",
    "p_pump",
]

_COMMON_RADIAL_BUILD_FIELDS = [
    "axis_t",
    "plasma_t",
    "vacuum_t",
    "firstwall_t",
    "blanket1_t",
    "reflector_t",
    "ht_shield_t",
    "structure_t",
    "gap1_t",
    "vessel_t",
    "gap2_t",
    "lt_shield_t",
    "bioshield_t",
]

_COMMON_OTHER_FIELDS = {
    "shield": ["f_SiC", "FPCPPFbLi", "f_W", "f_BFS"],
    "blanket": [
        "first_wall",
        "blanket_type",
        "primary_coolant",
        "secondary_coolant",
        "neutron_multiplier",
        "structure",
    ],
    "financial": ["interest_rate", "construction_years", "plant_lifetime_years"],
}

_MFE_REQUIRED_FIELDS = {
    "basic": _COMMON_BASIC_FIELDS,
    "power_input": _COMMON_POWER_INPUT_FIELDS + ["eta_pin"],
    "radial_build": _COMMON_RADIAL_BUILD_FIELDS + ["elon", "coil_t"],
    **_COMMON_OTHER_FIELDS,
}

_IFE_REQUIRED_FIELDS = {
    "basic": _COMMON_BASIC_FIELDS + ["implosion_frequency"],
    "power_input": _COMMON_POWER_INPUT_FIELDS
    + ["eta_pin1", "eta_pin2", "p_implosion", "p_ignition", "p_target"],
    "radial_build": _COMMON_RADIAL_BUILD_FIELDS,
    **_COMMON_OTHER_FIELDS,
}

_COMMON_REQUIRED_FIELDS = {
    "basic": _COMMON_BASIC_FIELDS,
    "power_input": _COMMON_POWER_INPUT_FIELDS,
    "radial_build": _COMMON_RADIAL_BUILD_FIELDS,
    **_COMMON_OTHER_FIELDS,
}

# ---------------------------------------------------------------------------
# Field-level range rules (data-driven table)
# (dataclass_attr, field_name, check_fn, constraint_description, is_error)
# ---------------------------------------------------------------------------

FIELD_RULES = [
    # --- Basic ---
    ("basic", "p_nrl", lambda v: v > 0, "> 0 (MW)", True),
    ("basic", "n_mod", lambda v: v >= 1, ">= 1", True),
    ("basic", "plant_availability", lambda v: 0 <= v <= 1, "in [0, 1]", True),
    ("basic", "plant_lifetime", lambda v: v > 0, "> 0 (years)", True),
    ("basic", "construction_time", lambda v: v > 0, "> 0 (years)", True),
    ("basic", "downtime", lambda v: v >= 0, ">= 0 (years)", True),
    ("basic", "yearly_inflation", lambda v: v >= 0, ">= 0", True),
    ("basic", "time_to_replace", lambda v: v > 0, "> 0 (years)", True),
    # --- PowerInput: efficiencies ---
    ("power_input", "f_sub", lambda v: 0 <= v <= 1, "in [0, 1]", True),
    ("power_input", "eta_p", lambda v: 0 < v <= 1, "in (0, 1]", True),
    ("power_input", "eta_th", lambda v: 0 < v <= 1, "in (0, 1]", True),
    ("power_input", "eta_pin", lambda v: 0 < v <= 1, "in (0, 1]", True),
    ("power_input", "eta_pin1", lambda v: 0 < v <= 1, "in (0, 1]", True),
    ("power_input", "eta_pin2", lambda v: 0 < v <= 1, "in (0, 1]", True),
    ("power_input", "eta_de", lambda v: 0 < v <= 1, "in (0, 1]", True),
    ("power_input", "mn", lambda v: v >= 1.0, ">= 1.0", True),
    # --- PowerInput: powers (non-negative) ---
    ("power_input", "p_cryo", lambda v: v >= 0, ">= 0 (MW)", True),
    ("power_input", "p_trit", lambda v: v >= 0, ">= 0 (MW)", True),
    ("power_input", "p_house", lambda v: v >= 0, ">= 0 (MW)", True),
    ("power_input", "p_cool", lambda v: v >= 0, ">= 0 (MW)", True),
    ("power_input", "p_coils", lambda v: v >= 0, ">= 0 (MW)", True),
    ("power_input", "p_input", lambda v: v > 0, "> 0 (MW)", True),
    ("power_input", "p_pump", lambda v: v >= 0, ">= 0 (MW)", True),
    ("power_input", "p_implosion", lambda v: v >= 0, ">= 0 (MW)", True),
    ("power_input", "p_ignition", lambda v: v >= 0, ">= 0 (MW)", True),
    ("power_input", "p_target", lambda v: v >= 0, ">= 0 (MW)", True),
    ("power_input", "f_dec", lambda v: 0 <= v <= 1, "in [0, 1]", True),
    # --- PowerInput: burn fractions (only checked if not None) ---
    ("power_input", "dd_f_T", lambda v: 0 <= v <= 1, "in [0, 1]", True),
    ("power_input", "dd_f_He3", lambda v: 0 <= v <= 1, "in [0, 1]", True),
    ("power_input", "dhe3_dd_frac", lambda v: 0 <= v <= 1, "in [0, 1]", True),
    ("power_input", "dhe3_f_T", lambda v: 0 <= v <= 1, "in [0, 1]", True),
    # --- RadialBuild ---
    ("radial_build", "elon", lambda v: v > 0, "> 0", True),
    ("radial_build", "axis_t", lambda v: v >= 0, ">= 0 (m)", True),
    ("radial_build", "plasma_t", lambda v: v > 0, "> 0 (m)", True),
    ("radial_build", "vacuum_t", lambda v: v >= 0, ">= 0 (m)", True),
    ("radial_build", "firstwall_t", lambda v: v >= 0, ">= 0 (m)", True),
    ("radial_build", "blanket1_t", lambda v: v >= 0, ">= 0 (m)", True),
    ("radial_build", "reflector_t", lambda v: v >= 0, ">= 0 (m)", True),
    ("radial_build", "ht_shield_t", lambda v: v >= 0, ">= 0 (m)", True),
    ("radial_build", "structure_t", lambda v: v >= 0, ">= 0 (m)", True),
    ("radial_build", "gap1_t", lambda v: v >= 0, ">= 0 (m)", True),
    ("radial_build", "vessel_t", lambda v: v >= 0, ">= 0 (m)", True),
    ("radial_build", "coil_t", lambda v: v >= 0, ">= 0 (m)", True),
    ("radial_build", "gap2_t", lambda v: v >= 0, ">= 0 (m)", True),
    ("radial_build", "lt_shield_t", lambda v: v >= 0, ">= 0 (m)", True),
    ("radial_build", "bioshield_t", lambda v: v >= 0, ">= 0 (m)", True),
    # --- Financial ---
    ("financial", "interest_rate", lambda v: v >= 0, ">= 0", True),
    ("financial", "construction_years", lambda v: v > 0, "> 0 (years)", True),
    ("financial", "plant_lifetime_years", lambda v: v > 0, "> 0 (years)", True),
    # --- Shield fractions ---
    ("shield", "f_SiC", lambda v: 0 <= v <= 1, "in [0, 1]", True),
    ("shield", "FPCPPFbLi", lambda v: 0 <= v <= 1, "in [0, 1]", True),
    ("shield", "f_W", lambda v: 0 <= v <= 1, "in [0, 1]", True),
    ("shield", "f_BFS", lambda v: 0 <= v <= 1, "in [0, 1]", True),
    # --- Warnings (unusual but possible) ---
    (
        "power_input",
        "eta_th",
        lambda v: v <= 0.65,
        "unusually high thermal efficiency (> 0.65)",
        False,
    ),
]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def validate_inputs(inputs: AllInputs) -> None:
    """
    Validate all inputs before costing calculations.

    Raises ValidationError if any hard errors found.
    Emits warnings.warn() for soft concerns.
    """
    result = ValidationResult()

    machine_type = _get_machine_type(inputs, result)
    if machine_type is None:
        result.raise_if_errors()
        return

    _validate_required_dataclasses(inputs, machine_type, result)
    _validate_required_fields(inputs, machine_type, result)
    _validate_field_rules(inputs, result)
    _validate_magnets(inputs, result)
    _validate_simplified_coils(inputs, machine_type, result)
    _validate_cross_field(inputs, machine_type, result)

    result.raise_if_errors()


# ---------------------------------------------------------------------------
# Tier 0: Extract machine type (needed for everything else)
# ---------------------------------------------------------------------------


def _get_machine_type(inputs: AllInputs, result: ValidationResult):
    if inputs.basic is None:
        result.error("AllInputs", "basic", None, "required (cannot be None)")
        return None
    if inputs.basic.fusion_machine_type is None:
        result.error("Basic", "fusion_machine_type", None, "required (cannot be None)")
        return None
    return inputs.basic.fusion_machine_type


# ---------------------------------------------------------------------------
# Tier 1a: Required top-level dataclasses
# ---------------------------------------------------------------------------


def _validate_required_dataclasses(
    inputs: AllInputs, machine_type: FusionMachineType, result: ValidationResult
):
    required = (
        _MFE_REQUIRED
        if machine_type == FusionMachineType.MFE
        else (
            _IFE_REQUIRED if machine_type == FusionMachineType.IFE else _COMMON_REQUIRED
        )
    )
    for attr in required:
        if getattr(inputs, attr, None) is None:
            result.error("AllInputs", attr, None, "required (cannot be None)")


# ---------------------------------------------------------------------------
# Tier 1b: Required fields within each dataclass
# ---------------------------------------------------------------------------


def _validate_required_fields(
    inputs: AllInputs, machine_type: FusionMachineType, result: ValidationResult
):
    required_fields = (
        _MFE_REQUIRED_FIELDS
        if machine_type == FusionMachineType.MFE
        else (
            _IFE_REQUIRED_FIELDS
            if machine_type == FusionMachineType.IFE
            else _COMMON_REQUIRED_FIELDS
        )
    )
    for dc_attr, fields in required_fields.items():
        dc_obj = getattr(inputs, dc_attr, None)
        if dc_obj is None:
            continue  # already caught by _validate_required_dataclasses
        dc_name = type(dc_obj).__name__
        for field_name in fields:
            value = getattr(dc_obj, field_name, None)
            if value is None:
                result.error(dc_name, field_name, None, "required (cannot be None)")


# ---------------------------------------------------------------------------
# Tier 2: Field-level range checks
# ---------------------------------------------------------------------------


def _validate_field_rules(inputs: AllInputs, result: ValidationResult):
    for dc_attr, field_name, check_fn, constraint, is_error in FIELD_RULES:
        dc_obj = getattr(inputs, dc_attr, None)
        if dc_obj is None:
            continue
        value = getattr(dc_obj, field_name, None)
        if value is None:
            continue  # optional or already caught by required check
        try:
            passed = check_fn(value)
        except (TypeError, ValueError):
            passed = False
        if not passed:
            dc_name = type(dc_obj).__name__
            if is_error:
                result.error(dc_name, field_name, value, constraint)
            else:
                result.warn(dc_name, field_name, value, constraint)


# ---------------------------------------------------------------------------
# Tier 2b: Per-magnet validation
# ---------------------------------------------------------------------------


def _validate_magnets(inputs: AllInputs, result: ValidationResult):
    if inputs.coils is None or not inputs.coils.magnets:
        return
    for i, m in enumerate(inputs.coils.magnets):
        prefix = f"Magnet[{i}]({m.name})"
        if m.coil_count is not None and m.coil_count < 1:
            result.error(prefix, "coil_count", m.coil_count, ">= 1")
        if m.r_centre is not None and m.r_centre <= 0:
            result.error(prefix, "r_centre", m.r_centre, "> 0 (m)")
        if m.dr is not None and m.dr <= 0:
            result.error(prefix, "dr", m.dr, "> 0 (m)")
        if m.dz is not None and m.dz <= 0:
            result.error(prefix, "dz", m.dz, "> 0 (m)")
        if m.frac_in is not None and not (0 <= m.frac_in <= 1):
            result.error(prefix, "frac_in", m.frac_in, "in [0, 1]")
        if m.mfr_factor is not None and m.mfr_factor <= 0:
            result.error(prefix, "mfr_factor", m.mfr_factor, "> 0")


# ---------------------------------------------------------------------------
# Tier 2c: Simplified coils validation
# ---------------------------------------------------------------------------


def _validate_simplified_coils(
    inputs: AllInputs, machine_type: FusionMachineType, result: ValidationResult
):
    if machine_type != FusionMachineType.MFE or inputs.coils is None:
        return

    coils = inputs.coils
    has_magnets = bool(coils.magnets)
    has_simplified = coils.b_max is not None and coils.r_coil is not None

    if not has_magnets and not has_simplified:
        result.error(
            "Coils",
            "magnets / b_max+r_coil",
            None,
            "must provide either magnets list (detailed mode) or b_max + r_coil (simplified mode)",
        )
        return

    if not has_simplified:
        return  # detailed mode — validated by _validate_magnets

    # Simplified mode field checks
    if coils.b_max <= 0:
        result.error("Coils", "b_max", coils.b_max, "> 0 (Tesla)")
    if coils.r_coil <= 0:
        result.error("Coils", "r_coil", coils.r_coil, "> 0 (meters)")
    if coils.cost_per_kAm is not None and coils.cost_per_kAm <= 0:
        result.error("Coils", "cost_per_kAm", coils.cost_per_kAm, "> 0 ($/kAm)")
    if coils.path_factor is not None and coils.path_factor <= 0:
        result.error("Coils", "path_factor", coils.path_factor, "> 0")
    if coils.n_coils is not None and coils.n_coils < 1:
        result.error("Coils", "n_coils", coils.n_coils, ">= 1")
    if coils.coil_markup is not None and coils.coil_markup <= 0:
        result.error("Coils", "coil_markup", coils.coil_markup, "> 0")


# ---------------------------------------------------------------------------
# Tier 3: Cross-field validation
# ---------------------------------------------------------------------------


def _validate_cross_field(
    inputs: AllInputs, machine_type: FusionMachineType, result: ValidationResult
):
    # Shield fractions should sum to approximately 1.0
    if inputs.shield is not None:
        s = inputs.shield
        fracs = [s.f_SiC, s.FPCPPFbLi, s.f_W, s.f_BFS]
        if all(v is not None for v in fracs):
            total = sum(fracs)
            if not (0.95 <= total <= 1.05):
                result.warn(
                    "Shield",
                    "sum(f_SiC, FPCPPFbLi, f_W, f_BFS)",
                    round(total, 4),
                    f"shield fractions sum to {total:.4f}, expected ~1.0",
                )

    # time_to_replace <= plant_lifetime
    if inputs.basic is not None:
        b = inputs.basic
        if b.time_to_replace is not None and b.plant_lifetime is not None:
            if b.time_to_replace > b.plant_lifetime:
                result.error(
                    "Basic",
                    "time_to_replace",
                    b.time_to_replace,
                    f"<= plant_lifetime ({b.plant_lifetime})",
                )

    # Division-by-zero prevention
    if inputs.power_input is not None:
        pi = inputs.power_input
        if machine_type == FusionMachineType.MFE:
            if pi.eta_pin is not None and pi.eta_pin == 0:
                result.error(
                    "PowerInput",
                    "eta_pin",
                    0,
                    "> 0 (division by zero in power balance)",
                )
        elif machine_type == FusionMachineType.IFE:
            for f in ["eta_pin1", "eta_pin2"]:
                v = getattr(pi, f, None)
                if v is not None and v == 0:
                    result.error(
                        "PowerInput",
                        f,
                        0,
                        "> 0 (division by zero in power balance)",
                    )

    # Copper coils without p_coils
    if (
        inputs.coils is not None
        and inputs.coils.coil_material == CoilMaterial.COPPER
        and inputs.power_input is not None
    ):
        p_coils = getattr(inputs.power_input, "p_coils", None)
        if p_coils is None or p_coils == 0:
            result.warn(
                "Coils",
                "coil_material=COPPER",
                "p_coils=0",
                "Copper coils require significant p_coils (100-500 MW) for resistive power dissipation",
            )

    # DD fuel: warn if burn fractions not explicitly set
    if (
        inputs.basic is not None
        and inputs.basic.fuel_type == FuelType.DD
        and inputs.power_input is not None
    ):
        if inputs.power_input.dd_f_T is None:
            result.warn(
                "PowerInput",
                "dd_f_T",
                None,
                "not set for DD fuel -- will use default 0.969",
            )
        if inputs.power_input.dd_f_He3 is None:
            result.warn(
                "PowerInput",
                "dd_f_He3",
                None,
                "not set for DD fuel -- will use default 0.689",
            )

    # DHe3 fuel: warn if side-reaction fractions not set
    if (
        inputs.basic is not None
        and inputs.basic.fuel_type == FuelType.DHE3
        and inputs.power_input is not None
    ):
        if inputs.power_input.dhe3_dd_frac is None:
            result.warn(
                "PowerInput",
                "dhe3_dd_frac",
                None,
                "not set for DHe3 fuel -- will use default 0.07",
            )
        if inputs.power_input.dhe3_f_T is None:
            result.warn(
                "PowerInput",
                "dhe3_f_T",
                None,
                "not set for DHe3 fuel -- will use default 0.97",
            )
