import typer
from . import (
    get_auth_token,
    get_report,
    list_runs,
    submit_predictions,
    verify_auth_token
)

app = typer.Typer(help="CLI tool for interacting with the SWE-bench M API")
app.add_typer(get_report.app, name="get-report")
app.add_typer(list_runs.app, name="list-runs")
app.add_typer(submit_predictions.app, name="submit")
app.add_typer(verify_auth_token.app, name="verify-token")
app.add_typer(get_auth_token.app, name="get-auth-token")

def main():
    """Run the SWE-bench CLI application"""
    import sys
    if len(sys.argv) == 1:
        app(['--help'])
    else:
        app()
