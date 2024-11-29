import os
import requests
import typer
from typing import Optional
from rich.console import Console
from sb_cli.config import API_BASE_URL, Subset
from sb_cli.utils import verify_response

app = typer.Typer(help="List all existing run IDs", name="list-runs")

def list_runs(
    subset: Subset = typer.Argument(..., help="Subset to list runs for"),
    split: str = typer.Argument(..., help="Split to list runs for"),
    api_key: Optional[str] = typer.Option(None, help="API key to use", envvar="SWEBENCH_API_KEY"),
):
    """List all existing run IDs in your account"""
    console = Console()
    headers = {
        "x-api-key": api_key
    }
    with console.status("[blue]Fetching runs..."):
        response = requests.post(
            f"{API_BASE_URL}/list-runs",
            headers=headers,
            json={"split": split, "subset": subset.value}
        )
        verify_response(response)
        result = response.json()
    
    if len(result['run_ids']) == 0:
        typer.echo(f"No runs found for subset {subset.value} and split {split}")
    else:
        typer.echo(f"Run IDs ({subset.value} - {split}):")
        for run_id in result['run_ids']:
            typer.echo(run_id)
