import typer
from . import (
    gen_auth_token,
    get_report,
    list_runs,
    submit,
    verify_token
)

app = typer.Typer(help="CLI tool for interacting with the SWE-bench M API")

app.command(name="get-report")(get_report.get_report)
app.command(name="list-runs")(list_runs.list_runs)
app.command(name="submit")(submit.submit)
app.command(name="verify-token")(verify_token.verify)
app.command(name="get-auth-token")(gen_auth_token.get_token)

def main():
    """Run the SWE-bench CLI application"""
    import sys
    if len(sys.argv) == 1:
        app(['--help'])
    else:
        app()
