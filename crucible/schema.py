# crucible/schema_extensions.py

from re import M
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

CrucibleRole = Literal[
    "input-column",
    "output-column",
    "group-key",
    "aggregation-column",
    "sort-column",
    "join-left-key",
    "join-right-key",
]

CrucibleSource = Literal[
    "input-schema",
    "left-schema",
    "right-schema",
    "context-store",
    "filesystem",
    "enum",
    "static",
]

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
    'datetime-picker'
]


def build_schema(
    *,
    type_: CrucibleType | None = None,
    role: CrucibleRole | None = None,
    source: CrucibleSource | None = None,
    editor: CrucibleEditor | None = None,
    advanced: bool | None = None,
    help_text: str | None = None,
) -> dict[str, Any]:
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