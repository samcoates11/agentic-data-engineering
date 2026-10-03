import pytest

from llm_tool_calling.de_agent.tools import data_tools


def test_list_files_finds_sample_dataset():
    assert "orders.csv" in data_tools.list_files()


def test_inspect_schema_reports_row_count_and_nulls():
    schema = data_tools.inspect_schema("orders.csv")
    assert schema["row_count"] == 10
    customer_col = next(c for c in schema["columns"] if c["name"] == "customer")
    assert customer_col["null_count"] == 1


def test_preview_rows_returns_requested_count():
    rows = data_tools.preview_rows("orders.csv", 3)
    assert len(rows) == 3
    assert rows[0]["order_id"] == 1001


def test_summarize_column_numeric():
    summary = data_tools.summarize_column("orders.csv", "quantity")
    assert summary["min"] == 1.0
    assert summary["max"] == 10.0


def test_summarize_column_categorical():
    summary = data_tools.summarize_column("orders.csv", "customer")
    assert summary["unique_count"] == 4
    assert summary["top_values"][0]["value"] == "Alice Chen"


def test_rejects_path_traversal():
    with pytest.raises(ValueError, match="outside the data directory"):
        data_tools.inspect_schema("../../etc/passwd")


def test_rejects_missing_file():
    with pytest.raises(ValueError, match="No such file"):
        data_tools.inspect_schema("nope.csv")


def test_rejects_unknown_column():
    with pytest.raises(ValueError, match="No column 'bogus'"):
        data_tools.summarize_column("orders.csv", "bogus")
