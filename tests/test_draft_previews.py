from datetime import date, datetime, time
from types import SimpleNamespace

import polars as pl
import pytest

from crucible import run_workflow
from crucible.models import FrameContext, StepConfig, StepExecutionContext, Workflow
from crucible.steps.concat import ConcatStep
from crucible.steps.join import JoinStep
from crucible.declarative.expressions import ExpressionBuilder, ValueExpression
from crucible.workflow.evaluation import EvaluationError
from crucible_server.schemas import FilterValuesRequest, WorkflowPreviewRequest
from crucible_server.services.previews import WorkflowPreviewService


def step(key, **parameters):
    return StepConfig(key=key, parameters=parameters)


@pytest.fixture
def draft(tmp_path):
    path = tmp_path / "source.csv"
    pl.DataFrame({"id": list(range(500)), "label": ["a.b", "axb"] * 250}).write_csv(path)
    return Workflow(name="draft", steps=[step("read_csv", path=str(path), infer_types=True)])


def service(workflows=None):
    workflows = workflows or {}

    def resolve(name):
        if name not in workflows:
            raise FileNotFoundError(f"Workflow not found: {name}")
        return workflows[name]

    return WorkflowPreviewService(SimpleNamespace(store=SimpleNamespace(get_workflow_model=resolve)))


def request(workflow, **kwargs):
    return WorkflowPreviewRequest(workflow=workflow, step_id=workflow.steps[-1].step_id, **kwargs)


def test_preview_limits_after_filter_and_searches_all_rows(draft):
    source_id = draft.steps[0].step_id
    draft.steps.append(step("filter_rows", condition={"left": {"column": "id"}, "operator": ">", "right": {"value": 450}}))
    previews = service()
    result = previews.preview(request(draft, preview_limit=3))
    assert [row["id"] for row in result.data] == [451, 452, 453]
    assert result.truncated and result.row_count is None
    assert result.input_schema == {"id": "Int64", "label": "String"}
    values = previews.filter_values(FilterValuesRequest(workflow=draft, step_id=source_id, column="id", search="499"))
    assert values.values == [499]


def test_selecting_step_and_filter_input(draft):
    source_id = draft.steps[0].step_id
    draft.steps.append(step("filter_rows", condition={"left": {"column": "id"}, "operator": ">", "right": {"value": 450}}))
    previews = service()
    assert previews.preview(WorkflowPreviewRequest(workflow=draft, step_id=source_id, preview_limit=1)).data[0]["id"] == 0
    values = previews.filter_values(FilterValuesRequest(workflow=draft, step_id=draft.steps[-1].step_id, before=True, column="id", search="0"))
    assert 0 in values.values


def test_zero_rows_retain_schema_and_writers_never_execute(draft, tmp_path):
    output = tmp_path / "must-not-exist.csv"
    draft.steps.extend([
        step("filter_rows", condition={"left": {"column": "id"}, "operator": "<", "right": {"value": 0}}),
        step("write_csv", path=str(output)),
    ])
    result = service().preview(request(draft))
    assert result.data == []
    assert result.frame_schema == {"id": "Int64", "label": "String"}
    assert not output.exists()


def test_column_order_and_writer_input_schema_are_preserved(draft, tmp_path):
    draft.steps.extend([
        step("rename_columns", mapping={"id": "2", "label": "1"}),
        step("write_csv", path=str(tmp_path / "output.csv")),
    ])
    result = service().preview(request(draft))
    assert result.columns == ["2", "1"]
    assert result.input_schema == {"2": "Int64", "1": "String"}


def test_preview_validates_only_selected_prefix(draft):
    target_id = draft.steps[0].step_id
    draft.steps.append(step("sort_rows"))
    result = service().preview(WorkflowPreviewRequest(workflow=draft, step_id=target_id))
    assert len(result.data) == 200
    with pytest.raises(EvaluationError) as exc:
        service().preview(request(draft))
    assert exc.value.step_id == draft.steps[-1].step_id


def test_missing_column_reports_configured_step(draft):
    draft.steps.append(step("select_columns", columns=["missing"]))
    with pytest.raises(EvaluationError) as exc:
        service().preview(request(draft))
    assert exc.value.step_id == draft.steps[-1].step_id
    assert "missing" in str(exc.value)


def test_unknown_and_duplicate_step_ids_are_rejected(draft):
    with pytest.raises(ValueError, match="Step not found"):
        service().preview(WorkflowPreviewRequest(workflow=draft, step_id="no-such-step"))
    draft.steps.append(draft.steps[0].model_copy())
    with pytest.raises(ValueError, match="unique"):
        service().preview(request(draft))


@pytest.mark.parametrize("field", ["preview_limit", "limit"])
def test_request_limits_are_bounded(draft, field):
    with pytest.raises(ValueError):
        FilterValuesRequest(workflow=draft, step_id=draft.steps[0].step_id, column="id", **{field: 1001})


@pytest.mark.parametrize("kind,value,expected", [
    ("date", "2026-11-13", date(2026, 11, 13)),
    ("datetime", "2026-11-13T12:30:00", datetime(2026, 11, 13, 12, 30)),
    ("time", "12:30:00", time(12, 30)),
])
def test_temporal_literals_round_trip(kind, value, expected):
    literal = ValueExpression.model_validate_json(ValueExpression(value=value, value_type=kind).model_dump_json())
    assert pl.select(ExpressionBuilder().build(literal)).item() == expected


