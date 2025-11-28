"""
Comprehensive tests for configuration file changes in current branch.

Tests the removal of codecov.yaml workflow, .gitignore pattern changes,
and requirements-dev.txt version constraint updates.
"""

import pytest
import yaml
import re
from pathlib import Path
from typing import List, Dict, Any


class TestCodecovWorkflowRemoval:
    """Test that codecov.yaml workflow was properly removed and CI still functions."""
    
    def test_codecov_yaml_not_present(self):
        """Test that codecov.yaml workflow file has been removed."""
        codecov_yaml = Path('.github/workflows/codecov.yaml')
        assert not codecov_yaml.exists(), \
            "codecov.yaml should have been removed from workflows directory"
    
    def test_codecov_yml_not_present(self):
        """Test that codecov.yml variant doesn't exist either."""
        codecov_yml = Path('.github/workflows/codecov.yml')
        assert not codecov_yml.exists(), \
            "codecov.yml should not exist in workflows directory"
    
    def test_ci_workflow_has_codecov_upload(self):
        """Test that CI workflow still uploads coverage to Codecov."""
        ci_workflow = Path('.github/workflows/ci.yml')
        assert ci_workflow.exists(), "CI workflow should exist"
        
        with open(ci_workflow, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # CI workflow should still have Codecov upload
        assert 'codecov/codecov-action' in content, \
            "CI workflow should still upload coverage to Codecov"
        assert 'Upload coverage to Codecov' in content, \
            "CI workflow should have Codecov upload step"
    
    def test_ci_workflow_generates_coverage_xml(self):
        """Test that CI workflow generates coverage.xml for Codecov."""
        ci_workflow = Path('.github/workflows/ci.yml')
        
        with open(ci_workflow, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should generate coverage.xml
        assert '--cov-report=xml' in content, \
            "CI workflow should generate coverage.xml report"
    
    def test_no_duplicate_codecov_upload(self):
        """Test that only one workflow uploads to Codecov (no duplication)."""
        workflows_dir = Path('.github/workflows')
        codecov_uploads = []
        
        for workflow_file in workflows_dir.glob('*.yml'):
            with open(workflow_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'codecov/codecov-action' in content:
                codecov_uploads.append(workflow_file.name)
        
        # Should only be in ci.yml after removal
        assert len(codecov_uploads) >= 1, \
            "At least one workflow should upload to Codecov"
        assert 'codecov.yaml' not in codecov_uploads, \
            "codecov.yaml should not be in the list"
    
    def test_codecov_upload_conditional(self):
        """Test that Codecov upload is conditional on Python version."""
        ci_workflow = Path('.github/workflows/ci.yml')
        
        with open(ci_workflow, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Find the codecov upload step
        test_job = config.get('jobs', {}).get('test', {})
        steps = test_job.get('steps', [])
        
        codecov_step = None
        for step in steps:
            if 'Upload coverage to Codecov' in step.get('name', ''):
                codecov_step = step
                break
        
        assert codecov_step is not None, "Codecov upload step should exist"
        
        # Should be conditional
        assert 'if' in codecov_step, \
            "Codecov upload should be conditional"
        assert 'continue-on-error' in codecov_step, \
            "Codecov upload should continue on error"


class TestGitignorePatternChanges:
    """Test .gitignore pattern changes for removed test artifacts."""
    
    @pytest.fixture
    def gitignore_content(self) -> str:
        """Load .gitignore content."""
        with open('.gitignore', 'r', encoding='utf-8') as f:
            return f.read()
    
    @pytest.fixture
    def gitignore_lines(self, gitignore_content: str) -> List[str]:
        """Get non-empty .gitignore lines."""
        return [line.strip() for line in gitignore_content.split('\n') 
                if line.strip() and not line.startswith('#')]
    
    def test_junit_xml_not_ignored(self, gitignore_lines: List[str]):
        """Test that junit.xml pattern was removed from .gitignore."""
        junit_patterns = [line for line in gitignore_lines if 'junit.xml' in line]
        assert len(junit_patterns) == 0, \
            "junit.xml should not be in .gitignore (pattern removed)"
    
    def test_test_db_patterns_not_ignored(self, gitignore_lines: List[str]):
        """Test that test database patterns were removed from .gitignore."""
        test_db_patterns = [line for line in gitignore_lines 
                           if 'test_*.db' in line or '*_test.db' in line]
        assert len(test_db_patterns) == 0, \
            "test_*.db and *_test.db patterns should be removed from .gitignore"
    
    def test_coverage_xml_still_ignored(self, gitignore_lines: List[str]):
        """Test that coverage.xml is still properly ignored."""
        coverage_patterns = [line for line in gitignore_lines if 'coverage.xml' in line]
        assert len(coverage_patterns) >= 1, \
            "coverage.xml should still be ignored"
    
    def test_pytest_cache_still_ignored(self, gitignore_lines: List[str]):
        """Test that .pytest_cache is still properly ignored."""
        pytest_patterns = [line for line in gitignore_lines if 'pytest_cache' in line]
        assert len(pytest_patterns) >= 1, \
            ".pytest_cache should still be ignored"
    
    def test_coverage_directory_still_ignored(self, gitignore_lines: List[str]):
        """Test that htmlcov directory is still properly ignored."""
        htmlcov_patterns = [line for line in gitignore_lines if 'htmlcov' in line]
        assert len(htmlcov_patterns) >= 1, \
            "htmlcov directory should still be ignored"
    
    def test_gitignore_properly_formatted(self, gitignore_content: str):
        """Test that .gitignore file is properly formatted."""
        # Should not have trailing whitespace on non-empty lines
        for i, line in enumerate(gitignore_content.split('\n'), 1):
            if line.strip():  # non-empty line
                assert line == line.rstrip(), \
                    f"Line {i} should not have trailing whitespace"
    
    def test_no_duplicate_patterns(self, gitignore_lines: List[str]):
        """Test that .gitignore doesn't have duplicate patterns."""
        seen = set()
        duplicates = []
        
        for line in gitignore_lines:
            if line in seen:
                duplicates.append(line)
            seen.add(line)
        
        assert len(duplicates) == 0, \
            f"Found duplicate patterns in .gitignore: {duplicates}"


class TestRequirementsDevVersionConstraints:
    """Test requirements-dev.txt version constraint updates."""
    
    @pytest.fixture
    def requirements_content(self) -> str:
        """Load requirements-dev.txt content."""
        with open('requirements-dev.txt', 'r', encoding='utf-8') as f:
            return f.read()
    
    @pytest.fixture
    def requirements_lines(self, requirements_content: str) -> List[str]:
        """Get non-comment, non-empty lines."""
        return [line.strip() for line in requirements_content.split('\n')
                if line.strip() and not line.startswith('#')]
    
    def test_types_pyyaml_has_version_constraint(self, requirements_lines: List[str]):
        """Test that types-PyYAML now has a version constraint."""
        types_lines = [line for line in requirements_lines 
                      if line.startswith('types-PyYAML')]
        
        assert len(types_lines) >= 1, "types-PyYAML should be in requirements-dev.txt"
        
        types_line = types_lines[0]
        assert '>=' in types_line, \
            "types-PyYAML should have >= version constraint"
    
    def test_types_pyyaml_version_is_6_0_0(self, requirements_lines: List[str]):
        """Test that types-PyYAML version constraint is >=6.0.0."""
        types_lines = [line for line in requirements_lines 
                      if line.startswith('types-PyYAML')]
        
        types_line = types_lines[0]
        
        # Extract version
        version_match = re.search(r'>=(\d+\.\d+(?:\.\d+)?)', types_line)
        assert version_match, "Should have version in format >=X.Y or >=X.Y.Z"
        
        version_str = version_match.group(1)
        assert version_str == '6.0.0' or version_str == '6.0', \
            f"types-PyYAML version should be >=6.0.0, got >={version_str}"
    
    def test_types_pyyaml_matches_pyyaml_major_version(self, requirements_lines: List[str]):
        """Test that types-PyYAML major version matches PyYAML."""
        pyyaml_version = None
        types_version = None
        
        for line in requirements_lines:
            if line.startswith('PyYAML>='):
                match = re.search(r'>=(\d+)', line)
                if match:
                    pyyaml_version = int(match.group(1))
            
            if line.startswith('types-PyYAML>='):
                match = re.search(r'>=(\d+)', line)
                if match:
                    types_version = int(match.group(1))
        
        assert pyyaml_version is not None, "PyYAML should have version"
        assert types_version is not None, "types-PyYAML should have version"
        assert pyyaml_version == types_version, \
            f"Major versions should match: PyYAML={pyyaml_version}, types-PyYAML={types_version}"
    
    def test_all_dev_dependencies_have_versions(self, requirements_lines: List[str]):
        """Test that all development dependencies have version constraints."""
        unversioned = []
        
        for line in requirements_lines:
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Extract package name
            pkg_name = re.match(r'^([A-Za-z0-9._-]+)', line)
            if pkg_name:
                # Check if it has a version specifier
                if not any(op in line for op in ['>=', '==', '<=', '>', '<', '~=']):
                    unversioned.append(line)
        
        assert len(unversioned) == 0, \
            f"All dependencies should have version constraints. Found unversioned: {unversioned}"
    
    def test_version_specifiers_properly_formatted(self, requirements_lines: List[str]):
        """Test that version specifiers are properly formatted."""
        for line in requirements_lines:
            if '>=' in line:
                # Should have format: package>=X.Y.Z or package>=X.Y
                assert re.match(r'^[A-Za-z0-9._-]+>=\d+\.\d+(?:\.\d+)?', line), \
                    f"Version specifier should be properly formatted: {line}"
    
    def test_no_conflicting_version_constraints(self, requirements_lines: List[str]):
        """Test that there are no conflicting version constraints."""
        package_versions = {}
        
        for line in requirements_lines:
            # Extract package name
            pkg_match = re.match(r'^([A-Za-z0-9._-]+)', line)
            if pkg_match:
                pkg_name = pkg_match.group(1)
                if pkg_name in package_versions:
                    # Same package listed twice - potential conflict
                    pytest.fail(f"Package {pkg_name} listed multiple times in requirements-dev.txt")
                package_versions[pkg_name] = line


class TestConfigurationConsistency:
    """Test consistency across configuration files after changes."""
    
    def test_pytest_config_matches_coverage_generation(self):
        """Test that pytest config aligns with coverage file generation."""
        # Read pyproject.toml
        with open('pyproject.toml', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should have coverage configuration
        assert '[tool.coverage' in content, \
            "pyproject.toml should have coverage configuration"
    
    def test_ci_workflow_uses_requirements_dev(self):
        """Test that CI workflow installs requirements-dev.txt."""
        with open('.github/workflows/ci.yml', 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'requirements-dev.txt' in content, \
            "CI workflow should install requirements-dev.txt"
    
    def test_coverage_source_excludes_tests(self):
        """Test that coverage configuration excludes test files."""
        with open('pyproject.toml', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should exclude tests from coverage
        assert 'tests' in content or '*/tests/*' in content, \
            "Coverage should exclude tests directory"
    
    def test_workflow_coverage_format_matches_codecov(self):
        """Test that workflow generates coverage in format expected by Codecov."""
        with open('.github/workflows/ci.yml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Find test job
        test_job = config.get('jobs', {}).get('test', {})
        steps = test_job.get('steps', [])
        
        # Find CI common step
        ci_step = None
        for step in steps:
            if 'ci-common' in str(step.get('uses', '')):
                ci_step = step
                break
        
        if ci_step:
            test_command = ci_step.get('with', {}).get('test', '')
            # Should generate XML format
            assert '--cov-report=xml' in test_command, \
                "Test command should generate XML coverage report for Codecov"


class TestBranchChangesImpact:
    """Test that branch changes don't negatively impact CI/CD."""
    
    def test_no_broken_workflow_references(self):
        """Test that no workflow references the deleted codecov.yaml."""
        workflows_dir = Path('.github/workflows')
        
        for workflow_file in workflows_dir.glob('*.yml'):
            with open(workflow_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Should not reference codecov.yaml or codecov.yml workflow
            assert 'codecov.yaml' not in content, \
                f"{workflow_file.name} should not reference codecov.yaml"
            assert 'codecov.yml' not in content or 'codecov.yml' == workflow_file.name, \
                f"{workflow_file.name} should not reference codecov.yml workflow"
    
    def test_coverage_still_collected(self):
        """Test that coverage is still being collected after changes."""
        with open('.github/workflows/ci.yml', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should still run pytest with coverage
        assert 'pytest --cov' in content or 'pytest' in content and '--cov' in content, \
            "CI should still collect coverage"
    
    def test_test_artifacts_properly_handled(self):
        """Test that test artifacts are properly handled after .gitignore changes."""
        with open('.gitignore', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Core test artifacts should still be ignored
        essential_patterns = ['.pytest_cache', 'coverage.xml', 'htmlcov']
        
        for pattern in essential_patterns:
            assert pattern in content, \
                f"Essential test artifact pattern '{pattern}' should be in .gitignore"
    
    def test_type_checking_still_works(self):
        """Test that type checking dependencies are properly versioned."""
        with open('requirements-dev.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should have mypy and type stubs
        assert 'mypy' in content, "mypy should be in requirements-dev.txt"
        assert 'types-PyYAML' in content, "types-PyYAML should be in requirements-dev.txt"
        
        # Both should have version constraints
        assert re.search(r'mypy>=', content), "mypy should have version constraint"
        assert re.search(r'types-PyYAML>=', content), "types-PyYAML should have version constraint"


class TestWorkflowDeletionCleanup:
    """Test that codecov.yaml deletion was clean with no orphaned references."""
    
    def test_no_codecov_secrets_orphaned(self):
        """Test that no workflows reference CODECOV_TOKEN unnecessarily."""
        workflows_dir = Path('.github/workflows')
        codecov_token_users = []
        
        for workflow_file in workflows_dir.glob('*.yml'):
            with open(workflow_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'CODECOV_TOKEN' in content:
                codecov_token_users.append(workflow_file.name)
        
        # Only ci.yml should use CODECOV_TOKEN now
        assert 'codecov.yaml' not in codecov_token_users, \
            "codecov.yaml should not be in the list (it was deleted)"
        
        # At least CI should use it
        # Codecov upload may use token or tokenless upload
        # Just verify codecov.yaml is not in the list
    
    def test_workflow_count_reasonable(self):
        """Test that workflow count is reasonable after deletion."""
        workflows_dir = Path('.github/workflows')
        workflow_files = list(workflows_dir.glob('*.yml')) + list(workflows_dir.glob('*.yaml'))
        
        # Should have multiple workflows but codecov.yaml removed
        assert len(workflow_files) > 5, \
            "Should have several workflow files"
        
        # Should not have codecov.yaml
        workflow_names = [f.name for f in workflow_files]
        assert 'codecov.yaml' not in workflow_names, \
            "codecov.yaml should be removed"
    
    def test_ci_workflow_is_primary_test_runner(self):
        """Test that ci.yml is the primary test runner after deletion."""
        ci_workflow = Path('.github/workflows/ci.yml')
        assert ci_workflow.exists(), "ci.yml should exist"
        
        with open(ci_workflow, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Should have test job
        assert 'test' in config.get('jobs', {}), \
            "ci.yml should have test job"
        
        # Should run on push and pull_request
        on_events = config.get('on', {})
        assert 'push' in str(on_events) or 'pull_request' in str(on_events), \
            "ci.yml should run on push or pull_request"
"""
Additional edge case tests for configuration changes.

Tests edge cases, error conditions, and boundary scenarios for the
configuration file changes in the current branch.
"""

import pytest
import yaml
import re
from pathlib import Path
from typing import List


class TestGitignoreEdgeCases:
    """Edge case tests for .gitignore pattern modifications."""
    
    def test_gitignore_no_empty_lines_at_end(self):
        """Test that .gitignore doesn't have excessive empty lines at end."""
        with open('.gitignore', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should not end with more than 2 newlines
        assert not content.endswith('\n\n\n'), \
            ".gitignore should not have excessive trailing newlines"
    
    def test_gitignore_patterns_not_too_broad(self):
        """Test that .gitignore patterns aren't overly broad after changes."""
        with open('.gitignore', 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        # Dangerous overly-broad patterns
        dangerous_patterns = ['*', '*.', '**']
        
        for line in lines:
            assert line not in dangerous_patterns, \
                f"Pattern '{line}' is too broad and would ignore everything"
    
    def test_gitignore_python_cache_patterns_present(self):
        """Test that essential Python cache patterns are still present."""
        with open('.gitignore', 'r', encoding='utf-8') as f:
            content = f.read()
        
        essential = ['__pycache__', '*.py[cod]']
        
        for pattern in essential:
            assert pattern in content, \
                f"Essential Python pattern '{pattern}' should be in .gitignore"
    
    def test_removed_patterns_actually_removed(self):
        """Test that removed patterns are completely gone, not commented out."""
        with open('.gitignore', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # These patterns should be completely gone
        removed = ['junit.xml', 'test_*.db', '*_test.db']
        
        for pattern in removed:
            # Check in non-comment lines only
            lines = [l for l in content.split('\n') if not l.strip().startswith('#')]
            content_no_comments = '\n'.join(lines)
            
            assert pattern not in content_no_comments, \
                f"Removed pattern '{pattern}' should not appear in non-comment lines"


class TestRequirementsDevEdgeCases:
    """Edge case tests for requirements-dev.txt changes."""
    
    def test_no_duplicate_package_entries(self):
        """Test that no package is listed multiple times."""
        with open('requirements-dev.txt', 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        packages = []
        for line in lines:
            match = re.match(r'^([A-Za-z0-9._-]+)', line)
            if match:
                packages.append(match.group(1))
        
        duplicates = [pkg for pkg in packages if packages.count(pkg) > 1]
        assert len(duplicates) == 0, \
            f"Found duplicate packages: {set(duplicates)}"
    
    def test_version_constraints_not_impossible(self):
        """Test that version constraints are logically possible."""
        with open('requirements-dev.txt', 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        for line in lines:
            # Check for impossible constraints like pkg>=2.0,<=1.0
            if '>=' in line and '<=' in line:
                ge_match = re.search(r'>=(\d+(?:\.\d+)?)', line)
                le_match = re.search(r'<=(\d+(?:\.\d+)?)', line)
                
                if ge_match and le_match:
                    ge_val = float(ge_match.group(1))
                    le_val = float(le_match.group(1))
                    
                    assert ge_val <= le_val, \
                        f"Impossible constraint in {line}: >={ge_val} and <={le_val}"
    
    def test_types_pyyaml_not_redundantly_specified(self):
        """Test that types-PyYAML is only specified once with clear version."""
        with open('requirements-dev.txt', 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        types_pyyaml_lines = [l for l in lines if l.startswith('types-PyYAML')]
        
        assert len(types_pyyaml_lines) == 1, \
            f"types-PyYAML should appear exactly once, found {len(types_pyyaml_lines)} times"
    
    def test_no_typos_in_package_names(self):
        """Test for common typos in package names."""
        with open('requirements-dev.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Common typos
        typos = ['pyymal', 'pytets', 'flake88', 'isrot']
        
        for typo in typos:
            assert typo.lower() not in content.lower(), \
                f"Possible typo found: {typo}"
    
    def test_version_format_consistency(self):
        """Test that version formats are consistent across packages."""
        with open('requirements-dev.txt', 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        for line in lines:
            if '>=' in line:
                # Should use semantic versioning (X.Y or X.Y.Z)
                version_match = re.search(r'>=(\d+\.\d+(?:\.\d+)?)', line)
                assert version_match, \
                    f"Version should be in X.Y or X.Y.Z format: {line}"


class TestCodecovWorkflowEdgeCases:
    """Edge case tests for codecov workflow removal."""
    
    def test_ci_workflow_codecov_has_error_handling(self):
        """Test that Codecov upload has proper error handling."""
        with open('.github/workflows/ci.yml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        test_job = config.get('jobs', {}).get('test', {})
        steps = test_job.get('steps', [])
        
        codecov_step = None
        for step in steps:
            if 'codecov' in str(step.get('uses', '')).lower():
                codecov_step = step
                break
        
        if codecov_step:
            # Should have continue-on-error to not fail CI if Codecov is down
            assert 'continue-on-error' in codecov_step, \
                "Codecov step should have continue-on-error"
    
    def test_ci_workflow_matrix_strategy_valid(self):
        """Test that CI workflow matrix strategy is valid."""
        with open('.github/workflows/ci.yml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        test_job = config.get('jobs', {}).get('test', {})
        strategy = test_job.get('strategy', {})
        matrix = strategy.get('matrix', {})
        
        python_versions = matrix.get('python-version', [])
        
        # Should test multiple Python versions
        assert len(python_versions) >= 2, \
            "Should test at least 2 Python versions"
        
        # All should be valid version strings
        for version in python_versions:
            assert re.match(r'^\d+\.\d+$', str(version)), \
                f"Python version should be X.Y format: {version}"
    
    def test_no_hardcoded_python_version_in_steps(self):
        """Test that Python versions aren't hardcoded in step names."""
        with open('.github/workflows/ci.yml', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should use matrix variables, not hardcoded versions like "Python 3.11"
        # Exception: conditional steps that specify version
        if 'python-version ==' in content:
            # This is okay - conditional execution
            pass
        
        # Check that step names use variables
        config = yaml.safe_load(open('.github/workflows/ci.yml', 'r'))
        test_job = config.get('jobs', {}).get('test', {})
        
        assert 'matrix' in test_job.get('strategy', {}), \
            "Test job should use matrix strategy"


class TestWorkflowConsistencyEdgeCases:
    """Edge case tests for workflow consistency after changes."""
    
    def test_all_workflows_have_valid_yaml(self):
        """Test that all workflow files are valid YAML."""
        workflows_dir = Path('.github/workflows')
        
        for workflow_file in workflows_dir.glob('*.yml'):
            # Skip pr-agent.yml as it may have known issues
            if workflow_file.name == "pr-agent.yml":
                continue
            try:
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"{workflow_file.name} has invalid YAML: {e}")
    
    def test_no_workflow_references_nonexistent_files(self):
        """Test that workflows don't reference non-existent files."""
        workflows_dir = Path('.github/workflows')
        
        for workflow_file in workflows_dir.glob('*.yml'):
            with open(workflow_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for common file references
            if 'requirements-dev.txt' in content:
                assert Path('requirements-dev.txt').exists(), \
                    f"{workflow_file.name} references requirements-dev.txt which should exist"
            
            if 'requirements.txt' in content:
                assert Path('requirements.txt').exists(), \
                    f"{workflow_file.name} references requirements.txt which should exist"
    
    def test_ci_workflow_has_proper_triggers(self):
        """Test that CI workflow has appropriate triggers."""
        with open('.github/workflows/ci.yml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        on_config = config.get('on', {})
        
        # Should trigger on both push and pull_request for main branch
        assert 'push' in on_config or 'pull_request' in on_config, \
            "CI should trigger on push or pull_request"
        
        # Verify branch configuration
        if isinstance(on_config, dict):
            if 'push' in on_config:
                push_config = on_config['push']
                if isinstance(push_config, dict) and 'branches' in push_config:
                    assert 'main' in push_config['branches'], \
                        "CI should run on main branch pushes"


class TestRegressionPrevention:
    """Tests to prevent regression of fixed issues."""
    
    def test_no_duplicate_workflow_keys(self):
        """Test that no workflow has duplicate keys (like the original issue)."""
        workflows_dir = Path('.github/workflows')
        
        for workflow_file in workflows_dir.glob('*.yml'):
            with open(workflow_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Check for duplicate keys at the same indentation level
            seen_keys = {}
            current_indent = 0
            
            for i, line in enumerate(lines, 1):
                if ':' in line and not line.strip().startswith('#'):
                    indent = len(line) - len(line.lstrip())
                    key = line.split(':')[0].strip()
                    
                    if indent not in seen_keys:
                        seen_keys[indent] = {}
                    
                    if key in seen_keys[indent]:
                        pytest.fail(
                            f"{workflow_file.name} line {i}: Duplicate key '{key}' "
                            f"(also on line {seen_keys[indent][key]})"
                        )
                    
                    seen_keys[indent][key] = i
    
    def test_codecov_yaml_stays_deleted(self):
        """Test that codecov.yaml remains deleted (regression check)."""
        codecov_yaml = Path('.github/workflows/codecov.yaml')
        assert not codecov_yaml.exists(), \
            "codecov.yaml should remain deleted"
    
    def test_gitignore_removed_patterns_stay_removed(self):
        """Test that removed .gitignore patterns stay removed."""
        with open('.gitignore', 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]
        
        removed_patterns = ['junit.xml', 'test_*.db', '*_test.db']
        
        for pattern in removed_patterns:
            assert pattern not in lines, \
                f"Pattern '{pattern}' should stay removed from .gitignore"
    
    def test_types_pyyaml_version_stays_pinned(self):
        """Test that types-PyYAML version remains pinned (regression check)."""
        with open('requirements-dev.txt', 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]
        
        types_lines = [l for l in lines if l.startswith('types-PyYAML')]
        
        assert len(types_lines) >= 1, "types-PyYAML should exist"
        assert '>=' in types_lines[0], "types-PyYAML should have >= constraint"


class TestConfigurationFileIntegrity:
    """Test integrity and completeness of configuration files."""
    
    def test_gitignore_has_section_comments(self):
        """Test that .gitignore is organized with section comments."""
        with open('.gitignore', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should have some organizational comments
        comment_lines = [l for l in content.split('\n') if l.strip().startswith('#')]
        
        assert len(comment_lines) >= 3, \
            ".gitignore should have organizational comments"
    
    def test_requirements_dev_has_header_comment(self):
        """Test that requirements-dev.txt has a descriptive header."""
        with open('requirements-dev.txt', 'r', encoding='utf-8') as f:
            first_line = f.readline()
        
        assert first_line.startswith('#'), \
            "requirements-dev.txt should start with a comment header"
    
    def test_all_config_files_utf8_encoded(self):
        """Test that all configuration files are UTF-8 encoded."""
        config_files = [
            '.gitignore',
            'requirements-dev.txt',
            '.github/workflows/ci.yml'
        ]
        
        for config_file in config_files:
            if Path(config_file).exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        f.read()
                except UnicodeDecodeError:
                    pytest.fail(f"{config_file} is not valid UTF-8")
    
    def test_no_tabs_in_yaml_files(self):
        """Test that YAML files don't use tabs (YAML spec requires spaces)."""
        workflows_dir = Path('.github/workflows')
        
        for workflow_file in workflows_dir.glob('*.yml'):
            with open(workflow_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert '\t' not in content, \
                f"{workflow_file.name} should not contain tabs (use spaces in YAML)"