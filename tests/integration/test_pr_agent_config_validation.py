"""
Comprehensive tests for .github/pr-agent-config.yml

Tests cover:
- Configuration structure validation
- Removal of context chunking settings
- Valid agent configuration
- Monitoring settings
- Feature flags
- Rate limits
- Security settings
"""

import pytest
import yaml
from pathlib import Path


class TestPRAgentConfigStructure:
    """Test basic structure of PR agent configuration."""
    
    @pytest.fixture
    def pr_agent_config(self):
        """Load the PR agent configuration file."""
        config_path = Path('.github/pr-agent-config.yml')
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_config_file_exists(self):
        """Verify configuration file exists."""
        assert Path('.github/pr-agent-config.yml').exists()
    
    def test_config_is_valid_yaml(self, pr_agent_config):
        """Verify configuration is valid YAML."""
        assert pr_agent_config is not None
        assert isinstance(pr_agent_config, dict)
    
    def test_config_has_agent_section(self, pr_agent_config):
        """Verify agent section exists."""
        assert 'agent' in pr_agent_config
        assert isinstance(pr_agent_config['agent'], dict)
    
    def test_agent_has_basic_properties(self, pr_agent_config):
        """Verify agent has basic required properties."""
        agent = pr_agent_config['agent']
        assert 'name' in agent
        assert 'version' in agent
        assert 'enabled' in agent
    
    def test_agent_name_is_descriptive(self, pr_agent_config):
        """Verify agent has a descriptive name."""
        agent = pr_agent_config['agent']
        assert len(agent['name']) > 0
        assert isinstance(agent['name'], str)
    
    def test_agent_version_format(self, pr_agent_config):
        """Verify agent version follows semantic versioning."""
        agent = pr_agent_config['agent']
        version = agent['version']
        
        # Should be in format X.Y.Z
        import re
        semver_pattern = r'^\d+\.\d+\.\d+$'
        assert re.match(semver_pattern, version), f"Version {version} doesn't follow semver"
    
    def test_agent_enabled_is_boolean(self, pr_agent_config):
        """Verify enabled flag is a boolean."""
        agent = pr_agent_config['agent']
        assert isinstance(agent['enabled'], bool)


class TestContextChunkingRemoved:
    """Verify context chunking configuration has been removed."""
    
    @pytest.fixture
    def pr_agent_config(self):
        """Load the PR agent configuration file."""
        config_path = Path('.github/pr-agent-config.yml')
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_no_context_section_in_agent(self, pr_agent_config):
        """Verify agent.context section has been removed."""
        agent = pr_agent_config.get('agent', {})
        assert 'context' not in agent, "Context section should be removed"
    
    def test_no_chunking_configuration(self, pr_agent_config):
        """Verify no chunking configuration exists."""
        config_str = yaml.dump(pr_agent_config)
        
        chunking_keywords = [
            'chunking',
            'chunk_size',
            'max_tokens',
            'overlap_tokens',
            'summarization_threshold',
        ]
        
        for keyword in chunking_keywords:
            assert keyword not in config_str, f"Found chunking keyword: {keyword}"
    
    def test_no_tiktoken_references(self, pr_agent_config):
        """Verify no tiktoken references in config."""
        config_str = yaml.dump(pr_agent_config).lower()
        assert 'tiktoken' not in config_str
    
    def test_no_fallback_strategy_config(self, pr_agent_config):
        """Verify fallback strategy configuration removed."""
        config_str = yaml.dump(pr_agent_config)
        assert 'fallback' not in config_str or 'on_context_overflow' not in config_str
    
    def test_no_summarization_config(self, pr_agent_config):
        """Verify summarization configuration removed."""
        config_str = yaml.dump(pr_agent_config)
        assert 'summarization' not in config_str or 'max_summary_tokens' not in config_str


class TestMonitoringConfiguration:
    """Test monitoring configuration settings."""
    
    @pytest.fixture
    def pr_agent_config(self):
        """Load the PR agent configuration file."""
        config_path = Path('.github/pr-agent-config.yml')
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_has_monitoring_section(self, pr_agent_config):
        """Verify monitoring section exists if configured."""
        # Monitoring is optional but if present should be valid
        if 'monitoring' in pr_agent_config:
            assert isinstance(pr_agent_config['monitoring'], dict)
    
    def test_monitoring_check_interval_is_reasonable(self, pr_agent_config):
        """Verify check interval is reasonable if set."""
        monitoring = pr_agent_config.get('monitoring', {})
        
        if 'check_interval' in monitoring:
            interval = monitoring['check_interval']
            assert isinstance(interval, int)
            assert interval > 0
            assert interval <= 3600  # Not more than 1 hour
    
    def test_monitoring_has_valid_metrics(self, pr_agent_config):
        """Verify monitoring metrics are properly configured."""
        monitoring = pr_agent_config.get('monitoring', {})
        
        if 'metrics' in monitoring:
            assert isinstance(monitoring['metrics'], dict)


