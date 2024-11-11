import requests
import typer
from .constants import URL_ROOT

app = typer.Typer(help="Get an authentication token for accessing the SWE-bench M API")

def get_token(
    email: str = typer.Argument(
        ..., 
        help="Email address to generate an authentication token for",
        show_default=False
    )
):
    """
    Generate a new authentication token for accessing the SWE-bench API.
    
    The token will be sent to the provided email address along with a verification code.
    You will need to verify the token using the 'verify-token' command before it can be used.
    """
    payload = {
        'email': email,
    }
    response = requests.post(f'{URL_ROOT}/gen-auth-token', json=payload)
    result = response.json()
    if response.status_code != 200:
        typer.secho(f"Error: {response.status_code} - {result['message']}", fg="red", err=True)
        raise typer.Exit(1)
    message = result['message']
    auth_token = result['auth_token']
    typer.echo(message)
    typer.echo(auth_token)
