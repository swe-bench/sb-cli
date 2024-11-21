import requests
import typer
from sb_cli.config import API_BASE_URL
from sb_cli.utils import verify_response

app = typer.Typer(help="Get an API key for accessing the SWE-bench M API")

def gen_api_key(
    email: str = typer.Argument(
        ..., 
        help="Email address to generate an API key for",
        show_default=False
    )
):
    """
    Generate a new API key for accessing the SWE-bench API.
    
    The API key will be sent to the provided email address along with a verification code.
    You will need to verify the API key using the 'verify-api-key' command before it can be used.
    """
    payload = {
        'email': email,
    }
    response = requests.post(f'{API_BASE_URL}/gen-api-key', json=payload)
    verify_response(response)
    result = response.json()
    message = result['message']
    api_key = result['api_key']
    typer.echo(message)
    typer.echo(api_key)
