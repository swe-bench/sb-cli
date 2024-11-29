import typer
import requests
from typing import Optional
from rich.console import Console
from sb_cli.config import API_BASE_URL, Subset
from sb_cli.utils import verify_response

app = typer.Typer(help="Delete a specific run by its ID")

def delete_run(
    subset: Subset = typer.Argument(..., help="Subset of the run to delete"),
    split: str = typer.Argument(..., help="Split of the run to delete"),
    run_id: str = typer.Argument(..., help="Run ID to delete"),
    api_key: Optional[str] = typer.Option(None, help="API key to use", envvar="SWEBENCH_API_KEY"),
):
    """Delete a specific run by its ID"""
    console = Console()
    headers = {
        "x-api-key": api_key
    }
    payload = {
        "run_id": run_id,
        "split": split,
        "subset": subset.value
    }
    
    with console.status(f"[blue]Deleting run {run_id}..."):
        response = requests.delete(
            f"{API_BASE_URL}/delete-run",
            headers=headers,
            json=payload
        )
        verify_response(response)
        result = response.json()
    
    if response.status_code == 200:
        typer.echo(f"Run {run_id} successfully deleted for subset {subset.value} and split {split}")
    else:
        typer.echo(f"Failed to delete run {run_id}: {result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    app()
