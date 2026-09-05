"""
GUI-facing schema metadata attached to step configuration fields.

`build_schema` produces a `json_schema_extra` dict of `crucible:*` keys that
step `Field(...)` declarations attach to their Pydantic model fields. These
keys are surfaced verbatim in each step's generated JSON Schema (see
`crucible.workflow.registry.StepsRegistry.list_step_keys`) and consumed by
`crucible_gui` to decide how to render each field's editor — without the
frontend needing to hardcode per-step form logic.
"""

from typing import Any, Literal


CrucibleType = Literal[
    "column-name",
    "file-path",
    "folder-path",
    "expression",
    "condition",
    "literal-value",
    'date',
    'datetime'
]
"""Semantic type of a field's value, independent of its JSON Schema type."""

CrucibleRole = Literal[
    "input-column",
    "output-column",
    "group-key",
    "aggregation-column",
    "sort-column",
    "join-left-key",
    "join-right-key",
]
"""What a column-typed field is used for, e.g. to scope which schema it should be picked from."""

CrucibleSource = Literal[
    "input-schema",
    "left-schema",
    "right-schema",
    "context-store",
    "filesystem",
    "enum",
    "static",
    'sheets'
]
"""Where the frontend should source a field's selectable options from."""

CrucibleEditor = Literal[
    "text",
    "number",
    "checkbox",
    "select",
    "column-select",
    "column-multiselect",
    "file-picker",
    "folder-picker",
    "expression-builder",
    "condition-builder",
    'date-picker',
    'datetime-picker',
]
"""Which editor widget the frontend should render for a field."""


def build_schema(
    *,
    type_: CrucibleType | None = None,
    role: CrucibleRole | None = None,
    source: CrucibleSource | None = None,
    editor: CrucibleEditor | None = None,
    advanced: bool | None = None,
    help_text: str | None = None,
) -> dict[str, Any]:
    """Build a `json_schema_extra` dict of `crucible:*` UI hints for a Pydantic field.

    Only the keys corresponding to non-`None` arguments are included, so
    each field only advertises the hints relevant to it (a JSON Schema
    consumer that doesn't understand `crucible:*` keys can safely ignore
    them).

    Args:
        type_ (CrucibleType | None, optional): Semantic type of the field's value. Defaults to None.
        role (CrucibleRole | None, optional): What a column-typed field is used for. Defaults to None.
        source (CrucibleSource | None, optional): Where selectable options should come from. Defaults to None.
        editor (CrucibleEditor | None, optional): Which editor widget to render. Defaults to None.
        advanced (bool | None, optional): Whether the field should be hidden behind an "advanced" toggle. Defaults to None.
        help_text (str | None, optional): Additional help text to show alongside the field. Defaults to None.

    Returns:
        dict[str, Any]: Mapping of `crucible:*` keys to pass as a field's `json_schema_extra`.
    """
    extra: dict[str, Any] = {}

    if type_ is not None:
        extra["crucible:type"] = type_

    if role is not None:
        extra["crucible:role"] = role

    if source is not None:
        extra["crucible:source"] = source

    if editor is not None:
        extra["crucible:editor"] = editor

    if advanced is not None:
        extra["crucible:advanced"] = advanced

    if help_text is not None:
        extra["crucible:help"] = help_text

    return extra
