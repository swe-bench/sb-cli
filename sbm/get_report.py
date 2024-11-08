import json
import os
import requests
import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(help="Get the evaluation report for a specific run")

def safe_save_json(data: dict, file_path: str, overwrite: bool = False):
    if Path(file_path).exists() and not overwrite:
        ext = 1
        while Path(f"{file_path}.json-{ext}").exists():
            ext += 1
        file_path = f"{file_path}.json-{ext}"
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
    typer.echo(f"Saved to {file_path}")


@app.callback(invoke_without_command=True, name="get-report")
def main(
    run_id: str = typer.Argument(..., help="Run ID"),
    auth_token: Optional[str] = typer.Option(None, '--auth_token', help="Auth token to verify", envvar="SWEBENCH_API_KEY"),
    overwrite: bool = typer.Option(False, '--overwrite', help="Overwrite existing report"),
    extra_args: Optional[list[str]] = typer.Option(None, '--extra_args', '-e', help="Additional arguments in the format KEY=VALUE")
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
    response = requests.post("https://api.swebench.com/get-report", json=payload)
    response.raise_for_status()
    response = response.json()
    report = response.pop('report')
    safe_save_json(report, f"{run_id}.json", overwrite)
    if response:
        safe_save_json(response, f"{run_id}.response.json", False)
