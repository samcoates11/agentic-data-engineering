"""Tool functions exposed to the model by agent.py.

Each function inspects a local CSV/Parquet file living under DATA_DIR. Every
function is paired with a Bedrock tool spec (name, description, JSON Schema
for its arguments) in TOOL_SPECS at the bottom of this file, which is what
agent.py turns into the Converse API's `toolConfig`.
"""

import json
import os
from pathlib import Path

import pandas as pd

# Project root is four levels up from this file (tools -> de_agent ->
# llm_tool_calling -> src -> project root). Overridable via DATA_DIR so the
# agent can be pointed at a different folder without code changes.
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = Path(os.environ.get("DATA_DIR", _PROJECT_ROOT / "data")).resolve()

_SUPPORTED_SUFFIXES = {".csv", ".parquet"}


def _resolve_path(filename: str) -> Path:
    """Resolve `filename` against DATA_DIR, rejecting anything that escapes it.

    The model supplies `filename` from user input, so this blocks path
    traversal (e.g. "../../etc/passwd") rather than trusting it outright.
    """
    path = (DATA_DIR / filename).resolve()
    if DATA_DIR not in path.parents and path != DATA_DIR:
        raise ValueError(f"'{filename}' is outside the data directory.")
    if not path.is_file():
        raise ValueError(f"No such file: '{filename}'.")
    if path.suffix not in _SUPPORTED_SUFFIXES:
        raise ValueError(f"Unsupported file type '{path.suffix}'. Use .csv or .parquet.")
    return path


def _load(filename: str) -> pd.DataFrame:
    path = _resolve_path(filename)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    return pd.read_parquet(path)


def _to_native(value):
    """Convert a pandas/numpy scalar to a plain JSON-serialisable Python value."""
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def list_files() -> list[str]:
    """List the data files available to inspect."""
    return sorted(
        p.name for p in DATA_DIR.iterdir() if p.is_file() and p.suffix in _SUPPORTED_SUFFIXES
    )


def inspect_schema(filename: str) -> dict:
    """Return row count and, per column, its dtype and null count/percentage."""
    df = _load(filename)
    row_count = len(df)
    columns = []
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        columns.append(
            {
                "name": col,
                "dtype": str(df[col].dtype),
                "null_count": null_count,
                "null_pct": round(null_count / row_count * 100, 2) if row_count else 0.0,
            }
        )
    return {"filename": filename, "row_count": row_count, "columns": columns}


def preview_rows(filename: str, n: int = 5) -> list[dict]:
    """Return the first `n` rows of the file as a list of records."""
    df = _load(filename)
    # Round-trip through pandas' own JSON encoder so NaN/NaT/Timestamp values
    # come out as JSON-safe null/ISO-date rather than raising or leaking
    # pandas-specific types into the response sent back to the model.
    return json.loads(df.head(n).to_json(orient="records", date_format="iso"))


def summarize_column(filename: str, column: str) -> dict:
    """Return summary statistics for one column: numeric stats or top values."""
    df = _load(filename)
    if column not in df.columns:
        raise ValueError(f"No column '{column}' in '{filename}'. Available: {list(df.columns)}")

    series = df[column]
    summary = {
        "filename": filename,
        "column": column,
        "dtype": str(series.dtype),
        "count": int(series.count()),
        "null_count": int(series.isna().sum()),
    }

    if pd.api.types.is_numeric_dtype(series):
        summary.update(
            {
                "min": _to_native(series.min()),
                "max": _to_native(series.max()),
                "mean": _to_native(series.mean()),
                "std": _to_native(series.std()),
            }
        )
    else:
        value_counts = series.value_counts().head(5)
        summary.update(
            {
                "unique_count": int(series.nunique()),
                "top_values": [
                    {"value": _to_native(value), "count": int(count)}
                    for value, count in value_counts.items()
                ],
            }
        )

    return summary


# Paired with each function: the name/description/JSON-Schema that
# agent.py turns into Bedrock's `toolConfig`. Keep in sync with the
# function signatures above.
TOOL_SPECS = [
    {
        "name": "list_files",
        "description": "List the data files (.csv, .parquet) available to inspect.",
        "schema": {"type": "object", "properties": {}},
        "function": list_files,
    },
    {
        "name": "inspect_schema",
        "description": (
            "Get a file's row count and, for each column, its data type and "
            "null count/percentage. Call this before asking about a file's columns."
        ),
        "schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "File name, from list_files."},
            },
            "required": ["filename"],
        },
        "function": inspect_schema,
    },
    {
        "name": "preview_rows",
        "description": "Preview the first N rows of a file to see example data.",
        "schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "File name, from list_files."},
                "n": {"type": "integer", "description": "Number of rows to return (default 5)."},
            },
            "required": ["filename"],
        },
        "function": preview_rows,
    },
    {
        "name": "summarize_column",
        "description": (
            "Get summary statistics for one column: min/max/mean/std for numeric "
            "columns, or the most common values for text/categorical columns."
        ),
        "schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "File name, from list_files."},
                "column": {"type": "string", "description": "Column name, from inspect_schema."},
            },
            "required": ["filename", "column"],
        },
        "function": summarize_column,
    },
]
