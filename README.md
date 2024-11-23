<p align="center">
  <img src="assets/sb-cli-logo.png" alt="SWE-bench CLI Logo" style="height: 12em">
</p>

# SWE-bench CLI

A command-line interface for interacting with the SWE-bench API. Use this tool to submit predictions, manage runs, and retrieve evaluation reports.

## Installation

```bash
pip install sb-cli
```

## Authentication

Before using the CLI, you'll need to get an API key:

1. Generate an API key:
```bash
sb-cli get-api-key your.email@example.com
```

2. Set your API key as an environment variable - and store it somewhere safe!
```bash
export SWEBENCH_API_KEY=your_api_key
# or add export SWEBENCH_API_KEY=your_api_key to your .*rc file
```

3. You'll receive an email with a verification code. Verify your API key:
```bash
sb-cli verify-api-key YOUR_VERIFICATION_CODE
```

## Usage

### Submit Predictions

Submit your model's predictions to SWE-bench:

```bash
sb-cli submit --predictions_path predictions.json --run_id my_run_id
```

> **Note:** By default, the CLI will watch the submission until evaluation is complete and generate a report.
> You can disable this behavior with `--gen_report False`.

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
