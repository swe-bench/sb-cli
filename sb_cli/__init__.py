import typer

app = typer.Typer(help="CLI tool for interacting with the SWE-bench M API")

from . import (
    gen_api_key,
    get_report,
    list_runs,
    submit,
    verify_api_key,
    delete_run,
    get_quotas
)

app.command(name="get-report")(get_report.get_report)
app.command(name="list-runs")(list_runs.list_runs)
app.command(name="submit")(submit.submit)
app.command(name="verify-api-key")(verify_api_key.verify)
app.command(name="gen-api-key")(gen_api_key.gen_api_key)
app.command(name="delete-run")(delete_run.delete_run)
app.command(name="get-quotas")(get_quotas.get_quotas)
def main():
    """Run the SWE-bench CLI application"""
    import sys
    if len(sys.argv) == 1:
        app(['--help'])
    else:
        app()
