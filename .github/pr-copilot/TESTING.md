# PR Copilot Testing Guide

Comprehensive testing documentation for the PR Copilot agent system.

## 📋 Test Coverage

The PR Copilot system has comprehensive test coverage across three main areas:

### 1. Unit Tests

Located in `tests/unit/`:

#### `test_pr_copilot_generate_status.py`
Tests for the status report generation script:
- ✅ CheckRunInfo dataclass creation
- ✅ PRStatus dataclass creation and immutability
- ✅ Fetching PR status from GitHub API
- ✅ Formatting task checklists (complete and incomplete)
- ✅ Formatting CI check sections
- ✅ Generating markdown reports
- ✅ Handling draft PRs
- ✅ Writing output to files and GitHub summaries

#### `test_pr_copilot_analyze_pr.py`
Tests for the PR analysis script:
- ✅ File categorization (Python, JavaScript, tests, workflows, configs, docs)
- ✅ Analyzing PR files (empty, small, large)
- ✅ Score calculation with thresholds
- ✅ Complexity assessment (low, medium, high risk)
- ✅ Large file penalty calculation
- ✅ Scope issue detection (long titles, multiple responsibilities, too many files)
- ✅ Related issue parsing
- ✅ Markdown report generation
- ✅ Configuration loading

#### `test_pr_copilot_suggest_fixes.py`
Tests for the fix suggestion parser:
- ✅ Extracting code suggestions (blocks and inline)
- ✅ Comment categorization (critical, bug, question, style, improvement)
- ✅ Actionable comment detection
- ✅ Parsing review comments
- ✅ Sorting by priority and date
- ✅ Generating fix proposals
- ✅ Handling multiple categories
- ✅ Long body truncation
- ✅ Configuration loading with defaults

### 2. Integration Tests

Located in `tests/integration/`:

#### `test_pr_copilot_workflow.py`
End-to-end workflow tests:
- ✅ Configuration file existence and validity
- ✅ Workflow file existence and validity
- ✅ Script file existence
- ✅ Requirements file validity
- ✅ Status generation integration
- ✅ PR analysis integration
- ✅ Fix suggestion integration
- ✅ Workflow triggers configuration
- ✅ Workflow jobs configuration
- ✅ Workflow permissions
- ✅ Agent settings validation
- ✅ Trigger settings validation
- ✅ Scope settings validation
- ✅ Auto-merge settings validation
- ✅ Documentation existence and content

### 3. Workflow Tests

The GitHub Actions workflow itself includes:
- ✅ Event trigger detection
- ✅ Concurrency control
- ✅ Welcome message posting
- ✅ Scope validation
- ✅ Status report generation
- ✅ Review comment handling
- ✅ Auto-merge eligibility checking
- ✅ Merge conflict detection

## 🚀 Running Tests

### Run All Tests

```bash
pytest tests/unit/test_pr_copilot_*.py tests/integration/test_pr_copilot_*.py -v
```

### Run Unit Tests Only

```bash
pytest tests/unit/test_pr_copilot_*.py -v
```

### Run Integration Tests Only

```bash
pytest tests/integration/test_pr_copilot_workflow.py -v
```

### Run Specific Test File

```bash
pytest tests/unit/test_pr_copilot_generate_status.py -v
```

### Run with Coverage

```bash
pytest tests/unit/test_pr_copilot_*.py --cov=.github/pr-copilot/scripts --cov-report=html
```

## 🧪 Test Fixtures

Common fixtures used across tests:

### `mock_github_client`
Mock GitHub API client for testing API interactions.

### `mock_pr`
Mock PR object with typical data (number, title, author, commits, files, etc.).

### `mock_reviews`
Mock review objects with different states (approved, changes requested, commented).

### `mock_check_runs`
Mock CI check run objects with various states (success, failure, pending).

### `mock_env_vars`
Mock environment variables required by scripts (GITHUB_TOKEN, PR_NUMBER, etc.).

## 📊 Test Scenarios

### Status Report Generation

**Scenario 1: Complete PR with all data**
- PR with commits, files, reviews, checks
- Expected: Full status report with all sections

**Scenario 2: Draft PR**
- PR marked as draft
- Expected: Draft indicator in report

**Scenario 3: PR with no checks**
- PR without CI checks configured
- Expected: "No checks configured" message

### PR Analysis

**Scenario 1: Low-risk PR**
- Few files, small changes, few commits
- Expected: Low complexity score, green indicator

**Scenario 2: Medium-risk PR**
- Moderate files, moderate changes
- Expected: Medium complexity score, yellow indicator

**Scenario 3: High-risk PR**
- Many files, large changes, many commits
- Expected: High complexity score, red indicator, recommendations

### Fix Suggestions

**Scenario 1: Critical security issue**
- Comment with "security vulnerability"
- Expected: Categorized as critical, priority 1

**Scenario 2: Style feedback**
- Comment about naming conventions
- Expected: Categorized as style, priority 3

**Scenario 3: Code suggestions**
- Comment with suggestion blocks
- Expected: Extracted and formatted code suggestions

## 🔍 Testing Best Practices

### 1. Mock External Dependencies
- Always mock GitHub API calls
- Use fixtures for consistent test data
- Avoid real API calls in tests

### 2. Test Behavior, Not Implementation
- Focus on what the function returns
- Don't test internal implementation details
- Test edge cases and error conditions

### 3. Keep Tests Independent
- Each test should run independently
- Don't rely on test execution order
- Clean up resources after tests

### 4. Use Descriptive Names
- Test names should describe what they test
- Use `test_<function>_<scenario>` pattern
- Include expected outcome in name

## 📝 Adding New Tests

When adding new functionality to PR Copilot:

1. **Write unit tests first** - Test individual functions
2. **Add integration tests** - Test component interactions
3. **Update this guide** - Document new test scenarios
4. **Run all tests** - Ensure nothing breaks
5. **Check coverage** - Aim for >80% coverage
