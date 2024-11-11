import os
import requests
import typer
from typing import Optional
from .constants import URL_ROOT

app = typer.Typer(help="List all existing run IDs", name="list-runs")

def list_runs(auth_token: Optional[str] = typer.Option(None, help="Auth token to verify", envvar="SWEBENCH_API_KEY")):
    """List all existing run IDs in your account"""
    payload = {
        "auth_token": auth_token
    }
    response = requests.post(f"{URL_ROOT}/list-runs", json=payload)
    result = response.json()
    if response.status_code != 200:
        typer.secho(f"Error: {result['message']}", fg="red", err=True)
        raise typer.Exit(1)
    elif len(result['run_ids']) == 0:
        typer.echo("No runs found")
    else:
        typer.echo("Run IDs:")
        for run_id in result['run_ids']:
            typer.echo(run_id)
