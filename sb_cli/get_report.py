import json
import os
import requests
import typer
from pathlib import Path
from typing import Optional
from .constants import API_BASE_URL
from rich.console import Console
from dataclasses import dataclass
from typing import Any

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

@dataclass
class Report:
    resolved_instances: int
    total_instances: int
    submitted_instances: int
    error_instances: int
    pending_instances: int
    completed_instances: int
    failed_instances: int

    @classmethod
    def from_dict(cls, data: dict) -> "Report":
        return cls(**data)

    def format_stats(self) -> str:
        resolved_total = self.resolved_instances / self.total_instances
        resolved_submitted = (self.resolved_instances / self.submitted_instances) if self.submitted_instances > 0 else 0 
        submitted = self.submitted_instances / self.total_instances
        return (
            f"Resolved (total): {resolved_total:.2%} ({self.total_instances})\n"
            f"Resolved (submitted): {resolved_submitted:.2%} ({self.submitted_instances})\n"
            f"Submitted: {submitted:.2%} ({self.submitted_instances})\n"
            f"Errors: {self.error_instances}\n"
            f"Pending: {self.pending_instances}\n"
            f"Successful runs: {self.completed_instances}\n"
            f"Failed runs: {self.failed_instances}"
        )

def save_report_files(
    run_id: str,
    report: dict,
    response: dict,
    output_dir: Optional[str],
    overwrite: bool
) -> tuple[Path, Optional[Path]]:
    """Save report and response files to disk."""
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        report_path = output_path / f"{run_id}.json"
        response_path = output_path / f"{run_id}.response.json"
    else:
        report_path = Path(f"{run_id}.json")
        response_path = Path(f"{run_id}.response.json")
    
    report_path = safe_save_json(report, report_path, overwrite)
    response_path = safe_save_json(response, response_path, False) if response else None
    
    return report_path, response_path

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
) -> None:
    """Get report for a run from the run ID and save it to disk."""
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
    try:
        with console.status(f"[bold blue]Creating report for run {run_id} (this may take a minute)...", spinner="dots"):
            response = requests.post(f"{API_BASE_URL}/get-report", json=payload)
            response.raise_for_status()
            response_data = response.json()
    except requests.RequestException as e:
        typer.echo(f"Error fetching report: {e}", err=True)
        raise typer.Exit(1)

    report_dict = response_data.pop('report')
    report = Report.from_dict(report_dict)
    typer.echo(report.format_stats())
    
    report_path, response_path = save_report_files(
        run_id, report_dict, response_data, output_dir, overwrite
    )
    
    typer.echo(f"Saved full report to {report_path}!")
    if response_path:
        typer.echo(f"Saved response to {response_path}")