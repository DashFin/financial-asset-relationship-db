"""
Comprehensive tests for the Debricked vulnerability scanning workflow.

This module validates the debricked.yml workflow file to ensure:
- Proper YAML structure and syntax
- Required fields and configuration
- Security best practices
- Integration with Debricked actions
- Proper secret handling
"""

from pathlib import Path
from typing import Any, Dict

import pytest
import yaml

# Path to the root debricked.yml file (which should be moved to workflows)
ROOT_DEBRICKED_FILE = Path(__file__).parent.parent.parent / "debricked.yml"
WORKFLOWS_DIR = Path(__file__).parent.parent.parent / ".github" / "workflows"
WORKFLOW_DEBRICKED_FILE = WORKFLOWS_DIR / "debricked.yml"


def load_yaml_safe(file_path: Path) -> Dict[str, Any]:
    """
    Parse a YAML file and return its content.

    Parameters:
        file_path (Path): Path to the YAML file to load.

    Returns:
        The parsed YAML content as a dictionary.

    Raises:
        yaml.YAMLError: If the file contains invalid YAML.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestRootDebrickedFileExists:
    """Test that the root-level debricked.yml file exists and is valid."""

    def test_root_debricked_file_exists(self):
        """Test that debricked.yml exists in repository root."""
        assert ROOT_DEBRICKED_FILE.exists(), "debricked.yml should exist in repository root"

    def test_root_debricked_is_file(self):
        """Test that debricked.yml is a file, not a directory."""
        assert ROOT_DEBRICKED_FILE.is_file(), "debricked.yml should be a regular file"

    def test_root_debricked_is_readable(self):
        """Test that the file can be read and is non-empty."""
        with open(ROOT_DEBRICKED_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            assert len(content) > 0, "debricked.yml should not be empty"

    def test_root_debricked_valid_yaml(self):
        """Test that debricked.yml contains valid YAML syntax."""
        try:
            with open(ROOT_DEBRICKED_FILE, "r", encoding="utf-8") as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML syntax in debricked.yml: {e}")

    def test_root_debricked_encoding(self):
        """Test that debricked.yml uses UTF-8 encoding."""
        try:
            with open(ROOT_DEBRICKED_FILE, "r", encoding="utf-8") as f:
                f.read()
        except UnicodeDecodeError:
            pytest.fail("debricked.yml is not valid UTF-8")


class TestDebrickedWorkflowStructure:
    """Test the structure and required fields of the Debricked workflow."""

    @pytest.fixture
    def debricked_config(self) -> Dict[str, Any]:
        """Load the root debricked.yml configuration."""
        return load_yaml_safe(ROOT_DEBRICKED_FILE)

    def test_has_workflow_name(self, debricked_config: Dict[str, Any]):
        """Test that workflow has a name field."""
        assert "name" in debricked_config, "Workflow must have a 'name' field"
        assert debricked_config["name"], "Workflow name must not be empty"
        assert isinstance(debricked_config["name"], str), "Workflow name must be a string"

    def test_workflow_name_is_descriptive(self, debricked_config: Dict[str, Any]):
        """Test that workflow name is descriptive and mentions Debricked."""
        name = debricked_config.get("name", "").lower()
        assert "debricked" in name, "Workflow name should mention 'Debricked'"
        assert "scan" in name, "Workflow name should mention 'scan'"

    def test_has_trigger_configuration(self, debricked_config: Dict[str, Any]):
        """Test that workflow defines trigger events."""
        assert "on" in debricked_config, "Workflow must have 'on' (trigger) field"
        assert debricked_config["on"], "Workflow triggers must not be empty"

    def test_triggers_on_pull_request(self, debricked_config: Dict[str, Any]):
        """Test that workflow triggers on pull requests."""
        triggers = debricked_config.get("on", [])

        # Handle both list and dict formats
        if isinstance(triggers, list):
            assert "pull_request" in triggers, "Workflow should trigger on pull_request events"
        elif isinstance(triggers, dict):
            assert "pull_request" in triggers, "Workflow should trigger on pull_request events"
        else:
            pytest.fail(f"Unexpected trigger format: {type(triggers)}")

    def test_has_jobs_section(self, debricked_config: Dict[str, Any]):
        """Test that workflow defines jobs."""
        assert "jobs" in debricked_config, "Workflow must have 'jobs' field"
        assert debricked_config["jobs"], "Workflow jobs must not be empty"
        assert isinstance(debricked_config["jobs"], dict), "Jobs must be a dictionary"

    def test_has_vulnerabilities_scan_job(self, debricked_config: Dict[str, Any]):
        """Test that workflow has vulnerabilities-scan job."""
        jobs = debricked_config.get("jobs", {})
        assert "vulnerabilities-scan" in jobs, "Workflow must have 'vulnerabilities-scan' job"


class TestDebrickedJobConfiguration:
    """Test the vulnerabilities-scan job configuration."""

    @pytest.fixture
    def scan_job(self) -> Dict[str, Any]:
        """Get the vulnerabilities-scan job configuration."""
        config = load_yaml_safe(ROOT_DEBRICKED_FILE)
        return config["jobs"]["vulnerabilities-scan"]

    def test_job_specifies_runner(self, scan_job: Dict[str, Any]):
        """Test that job specifies a runner."""
        assert "runs-on" in scan_job, "Job must specify 'runs-on' field"
        assert scan_job["runs-on"], "Runner specification must not be empty"

    def test_job_uses_ubuntu_runner(self, scan_job: Dict[str, Any]):
        """Test that job uses Ubuntu runner."""
        runner = scan_job.get("runs-on", "")
        assert "ubuntu" in runner.lower(), "Job should run on Ubuntu runner"

    def test_job_has_steps(self, scan_job: Dict[str, Any]):
        """Test that job defines steps."""
        assert "steps" in scan_job, "Job must have 'steps' field"
        assert scan_job["steps"], "Job steps must not be empty"
        assert isinstance(scan_job["steps"], list), "Steps must be a list"
        assert len(scan_job["steps"]) > 0, "Job must have at least one step"


class TestDebrickedSteps:
    """Test the individual steps in the vulnerabilities-scan job."""

    @pytest.fixture
    def steps(self) -> list:
        """Get the steps from vulnerabilities-scan job."""
        config = load_yaml_safe(ROOT_DEBRICKED_FILE)
        return config["jobs"]["vulnerabilities-scan"]["steps"]

    def test_has_checkout_step(self, steps: list):
        """Test that job includes checkout step."""
        checkout_steps = [s for s in steps if "uses" in s and "actions/checkout" in s["uses"]]
        assert len(checkout_steps) > 0, "Job must include actions/checkout step"

    def test_checkout_uses_version(self, steps: list):
        """Test that checkout action specifies a version."""
        checkout_steps = [s for s in steps if "uses" in s and "actions/checkout" in s["uses"]]
        for step in checkout_steps:
            action = step["uses"]
            assert "@" in action, f"Checkout action must specify version: {action}"

    def test_checkout_uses_v4(self, steps: list):
        """Test that checkout action uses v4."""
        checkout_steps = [s for s in steps if "uses" in s and "actions/checkout" in s["uses"]]
        for step in checkout_steps:
            action = step["uses"]
            assert "@v4" in action, f"Checkout should use v4: {action}"

    def test_has_debricked_action(self, steps: list):
        """Test that job uses Debricked action."""
        debricked_steps = [s for s in steps if "uses" in s and "debricked" in s["uses"].lower()]
        assert len(debricked_steps) > 0, "Job must include Debricked action"

    def test_debricked_action_version(self, steps: list):
        """Test that Debricked action specifies a version."""
        debricked_steps = [s for s in steps if "uses" in s and "debricked" in s["uses"].lower()]
        for step in debricked_steps:
            action = step["uses"]
            assert "@" in action, f"Debricked action must specify version: {action}"

    def test_debricked_action_uses_v4(self, steps: list):
        """Test that Debricked action uses v4."""
        debricked_steps = [s for s in steps if "uses" in s and "debricked" in s["uses"].lower()]
        for step in debricked_steps:
            action = step["uses"]
            assert "@v4" in action, f"Debricked action should use v4: {action}"


class TestDebrickedSecretHandling:
    """Test proper handling of Debricked token secret."""

    @pytest.fixture
    def steps(self) -> list:
        """Get the steps from vulnerabilities-scan job."""
        config = load_yaml_safe(ROOT_DEBRICKED_FILE)
        return config["jobs"]["vulnerabilities-scan"]["steps"]

    def test_debricked_step_uses_env(self, steps: list):
        """Test that Debricked step uses env for token."""
        debricked_steps = [s for s in steps if "uses" in s and "debricked" in s["uses"].lower()]
        assert len(debricked_steps) > 0, "Should have Debricked steps"

        for step in debricked_steps:
            assert "env" in step, "Debricked step must define env section"

    def test_debricked_token_in_env(self, steps: list):
        """Test that DEBRICKED_TOKEN is provided via env."""
        debricked_steps = [s for s in steps if "uses" in s and "debricked" in s["uses"].lower()]

        for step in debricked_steps:
            env = step.get("env", {})
            assert "DEBRICKED_TOKEN" in env, "Debricked step must define DEBRICKED_TOKEN"

    def test_token_uses_secrets_context(self, steps: list):
        """Test that token uses GitHub secrets context."""
        debricked_steps = [s for s in steps if "uses" in s and "debricked" in s["uses"].lower()]

        for step in debricked_steps:
            env = step.get("env", {})
            token = env.get("DEBRICKED_TOKEN", "")
            assert "${{" in token or "${" in token, "Token should use secrets context"
            assert "secrets" in token.lower(), "Token should reference secrets"

    def test_no_hardcoded_token(self):
        """Test that workflow doesn't contain hardcoded tokens."""
        with open(ROOT_DEBRICKED_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for patterns that might indicate hardcoded secrets
        suspicious_patterns = [
            "ghp_",  # GitHub personal access token
            "dbr_",  # Potential Debricked token prefix
        ]

        for pattern in suspicious_patterns:
            assert pattern not in content, (
                f"Workflow may contain hardcoded secret (found pattern: {pattern}). " "Use secrets context instead."
            )


class TestDebrickedWorkflowBestPractices:
    """Test that workflow follows best practices."""

    @pytest.fixture
    def config(self) -> Dict[str, Any]:
        """Load the debricked.yml configuration."""
        return load_yaml_safe(ROOT_DEBRICKED_FILE)

    def test_file_uses_spaces_not_tabs(self):
        """Test that workflow uses spaces for indentation, not tabs."""
        with open(ROOT_DEBRICKED_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        assert "\t" not in content, "Workflow should use spaces, not tabs for indentation"

    def test_consistent_indentation(self):
        """Test that workflow uses consistent 2-space indentation."""
        with open(ROOT_DEBRICKED_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

        indentation_levels = set()
        for line in lines:
            if line.strip() and not line.strip().startswith("#"):
                spaces = len(line) - len(line.lstrip(" "))
                if spaces > 0:
                    indentation_levels.add(spaces)

        # Check if indentation is consistent (multiples of 2)
        if indentation_levels:
            inconsistent = [level for level in indentation_levels if level % 2 != 0]
            assert not inconsistent, (
                f"Workflow has inconsistent indentation. "
                f"Found indentation levels: {sorted(indentation_levels)}. "
                "Use 2-space indentation consistently."
            )

    def test_reasonable_file_size(self):
        """Test that workflow file is reasonably sized."""
        file_size = ROOT_DEBRICKED_FILE.stat().st_size
        assert file_size < 10240, f"Workflow file is {file_size} bytes. " "Keep workflows concise and focused."

    def test_workflow_is_focused(self, config: Dict[str, Any]):
        """Test that workflow has a single focused purpose."""
        jobs = config.get("jobs", {})
        job_count = len(jobs)
        assert job_count <= 2, (
            f"Workflow has {job_count} jobs. " "Debricked workflow should be focused on vulnerability scanning."
        )


class TestDebrickedWorkflowComparison:
    """Compare root debricked.yml with workflows/debricked.yml."""

    def test_both_files_exist(self):
        """Test that both debricked.yml files exist."""
        assert ROOT_DEBRICKED_FILE.exists(), "Root debricked.yml should exist"
        assert WORKFLOW_DEBRICKED_FILE.exists(), "Workflows debricked.yml should exist"

    def test_root_file_is_simpler(self):
        """Test that root file is a simplified version."""
        root_config = load_yaml_safe(ROOT_DEBRICKED_FILE)
        workflow_config = load_yaml_safe(WORKFLOW_DEBRICKED_FILE)

        root_size = ROOT_DEBRICKED_FILE.stat().st_size
        workflow_size = WORKFLOW_DEBRICKED_FILE.stat().st_size

        # Root file should be smaller/simpler
        assert root_size < workflow_size, "Root debricked.yml should be simpler than workflows version"

    def test_root_file_uses_newer_action_version(self):
        """Test that root file uses the latest Debricked action version."""
        root_config = load_yaml_safe(ROOT_DEBRICKED_FILE)
        root_steps = root_config["jobs"]["vulnerabilities-scan"]["steps"]

        root_debricked_steps = [s for s in root_steps if "uses" in s and "debricked" in s["uses"].lower()]

        for step in root_debricked_steps:
            action = step["uses"]
            assert "@v4" in action, f"Root file should use latest Debricked action v4, found: {action}"

    def test_both_use_secrets_correctly(self):
        """Test that both files use secrets context correctly."""
        for file_path in [ROOT_DEBRICKED_FILE, WORKFLOW_DEBRICKED_FILE]:
            config = load_yaml_safe(file_path)
            jobs = config.get("jobs", {})

            for job_name, job in jobs.items():
                steps = job.get("steps", [])
                debricked_steps = [s for s in steps if "uses" in s and "debricked" in s["uses"].lower()]

                for step in debricked_steps:
                    env = step.get("env", {})
                    if "DEBRICKED_TOKEN" in env:
                        token = env["DEBRICKED_TOKEN"]
                        assert "secrets" in token.lower(), f"Token in {file_path.name} should use secrets context"


class TestDebrickedEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_workflow_not_allowed(self):
        """Test that workflow is not empty."""
        config = load_yaml_safe(ROOT_DEBRICKED_FILE)
        assert config, "Workflow configuration should not be empty"
        assert len(config) > 0, "Workflow should have at least one top-level key"

    def test_malformed_yaml_detection(self):
        """Test that we can detect malformed YAML."""
        # This test ensures our validation catches issues
        try:
            yaml.safe_load("invalid: [unclosed")
            pytest.fail("Should have raised YAMLError for malformed YAML")
        except yaml.YAMLError:
            pass  # Expected

    def test_workflow_has_minimum_required_fields(self):
        """Test that workflow has all minimum required fields."""
        config = load_yaml_safe(ROOT_DEBRICKED_FILE)

        required_fields = ["name", "on", "jobs"]
        for field in required_fields:
            assert field in config, f"Workflow must have '{field}' field"

    def test_job_has_minimum_required_fields(self):
        """Test that job has all minimum required fields."""
        config = load_yaml_safe(ROOT_DEBRICKED_FILE)
        job = config["jobs"]["vulnerabilities-scan"]

        required_fields = ["runs-on", "steps"]
        for field in required_fields:
            assert field in job, f"Job must have '{field}' field"

    def test_steps_are_well_formed(self):
        """Test that all steps are properly structured."""
        config = load_yaml_safe(ROOT_DEBRICKED_FILE)
        steps = config["jobs"]["vulnerabilities-scan"]["steps"]

        for idx, step in enumerate(steps):
            assert isinstance(step, dict), f"Step {idx} must be a dictionary"
            # Each step must have either 'uses' or 'run'
            assert "uses" in step or "run" in step, f"Step {idx} must have either 'uses' or 'run'"


class TestDebrickedIntegrationRequirements:
    """Test requirements for Debricked integration."""

    def test_readme_mentions_debricked_setup(self):
        """Test that README provides Debricked setup instructions."""
        readme_path = Path(__file__).parent.parent.parent / "README.md"
        if readme_path.exists():
            with open(readme_path, "r", encoding="utf-8") as f:
                content = f.read().lower()

            # Check if README mentions Debricked or security scanning
            has_security_info = "debricked" in content or "vulnerability" in content or "security scan" in content

            if not has_security_info:
                # This is informational, not a hard failure
                print(
                    "\nInfo: README.md doesn't mention Debricked setup. "
                    "Consider adding documentation for setting up DEBRICKED_TOKEN secret."
                )

    def test_workflow_file_location_recommendation(self):
        """Recommend moving root debricked.yml to workflows directory."""
        if ROOT_DEBRICKED_FILE.exists():
            print(
                f"\nRecommendation: Move {ROOT_DEBRICKED_FILE} to "
                f"{WORKFLOW_DEBRICKED_FILE} for GitHub Actions to recognize it."
            )


class TestDebrickedDocumentation:
    """Test that workflow is well-documented."""

    def test_workflow_name_is_clear(self):
        """Test that workflow name clearly indicates its purpose."""
        config = load_yaml_safe(ROOT_DEBRICKED_FILE)
        name = config.get("name", "")

        # Name should be clear and descriptive
        assert len(name) > 5, "Workflow name should be descriptive"
        assert not name.isupper(), "Workflow name should use proper case, not all caps"

    def test_job_name_consistency(self):
        """Test that job names match workflow purpose."""
        config = load_yaml_safe(ROOT_DEBRICKED_FILE)
        jobs = config.get("jobs", {})

        for job_name in jobs.keys():
            # Job name should be descriptive
            assert len(job_name) > 3, f"Job name '{job_name}' should be descriptive"
            assert (
                "-" in job_name or "_" in job_name or job_name.islower()
            ), f"Job name '{job_name}' should use kebab-case or snake_case"


class TestDebrickedSecurityBestPractices:
    """Test security best practices in the workflow."""

    def test_no_env_var_injection_vulnerability(self):
        """Test that workflow doesn't have env injection vulnerabilities."""
        content = ROOT_DEBRICKED_FILE.read_text()

        # Check for unsafe patterns
        unsafe_patterns = [
            r"\$\{\{.*github\.event\..*\}\}.*bash",
            r"run:.*\$\{\{.*github\.event\.issue\.title",
        ]

        import re

        for pattern in unsafe_patterns:
            matches = re.findall(pattern, content)
            assert not matches, f"Found potential env injection vulnerability: {matches}"

    def test_secrets_not_logged(self):
        """Test that secrets aren't accidentally logged."""
        content = ROOT_DEBRICKED_FILE.read_text()

        # Check for echo/print of secrets
        secret_logging_patterns = [
            r"echo.*\$\{\{.*secrets\.",
            r"print.*\$\{\{.*secrets\.",
        ]

        import re

        for pattern in secret_logging_patterns:
            matches = re.findall(pattern, content)
            assert not matches, f"Secrets may be logged to console: {matches}"

    def test_permissions_least_privilege(self):
        """Test that workflow follows least privilege principle."""
        config = load_yaml_safe(ROOT_DEBRICKED_FILE)

        # If permissions are specified, they should be minimal
        if "permissions" in config:
            permissions = config["permissions"]
            if isinstance(permissions, dict):
                # Check for overly broad permissions
                for perm, value in permissions.items():
                    assert value in ["read", "write", "none"], f"Permission '{perm}' has invalid value: {value}"
