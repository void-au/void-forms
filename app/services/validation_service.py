import re
from typing import Any

from app.models.config import SiteConfig, ValidationRule


def validate_submission(
    attributes: dict[str, Any],
    site: SiteConfig,
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []

    provided_keys = set(attributes.keys())
    disallowed = provided_keys - site.allowed_attributes
    for field_name in sorted(disallowed):
        errors.append(
            {
                "field": field_name,
                "message": "attribute_not_allowed",
            }
        )

    for field_name, rule in site.validation.items():
        value = attributes.get(field_name)
        _validate_rule(field_name, value, rule, errors)

    return errors


def _validate_rule(
    field_name: str,
    value: Any,
    rule: ValidationRule,
    errors: list[dict[str, str]],
) -> None:
    if rule.required and (value is None or str(value).strip() == ""):
        errors.append({"field": field_name, "message": "required"})
        return

    if value is None:
        return

    value_text = str(value)

    if rule.type == "email" and "@" not in value_text:
        errors.append({"field": field_name, "message": "invalid_email"})

    if rule.min_length is not None and len(value_text) < rule.min_length:
        errors.append({"field": field_name, "message": "too_short"})

    if rule.max_length is not None and len(value_text) > rule.max_length:
        errors.append({"field": field_name, "message": "too_long"})

    if rule.options and value_text not in rule.options:
        errors.append({"field": field_name, "message": "invalid_option"})

    if rule.regex and not re.fullmatch(rule.regex, value_text):
        errors.append({"field": field_name, "message": "invalid_format"})
