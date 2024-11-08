import os
import requests
import typer
from typing import Optional

app = typer.Typer(help="List all existing run IDs", name="list-runs")

@app.callback(invoke_without_command=True)
def main(auth_token: Optional[str] = typer.Option(None, help="Auth token to verify", envvar="SWEBENCH_API_KEY")):
    """List all existing run IDs in your account"""
    payload = {
        "auth_token": auth_token
    }
    response = requests.post("https://api.swebench.com/list-runs", json=payload)
    result = response.json()
    if 'error' in result:
        typer.secho(f"Error: {result['error']}", fg="red", err=True)
    else:
        typer.echo("Run IDs:")
        for run_id in result['run_ids']:
            typer.echo(run_id)
