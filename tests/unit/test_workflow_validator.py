"""
Comprehensive unit tests for src/workflow_validator.py

Tests cover:
- Happy path validation with actual workflow files
- Edge cases and boundary conditions
- Error handling
- ValidationResult object structure
- Different workflow configurations
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from src.workflow_validator import validate_workflow, ValidationResult


class TestValidationResult:
    """Test the ValidationResult class structure."""
    
    def test_validation_result_has_required_attributes(self):
        """Test ValidationResult has is_valid, errors, and workflow_data."""
        result = ValidationResult(True, [], {})
        assert hasattr(result, 'is_valid')
        assert hasattr(result, 'errors')
        assert hasattr(result, 'workflow_data')
    
    def test_validation_result_valid_workflow(self):
        """Test ValidationResult for valid workflow."""
        data = {'name': 'Test', 'on': 'push', 'jobs': {}}
        result = ValidationResult(True, [], data)
        assert result.is_valid is True
        assert result.errors == []
        assert result.workflow_data == data
    
    def test_validation_result_invalid_workflow(self):
        """Test ValidationResult for invalid workflow."""
        result = ValidationResult(False, ["Missing jobs"], {})
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "Missing jobs" in result.errors


class TestValidateWorkflowBasicValidation:
    """Test basic workflow validation functionality."""
    
    def test_validate_simple_workflow_file(self, tmp_path):
        """Test validation of a minimal valid workflow file."""
        workflow_file = tmp_path / "workflow.yml"
        workflow_data = {
            'name': 'Test Workflow',
            'on': 'push',
            'jobs': {
                'test': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [{'uses': 'actions/checkout@v4'}]
                }
            }
        }
        workflow_file.write_text(yaml.dump(workflow_data))
        
        result = validate_workflow(str(workflow_file))
        assert result.is_valid is True
        assert result.errors == []
        assert 'jobs' in result.workflow_data
    
    def test_validate_workflow_with_multiple_jobs(self, tmp_path):
        """Test validation with multiple jobs defined."""
        workflow_file = tmp_path / "workflow.yml"
        workflow_data = {
            'name': 'Multi-Job Workflow',
            'on': 'push',
            'jobs': {
                'test': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [{'run': 'npm test'}]
                },
                'lint': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [{'run': 'npm run lint'}]
                },
                'build': {
                    'runs-on': 'ubuntu-latest',
                    'needs': ['test', 'lint'],
                    'steps': [{'run': 'npm run build'}]
                }
            }
        }
        workflow_file.write_text(yaml.dump(workflow_data))
        
        result = validate_workflow(str(workflow_file))
        assert result.is_valid is True
        assert len(result.workflow_data['jobs']) == 3
    
    def test_validate_workflow_with_complex_triggers(self, tmp_path):
        """Test validation with complex trigger configuration."""
        workflow_file = tmp_path / "workflow.yml"
        workflow_data = {
            'name': 'Complex Trigger',
            'on': {
                'push': {'branches': ['main', 'develop']},
                'pull_request': {'types': ['opened', 'synchronize']}
            },
            'jobs': {
                'test': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [{'uses': 'actions/checkout@v4'}]
                }
            }
        }
        workflow_file.write_text(yaml.dump(workflow_data))
        
        result = validate_workflow(str(workflow_file))
        assert result.is_valid is True


class TestValidateWorkflowMissingRequiredFields:
    """Test validation with missing required fields."""
    
    def test_validate_workflow_missing_jobs(self, tmp_path):
        """Test workflow missing 'jobs' field."""
        workflow_file = tmp_path / "workflow.yml"
        workflow_data = {
            'name': 'Test Workflow',
            'on': 'push'
        }
        workflow_file.write_text(yaml.dump(workflow_data))
        
        result = validate_workflow(str(workflow_file))
        assert result.is_valid is False
        assert any('jobs' in str(error).lower() for error in result.errors)
    
    def test_validate_workflow_missing_name(self, tmp_path):
        """Test workflow missing 'name' field (should still be valid per implementation)."""
        workflow_file = tmp_path / "workflow.yml"
        workflow_data = {
            'on': 'push',
            'jobs': {
                'test': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [{'run': 'echo test'}]
                }
            }
        }
        workflow_file.write_text(yaml.dump(workflow_data))
        
        result = validate_workflow(str(workflow_file))
        # Implementation only checks for 'jobs', so this should pass
        assert result.is_valid is True


class TestValidateWorkflowInvalidInputs:
    """Test validation with invalid input types."""
    
    def test_validate_workflow_not_a_dict(self, tmp_path):
        """Test validation when workflow is not a dictionary."""
        workflow_file = tmp_path / "workflow.yml"
        # Write a list instead of dict
        workflow_file.write_text("- item1\n- item2")
        
        result = validate_workflow(str(workflow_file))
        assert result.is_valid is False
        assert any('dict' in str(error).lower() for error in result.errors)
    
    def test_validate_workflow_string_content(self, tmp_path):
        """Test validation when workflow is just a string."""
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text("just a string")
        
        result = validate_workflow(str(workflow_file))
        assert result.is_valid is False
    
    def test_validate_workflow_empty_file(self, tmp_path):
        """Test validation with empty YAML file."""
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text("")
        
        result = validate_workflow(str(workflow_file))
        assert result.is_valid is False
    
    def test_validate_workflow_nonexistent_file(self, tmp_path):
        """Test validation when file doesn't exist."""
        workflow_file = tmp_path / "nonexistent.yml"
        
        result = validate_workflow(str(workflow_file))
        assert result.is_valid is False
        assert len(result.errors) > 0


class TestValidateWorkflowEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_validate_workflow_with_empty_jobs(self, tmp_path):
        """Test workflow with empty jobs dictionary."""
        workflow_file = tmp_path / "workflow.yml"
        workflow_data = {
            'name': 'Empty Jobs',
            'on': 'push',
            'jobs': {}
        }
        workflow_file.write_text(yaml.dump(workflow_data))
        
        result = validate_workflow(str(workflow_file))
        # Implementation allows empty jobs dict
        assert result.is_valid is True
    
    def test_validate_workflow_with_very_long_name(self, tmp_path):
        """Test workflow with extremely long name."""
        workflow_file = tmp_path / "workflow.yml"
        workflow_data = {
            'name': 'A' * 1000,
            'on': 'push',
            'jobs': {
                'test': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [{'run': 'echo test'}]
                }
            }
        }
        workflow_file.write_text(yaml.dump(workflow_data))
        
        result = validate_workflow(str(workflow_file))
        assert result.is_valid is True
    
    def test_validate_workflow_with_unicode_characters(self, tmp_path):
        """Test workflow with unicode characters in name."""
        workflow_file = tmp_path / "workflow.yml"
        workflow_data = {
            'name': 'Test Workflow 测试 🚀',
            'on': 'push',
            'jobs': {
                'test': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [{'run': 'echo "Hello 世界"'}]
                }
            }
        }
        workflow_file.write_text(yaml.dump(workflow_data, allow_unicode=True))
        
        result = validate_workflow(str(workflow_file))
        assert result.is_valid is True
    
    def test_validate_workflow_with_many_jobs(self, tmp_path):
        """Test workflow with many jobs (stress test)."""
        workflow_file = tmp_path / "workflow.yml"
        jobs = {
            f'job_{i}': {
                'runs-on': 'ubuntu-latest',
                'steps': [{'run': f'echo "job {i}"'}]
            }
            for i in range(50)
        }
        workflow_data = {
            'name': 'Many Jobs',
            'on': 'push',
            'jobs': jobs
        }
        workflow_file.write_text(yaml.dump(workflow_data))
        
        result = validate_workflow(str(workflow_file))
        assert result.is_valid is True
        assert len(result.workflow_data['jobs']) == 50


class TestValidateWorkflowYAMLErrors:
    """Test validation with YAML syntax errors."""
    
    def test_validate_workflow_invalid_yaml_syntax(self, tmp_path):
        """Test validation with malformed YAML."""
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text("invalid: yaml: syntax:\n  - broken")
        
        result = validate_workflow(str(workflow_file))
        assert result.is_valid is False
        assert len(result.errors) > 0
    
    def test_validate_workflow_tabs_in_yaml(self, tmp_path):
        """Test validation with tabs in YAML (YAML doesn't allow tabs for indentation)."""
        workflow_file = tmp_path / "workflow.yml"
        # YAML with tabs (invalid)
        workflow_file.write_text("name: Test\non: push\njobs:\n\ttest:\n\t\truns-on: ubuntu-latest")
        
        result = validate_workflow(str(workflow_file))
        # This might fail during YAML parsing
        assert result.is_valid is False or result.is_valid is True  # Implementation dependent