def test_distinct_null_empty_boolean_and_literal_search(tmp_path):
    path = tmp_path / "source.csv"
    pl.DataFrame({"text": ["a.b", "axb", None, ""], "flag": [True, False, None, False]}).write_csv(path)
    workflow = Workflow(name="values", steps=[step("read_csv", path=str(path), infer_types=True)])
    previews = service()
    values = previews.filter_values(FilterValuesRequest(workflow=workflow, step_id=workflow.steps[0].step_id, column="text", search="."))
    assert values.values == ["a.b"]
    flags = previews.filter_values(FilterValuesRequest(workflow=workflow, step_id=workflow.steps[0].step_id, column="flag"))
    assert flags.values == [None, False, True]
    text = previews.filter_values(FilterValuesRequest(workflow=workflow, step_id=workflow.steps[0].step_id, column="text"))
    assert text.values == [None, "", "a.b", "axb"]


def test_reference_is_live_isolated_and_skips_writers(draft, tmp_path):
    output = tmp_path / "reference-output.csv"
    draft.steps.extend([step("limit_rows", limit=2, mode="head"), step("write_csv", path=str(output))])
    workflow = Workflow(name="consumer", steps=[step("read_workflow", workflow_name="draft")])
    previews = service({"draft": draft})
    assert len(previews.preview(request(workflow)).data) == 2
    draft.steps[-2].parameters["limit"] = 4
    assert len(previews.preview(request(workflow)).data) == 4
    assert not output.exists()


def test_nested_reference_and_cycle_detection(draft):
    middle = Workflow(name="middle", steps=[step("read_workflow", workflow_name="draft")])
    root = Workflow(name="root", steps=[step("read_workflow", workflow_name="middle")])
    previews = service({"draft": draft, "middle": middle, "root": root})
    assert len(previews.preview(request(root, preview_limit=2)).data) == 2
    draft.steps = [step("read_workflow", workflow_name="root")]
    with pytest.raises(EvaluationError, match="cycle") as exc:
        previews.preview(request(root))
    assert exc.value.workflow_name == "draft"
    assert exc.value.step_id == draft.steps[0].step_id


def test_missing_dependency_has_reference_step_context():
    workflow = Workflow(name="root", steps=[step("read_workflow", workflow_name="gone")])
    with pytest.raises(EvaluationError, match="gone") as exc:
        service().preview(request(workflow))
    assert exc.value.step_id == workflow.steps[0].step_id


def test_explicit_sources_leave_unrelated_context_intact():
    left = FrameContext(df=pl.DataFrame({"id": [1, 2]}).lazy())
    right = FrameContext(df=pl.DataFrame({"id": [2, 3]}).lazy())
    context = StepExecutionContext(extra_inputs={"chosen": right, "unrelated": right})
    result = JoinStep(step("join", left_on="id", right_on="id", right_context_key="chosen")).execute(left, context)
    assert result.df.collect().height == 2
    assert set(context.extra_inputs) == {"unrelated"}
    context.extra_inputs["chosen"] = right
    result = ConcatStep(step("concat", context_keys=["chosen"])).execute(left, context)
    assert result.df.collect().height == 4
    assert set(context.extra_inputs) == {"unrelated"}


def test_cli_workflow_reference_uses_sibling_and_skips_dependency_writes(draft, tmp_path):
    from crucible.workflow.loader import WorkflowLoader

    dependency_output = tmp_path / "dependency.csv"
    consumer_output = tmp_path / "consumer.csv"
    draft.steps.extend([step("limit_rows", limit=3, mode="head"), step("write_csv", path=str(dependency_output))])
    root = Workflow(name="root", steps=[step("read_workflow", workflow_name="draft"), step("write_csv", path=str(consumer_output))])
    loader = WorkflowLoader()
    loader.save(draft, tmp_path / "draft.yaml")
    loader.save(root, tmp_path / "root.yaml")
    result = run_workflow(tmp_path / "root.yaml", inspect=True)
    assert result.success, result.error
    assert len(result.preview) == 3
    assert consumer_output.exists()
    assert not dependency_output.exists()


def test_lazy_errors_identify_upstream_step_and_reference_workflow(draft):
    failing = step("filter_rows", condition={"left": {"column": "id"}, "operator": ">", "right": {"value": "invalid-number"}})
    draft.steps.extend([failing, step("sort_rows", columns=[{"name": "id", "direction": "asc"}])])
    with pytest.raises(EvaluationError) as exc:
        service().preview(request(draft))
    assert exc.value.step_id == failing.step_id
    root = Workflow(name="root", steps=[step("read_workflow", workflow_name="draft")])
    with pytest.raises(EvaluationError) as exc:
        service({"draft": draft}).preview(request(root))
    assert exc.value.step_id == failing.step_id
    assert exc.value.workflow_name == "draft"


def test_join_and_append_saved_workflows_preserve_unselected_context(draft):
    source = step("read_workflow", workflow_name="draft", context_store=True, context_key="selected")
    workflow = Workflow(name="combine", steps=[
        draft.steps[0],
        step("read_workflow", workflow_name="draft", context_store=True, context_key="unrelated"),
        source,
        step("join", left_on="id", right_on="id", how="inner", right_context_key="selected"),
        step("concat", how="diagonal", context_keys=["unrelated"]),
    ])
    result = service({"draft": draft}).preview(request(workflow, preview_limit=1000))
    assert len(result.data) == 1000
    assert "label_right" in result.frame_schema
