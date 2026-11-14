from pathlib import Path
import runpy

import polars as pl

from crucible.runner import WorkflowRunner
from crucible_workspace.store import WorkflowStore


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def load_examples():
    runpy.run_path(str(EXAMPLES / "load.py"))["load_examples"]()


def test_examples_clean_and_export_data(tmp_path, monkeypatch):
    monkeypatch.setenv("CRUCIBLE_WORKSPACE_DIR", str(tmp_path))
    load_examples()
    store = WorkflowStore()
    runner = WorkflowRunner()

    # Summary resolves cleanup from the store and must not execute its writer.
    summary = runner.run(
        store.get_workflow_path("example_cafe_summary"),
        inspect=True,
        resolve_workflow=store.get_workflow_model,
    )
    assert summary.success, summary.error
    output = tmp_path / "example-output"
    assert not (output / "clean_cafe_sales.csv").exists()
    assert pl.read_csv(output / "cafe_summary.csv").to_dicts() == [
        {"Category": "Drinks", "Units Sold": 10.0, "Revenue": 21.5},
        {"Category": "Food", "Units Sold": 8.0, "Revenue": 22.0},
    ]

    for name in ("example_cafe_cleanup", "example_stock_cleanup"):
        result = runner.run(store.get_workflow_path(name), inspect=True)
        assert result.success, result.error

    cafe = pl.read_csv(output / "clean_cafe_sales.csv")
    assert cafe["Transaction ID"].to_list() == [f"DEMO{i:03}" for i in range(1, 11)]
    assert cafe["Total Spent"].sum() == 43.5
    stock = pl.read_csv(output / "clean_stock.csv")
    assert stock["SKU"].to_list() == ["ST001", "ST002", "ST004", "ST005"]
    assert stock["Item"].to_list() == ["Coffee beans", "Tea bags", "Cake slices", "Cookies"]
    assert stock["Supplier"][1] == "Unspecified"
    assert stock["Stock Value"].sum() == 161.5


def test_loading_examples_preserves_edits_and_uses_current_workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("CRUCIBLE_WORKSPACE_DIR", str(tmp_path))
    load_examples()
    store = WorkflowStore()
    content = store.read_workflow("example_cafe_cleanup")
    edited = content.replace("name: example_cafe_cleanup", "name: My edited example", 1)
    store.update_workflow("example_cafe_cleanup", edited)
    load_examples()
    assert store.read_workflow("example_cafe_cleanup") == edited
    assert len(store.list_workflows()) == 3
    workflow = store.get_workflow_model("example_cafe_cleanup")
    assert workflow.steps[0].parameters["path"] == str(EXAMPLES / "data/dirty_cafe_sales.csv")
    assert workflow.steps[-1].parameters["path"] == str(tmp_path / "example-output/clean_cafe_sales.csv")
