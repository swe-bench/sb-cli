import json
import time
import requests
import typer
from typing import Optional, List
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.console import Console
from sb_cli.config import API_BASE_URL
from sb_cli.get_report import get_report
from sb_cli.utils import verify_response

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
    
    
def wait_for_running(all_ids: list[str], api_key: str, run_id: str, console: Console, timeout):
    """Spin a progress bar until no predictions are pending."""
    headers = {
        "x-api-key": api_key
    }
    poll_payload = {
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
            poll_response = requests.get(f'{API_BASE_URL}/poll-jobs', json=poll_payload, headers=headers)
            verify_response(poll_response)
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


def wait_for_completion(all_ids: list[str], api_key: str, run_id: str, console: Console, timeout):
    """Spin a progress bar until all predictions are complete."""
    headers = {
        "x-api-key": api_key
    }
    poll_payload = {
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
            poll_response = requests.get(f'{API_BASE_URL}/poll-jobs', json=poll_payload, headers=headers)
            verify_response(poll_response)
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
    api_key: Optional[str] = typer.Option(
        None, 
        '--api_key', 
        help="API key to use - (defaults to SWEBENCH_API_KEY)", 
        envvar="SWEBENCH_API_KEY"
    ),
    instance_ids: Optional[str] = typer.Option(
        None, 
        '--instance_ids',
        help="Instance ID subset to submit predictions - (defaults to all submitted instances)",
        callback=lambda x: x.split(',') if x else None  # Split comma-separated string into list
    ),
    output_dir: Optional[str] = typer.Option(
        'sb-cli-reports',
        '--output_dir',
        '-o',
        help="Directory to save report files"
    ),
    overwrite: bool = typer.Option(False, '--overwrite', help="Overwrite existing report"),
    report: bool = typer.Option(
        True,
        '--report/--no-report',
        help="Generate a report after evaluation is complete"
    )
):
    """Submit predictions to the SWE-bench M API."""
    console = Console()
    predictions = process_predictions(predictions_path, instance_ids)
    headers = {
        "x-api-key": api_key
    }
    payload = {
        "predictions": predictions,
        "split": "dev",
        "instance_ids": instance_ids,
        "run_id": run_id
    }
    response = requests.post(f'{API_BASE_URL}/submit', json=payload, headers=headers)
    verify_response(response)
    launch_data = response.json()
    all_ids = launch_data['new_ids'] + launch_data['completed_ids']
    if len(launch_data['completed_ids']) > 0:
        console.print(f'[bold yellow]Warning: {len(launch_data["completed_ids"])} predictions already submitted. These will not be re-evaluated[/]')
    if len(launch_data['new_ids']) > 0:
        console.print(f'[bold green]✓ {len(launch_data["new_ids"])} new predictions uploaded[/]')
    wait_for_running(all_ids, api_key, run_id, console, timeout=60 * 5)
    if report:
        wait_for_completion(all_ids, api_key, run_id, console, timeout=60 * 30)
        get_report(
            run_id=run_id,
            api_key=api_key,
            output_dir=output_dir,
            overwrite=overwrite,
            extra_args=None,
        )