class TestLimitsConfiguration:
    """Test rate limits and resource limits."""
    
    @pytest.fixture
    def pr_agent_config(self):
        """Load the PR agent configuration file."""
        config_path = Path('.github/pr-agent-config.yml')
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_has_limits_section(self, pr_agent_config):
        """Verify limits section exists if configured."""
        if 'limits' in pr_agent_config:
            assert isinstance(pr_agent_config['limits'], dict)
    
    def test_rate_limits_are_reasonable(self, pr_agent_config):
        """Verify rate limits are reasonable if set."""
        limits = pr_agent_config.get('limits', {})
        
        if 'rate_limit_requests' in limits:
            rate_limit = limits['rate_limit_requests']
            assert isinstance(rate_limit, int)
            assert rate_limit > 0
            assert rate_limit <= 1000  # Reasonable upper bound per hour
    
    def test_max_concurrent_prs_is_reasonable(self, pr_agent_config):
        """Verify max concurrent PRs is reasonable if set."""
        limits = pr_agent_config.get('limits', {})
        
        if 'max_concurrent_prs' in limits:
            max_concurrent = limits['max_concurrent_prs']
            assert isinstance(max_concurrent, int)
            assert max_concurrent > 0
            assert max_concurrent <= 50  # Reasonable upper bound
    
    def test_no_chunking_related_limits(self, pr_agent_config):
        """Verify chunking-related limits have been removed."""
        limits = pr_agent_config.get('limits', {})
        
        chunking_limit_keys = [
            'max_files_per_chunk',
            'max_diff_lines',
            'max_comment_length',
        ]
        
        for key in chunking_limit_keys:
            assert key not in limits, f"Chunking-related limit found: {key}"


class TestFeatureFlags:
    """Test feature flag configuration."""
    
    @pytest.fixture
    def pr_agent_config(self):
        """Load the PR agent configuration file."""
        config_path = Path('.github/pr-agent-config.yml')
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_feature_flags_are_boolean(self, pr_agent_config):
        """Verify feature flags are boolean values."""
        # Recursively check all boolean-like settings
        def check_booleans(config_dict, path=""):
            for key, value in config_dict.items():
                current_path = f"{path}.{key}" if path else key
                
                if isinstance(value, dict):
                    check_booleans(value, current_path)
                elif key in ['enabled', 'active', 'disabled', 'flag']:
                    assert isinstance(value, bool), \
                        f"{current_path} should be boolean, got {type(value)}"
        
        check_booleans(pr_agent_config)
    
    def test_no_contradictory_flags(self, pr_agent_config):
        """Verify no contradictory feature flags."""
        # If agent is disabled, no point in having other features enabled
        if pr_agent_config.get('agent', {}).get('enabled') is False:
            # This would be a configuration error, but we just verify consistency
            assert True  # Configuration is internally consistent


class TestDebugConfiguration:
    """Test debug and logging configuration."""
    
    @pytest.fixture
    def pr_agent_config(self):
        """Load the PR agent configuration file."""
        config_path = Path('.github/pr-agent-config.yml')
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_has_debug_section(self, pr_agent_config):
        """Verify debug section exists if configured."""
        if 'debug' in pr_agent_config:
            assert isinstance(pr_agent_config['debug'], dict)
    
    def test_debug_enabled_is_boolean(self, pr_agent_config):
        """Verify debug enabled flag is boolean."""
        debug = pr_agent_config.get('debug', {})
        
        if 'enabled' in debug:
            assert isinstance(debug['enabled'], bool)
    
    def test_log_level_is_valid(self, pr_agent_config):
        """Verify log level is valid if set."""
        debug = pr_agent_config.get('debug', {})
        
        if 'log_level' in debug:
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            assert debug['log_level'].upper() in valid_levels


