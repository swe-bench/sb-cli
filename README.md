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
sb-cli gen-api-key your.email@example.com
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

## Subsets and Splits

SWE-bench has different subsets and splits available:

### Subsets
- `swe-bench-m`: The main dataset
- `swe-bench_lite`: A smaller subset for testing and development

### Splits
- `dev`: Development/validation split
- `test`: Test split (currently only available for `swe-bench_lite`)

You'll need to specify both a subset and split for most commands.

## Usage

### Submit Predictions

Submit your model's predictions to SWE-bench:

```bash
sb-cli submit swe-bench-m test \
    --predictions_path predictions.json \
    --run_id my_run_id
```

Options:
- `--instance_ids`: Comma-separated list of specific instance IDs to submit (optional)
- `--output_dir`: Directory to save report files (default: sb-cli-reports)
- `--overwrite`: Overwrite existing report (default: 0)
- `--gen_report`: Generate a report after evaluation is complete (default: 1)

### Get Report

Retrieve evaluation results for a specific run:

```bash
sb-cli get-report swe-bench-m dev my_run_id -o ./reports
```

### List Runs

View all your existing run IDs for a specific subset and split:

```bash
sb-cli list-runs swe-bench-m dev
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
