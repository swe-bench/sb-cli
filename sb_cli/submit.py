import json
import time
import requests
import typer
from typing import Optional, List
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.console import Console
from .constants import URL_ROOT
from .get_report import get_report

app = typer.Typer(help="Submit predictions to the SBM API")

def process_predictions(predictions_path: str, instance_ids: list[str]):
    with open(predictions_path, 'r') as f:
        if predictions_path.endswith('.json'):
            predictions = json.load(f)
        else:
            predictions = [json.loads(line) for line in f]
    preds = []
    if isinstance(predictions, list):
        for p in predictions:
            instance_id = p['instance_id']
            if instance_ids and instance_id not in instance_ids:
                continue
            preds.append({
                'instance_id': instance_id,
                'model_patch': p['model_patch'],
                'model_name_or_path': p['model_name_or_path']
            })
    else:
        for instance_id, p in predictions.items():
            if instance_ids and instance_id not in instance_ids:
                continue
            preds.append({
                'instance_id': instance_id,
                'model_patch': p['model_patch'],
                'model_name_or_path': p['model_name_or_path']
            })
    if len(set([p['model_name_or_path'] for p in preds])) > 1:
        raise ValueError("All predictions must be for the same model")
    if len(set([p['instance_id'] for p in preds])) != len(preds):
        raise ValueError("Duplicate instance IDs found in predictions - please remove duplicates before submitting")
    return {p['instance_id']: p for p in preds}


def process_poll_response(results: dict, all_ids: list[str]):
    running_ids = set(results['running']) & set(all_ids)
    completed_ids = set(results['completed']) & set(all_ids)
    pending_ids = set(all_ids) - running_ids - completed_ids
    return {
        'running': list(running_ids),
        'completed': list(completed_ids),
        'pending': list(pending_ids)
    }
    
    
def wait_for_running(all_ids: list[str], auth_token: str, run_id: str, console: Console, timeout):
    """Spin a progress bar until no predictions are pending."""
    poll_payload = {
        'auth_token': auth_token,
        'run_id': run_id
    }
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Processing submission..."),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    )
    start_time = time.time()
    with progress:
        task = progress.add_task("", total=len(all_ids))
        while True:
            poll_response = requests.get(f'{URL_ROOT}/poll-jobs', json=poll_payload)
            poll_response.raise_for_status()
            poll_results = process_poll_response(poll_response.json(), all_ids)
            progress.update(task, completed=len(poll_results['running']) + len(poll_results['completed']))
            if len(poll_results['pending']) == 0:
                break
            elif time.time() - start_time > timeout:
                raise ValueError("Submission timed out")
            else:
                time.sleep(8)
        progress.stop()
    console.print("[bold green]✓ Submission complete![/]")


def wait_for_completion(all_ids: list[str], auth_token: str, run_id: str, console: Console, timeout):
    """Spin a progress bar until all predictions are complete."""
    poll_payload = {
        'auth_token': auth_token,
        'run_id': run_id
    }
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Evaluating predictions..."),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    )
    start_time = time.time()
    with progress:
        task = progress.add_task("", total=len(all_ids))
        while True:
            poll_response = requests.get(f'{URL_ROOT}/poll-jobs', json=poll_payload)
            poll_response.raise_for_status()
            poll_results = process_poll_response(poll_response.json(), all_ids)
            progress.update(task, completed=len(poll_results['completed']))
            if len(poll_results['completed']) == len(all_ids):
                break
            elif time.time() - start_time > timeout:
                raise ValueError("Evaluation waiter timed out - re-run the command to continue waiting")
            else:
                time.sleep(15)
        progress.stop()
    console.print("[bold green]✓ Evaluation complete![/]")
        

def submit(
    predictions_path: str = typer.Option(
        ..., 
        '--predictions_path', 
        help="Path to the predictions file"
    ),
    run_id: str = typer.Option(..., '--run_id', help="Run ID for the predictions"),
    auth_token: Optional[str] = typer.Option(
        None, 
        '--auth_token', 
        help="Auth token to use - (defaults to SWEBENCH_API_KEY)", 
        envvar="SWEBENCH_API_KEY"
    ),
    instance_ids: Optional[str] = typer.Option(
        None, 
        '--instance_ids',
        help="Instance ID subset to submit predictions - (defaults to all submitted instances)",
        callback=lambda x: x.split(',') if x else None  # Split comma-separated string into list
    ),
    watch: bool = typer.Option(
        True,
        '--watch/--no-watch',
        help="Watch the submission until evaluation is complete"
    ),
    report: bool = typer.Option(
        True,
        '--report/--no-report',
        help="Generate a report after evaluation is complete"
    )
):
    """Submit predictions to the SWE-bench M API."""
    predictions = process_predictions(predictions_path, instance_ids)
    payload = {
        "auth_token": auth_token,
        "predictions": predictions,
        "split": "dev",
        "instance_ids": instance_ids,
        "run_id": run_id
    }
    response = requests.post(f'{URL_ROOT}/submit', json=payload)
    if response.status_code != 202:
        raise ValueError(f"Error submitting predictions: {response.text}")
    launch_data = response.json()
    all_ids = launch_data['new_ids'] + launch_data['completed_ids']
    console = Console()
    wait_for_running(all_ids, auth_token, run_id, console, timeout=60 * 5)
    if watch:
        wait_for_completion(all_ids, auth_token, run_id, console, timeout=60 * 30)
    if report:
        get_report(run_id, auth_token, extra_args=None)