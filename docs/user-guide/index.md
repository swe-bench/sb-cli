# User Guide Overview

This guide provides detailed information about using the SWE-bench CLI. Each command is documented with examples and common use cases.

## Available Commands

- **[submit](submit.md)**: Submit model predictions for evaluation
- **[get-report](get-report.md)**: Retrieve evaluation reports
- **[list-runs](list-runs.md)**: View all your submitted runs
- **[delete-run](delete-run.md)**: Remove a specific run

## Dataset Information

SWE-bench has different subsets and splits available:

### Subsets
- `swe-bench-m`: The main dataset
- `swe-bench_lite`: A smaller subset for testing and development
- `swe-bench_verified`: 500 verified problems from SWE-bench [Learn more](https://openai.com/index/introducing-swe-bench-verified/)

### Splits
- `dev`: Development/validation split
- `test`: Test split (currently only available for `swe-bench_lite`)

## Common Workflows

1. **Basic Evaluation**:
   ```bash
   sb-cli submit swe-bench-m dev --predictions_path preds.json --run_id my_run
   sb-cli get-report swe-bench-m dev my_run
   ```

2. **Development Testing**:
   ```bash
   sb-cli submit swe-bench_lite dev --predictions_path test.json --run_id test_run
   ```

3. **Managing Runs**:
   ```bash
   sb-cli list-runs swe-bench-m dev
   sb-cli delete-run swe-bench-m dev old_run_id
   ```
