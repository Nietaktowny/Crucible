from typing import Annotated

from pydantic import AfterValidator, Field


def validate_column_name(value: str) -> str:
    value = value.strip()

    if not value:
        raise ValueError("Column name cannot be empty.")

    return value


ColumnName = Annotated[
    str,
    AfterValidator(validate_column_name),
    Field(
        description="Name of a dataframe column.",
        json_schema_extra={
            "crucible:type": "column-name",
        },
    ),
]