import os
import requests
import typer
from typing import Optional

app = typer.Typer(help="List all existing run IDs", name="list-runs")

def list_runs(auth_token: Optional[str] = typer.Option(None, help="Auth token to verify", envvar="SWEBENCH_API_KEY")):
    """List all existing run IDs in your account"""
    payload = {
        "auth_token": auth_token
    }
    response = requests.post("https://api.swebench.com/list-runs", json=payload)
    result = response.json()
    if 'error' in result:
        typer.secho(f"Error: {result['error']}", fg="red", err=True)
    elif len(result['run_ids']) == 0:
        typer.echo("No runs found")
    else:
        typer.echo("Run IDs:")
        for run_id in result['run_ids']:
            typer.echo(run_id)
