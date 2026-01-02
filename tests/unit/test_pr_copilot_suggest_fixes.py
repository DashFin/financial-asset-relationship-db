"""
Unit tests for PR Copilot suggest_fixes.py script.

Tests review comment parsing, categorization, and fix proposal generation.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".github" / "pr-copilot" / "scripts"))

from suggest_fixes import (
    categorize_comment,
    extract_code_suggestions,
    generate_fix_proposals,
    is_actionable,
    load_config,
    parse_review_comments,
)


def test_extract_code_suggestions_with_suggestion_block():
    """Test extracting code suggestions from suggestion blocks."""
    comment = """
    Please change this:
    ```suggestion
    def fixed_function():
        return True
    ```
    """

    suggestions = extract_code_suggestions(comment)

    assert len(suggestions) == 1
    assert suggestions[0]["type"] == "code_suggestion"
    assert "def fixed_function()" in suggestions[0]["content"]


def test_extract_code_suggestions_inline():
    """Test extracting inline code suggestions."""
    comment = "You should use `const` instead of `var` here."

    suggestions = extract_code_suggestions(comment)

    assert len(suggestions) == 1
    assert suggestions[0]["type"] == "inline_suggestion"
    assert suggestions[0]["content"] == "const"


def test_extract_code_suggestions_multiple():
    """Test extracting multiple code suggestions."""
    comment = """
    Change to `async` and replace with `await fetch()`
    ```suggestion
    async function getData() {
        return await fetch();
    }
    ```
    """

    suggestions = extract_code_suggestions(comment)

    assert len(suggestions) >= 2


def test_extract_code_suggestions_none():
    """Test extracting code suggestions when none exist."""
    comment = "This looks good to me!"

    suggestions = extract_code_suggestions(comment)

    assert len(suggestions) == 0


def test_categorize_comment_critical():
    """Test categorizing critical security comments."""
    comment = "This has a critical security vulnerability that needs immediate attention"

    category, priority = categorize_comment(comment)

    assert category == "critical"
    assert priority == 1


def test_categorize_comment_bug():
    """Test categorizing bug-related comments."""
    comment = "This code has a bug that causes the function to fail"

    category, priority = categorize_comment(comment)

    assert category == "bug"
    assert priority == 1


def test_categorize_comment_question():
    """Test categorizing question comments."""
    comment = "Why did you choose this approach? Can you explain?"

    category, priority = categorize_comment(comment)

    assert category == "question"
    assert priority == 3


def test_categorize_comment_style():
    """Test categorizing style-related comments."""
    comment = "Please follow the naming convention for this variable"

    category, priority = categorize_comment(comment)

    assert category == "style"
    assert priority == 3


def test_categorize_comment_improvement():
    """Test categorizing improvement suggestions."""
    comment = "Consider refactoring this to improve performance"

    category, priority = categorize_comment(comment)

    assert category == "improvement"
    assert priority == 2


def test_categorize_comment_default():
    """Test default categorization for generic comments."""
    comment = "This could be better"

    category, priority = categorize_comment(comment)

    assert category == "improvement"
    assert priority == 2


def test_is_actionable_with_keywords():
    """Test actionable detection with configured keywords."""
    keywords = ["please", "fix", "change", "update"]

    assert is_actionable("Please fix this issue", keywords) is True
    assert is_actionable("You should change this", keywords) is True
    assert is_actionable("Update the documentation", keywords) is True


def test_is_actionable_without_keywords():
    """Test non-actionable comments."""
    keywords = ["please", "fix", "change", "update"]

    assert is_actionable("Looks good!", keywords) is False
    assert is_actionable("LGTM", keywords) is False
    assert is_actionable("Nice work", keywords) is False


def test_is_actionable_case_insensitive():
    """Test that actionable detection is case-insensitive."""
    keywords = ["please", "fix"]

    assert is_actionable("PLEASE FIX THIS", keywords) is True
    assert is_actionable("Please Fix This", keywords) is True


def test_parse_review_comments_empty():
    """Test parsing review comments when none exist."""
    mock_pr = Mock()
    mock_pr.get_review_comments.return_value = []
    mock_pr.get_reviews.return_value = []

    keywords = ["please", "fix"]
    items = parse_review_comments(mock_pr, keywords)

    assert len(items) == 0


def test_parse_review_comments_file_level():
    """Test parsing file-level review comments."""
    mock_comment = Mock()
    mock_comment.id = 1
    mock_comment.user.login = "reviewer"
    mock_comment.body = "Please fix this typo"
    mock_comment.path = "main.py"
    mock_comment.original_line = 42
    mock_comment.html_url = "https://github.com/test/repo/pull/1#discussion_r1"
    mock_comment.created_at = datetime(2024, 1, 1)

    mock_pr = Mock()
    mock_pr.get_review_comments.return_value = [mock_comment]
    mock_pr.get_reviews.return_value = []

    keywords = ["please", "fix"]
    items = parse_review_comments(mock_pr, keywords)

    assert len(items) == 1
    assert items[0]["author"] == "reviewer"
    assert items[0]["body"] == "Please fix this typo"
    assert items[0]["file"] == "main.py"
    assert items[0]["line"] == 42


def test_parse_review_comments_changes_requested():
    """Test parsing review-level comments with changes requested."""
    mock_review = Mock()
    mock_review.id = 2
    mock_review.user.login = "maintainer"
    mock_review.body = "Please update the tests"
    mock_review.state = "CHANGES_REQUESTED"
    mock_review.html_url = "https://github.com/test/repo/pull/1#pullrequestreview-2"
    mock_review.submitted_at = datetime(2024, 1, 2)

    mock_pr = Mock()
    mock_pr.get_review_comments.return_value = []
    mock_pr.get_reviews.return_value = [mock_review]

    keywords = ["please", "update"]
    items = parse_review_comments(mock_pr, keywords)

    assert len(items) == 1
    assert items[0]["author"] == "maintainer"
    assert items[0]["body"] == "Please update the tests"


def test_parse_review_comments_approved_ignored():
    """Test that approved reviews without actionable keywords are ignored."""
    mock_review = Mock()
    mock_review.id = 3
    mock_review.user.login = "approver"
    mock_review.body = "Looks good to me!"
    mock_review.state = "APPROVED"
    mock_review.html_url = "https://github.com/test/repo/pull/1#pullrequestreview-3"
    mock_review.submitted_at = datetime(2024, 1, 3)

    mock_pr = Mock()
    mock_pr.get_review_comments.return_value = []
    mock_pr.get_reviews.return_value = [mock_review]

    keywords = ["please", "fix"]
    items = parse_review_comments(mock_pr, keywords)

    assert len(items) == 0


def test_parse_review_comments_sorting():
    """Test that comments are sorted by priority and date."""
    comment1 = Mock()
    comment1.id = 1
    comment1.user.login = "user1"
    comment1.body = "Please fix this bug"
    comment1.path = "file.py"
    comment1.original_line = 10
    comment1.html_url = "url1"
    comment1.created_at = datetime(2024, 1, 2)

    comment2 = Mock()
    comment2.id = 2
    comment2.user.login = "user2"
    comment2.body = "Consider improving this"
    comment2.path = "file.py"
    comment2.original_line = 20
    comment2.html_url = "url2"
    comment2.created_at = datetime(2024, 1, 1)

    mock_pr = Mock()
    mock_pr.get_review_comments.return_value = [comment1, comment2]
    mock_pr.get_reviews.return_value = []

    keywords = ["please", "fix", "consider"]
    items = parse_review_comments(mock_pr, keywords)

    assert len(items) == 2
    assert items[0]["body"] == "Please fix this bug"
    assert items[1]["body"] == "Consider improving this"


def test_generate_fix_proposals_empty():
    """Test generating fix proposals with no actionable items."""
    proposals = generate_fix_proposals([])

    assert "No actionable items found" in proposals


def test_generate_fix_proposals_single_item():
    """Test generating fix proposals with single item."""
    items = [
        {
            "id": 1,
            "author": "reviewer",
            "body": "Please fix the typo in line 10",
            "category": "style",
            "priority": 3,
            "file": "main.py",
            "line": 10,
            "code_suggestions": [],
            "url": "https://github.com/test/repo/pull/1#discussion_r1",
            "created_at": datetime(2024, 1, 1),
        }
    ]

    proposals = generate_fix_proposals(items)

    assert "🔧 **Fix Proposals from Review Comments**" in proposals
    assert "🎨 Style (1)" in proposals
    assert "@reviewer" in proposals
    assert "Please fix the typo" in proposals
    assert "**Total Actionable Items:** 1" in proposals


def test_generate_fix_proposals_multiple_categories():
    """Test generating fix proposals with multiple categories."""
    items = [
        {
            "id": 1,
            "author": "user1",
            "body": "Critical security issue here",
            "category": "critical",
            "priority": 1,
            "file": None,
            "line": None,
            "code_suggestions": [],
            "url": "url1",
            "created_at": datetime(2024, 1, 1),
        },
        {
            "id": 2,
            "author": "user2",
            "body": "This has a bug",
            "category": "bug",
            "priority": 1,
            "file": "test.py",
            "line": 5,
            "code_suggestions": [],
            "url": "url2",
            "created_at": datetime(2024, 1, 2),
        },
    ]

    proposals = generate_fix_proposals(items)

    assert "🚨 Critical (1)" in proposals
    assert "🐛 Bug (1)" in proposals
    assert "**Total Actionable Items:** 2" in proposals
    assert "⚠️ **Priority:** Address critical issues and bugs first" in proposals


def test_load_config_with_defaults():
    """Test loading config with default values when file not found."""
    with patch("builtins.open", side_effect=FileNotFoundError):
        config = load_config()

        assert "review_handling" in config
        assert "actionable_keywords" in config["review_handling"]
        assert "please" in config["review_handling"]["actionable_keywords"]


def test_load_config_from_file():
    """Test loading config from file."""
    mock_config = {"review_handling": {"actionable_keywords": ["custom", "keywords"]}}

    with patch("builtins.open", create=True):
        with patch("yaml.safe_load", return_value=mock_config):
            config = load_config()

            assert config == mock_config
