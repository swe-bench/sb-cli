<p align="center">
  <img src="assets/sb-cli-logo.png" alt="SWE-bench CLI Logo" style="max-width: 100%; max-height: 250px;">
</p>


# SWE-bench CLI

A command-line interface for interacting with the SWE-bench API. Use this tool to submit predictions, manage runs, and retrieve evaluation reports.

## Installation

```bash
pip install sb-cli
```

## Authentication

Before using the CLI, you'll need to get an authentication token:

1. Generate a token:
```bash
sb-cli get-auth-token your.email@example.com
```

2. You'll receive an email with a verification code. Verify your token:
```bash
sb-cli verify-token YOUR_VERIFICATION_CODE
```

3. Set your authentication token as an environment variable - and store it somewhere safe!
```bash
export SWEBENCH_API_KEY=your_auth_token
```

## Usage

### Submit Predictions

Submit your model's predictions to SWE-bench:

```bash
sb-cli submit --predictions_path predictions.json --run_id my_run_id
```

> **Note:** By default, the CLI will watch the submission until evaluation is complete and generate a report.
> You can disable this behavior with the `--no-report` flag.

### Get Report

Retrieve evaluation results for a specific run:

```bash
sb-cli get-report my_run_id -o ./reports
```

### List Runs

View all your existing run IDs:

```bash
sb-cli list-runs
```

## Predictions File Format

Your predictions file should be a JSON file in one of these formats:

```json
{
    "instance_id_1": {
        "model_patch": "...",
        "model_name_or_path": "..."
    },
    "instance_id_2": {
        "model_patch": "...",
        "model_name_or_path": "..."
    }
}
```

Or as a list:

```json
[
    {
        "instance_id": "instance_id_1",
        "model_patch": "...",
        "model_name_or_path": "..."
    },
    {
        "instance_id": "instance_id_2",
        "model_patch": "...",
        "model_name_or_path": "..."
    }
]
```
