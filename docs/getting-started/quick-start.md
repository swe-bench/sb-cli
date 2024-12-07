# Quick Start

This guide will help you submit your first predictions to SWE-bench and get an evaluation report.

## Prerequisites

Before starting, ensure you have:
- Installed the CLI (`pip install sb-cli`)
- Generated and verified your API key
- Set up your `SWEBENCH_API_KEY` environment variable

## 1. Prepare Your Predictions

Create a JSON file (`predictions.json`) with your model's predictions:

```json
{
    "instance_id_1": {
        "model_patch": "your code changes here",
        "model_name_or_path": "your-model-name"
    },
    "instance_id_2": {
        "model_patch": "more code changes",
        "model_name_or_path": "your-model-name"
    }
}
```

## 2. Submit Predictions

Submit your predictions to SWE-bench:

```bash
sb-cli submit swe-bench-m dev \
    --predictions_path predictions.json \
    --run_id my_first_run
```

The CLI will:
1. Upload your predictions
2. Monitor the evaluation progress
3. Generate a report when complete

## 3. Check Results

Get your evaluation report:

```bash
sb-cli get-report swe-bench-m dev my_first_run
```

## 4. View All Runs

List all your submitted runs:

```bash
sb-cli list-runs swe-bench-m dev
```

## Next Steps

- Read the [User Guide](../user-guide/index.md) for detailed command information
- Learn about different [submission options](../user-guide/submit.md)
- Understand how to [manage your runs](../user-guide/list-runs.md)
