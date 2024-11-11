import json
import os
import requests
import typer
from pathlib import Path
from typing import Optional
from .constants import URL_ROOT
from rich.console import Console

app = typer.Typer(help="Get the evaluation report for a specific run")

def safe_save_json(data: dict, file_path: Path, overwrite: bool = False):
    if file_path.exists() and not overwrite:
        ext = 1
        while file_path.with_suffix(f".json-{ext}").exists():
            ext += 1
        file_path = file_path.with_suffix(f".json-{ext}")
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
    return file_path


def get_str_report(report: dict) -> dict:
    resolved_total = report['resolved_instances'] / report['total_instances']
    resolved_submitted = (report['resolved_instances'] / report['submitted_instances']) if report['submitted_instances'] > 0 else 0 
    submitted = report['submitted_instances'] / report['total_instances']
    return (
        f"Resolved (total): {resolved_total:.2%} ({report['total_instances']})\n"
        f"Resolved (submitted): {resolved_submitted:.2%} ({report['submitted_instances']})\n"
        f"Submitted: {submitted:.2%} ({report['submitted_instances']})\n"
        f"Errors: {report['error_instances']}\n"
        f"Pending: {report['pending_instances']}\n"
        f"Successful runs: {report['completed_instances']}\n"
        f"Failed runs: {report['failed_instances']}"
    )


def get_report(
    run_id: str = typer.Argument(..., help="Run ID"),
    auth_token: Optional[str] = typer.Option(
        None,
        '--auth_token',
        help="Auth token to verify",
        envvar="SWEBENCH_API_KEY"
    ),
    overwrite: bool = typer.Option(False, '--overwrite', help="Overwrite existing report"),
    output_dir: Optional[str] = typer.Option(
        None,
        '--output_dir',
        '-o',
        help="Directory to save report files"
    ),
    extra_args: Optional[list[str]] = typer.Option(
        None,
        '--extra_args',
        '-e',
        help="Additional arguments in the format KEY=VALUE"
    )
):
    """Get report for a run from the run ID"""
    kwargs = {}
    if extra_args:
        for arg in extra_args:
            try:
                key, value = arg.split('=', 1)
                kwargs[key] = value
            except ValueError:
                typer.echo(f"Warning: Skipping malformed argument: {arg}")
    payload = {
        'auth_token': auth_token,
        'run_id': run_id,
        **kwargs
    }
    console = Console()
    with console.status(f"[bold blue]Creating report for run {run_id}...", spinner="dots"):
        response = requests.post(f"{URL_ROOT}/get-report", json=payload)
        response.raise_for_status()
        response = response.json()
    report = response.pop('report')
    typer.echo(get_str_report(report))
    
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        report_path = output_path / f"{run_id}.json"
        response_path = output_path / f"{run_id}.response.json"
    else:
        report_path = Path(f"{run_id}.json")
        response_path = Path(f"{run_id}.response.json")
        
    report_path = safe_save_json(report, report_path, overwrite)
    typer.echo(f"Saved full report to {report_path}!")
    if response:
        response_path = safe_save_json(response, response_path, False)
        typer.echo(f"Saved response to {response_path}")