# Quick Guide: Running the New Tests

## Test Files Created

1. **`tests/unit/test_workflow_validator.py`** - Unit tests for workflow validation
2. **`tests/integration/test_simplified_workflows.py`** - Integration tests for workflow simplifications
3. **`tests/integration/test_pr_agent_config_validation.py`** - Integration tests for configuration

---

## Quick Commands

### Run All New Tests
```bash
pytest tests/unit/test_workflow_validator.py \
       tests/integration/test_simplified_workflows.py \
       tests/integration/test_pr_agent_config_validation.py \
       -v
```

### Run Individual Test Files
```bash
# Unit tests
pytest tests/unit/test_workflow_validator.py -v

# Workflow integration tests  
pytest tests/integration/test_simplified_workflows.py -v

# Configuration tests
pytest tests/integration/test_pr_agent_config_validation.py -v
```

### Run with Coverage
```bash
pytest tests/unit/test_workflow_validator.py \
       tests/integration/test_simplified_workflows.py \
       tests/integration/test_pr_agent_config_validation.py \
       --cov=src --cov=.github \
       --cov-report=term-missing \
       --cov-report=html
```

### Run Specific Test Class
```bash
pytest tests/unit/test_workflow_validator.py::TestWorkflowValidatorBasicValidation -v
```

### Run Tests Matching Pattern
```bash
pytest -k "edge_case" -v
pytest -k "security" -v
pytest -k "validation" -v
```

---

## Expected Results

All tests should pass with output similar to: