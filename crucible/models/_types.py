from typing import Annotated

from pydantic import AfterValidator, Field


def validate_column_name(value: str) -> str:
    """
    Validate a dataframe column name.

    Leading and trailing whitespace is removed before validation.

    Args:
        value:
            Column name provided by the user or workflow definition.

    Returns:
        Normalized column name.

    Raises:
        ValueError:
            If the column name is empty after trimming whitespace.
    """
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
"""
Validated dataframe column name.

This type is used throughout Crucible whenever a parameter references an input
or output column.

Features:

- strips leading and trailing whitespace
- rejects empty column names
- generates JSON Schema metadata for GUI editors
- provides a consistent semantic type across workflow definitions

The generated JSON Schema includes the custom metadata:

```json
{
  "crucible:type": "column-name"
}
```
"""