import json
import os
import requests
import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from sb_cli.config import API_BASE_URL, Subset
from sb_cli.utils import verify_response

app = typer.Typer(help="Get the evaluation report for a specific run")

def safe_save_json(data: dict, file_path: Path, overwrite: bool = False):
    if file_path.exists() and not overwrite:
        ext = 1
        base_stem = file_path.stem
        while (file_path.parent / f"{base_stem}-{ext}.json").exists():
            ext += 1
        file_path = file_path.parent / f"{base_stem}-{ext}.json"
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
    return file_path


def get_str_report(report: dict) -> dict:
    resolved_total = report['resolved_instances'] / report['total_instances']
    resolved_submitted = (report['resolved_instances'] / report['submitted_instances']) if report['submitted_instances'] > 0 else 0 
    submitted = report['submitted_instances'] / report['total_instances']
    return (
        f"Resolved (total): {resolved_total:.2%} ({report['resolved_instances']} / {report['total_instances']})\n"
        f"Resolved (submitted): {resolved_submitted:.2%} ({report['resolved_instances']} / {report['submitted_instances']})\n"
        f"Submitted: {submitted:.2%} ({report['submitted_instances']})\n"
        f"Errors: {report['error_instances']}\n"
        f"Pending: {report['pending_instances']}\n"
        f"Successful runs: {report['completed_instances']}\n"
        f"Failed runs: {report['failed_instances']}"
    )


def get_report(
    subset: Subset = typer.Argument(
        help="Subset to evaluate",
        callback=lambda x: x.value if isinstance(x, Subset) else x
    ),
    split: str = typer.Argument(
        ...,
        help="Split to evaluate"
    ),
    run_id: str = typer.Argument(..., help="Run ID"),
    api_key: Optional[str] = typer.Option(
        None,
        '--api_key',
        help="API key to use",
        envvar="SWEBENCH_API_KEY"
    ),
    overwrite: int = typer.Option(0, '--overwrite', help="Overwrite existing report"),
    output_dir: Optional[str] = typer.Option(
        'sb-cli-reports',
        '--output_dir',
        '-o',
        help="Directory to save report files"
    ),
    extra_args: Optional[str] = typer.Option(
        '',
        '--extra_arg',
        '-e',
        help="Additional argument in the format KEY=VALUE",
    )
):
    """Get report for a run from the run ID"""
    kwargs = {}
    if extra_args and isinstance(extra_args, str):
        kwargs = {arg.split('=')[0]: arg.split('=')[1] for arg in extra_args.split(',')}
    elif extra_args and not isinstance(extra_args, typer.models.OptionInfo):
        raise ValueError(f"Invalid extra arguments: has type {type(extra_args)}")
    payload = {
        'run_id': run_id,
        'subset': subset,
        'split': split,
        **kwargs
    }
    headers = {'x-api-key': api_key} if api_key else {}
    console = Console()
    with console.status(f"[blue]Creating report for run {run_id}...", spinner="dots"):
        response = requests.post(f"{API_BASE_URL}/get-report", json=payload, headers=headers)
        verify_response(response)
        response = response.json()
    report = response.pop('report')
    typer.echo(get_str_report(report))
    report_name = f"{subset}__{split}__{run_id}"
    
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        report_path = output_path / f"{report_name}.json"
        response_path = output_path / f"{report_name}.response.json"
    else:
        report_path = Path(f"{report_name}.json")
        response_path = Path(f"{report_name}.response.json")
        
    report_path = safe_save_json(report, report_path, overwrite)
    typer.echo(f"Saved full report to {report_path}!")
    if response:
        response_path = safe_save_json(response, response_path, False)
        typer.echo(f"Saved response to {response_path}")