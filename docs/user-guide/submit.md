# Submit Command

The `submit` command uploads your model's predictions for evaluation.

## Usage

```bash
sb-cli submit <subset> <split> --predictions_path <path> [options]
```

## Arguments

- `subset`: Dataset subset (`swe-bench-m`, `swe-bench_lite`, `swe-bench_verified`)
- `split`: Dataset split (`dev` or `test`)

## Options

- `--predictions_path`: Path to your predictions file (required)
- `--run_id`: Unique identifier for this submission. You can use the values PARENT or STEM to use the parent directory name or the stem of the predictions file name. (default: PARENT)
- `--instance_ids`: Comma-separated list of specific instances to submit
- `--output_dir`: Directory to save report files (default: sb-cli-reports)
- `--overwrite`: Overwrite existing report (0/1, default: 0)
- `--gen_report`: Generate report after completion (0/1, default: 1)
- `--verify_submission`: Verify submission before waiting (0/1, default: 1)
- `--wait_for_evaluation`: Wait for evaluation to complete (0/1, default: 1)

## Predictions File Format

Your predictions file should be a JSON file in one of these formats:

### Dictionary Format
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

### List Format
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

## Examples

1. Basic submission:
```bash
sb-cli submit swe-bench-m dev --predictions_path preds.json
```

2. Custom run ID and output directory:
```bash
sb-cli submit swe-bench-m dev \
    --predictions_path preds.json \
    --run_id custom_run \
    --output_dir ./reports
```

3. Submit specific instances:
```bash
sb-cli submit swe-bench-m dev \
    --predictions_path preds.json \
    --instance_ids id1,id2,id3
```