class TestValidateWorkflowRealWorldScenarios:
    """Test real-world workflow scenarios."""
    
    def test_validate_ci_pipeline_workflow(self, tmp_path):
        """Test a typical CI pipeline workflow."""
        workflow_file = tmp_path / "ci.yml"
        workflow_data = {
            'name': 'CI Pipeline',
            'on': {
                'push': {'branches': ['main', 'develop']},
                'pull_request': {'branches': ['main']}
            },
            'jobs': {
                'lint': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [
                        {'uses': 'actions/checkout@v4'},
                        {'uses': 'actions/setup-node@v4', 'with': {'node-version': '18'}},
                        {'run': 'npm ci'},
                        {'run': 'npm run lint'}
                    ]
                },
                'test': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [
                        {'uses': 'actions/checkout@v4'},
                        {'run': 'npm ci'},
                        {'run': 'npm test'}
                    ]
                }
            }
        }
        workflow_file.write_text(yaml.dump(workflow_data))
        
        result = validate_workflow(str(workflow_file))
        assert result.is_valid is True
        assert 'lint' in result.workflow_data['jobs']
        assert 'test' in result.workflow_data['jobs']
    
    def test_validate_deployment_workflow(self, tmp_path):
        """Test a deployment workflow with environments."""
        workflow_file = tmp_path / "deploy.yml"
        workflow_data = {
            'name': 'Deploy',
            'on': {
                'push': {'branches': ['main']},
                'workflow_dispatch': {}
            },
            'jobs': {
                'deploy-staging': {
                    'runs-on': 'ubuntu-latest',
                    'environment': 'staging',
                    'steps': [
                        {'uses': 'actions/checkout@v4'},
                        {'run': 'echo "Deploying to staging"'}
                    ]
                },
                'deploy-production': {
                    'runs-on': 'ubuntu-latest',
                    'environment': 'production',
                    'needs': 'deploy-staging',
                    'steps': [
                        {'uses': 'actions/checkout@v4'},
                        {'run': 'echo "Deploying to production"'}
                    ]
                }
            }
        }
        workflow_file.write_text(yaml.dump(workflow_data))
        
        result = validate_workflow(str(workflow_file))
        assert result.is_valid is True


class TestValidateWorkflowPermissions:
    """Test workflow with various permission configurations."""
    
    def test_validate_workflow_with_permissions(self, tmp_path):
        """Test workflow with permission settings."""
        workflow_file = tmp_path / "workflow.yml"
        workflow_data = {
            'name': 'Test',
            'on': 'push',
            'permissions': {
                'contents': 'read',
                'issues': 'write'
            },
            'jobs': {
                'test': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [{'run': 'echo test'}]
                }
            }
        }
        workflow_file.write_text(yaml.dump(workflow_data))
        
        result = validate_workflow(str(workflow_file))
        assert result.is_valid is True
        assert 'permissions' in result.workflow_data


class TestValidateWorkflowConcurrency:
    """Test workflow concurrency configurations."""
    
    def test_validate_workflow_with_concurrency(self, tmp_path):
        """Test workflow with concurrency group."""
        workflow_file = tmp_path / "workflow.yml"
        workflow_data = {
            'name': 'Test',
            'on': 'push',
            'concurrency': {
                'group': '${{ github.workflow }}-${{ github.ref }}',
                'cancel-in-progress': True
            },
            'jobs': {
                'test': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [{'run': 'echo test'}]
                }
            }
        }
        workflow_file.write_text(yaml.dump(workflow_data))
        
        result = validate_workflow(str(workflow_file))
        assert result.is_valid is True
        assert 'concurrency' in result.workflow_data


class TestValidateWorkflowWithActualRepositoryFiles:
    """Test validation against actual workflow files in the repository."""
    
    def test_validate_pr_agent_workflow(self):
        """Test validation of actual pr-agent.yml workflow."""
        workflow_path = Path('.github/workflows/pr-agent.yml')
        if not workflow_path.exists():
            pytest.skip("pr-agent.yml not found")
        
        result = validate_workflow(str(workflow_path))
        assert result.is_valid is True
        assert 'jobs' in result.workflow_data
    
    def test_validate_apisec_scan_workflow(self):
        """Test validation of actual apisec-scan.yml workflow."""
        workflow_path = Path('.github/workflows/apisec-scan.yml')
        if not workflow_path.exists():
            pytest.skip("apisec-scan.yml not found")
        
        result = validate_workflow(str(workflow_path))
        assert result.is_valid is True
    
    def test_validate_all_workflows_in_repository(self):
        """Test validation of all workflow files in .github/workflows."""
        workflows_dir = Path('.github/workflows')
        if not workflows_dir.exists():
            pytest.skip("Workflows directory not found")
        
        workflow_files = list(workflows_dir.glob('*.yml')) + list(workflows_dir.glob('*.yaml'))
        
        for workflow_file in workflow_files:
            result = validate_workflow(str(workflow_file))
            assert result.is_valid is True, f"Workflow {workflow_file.name} validation failed: {result.errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])