import typer
from . import (
    get_report,
    list_runs,
    submit_predictions,
    verify_auth_token,
    get_auth_token
)

app = typer.Typer(help="CLI tool for interacting with the SWE-bench M API")

app.command(name="get-report")(get_report.get_report)
app.command(name="list-runs")(list_runs.list_runs)
app.command(name="submit")(submit_predictions.submit)
app.command(name="verify-token")(verify_auth_token.verify)
app.command(name="get-auth-token")(get_auth_token.get_token)

def main():
    """Run the SWE-bench CLI application"""
    import sys
    if len(sys.argv) == 1:
        app(['--help'])
    else:
        app()
