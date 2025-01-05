# Get Quotas Command

The `get-quotas` command displays your remaining submission quotas for each dataset subset and split combination.

## Usage

```bash
sb-cli get-quotas
```

Example output:
```bash
> sb-cli get-quotas
        Remaining Submission Quotas
┏━━━━━━━━━━━━━━━━----┳━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Subset             ┃ Split ┃ Remaining Runs ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ swe-bench-m        │ test  │              1 │
│ swe-bench-m        │ dev   │            997 │
│ swe-bench_lite     │ test  │              1 │
│ swe-bench_lite     │ dev   │            976 │
│ swe-bench_verified │ test  │              1 │
└────────────────────┴───────┴────────────────┘
```

## Options

- `--api_key`: API key to use (defaults to `SWEBENCH_API_KEY` environment variable)

## Output Format

The command displays a table with three columns:
- **Subset**: Dataset subset (`swe-bench-m`,`swe-bench_lite`,`swe-bench_verified`)
- **Split**: Dataset split (`dev` or `test`)
- **Remaining Runs**: Number of submissions remaining for this subset/split combination

This command will display the remaining submissions you can make for each dataset subset and split combination.

## Notes
- Quotas are refreshed periodically according to your subscription level
