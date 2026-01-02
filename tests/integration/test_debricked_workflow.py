"""Integration tests for the Debricked GitHub Actions workflow."""

from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

from tests.integration.test_github_workflows import GitHubActionsYamlLoader

WORKFLOW_FILE = Path(__file__).parent.parent.parent / ".github" / "workflows" / "debricked.yml"


@pytest.fixture(scope="module")
def workflow_content() -> str:
    assert WORKFLOW_FILE.exists(), f"{WORKFLOW_FILE} does not exist"
    return WORKFLOW_FILE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def workflow_config(workflow_content: str) -> Dict[str, Any]:
    return yaml.load(workflow_content, Loader=GitHubActionsYamlLoader)


@pytest.fixture(scope="module")
def scan_job(workflow_config: Dict[str, Any]) -> Dict[str, Any]:
    jobs = workflow_config.get("jobs", {})
    assert "vulnerabilities-scan" in jobs, "Debricked workflow must define 'vulnerabilities-scan' job"
    return jobs["vulnerabilities-scan"]


@pytest.fixture(scope="module")
def job_steps(scan_job: Dict[str, Any]) -> List[Dict[str, Any]]:
    steps = scan_job.get("steps", [])
    assert isinstance(steps, list) and steps, "Debricked job must define non-empty steps"
    return steps


def test_workflow_name(workflow_config: Dict[str, Any]):
    name = workflow_config.get("name", "")
    assert isinstance(name, str) and name.strip(), "Workflow must have a non-empty name"
    assert "debricked" in name.lower()


def test_workflow_triggers(workflow_config: Dict[str, Any]):
    triggers = workflow_config.get("on", {})
    assert isinstance(triggers, dict), "Workflow triggers must be a mapping"

    for key in ["push", "pull_request", "workflow_dispatch"]:
        assert key in triggers, f"Workflow must define '{key}' trigger"

    for key in ["push", "pull_request"]:
        event = triggers.get(key, {})
        branches = event.get("branches", [])
        assert branches, f"'{key}' trigger must define branches"
        assert "main" in branches, f"'{key}' trigger must run on main"


def test_job_runs_on_ubuntu(scan_job: Dict[str, Any]):
    runs_on = scan_job.get("runs-on", "")
    assert isinstance(runs_on, str) and runs_on.strip()
    assert "ubuntu" in runs_on.lower()


def test_checkout_step_present(job_steps: List[Dict[str, Any]]):
    checkout_steps = [step for step in job_steps if step.get("uses", "").startswith("actions/checkout")]
    assert checkout_steps, "Debricked job must include actions/checkout"
    assert all("@" in step["uses"] for step in checkout_steps), "Checkout steps must specify a version"


def test_debricked_step_present(job_steps: List[Dict[str, Any]]):
    debricked_steps = [step for step in job_steps if "debricked" in step.get("uses", "")]
    assert debricked_steps, "Debricked job must include a Debricked action"
    assert all("@" in step["uses"] for step in debricked_steps), "Debricked steps must specify a version"


def test_debricked_token_from_secrets(job_steps: List[Dict[str, Any]]):
    debricked_steps = [step for step in job_steps if "debricked" in step.get("uses", "")]
    assert debricked_steps

    for step in debricked_steps:
        env = step.get("env", {})
        assert "DEBRICKED_TOKEN" in env
        token = env["DEBRICKED_TOKEN"]
        assert isinstance(token, str)
        assert "${{" in token and "secrets" in token.lower()


def test_no_hardcoded_tokens(workflow_content: str):
    suspicious_patterns = ["ghp_", "gho_", "ghu_", "ghs_", "ghr_"]
    for pattern in suspicious_patterns:
        assert pattern not in workflow_content
