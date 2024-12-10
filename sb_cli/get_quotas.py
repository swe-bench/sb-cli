import requests
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from sb_cli.config import API_BASE_URL
from sb_cli.utils import verify_response

app = typer.Typer(help="Get remaining quota counts for your API key")

def get_quotas(
    api_key: Optional[str] = typer.Option(
        None, 
        '--api_key', 
        help="API key to use", 
        envvar="SWEBENCH_API_KEY"
    ),
):
    """Get remaining quota counts for all authorized subsets and splits."""
    console = Console()
    headers = {"x-api-key": api_key}

    with console.status("[blue]Fetching quota information..."):
        response = requests.get(f"{API_BASE_URL}/get-quotas", headers=headers)
        verify_response(response)
        result = response.json()

    # Create a rich table to display the quotas
    table = Table(title="Remaining Submission Quotas")
    table.add_column("Subset", style="cyan")
    table.add_column("Split", style="magenta")
    table.add_column("Remaining Runs", style="green", justify="right")

    quotas = result["remaining_quotas"]
    if not quotas:
        console.print("[yellow]No remaining quotas found for any subset/split combination[/]")
        return

    # Add rows to the table
    for subset, splits in quotas.items():
        for split, remaining in splits.items():
            table.add_row(subset, split, str(remaining))

    console.print(table)
