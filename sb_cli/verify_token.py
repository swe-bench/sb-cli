import requests
import typer
from typing import Optional
from .constants import API_BASE_URL

app = typer.Typer()

def verify(
    verification_code: str = typer.Argument(..., help="Verification code to verify"),
    auth_token: Optional[str] = typer.Option(None, '--auth_token', help="Auth token to verify", envvar="SWEBENCH_API_KEY"),
):
    """Verify auth token against the SWE-bench M API."""
    try:
        payload = {
            'auth_token': auth_token,
            'verification_code': verification_code
        }
        response = requests.post(f"{API_BASE_URL}/verify-token", json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        message = response.json()['message']
        typer.echo(message)
    except requests.RequestException as e:
        typer.secho(f"API request failed: {str(e)}", fg="red", err=True)
        raise typer.Exit(1)
