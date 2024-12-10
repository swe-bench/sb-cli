# Quick Start

This guide will help you submit your first predictions to SWE-bench and get an evaluation report.

## Prerequisites

Before starting, ensure you have:
- Installed the CLI (`pip install sb-cli`)
- Generated and verified your API key (see [Authentication](authentication.md))
- Set up your `SWEBENCH_API_KEY` environment variable

## 1. Prepare Your Predictions

Create a JSON file (`preds.json`) with your model's predictions for the [SWE-bench M](https://arxiv.org/abs/2410.03859) `dev` split:

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
    --predictions_path preds.json \
    --run_id my_first_run
```

The CLI will:
1. Upload your predictions
2. Monitor the evaluation progress
3. Generate a report when complete

## 3. Check Results

You can access your evaluation report again by running:

```bash
sb-cli get-report swe-bench-m dev my_first_run
```

## 4. View All Runs

You can view all your submitted runs for `swe-bench-m` / `dev` by running:

```bash
sb-cli list-runs swe-bench-m dev
```
