from importlib import resources
from typing import Optional

from pyfecons.report import HydratedTemplate, ReportOverrides, ReportSection

# Shared templates path - templates common to both MFE and IFE
SHARED_TEMPLATES_PATH = "pyfecons.costing.shared.templates"


def read_template(templates_path: str, template_file: str) -> str:
    """Read a template file from the specified package path."""
    try:
        with resources.files(templates_path).joinpath(template_file).open(
            "r", encoding="utf-8"
        ) as file:
            return file.read()
    except (FileNotFoundError, TypeError):
        # Fallback for older Python versions
        with resources.path(templates_path, template_file) as template_path:
            with open(template_path, "r", encoding="utf-8") as file:
                return file.read()


def template_exists(templates_path: str, template_file: str) -> bool:
    """Check if a template file exists in the specified package path."""
    try:
        return resources.files(templates_path).joinpath(template_file).is_file()
    except (TypeError, AttributeError):
        # Fallback for older Python versions
        try:
            with resources.path(templates_path, template_file):
                return True
        except FileNotFoundError:
            return False


def replace_values(template_content: str, replacements: dict[str, str]) -> str:
    for key, value in replacements.items():
        template_content = template_content.replace(key, str(value))
    return template_content


def hydrate_templates(
    templates_path: str,
    template_providers: list[ReportSection],
    overrides: Optional[ReportOverrides] = None,
) -> list[HydratedTemplate]:
    hydrated_templates = []
    for provider in template_providers:
        template_content = get_template_contents(
            templates_path, provider.template_file, overrides
        )
        contents = replace_values(template_content, provider.replacements)
        hydrated_templates.append(HydratedTemplate(provider, contents))
    return hydrated_templates


def combine_figures(template_providers: list[ReportSection]) -> dict[str, bytes]:
    all_figures = {}
    for provider in template_providers:
        all_figures.update(provider.figures)
    return all_figures


def load_document_template(
    templates_path: str,
    document_template: str,
    overrides: Optional[ReportOverrides] = None,
    replacements: Optional[dict[str, str]] = None,
) -> HydratedTemplate:
    template_content = get_template_contents(
        templates_path, document_template, overrides
    )
    if replacements:
        template_content = replace_values(template_content, replacements)
    return HydratedTemplate(
        ReportSection(template_file=document_template),
        template_content,
    )


def get_template_contents(
    templates_path: str, template_file: str, overrides: Optional[ReportOverrides] = None
) -> str:
    """Get template contents with fallback to shared templates.

    Priority order:
    1. Customer overrides (if provided)
    2. Machine-specific template (mfe/ife)
    3. Shared template (common to both)
    """
    # Check overrides first
    if overrides is not None and template_file in overrides.templates.keys():
        return overrides.templates[template_file]

    # Try machine-specific path first
    if template_exists(templates_path, template_file):
        return read_template(templates_path, template_file)

    # Fall back to shared templates
    if template_exists(SHARED_TEMPLATES_PATH, template_file):
        return read_template(SHARED_TEMPLATES_PATH, template_file)

    # If not found anywhere, raise an error
    raise FileNotFoundError(
        f"Template '{template_file}' not found in {templates_path} or {SHARED_TEMPLATES_PATH}"
    )
