import yaml


class ValidationResult:
    def __init__(self, is_valid, errors, workflow_data):
        self.is_valid = is_valid
        self.errors = errors
        self.workflow_data = workflow_data


def validate_workflow(workflow_path):
    try:
        with open(workflow_path, 'r') as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return ValidationResult(False, ["Workflow must be a dict"], {})
        if 'jobs' not in data:
            return ValidationResult(False, ["Workflow must have jobs"], data)
        # Additional validations can be added here if needed
        return ValidationResult(True, [], data)
    except Exception as e:
        return ValidationResult(False, [str(e)], {})