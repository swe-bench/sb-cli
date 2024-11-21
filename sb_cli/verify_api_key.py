import requests
import typer
from typing import Optional
from sb_cli.config import API_BASE_URL
from sb_cli.utils import verify_response

app = typer.Typer()

def verify(
    verification_code: str = typer.Argument(..., help="Verification code to verify"),
    api_key: Optional[str] = typer.Option(None, '--api_key', help="API key to verify", envvar="SWEBENCH_API_KEY"),
):
    """Verify API key against the SWE-bench M API."""
    headers = {
        "x-api-key": api_key
    }
    try:
        payload = {
            'verification_code': verification_code
        }
        response = requests.post(f"{API_BASE_URL}/verify-api-key", json=payload, headers=headers)
        verify_response(response)
        message = response.json()['message']
        typer.echo(message)
    except requests.RequestException as e:
        typer.secho(f"API request failed: {str(e)}", fg="red", err=True)
        raise typer.Exit(1)
