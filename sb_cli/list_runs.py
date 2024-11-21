import os
import requests
import typer
from typing import Optional
from sb_cli.config import API_BASE_URL
from sb_cli.utils import verify_response

app = typer.Typer(help="List all existing run IDs", name="list-runs")

def list_runs(api_key: Optional[str] = typer.Option(None, help="API key to use", envvar="SWEBENCH_API_KEY")):
    """List all existing run IDs in your account"""
    headers = {
        "x-api-key": api_key
    }
    response = requests.post(f"{API_BASE_URL}/list-runs", headers=headers)
    verify_response(response)
    result = response.json()
    if len(result['run_ids']) == 0:
        typer.echo("No runs found")
    else:
        typer.echo("Run IDs:")
        for run_id in result['run_ids']:
            typer.echo(run_id)
