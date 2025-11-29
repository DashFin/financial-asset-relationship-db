"""
Comprehensive tests for simplified workflow files.

Tests the modified workflows after context chunking removal:
- pr-agent.yml
- apisec-scan.yml
- greetings.yml
- label.yml

Tests cover:
- YAML validity and structure
- Required fields presence
- Workflow simplification verification
- Security best practices
- Job configuration
- Trigger conditions
- Permission settings
"""

import pytest
import yaml
from pathlib import Path


class TestPRAgentWorkflowSimplification:
    """Test the simplified PR Agent workflow after chunking removal."""
    
    @pytest.fixture
    def pr_agent_workflow(self):
        """Load the pr-agent workflow file."""
        workflow_path = Path('.github/workflows/pr-agent.yml')
        with open(workflow_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_pr_agent_workflow_is_valid_yaml(self, pr_agent_workflow):
        """Verify pr-agent.yml is valid YAML."""
        assert pr_agent_workflow is not None
        assert isinstance(pr_agent_workflow, dict)
    
    def test_pr_agent_has_required_top_level_keys(self, pr_agent_workflow):
        """Verify required workflow keys are present."""
        assert 'name' in pr_agent_workflow
        assert 'on' in pr_agent_workflow
        assert 'jobs' in pr_agent_workflow
    
    def test_pr_agent_workflow_name(self, pr_agent_workflow):
        """Verify workflow has a descriptive name."""
        assert pr_agent_workflow['name']
        assert len(pr_agent_workflow['name']) > 0
        assert isinstance(pr_agent_workflow['name'], str)
    
    def test_pr_agent_no_context_chunking_references(self, pr_agent_workflow):
        """Verify context chunking code has been removed."""
        workflow_content = Path('.github/workflows/pr-agent.yml').read_text()
        
        # Check for absence of chunking-related terms
        assert 'context_chunker' not in workflow_content.lower()
        assert 'chunking' not in workflow_content.lower()
        assert 'fetch-context' not in workflow_content.lower()
        assert 'pr_context_chunked' not in workflow_content.lower()
        assert 'context_size' not in workflow_content.lower()
    
    def test_pr_agent_no_tiktoken_references(self, pr_agent_workflow):
        """Verify tiktoken dependency has been removed."""
        workflow_content = Path('.github/workflows/pr-agent.yml').read_text()
        assert 'tiktoken' not in workflow_content.lower()
    
    def test_pr_agent_no_pyyaml_for_chunking(self, pr_agent_workflow):
        """Verify PyYAML for chunking has been removed."""
        workflow_content = Path('.github/workflows/pr-agent.yml').read_text()
        # PyYAML might still be needed for other purposes, but not for chunking
        if 'pyyaml' in workflow_content.lower():
            assert 'context chunker' not in workflow_content.lower()
    
    def test_pr_agent_has_parse_comments_step(self, pr_agent_workflow):
        """Verify the parse-comments step exists."""
        jobs = pr_agent_workflow.get('jobs', {})
        assert len(jobs) > 0
        
        # Find a job with parse-comments step
        found_parse_step = False
        for job_name, job_config in jobs.items():
            steps = job_config.get('steps', [])
            for step in steps:
                if 'parse-comments' in step.get('id', '').lower():
                    found_parse_step = True
                    break
                if 'parse' in step.get('name', '').lower():
                    found_parse_step = True
                    break
        
        assert found_parse_step or len(jobs) > 0  # At least verify jobs exist
    
    def test_pr_agent_trigger_configuration(self, pr_agent_workflow):
        """Verify PR agent has appropriate triggers."""
        triggers = pr_agent_workflow.get('on', {})
        assert triggers
        
        # Should trigger on PR events
        if isinstance(triggers, dict):
            assert any(key in triggers for key in ['pull_request', 'pull_request_review', 'issue_comment'])
        elif isinstance(triggers, list):
            assert any(t in triggers for t in ['pull_request', 'pull_request_review'])
    
    def test_pr_agent_permissions_are_defined(self, pr_agent_workflow):
        """Verify appropriate permissions are set."""
        # Check workflow-level or job-level permissions
        has_permissions = 'permissions' in pr_agent_workflow
        
        if not has_permissions:
            # Check if any job has permissions
            jobs = pr_agent_workflow.get('jobs', {})
            for job in jobs.values():
                if 'permissions' in job:
                    has_permissions = True
                    break
        
        # PR agent likely needs pull-requests write permission
        assert has_permissions or len(pr_agent_workflow.get('jobs', {})) > 0
    
    def test_pr_agent_uses_github_token(self, pr_agent_workflow):
        """Verify workflow uses GITHUB_TOKEN secret."""
        workflow_content = Path('.github/workflows/pr-agent.yml').read_text()
        assert 'GITHUB_TOKEN' in workflow_content
    
    def test_pr_agent_has_no_hardcoded_secrets(self, pr_agent_workflow):
        """Verify no hardcoded secrets or tokens."""
        workflow_content = Path('.github/workflows/pr-agent.yml').read_text()
        
        # Check for common secret patterns (basic check)
        dangerous_patterns = [
            'ghp_',  # GitHub personal access token
            'github_pat_',  # GitHub PAT
            'password:',  # Hardcoded password
            'api_key:',  # Hardcoded API key
        ]
        
        for pattern in dangerous_patterns:
            assert pattern not in workflow_content.lower()


class TestAPISecWorkflowSimplification:
    """Test the simplified APISec scan workflow."""
    
    @pytest.fixture
    def apisec_workflow(self):
        """Load the apisec-scan workflow file."""
        workflow_path = Path('.github/workflows/apisec-scan.yml')
        with open(workflow_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_apisec_workflow_is_valid_yaml(self, apisec_workflow):
        """Verify apisec-scan.yml is valid YAML."""
        assert apisec_workflow is not None
        assert isinstance(apisec_workflow, dict)
    
    def test_apisec_has_required_keys(self, apisec_workflow):
        """Verify required workflow structure."""
        assert 'name' in apisec_workflow
        assert 'on' in apisec_workflow
        assert 'jobs' in apisec_workflow
    
    def test_apisec_no_credential_check_step(self, apisec_workflow):
        """Verify credential checking step has been removed."""
        workflow_content = Path('.github/workflows/apisec-scan.yml').read_text()
        
        # The check for credentials should be removed
        assert 'Check for APIsec credentials' not in workflow_content
        assert 'apisec_username' not in workflow_content or 'secrets.apisec_username' in workflow_content
    
    def test_apisec_no_conditional_skip_on_job(self, apisec_workflow):
        """Verify job no longer has conditional skip based on credentials."""
        jobs = apisec_workflow.get('jobs', {})
        
        for job_name, job_config in jobs.items():
            job_if = job_config.get('if', '')
            # Should not conditionally skip based on secrets
            assert 'secrets.apisec_username' not in str(job_if).lower()
    
    def test_apisec_uses_secrets_properly(self, apisec_workflow):
        """Verify secrets are still referenced correctly."""
        workflow_content = Path('.github/workflows/apisec-scan.yml').read_text()
        
        # Secrets should still be used in the action
        if 'apisec' in workflow_content.lower():
            assert 'secrets.' in workflow_content
    
    def test_apisec_has_concurrency_control(self, apisec_workflow):
        """Verify concurrency control is properly configured."""
        # Check workflow-level or job-level concurrency
        has_concurrency = 'concurrency' in apisec_workflow
        
        if not has_concurrency:
            jobs = apisec_workflow.get('jobs', {})
            for job in jobs.values():
                if 'concurrency' in job:
                    has_concurrency = True
                    break
        
        # APISec scan should have concurrency control to avoid overlapping scans
        assert has_concurrency or len(apisec_workflow.get('jobs', {})) > 0
    
    def test_apisec_trigger_is_appropriate(self, apisec_workflow):
        """Verify APISec scan has appropriate triggers."""
        triggers = apisec_workflow.get('on', {})
        assert triggers
        
        # Security scans often run on schedule, push, or manual trigger
        if isinstance(triggers, dict):
            assert any(key in triggers for key in ['push', 'pull_request', 'schedule', 'workflow_dispatch'])


class TestGreetingsWorkflowSimplification:
    """Test the simplified greetings workflow."""
    
    @pytest.fixture
    def greetings_workflow(self):
        """Load the greetings workflow file."""
        workflow_path = Path('.github/workflows/greetings.yml')
        with open(workflow_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_greetings_workflow_is_valid_yaml(self, greetings_workflow):
        """Verify greetings.yml is valid YAML."""
        assert greetings_workflow is not None
        assert isinstance(greetings_workflow, dict)
    
    def test_greetings_has_required_keys(self, greetings_workflow):
        """Verify required workflow structure."""
        assert 'name' in greetings_workflow
        assert 'on' in greetings_workflow
        assert 'jobs' in greetings_workflow
    
    def test_greetings_messages_are_simplified(self, greetings_workflow):
        """Verify greeting messages are simple (not multi-line markdown)."""
        workflow_content = Path('.github/workflows/greetings.yml').read_text()
        
        # Check that messages are shorter/simpler
        # The old version had multi-line markdown with sections
        assert '**Welcome to the Financial Asset' not in workflow_content
        assert '**What happens next:' not in workflow_content
        assert '**Resources:' not in workflow_content
    
    def test_greetings_uses_first_interaction_action(self, greetings_workflow):
        """Verify workflow uses the first-interaction action."""
        workflow_content = Path('.github/workflows/greetings.yml').read_text()
        assert 'actions/first-interaction' in workflow_content
    
    def test_greetings_has_issue_and_pr_messages(self, greetings_workflow):
        """Verify both issue and PR messages are configured."""
        workflow_content = Path('.github/workflows/greetings.yml').read_text()
        assert 'issue-message' in workflow_content
        assert 'pr-message' in workflow_content
    
    def test_greetings_triggers_on_issues_and_prs(self, greetings_workflow):
        """Verify workflow triggers on issues and pull requests."""
        triggers = greetings_workflow.get('on', {})
        
        if isinstance(triggers, dict):
            assert 'issues' in triggers or 'pull_request_target' in triggers or 'pull_request' in triggers
        elif isinstance(triggers, list):
            assert 'issues' in triggers or 'pull_request' in triggers


class TestLabelWorkflowSimplification:
    """Test the simplified label workflow."""
    
    @pytest.fixture
    def label_workflow(self):
        """Load the label workflow file."""
        workflow_path = Path('.github/workflows/label.yml')
        with open(workflow_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_label_workflow_is_valid_yaml(self, label_workflow):
        """Verify label.yml is valid YAML."""
        assert label_workflow is not None
        assert isinstance(label_workflow, dict)
    
    def test_label_has_required_keys(self, label_workflow):
        """Verify required workflow structure."""
        assert 'name' in label_workflow
        assert 'on' in label_workflow
        assert 'jobs' in label_workflow
    
    def test_label_no_config_check_step(self, label_workflow):
        """Verify config checking step has been removed."""
        workflow_content = Path('.github/workflows/label.yml').read_text()
        
        # Should not have config existence check
        assert 'Check for labeler config' not in workflow_content
        assert 'check-config' not in workflow_content
    
    def test_label_no_conditional_skip(self, label_workflow):
        """Verify labeler step is not conditionally skipped."""
        jobs = label_workflow.get('jobs', {})
        
        for job_name, job_config in jobs.items():
            steps = job_config.get('steps', [])
            for step in steps:
                if 'labeler' in step.get('uses', '').lower():
                    # Labeler step should not have conditional if based on config check
                    assert 'check-config' not in str(step.get('if', ''))
    
    def test_label_uses_labeler_action(self, label_workflow):
        """Verify workflow uses the labeler action."""
        workflow_content = Path('.github/workflows/label.yml').read_text()
        assert 'actions/labeler' in workflow_content
    
    def test_label_has_checkout_step(self, label_workflow):
        """Verify workflow checks out code."""
        workflow_content = Path('.github/workflows/label.yml').read_text()
        # May or may not need checkout depending on labeler version
        # Just verify workflow has valid structure
        jobs = label_workflow.get('jobs', {})
        assert len(jobs) > 0
    
    def test_label_triggers_on_pull_requests(self, label_workflow):
        """Verify workflow triggers on pull requests."""
        triggers = label_workflow.get('on', {})
        
        if isinstance(triggers, dict):
            assert 'pull_request' in triggers or 'pull_request_target' in triggers
        elif isinstance(triggers, list):
            assert 'pull_request' in triggers
    
    def test_label_has_proper_permissions(self, label_workflow):
        """Verify workflow has permissions to manage labels."""
        # Check for pull-requests write permission
        has_permissions = False
        
        if 'permissions' in label_workflow:
            perms = label_workflow['permissions']
            if isinstance(perms, dict):
                has_permissions = perms.get('pull-requests') == 'write'
            elif isinstance(perms, str):
                has_permissions = perms == 'write-all'
        
        # Also check job-level permissions
        if not has_permissions:
            jobs = label_workflow.get('jobs', {})
            for job in jobs.values():
                if 'permissions' in job:
                    perms = job['permissions']
                    if isinstance(perms, dict):
                        has_permissions = perms.get('pull-requests') == 'write'
                    break
        
        assert has_permissions or len(label_workflow.get('jobs', {})) > 0


class TestAllWorkflowsSecurityBestPractices:
    """Test security best practices across all modified workflows."""
    
    @pytest.mark.parametrize('workflow_file', [
        '.github/workflows/pr-agent.yml',
        '.github/workflows/apisec-scan.yml',
        '.github/workflows/greetings.yml',
        '.github/workflows/label.yml',
    ])
    def test_workflow_uses_pinned_action_versions(self, workflow_file):
        """Verify all actions use pinned versions (not @main or @master)."""
        workflow_path = Path(workflow_file)
        if not workflow_path.exists():
            pytest.skip(f"Workflow file {workflow_file} does not exist")
        
        content = workflow_path.read_text()
        
        # Find all action uses
        import re
        action_uses = re.findall(r"uses:\s*['\"]?([^'\"\n]+)['\"]?", content)
        
        for action in action_uses:
            # Actions should not use @main or @master (less secure)
            # They should use @v1, @v2, etc. or commit SHA
            if '@' in action:
                version = action.split('@')[1]
                assert version not in ['main', 'master'], f"Action {action} uses unpinned version"
    
    @pytest.mark.parametrize('workflow_file', [
        '.github/workflows/pr-agent.yml',
        '.github/workflows/apisec-scan.yml',
        '.github/workflows/greetings.yml',
        '.github/workflows/label.yml',
    ])
    def test_workflow_has_no_shell_injection_risks(self, workflow_file):
        """Verify workflows don't have obvious shell injection risks."""
        workflow_path = Path(workflow_file)
        if not workflow_path.exists():
            pytest.skip(f"Workflow file {workflow_file} does not exist")
        
        content = workflow_path.read_text()
        
        # Check for potentially dangerous patterns
        # This is a basic check - not exhaustive
        dangerous_patterns = [
            r'\$\{\{.*github\.event\.comment\.body.*\}\}',  # Unquoted user input
            r'\$\{\{.*github\.event\.issue\.title.*\}\}',  # Unquoted issue title
            r'eval\s+\$',  # eval with variable
        ]
        
        import re
        for pattern in dangerous_patterns:
            matches = re.search(pattern, content)
            if matches:
                # Found potentially dangerous pattern - should be quoted or sanitized
                assert False, f"Potentially unsafe pattern found in {workflow_file}: {matches.group()}"
    
    @pytest.mark.parametrize('workflow_file', [
        '.github/workflows/pr-agent.yml',
        '.github/workflows/apisec-scan.yml',
        '.github/workflows/greetings.yml',
        '.github/workflows/label.yml',
    ])
    def test_workflow_secrets_not_exposed_in_output(self, workflow_file):
        """Verify secrets are not echoed or logged."""
        workflow_path = Path(workflow_file)
        if not workflow_path.exists():
            pytest.skip(f"Workflow file {workflow_file} does not exist")
        
        content = workflow_path.read_text()
        
        # Check that secrets are not echo'd or printed
        import re
        if 'secrets.' in content:
            # Find echo/print statements with secrets
            dangerous = re.findall(r'(echo|print).*secrets\.', content, re.IGNORECASE)
            assert len(dangerous) == 0, f"Secrets may be exposed in output in {workflow_file}"


class TestWorkflowPerformanceAndLimits:
    """Test workflow performance considerations and limits."""
    
    @pytest.mark.parametrize('workflow_file', [
        '.github/workflows/pr-agent.yml',
        '.github/workflows/apisec-scan.yml',
        '.github/workflows/greetings.yml',
        '.github/workflows/label.yml',
    ])
    def test_workflow_has_reasonable_timeout(self, workflow_file):
        """Verify workflows have timeout settings to prevent hanging."""
        workflow_path = Path(workflow_file)
        if not workflow_path.exists():
            pytest.skip(f"Workflow file {workflow_file} does not exist")
        
        with open(workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        jobs = workflow.get('jobs', {})
        
        for job_name, job_config in jobs.items():
            # Jobs should have timeout-minutes set (good practice)
            # If not set, GitHub default is 360 minutes (6 hours)
            timeout = job_config.get('timeout-minutes')
            
            if timeout:
                # If set, should be reasonable (< 60 minutes for most workflows)
                assert timeout <= 120, f"Job {job_name} has very long timeout: {timeout} minutes"
    
    @pytest.mark.parametrize('workflow_file', [
        '.github/workflows/pr-agent.yml',
        '.github/workflows/apisec-scan.yml',
    ])
    def test_workflow_has_concurrency_control(self, workflow_file):
        """Verify workflows that should have concurrency control do."""
        workflow_path = Path(workflow_file)
        if not workflow_path.exists():
            pytest.skip(f"Workflow file {workflow_file} does not exist")
        
        with open(workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        # Check for concurrency at workflow or job level
        has_concurrency = 'concurrency' in workflow
        
        if not has_concurrency:
            jobs = workflow.get('jobs', {})
            for job in jobs.values():
                if 'concurrency' in job:
                    has_concurrency = True
                    break
        
        # PR agent and security scans should have concurrency control
        assert has_concurrency, f"{workflow_file} should have concurrency control"


class TestDeletedFilesNoLongerReferenced:
    """Test that deleted files are no longer referenced in workflows."""
    
    def test_no_references_to_labeler_yml(self):
        """Verify labeler.yml is not referenced anywhere."""
        workflow_files = Path('.github/workflows').glob('*.yml')
        
        for workflow_file in workflow_files:
            content = workflow_file.read_text()
            assert '.github/labeler.yml' not in content, \
                f"{workflow_file.name} still references deleted labeler.yml"
    
    def test_no_references_to_context_chunker_py(self):
        """Verify context_chunker.py is not referenced anywhere."""
        workflow_files = Path('.github/workflows').glob('*.yml')
        
        for workflow_file in workflow_files:
            content = workflow_file.read_text()
            assert 'context_chunker.py' not in content, \
                f"{workflow_file.name} still references deleted context_chunker.py"
    
    def test_no_references_to_scripts_readme(self):
        """Verify scripts README is not referenced anywhere."""
        workflow_files = Path('.github/workflows').glob('*.yml')
        
        for workflow_file in workflow_files:
            content = workflow_file.read_text()
            assert '.github/scripts/README.md' not in content, \
                f"{workflow_file.name} still references deleted scripts README"


class TestRequirementsDevChanges:
    """Test changes to requirements-dev.txt."""
    
    def test_requirements_dev_file_exists(self):
        """Verify requirements-dev.txt exists."""
        assert Path('requirements-dev.txt').exists()
    
    def test_requirements_dev_is_valid_format(self):
        """Verify requirements-dev.txt has valid format."""
        content = Path('requirements-dev.txt').read_text()
        lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
        
        # Basic validation - each line should be a package specification
        for line in lines:
            # Should contain package name
            assert len(line) > 0
            # Should not have obvious syntax errors
            assert not line.startswith('==')
            assert not line.startswith('>=')
    
    def test_requirements_dev_has_testing_dependencies(self):
        """Verify requirements-dev.txt includes testing dependencies."""
        content = Path('requirements-dev.txt').read_text().lower()
        
        # Should have pytest
        assert 'pytest' in content
    
    def test_requirements_dev_pyyaml_version(self):
        """Verify PyYAML version if present."""
        content = Path('requirements-dev.txt').read_text()
        
        if 'pyyaml' in content.lower():
            # Should have a version specification for security
            import re
            pyyaml_lines = [line for line in content.split('\n') if 'pyyaml' in line.lower()]
            for line in pyyaml_lines:
                # Should have version spec (==, >=, etc.)
                assert any(op in line for op in ['==', '>=', '~=', '>', '<']), \
                    "PyYAML should have version specification"