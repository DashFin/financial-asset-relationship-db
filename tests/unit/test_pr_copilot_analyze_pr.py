# pylint: disable=redefined-outer-name, unused-argument
"""
Unit tests for PR Copilot analyze_pr.py script.

Tests PR complexity analysis, scope validation, and risk assessment functionality.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".github" / "pr-copilot" / "scripts"))

from analyze_pr import (AnalysisData, analyze_pr_files, assess_complexity,
                        categorize_filename, find_related_issues,
                        find_scope_issues, generate_markdown, load_config)


@pytest.fixture
def mock_config():
    """Provide a mock configuration for tests."""
    return {
        "scope": {
            "warn_on_long_title": 80,
            "max_files_changed": 20,
            "max_total_changes": 500,
            "max_file_types_changed": 5,
        }
    }


@pytest.fixture
def mock_config_missing():
    """Mock configuration file that doesn't exist."""
    with patch("os.path.exists", return_value=False):
        yield


@pytest.fixture
def mock_config_valid():
    """Mock valid configuration file."""
    mock_config = {"scope": {"warn_on_long_title": 80}}
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", create=True):
            with patch("yaml.safe_load", return_value=mock_config):
                yield mock_config


@pytest.fixture
def mock_pr_low_risk():
    """Create a mock PR object for low-risk scenarios."""
    pr = Mock()
    pr.number = 1
    pr.user = Mock(login="testuser")
    pr.title = "Add new feature"
    pr.body = "This PR adds a new feature"
    return pr


@pytest.fixture
def mock_pr_data():
    """Provide mock PR data for tests."""
    return {
        "title": "Add new feature for user authentication",
        "body": "This PR implements user authentication. Fixes #123",
        "files": [
            {"filename": "src/auth.py", "additions": 50, "deletions": 10, "changes": 60},
            {"filename": "tests/test_auth.py", "additions": 30, "deletions": 5, "changes": 35},
        ],
        "commits": 3,
    }


@pytest.fixture
def mock_file_data():
    """Provide mock file analysis data."""
    return {
        "file_count": 5,
        "file_categories": {"python": 3, "test": 2},
        "total_additions": 100,
        "total_deletions": 20,
        "total_changes": 120,
        "large_files": [],
        "has_large_files": False,
    }


def test_categorize_filename():
    """Test file categorization logic."""
    assert categorize_filename("src/main.py") == "python"
    assert categorize_filename("tests/test_main.py") == "test"
    assert categorize_filename("README.md") == "documentation"
    assert categorize_filename(".github/workflows/ci.yml") == "workflow"
    assert categorize_filename("package.json") == "config"


def test_assess_complexity_low(mock_file_data):
    """Test complexity assessment for simple changes."""
    result = assess_complexity(mock_file_data, 2)
    assert result[1] == "Low"
    assert result[0] < 40


def test_assess_complexity_medium():
    """Test complexity assessment for moderate changes."""
    file_data = {
        "file_count": 15,
        "total_changes": 600,
        "large_files": [],
        "has_large_files": False,
    }
    result = assess_complexity(file_data, 8)
    assert result[1] == "Medium"
    assert 40 <= result[0] < 70


def test_assess_complexity_high():
    """Test complexity assessment for complex changes."""
    file_data = {
        "file_count": 30,
        "total_changes": 1500,
        "large_files": [{"filename": "large.py", "changes": 800}],
        "has_large_files": True,
    }
    result = assess_complexity(file_data, 25)
    assert result[1] == "High"
    assert result[0] >= 70


def test_find_scope_issues_long_title(mock_config, mock_file_data):
    """Test detection of overly long PR titles."""
    long_title = "A" * 100
    issues = find_scope_issues(long_title, mock_file_data, mock_config)
    assert any("too long" in issue.lower() for issue in issues)


def test_find_scope_issues_many_files(mock_config):
    """Test detection of PRs with too many files."""
    file_data = {
        "file_count": 25,
        "total_changes": 100,
        "file_categories": {"python": 25},
    }
    issues = find_scope_issues("Short title", file_data, mock_config)
    assert any("many files" in issue.lower() for issue in issues)


