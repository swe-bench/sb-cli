# List Runs Command

The `list-runs` command shows all your submitted runs for a specific subset and split.

## Usage

```bash
sb-cli list-runs <subset> <split>
```

## Arguments

- `subset`: Dataset subset (`swe-bench-m`,`swe-bench_lite`,`swe-bench_verified`)
- `split`: Dataset split (`dev` or `test`)

## Output

The command displays a list of all run IDs associated with your API key for the specified subset and split. If no runs are found, it will indicate this.

## Examples

1. List runs for main dataset:
```bash
sb-cli list-runs swe-bench-m dev
```

2. List runs for lite dataset:
```bash
sb-cli list-runs swe-bench_lite dev
```

## Common Use Cases

- Finding old run IDs before deletion
- Checking submission history
- Verifying successful submissions
- Managing multiple experiments
