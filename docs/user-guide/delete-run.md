# Delete Run Command

!!! warning
    This command is currently disabled.

The `delete-run` command removes a specific run id and its associated data.

## Usage

```bash
sb-cli delete-run <subset> <split> <run_id>
```

## Arguments

- `subset`: Dataset subset (`swe-bench-m`, `swe-bench_lite`, `swe-bench_verified`)
- `split`: Dataset split (`dev` or `test`)
- `run_id`: ID of the run to delete

## Important Notes

- Deletion is permanent and cannot be undone
- Only runs associated with your API key can be deleted
- Running evaluations will be cancelled
- Associated reports will be removed

## Examples

1. Delete a specific run:
```bash
sb-cli delete-run swe-bench-m dev my_run_id
```

## Best Practices

1. Always verify the run ID before deletion:
```bash
sb-cli list-runs swe-bench-m dev
```

2. Save important reports before deletion:
```bash
sb-cli get-report swe-bench-m dev my_run_id -o ./backup
sb-cli delete-run swe-bench-m dev my_run_id
```

3. Consider keeping a local backup of important results before deletion