def test_find_scope_issues_many_lines(mock_config):
    """Test detection of PRs with too many line changes."""
    file_data = {
        "file_count": 5,
        "total_changes": 600,
        "file_categories": {"python": 5},
    }
    issues = find_scope_issues("Short title", file_data, mock_config)
    assert any("changeset" in issue.lower() for issue in issues)


def test_find_related_issues():
    """Test extraction of related issue numbers from PR body."""
    body = "This PR fixes #123 and resolves #456. Closes #789"
    repo_url = "https://github.com/test/repo"
    issues = find_related_issues(body, repo_url)
    issue_numbers = [issue["number"] for issue in issues]
    assert "123" in issue_numbers
    assert "456" in issue_numbers
    assert "789" in issue_numbers


def test_analyze_pr_files():
    """Test PR file analysis."""
    mock_files = [
        Mock(filename="src/auth.py", additions=50, deletions=10),
        Mock(filename="tests/test_auth.py", additions=30, deletions=5),
    ]
    result = analyze_pr_files(mock_files)
    assert result["file_count"] == 2
    assert result["total_additions"] == 80
    assert result["total_deletions"] == 15
    assert result["total_changes"] == 95


def test_load_config_with_file():
    """Test loading configuration from a file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write("scope:\n  warn_on_long_title: 100\n")
        config_path = f.name

    try:
        with patch("analyze_pr.CONFIG_PATH", config_path):
            config = load_config()
            assert "scope" in config
            assert config["scope"]["warn_on_long_title"] == 100
    finally:
        os.unlink(config_path)


def test_load_config_default():
    """Test loading default configuration when file doesn't exist."""
    with patch("os.path.exists", return_value=False):
        config = load_config()
        assert isinstance(config, dict)


def test_generate_markdown(mock_pr_low_risk, mock_file_data):
    """Test markdown report generation."""
    analysis = AnalysisData(
        file_analysis=mock_file_data,
        complexity_score=25,
        risk_level="Low",
        scope_issues=[],
        related_issues=[{"number": "123", "url": "https://github.com/test/repo/issues/123"}],
        commit_count=3
    )

    markdown = generate_markdown(mock_pr_low_risk, analysis)
    assert "PR Analysis Report" in markdown
    assert "Low" in markdown
    assert "#1" in markdown
    assert isinstance(markdown, str)
    assert len(markdown) > 0


def test_find_scope_issues_multiple_responsibilities(mock_config, mock_file_data):
    """Test detection of titles suggesting multiple responsibilities."""
    title = "Add feature and fix bug"
    issues = find_scope_issues(title, mock_file_data, mock_config)
    assert any("multiple responsibilities" in issue.lower() for issue in issues)


def test_analyze_pr_files_with_large_files():
    """Test PR file analysis with large files."""
    mock_files = [
        Mock(filename="src/large.py", additions=600, deletions=100),
        Mock(filename="src/small.py", additions=10, deletions=5),
    ]
    result = analyze_pr_files(mock_files)
    assert result["has_large_files"] is True
    assert len(result["large_files"]) == 1
    assert result["large_files"][0]["filename"] == "src/large.py"


def test_categorize_filename_workflow():
    """Test that workflow files are correctly categorized."""
    assert categorize_filename(".github/workflows/test.yml") == "workflow"
    assert categorize_filename(".github/workflows/ci.yaml") == "workflow"


def test_find_scope_issues_high_context_switching(mock_config):
    """Test detection of high context switching."""
    file_data = {
        "file_count": 10,
        "total_changes": 200,
        "file_categories": {
            "python": 2,
            "javascript": 2,
            "config": 2,
            "documentation": 2,
            "test": 2,
            "style": 2,
        },
    }
    issues = find_scope_issues("Short title", file_data, mock_config)
    assert any("context switching" in issue.lower() for issue in issues)
