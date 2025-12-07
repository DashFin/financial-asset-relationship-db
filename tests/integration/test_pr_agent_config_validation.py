"""
Validation tests for PR agent configuration changes.

Tests the simplified PR agent configuration, ensuring:
- Version downgrade from 1.1.0 to 1.0.0
- Removal of context chunking features
- Removal of tiktoken dependencies
- Simplified configuration structure
"""

import pytest
import yaml
from pathlib import Path


class TestPRAgentConfigSimplification:
    """Test PR agent config simplification changes."""
    
    @pytest.fixture
    def pr_agent_config(self):
        """Load PR agent configuration."""
        config_path = Path(".github/pr-agent-config.yml")
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_version_reverted_to_1_0_0(self, pr_agent_config):
        """Verify PR agent version reverted from 1.1.0 to 1.0.0."""
        assert pr_agent_config['agent']['version'] == '1.0.0'
    
    def test_no_context_configuration(self, pr_agent_config):
        """Verify context configuration section removed."""
        agent_config = pr_agent_config['agent']
        assert 'context' not in agent_config
    
    def test_no_chunking_settings(self, pr_agent_config):
        """Verify chunking settings removed from config."""
        config_str = yaml.dump(pr_agent_config)
        assert 'chunking' not in config_str.lower()
        assert 'chunk_size' not in config_str.lower()
        assert 'overlap_tokens' not in config_str.lower()
    
    def test_no_tiktoken_references(self, pr_agent_config):
        """Verify tiktoken references removed."""
        config_str = yaml.dump(pr_agent_config)
        assert 'tiktoken' not in config_str.lower()
    
    def test_no_fallback_strategies(self, pr_agent_config):
        """Verify fallback strategies removed from limits."""
        limits = pr_agent_config.get('limits', {})
        assert 'fallback' not in limits
    
    def test_basic_config_structure_intact(self, pr_agent_config):
        """Verify basic configuration sections still present."""
        # Essential sections should remain
        assert 'agent' in pr_agent_config
        assert 'monitoring' in pr_agent_config
        assert 'actions' in pr_agent_config
        assert 'quality' in pr_agent_config
        assert 'security' in pr_agent_config
    
    def test_monitoring_config_present(self, pr_agent_config):
        """Verify monitoring configuration preserved."""
        monitoring = pr_agent_config['monitoring']
        assert 'check_interval' in monitoring
        assert 'max_retries' in monitoring
        assert 'timeout' in monitoring
    
    def test_limits_simplified(self, pr_agent_config):
        """Verify limits section simplified."""
        limits = pr_agent_config['limits']
        
        # Should not have complex chunking limits
        assert 'max_files_per_chunk' not in limits
        assert 'max_diff_lines' not in limits
        
        # Should have basic limits
        assert 'max_execution_time' in limits
        assert 'max_concurrent_prs' in limits


class TestPRAgentConfigYAMLValidity:
    """Test YAML validity and structure."""
    
    def test_config_is_valid_yaml(self):
        """Verify config file is valid YAML."""
        config_path = Path(".github/pr-agent-config.yml")
        with open(config_path, 'r') as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"PR agent config has invalid YAML: {e}")
    
    def test_no_duplicate_keys(self):
        """Verify no duplicate keys in YAML."""
        config_path = Path(".github/pr-agent-config.yml")
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Simple check for obvious duplicates
        lines = content.split('\n')
        seen_keys = set()
        for line in lines:
            if ':' in line and not line.strip().startswith('#'):
                key = line.split(':')[0].strip()
                if key in seen_keys:
                    pytest.fail(f"Duplicate key found: {key}")
                seen_keys.add(key)
    
    def test_consistent_indentation(self):
        """Verify consistent 2-space indentation."""
        config_path = Path(".github/pr-agent-config.yml")
        with open(config_path, 'r') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            if line.strip() and not line.strip().startswith('#'):
                indent = len(line) - len(line.lstrip())
                if indent > 0:
                    assert indent % 2 == 0, \
                        f"Line {i} has inconsistent indentation: {indent} spaces"


class TestPRAgentConfigSecurity:
    """Test security aspects of configuration."""
    
    @pytest.fixture
    def pr_agent_config(self):
        """Load PR agent configuration."""
        config_path = Path(".github/pr-agent-config.yml")
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_no_hardcoded_credentials(self, pr_agent_config):
        """Verify no hardcoded credentials in config."""
        config_str = yaml.dump(pr_agent_config).lower()
        
        # Check for common credential indicators
        sensitive_patterns = [
            'password', 'secret', 'token', 'api_key', 'apikey',
            'access_key', 'private_key'
        ]
        
        for pattern in sensitive_patterns:
            if pattern in config_str:
                # Should only appear in field names, not values
                assert 'null' in config_str or 'webhook' in config_str, \
                    f"Potential hardcoded credential found: {pattern}"
    
    def test_safe_configuration_values(self, pr_agent_config):
        """Verify configuration values are safe."""
        limits = pr_agent_config['limits']
        
        # Check for reasonable numeric limits
        assert limits['max_execution_time'] <= 3600, "Execution time too high"
        assert limits['max_concurrent_prs'] <= 10, "Too many concurrent PRs"
        assert limits['rate_limit_requests'] <= 1000, "Rate limit too high"


class TestPRAgentConfigRemovedComplexity:
    """Test that complex features were properly removed."""
    
    @pytest.fixture
    def pr_agent_config_content(self):
        """Load PR agent configuration as string."""
        config_path = Path(".github/pr-agent-config.yml")
        with open(config_path, 'r') as f:
            return f.read()
    
    def test_no_summarization_settings(self, pr_agent_config_content):
        """Verify summarization settings removed."""
        assert 'summarization' not in pr_agent_config_content.lower()
        assert 'max_summary_tokens' not in pr_agent_config_content
    
    def test_no_token_management(self, pr_agent_config_content):
        """Verify token management settings removed."""
        assert 'max_tokens' not in pr_agent_config_content
        assert 'context_length' not in pr_agent_config_content
    
    def test_no_llm_model_references(self, pr_agent_config_content):
        """Verify LLM model references removed."""
        assert 'gpt-3.5-turbo' not in pr_agent_config_content
        assert 'gpt-4' not in pr_agent_config_content