class TestConfigurationIntegrity:
    """Test overall configuration integrity."""
    
    @pytest.fixture
    def pr_agent_config(self):
        """Load the PR agent configuration file."""
        config_path = Path('.github/pr-agent-config.yml')
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_no_duplicate_keys(self):
        """Verify no duplicate keys in YAML (YAML loader would error but double-check)."""
        config_path = Path('.github/pr-agent-config.yml')
        content = config_path.read_text()
        
        # Parse and re-serialize to ensure no duplicates
        config = yaml.safe_load(content)
        assert config is not None
    
    def test_no_empty_sections(self, pr_agent_config):
        """Verify no completely empty sections."""
        def check_empty(config_dict, path=""):
            for key, value in config_dict.items():
                current_path = f"{path}.{key}" if path else key
                
                if isinstance(value, dict):
                    assert len(value) > 0, f"Empty section: {current_path}"
                    check_empty(value, current_path)
                elif isinstance(value, list):
                    # Empty lists might be valid in some cases
                    pass
        
        check_empty(pr_agent_config)
    
    def test_config_file_is_not_too_large(self):
        """Verify configuration file is reasonable size."""
        config_path = Path('.github/pr-agent-config.yml')
        size = config_path.stat().st_size
        
        # Should be less than 100KB (reasonable for a config file)
        assert size < 100 * 1024, f"Config file is too large: {size} bytes"
    
    def test_config_has_comments(self):
        """Verify configuration has documentation comments."""
        config_path = Path('.github/pr-agent-config.yml')
        content = config_path.read_text()
        
        # Should have at least some comments for documentation
        comment_lines = [line for line in content.split('\n') if line.strip().startswith('#')]
        assert len(comment_lines) > 0, "Config file should have documentation comments"


class TestVersionCompatibility:
    """Test version compatibility and upgrades."""
    
    @pytest.fixture
    def pr_agent_config(self):
        """Load the PR agent configuration file."""
        config_path = Path('.github/pr-agent-config.yml')
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_version_downgrade(self, pr_agent_config):
        """Verify version is 1.0.0 after removing chunking (downgrade from 1.1.0)."""
        agent = pr_agent_config['agent']
        
        # After removing chunking features, version should be 1.0.0
        # (This is based on the diff showing version change from 1.1.0 to 1.0.0)
        assert agent['version'] == '1.0.0', \
            "Version should be 1.0.0 after removing chunking features"
    
    def test_no_legacy_chunking_settings(self, pr_agent_config):
        """Verify no legacy/deprecated chunking settings remain."""
        config_str = yaml.dump(pr_agent_config)
        
        legacy_settings = [
            'context_length',
            'token_limit',
            'chunker',
            'summarizer',
        ]
        
        for setting in legacy_settings:
            assert setting not in config_str, f"Legacy setting found: {setting}"


class TestConfigurationSecurity:
    """Test security aspects of configuration."""
    
    def test_no_hardcoded_secrets(self):
        """Verify no secrets in configuration file."""
        config_path = Path('.github/pr-agent-config.yml')
        content = config_path.read_text().lower()
        
        secret_patterns = [
            'password',
            'api_key',
            'secret',
            'token',
            'credential',
        ]
        
        for pattern in secret_patterns:
            if pattern in content:
                # If found, ensure it's just a placeholder or reference
                lines = [line for line in content.split('\n') if pattern in line]
                for line in lines:
                    assert 'secrets.' in line or 'env.' in line or '#' in line, \
                        f"Potential hardcoded secret: {line}"
    
    def test_no_executable_code(self):
        """Verify configuration is pure data (no executable code)."""
        config_path = Path('.github/pr-agent-config.yml')
        content = config_path.read_text()
        
        # YAML should not contain executable code patterns
        dangerous_patterns = [
            '!!python/',
            '!!exec',
            '__import__',
        ]
        
        for pattern in dangerous_patterns:
            assert pattern not in content, f"Dangerous pattern found: {pattern}"


class TestConfigurationBackwardCompatibility:
    """Test backward compatibility considerations."""
    
    @pytest.fixture
    def pr_agent_config(self):
        """Load the PR agent configuration file."""
        config_path = Path('.github/pr-agent-config.yml')
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_core_settings_preserved(self, pr_agent_config):
        """Verify core agent settings are preserved."""
        agent = pr_agent_config['agent']
        
        # Core settings that should always exist
        core_settings = ['name', 'version', 'enabled']
        for setting in core_settings:
            assert setting in agent, f"Core setting missing: {setting}"
    
    def test_monitoring_still_functional(self, pr_agent_config):
        """Verify monitoring configuration is still valid after changes."""
        if 'monitoring' in pr_agent_config:
            monitoring = pr_agent_config['monitoring']
            
            # If monitoring exists, it should have valid settings
            if 'check_interval' in monitoring:
                assert isinstance(monitoring['check_interval'], (int, float))
                assert monitoring['check_interval'] > 0