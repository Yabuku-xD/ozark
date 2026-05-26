from backend.engine.dataset_io import export_dataset
from backend.engine.datasets import scenario_dict_to_definition, scenario_from_result
from backend.engine.eval_policy import EvalPolicy
from backend.engine.evaluators import EvaluatorRunner, builtin_evaluators
from backend.engine.ingest import normalize_payload
from backend.engine.issues import findings_to_issues
from backend.engine.reports import build_release_report


def test_evaluators_detect_secret_output():
    run = {
        "id": "run-1",
        "results": [{
            "scenario_name": "secret leak",
            "passed": True,
            "score": 100,
            "called_tools": [],
            "violations": [],
            "trace": [{"kind": "assistant", "content": "api_key = sk-123456789012345678901234"}],
            "latency_ms": 1,
        }]
    }

    report = EvaluatorRunner(builtin_evaluators()).evaluate_run(run)

    assert report["passed"] is False
    assert report["failed_count"] == 1
    assert report["findings"][0]["signature"]


def test_eval_policy_blocks_failed_run():
    run = {"score": 70, "confidence": 0.7, "failed_count": 1, "results": []}

    gate = EvalPolicy().evaluate(run).to_dict()

    assert gate["passed"] is False
    assert any("score" in failure for failure in gate["failures"])


def test_ingest_normalizes_jsonl_style_events():
    payload = {
        "events": [
            {"trace_id": "abc", "role": "user", "content": "hello", "latency_ms": 5},
            {"trace_id": "abc", "role": "assistant", "content": "hi", "latency_ms": 7},
        ]
    }

    run = normalize_payload(payload, "prod-agent", "Prod Agent")

    assert run["scenario_count"] == 1
    assert run["total_latency_ms"] == 12
    assert run["results"][0]["scenario_name"] == "prod/abc"


def test_release_report_decision_ready_when_clean():
    run = {"id": "run-1", "score": 90, "status": "passed", "summary": "ok", "results": []}
    gate = {"passed": True, "failures": []}
    eval_report = {"passed": True, "score": 1.0, "finding_count": 0, "failed_count": 0}

    report = build_release_report(run, gate, eval_report, [])

    assert report["decision"] == "ready"


def test_blocked_tools_evaluator_does_not_flag_unrelated_tools():
    run = {
        "results": [{
            "scenario_name": "privacy",
            "passed": False,
            "score": 50,
            "called_tools": ["lookup_user"],
            "violations": [{"severity": "block", "guardrail": "pii", "message": "PII leak", "evidence": "email"}],
            "trace": [],
            "latency_ms": 1,
        }]
    }

    report = EvaluatorRunner(builtin_evaluators()).evaluate_run(run)

    blocked_tool_findings = [f for f in report["findings"] if f["evaluator_id"] == "no-blocked-tools"]
    assert blocked_tool_findings[0]["passed"] is True


def test_findings_to_issues_deduplicates_signatures_within_run():
    run = {"id": "run-1"}
    finding = {
        "passed": False,
        "evaluator_id": "eval-1",
        "severity": "high",
        "message": "same failure",
        "metadata": {"scenario_name": "same"},
    }

    issues = findings_to_issues(run, {"findings": [finding, finding]}, lambda signature: None)

    assert len(issues) == 1
    assert issues[0]["occurrence_count"] == 2


def test_promoted_regression_scenario_deserializes():
    scenario = scenario_from_result({"scenario_name": "failed", "scenario_type": "security", "passed": False, "score": 10, "user_prompt": "real user prompt"}, "run-1")

    restored = scenario_dict_to_definition(scenario)

    assert restored.agent_type == "custom"
    assert restored.user_prompt == "real user prompt"


def test_dataset_export_schema():
    dataset = {
        "id": "ds-1",
        "name": "Regressions",
        "description": "desc",
        "source": "test",
        "metadata": {},
        "items": [{"scenario": {"name": "s1"}, "tags": ["regression"]}],
    }

    pack = export_dataset(dataset)

    assert pack["schema"] == "ozark.dataset.v1"
    assert pack["items"][0]["scenario"]["name"] == "s1"
