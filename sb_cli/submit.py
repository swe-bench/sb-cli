import json
import time
import requests
import typer
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.console import Console
from sb_cli.config import API_BASE_URL, Subset
from sb_cli.get_report import get_report
from sb_cli.utils import verify_response

app = typer.Typer(help="Submit predictions to the SBM API")

# Helper Functions
def chunk_dict(data: dict, chunk_size: int):
    """Split dictionary into chunks of specified size."""
    items = list(data.items())
    for i in range(0, len(items), chunk_size):
        chunk = dict(items[i:i + chunk_size])
        yield chunk

def submit_chunk(chunk: dict, headers: dict, payload_base: dict):
    """Submit a single chunk of predictions."""
    payload = payload_base.copy()
    payload["predictions"] = chunk
    response = requests.post(f'{API_BASE_URL}/submit', json=payload, headers=headers)
    verify_response(response)
    return response.json()

# Prediction Processing
def process_predictions(predictions_path: str, instance_ids: list[str]):
    """Load and validate predictions from file."""
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
    """Process polling response and categorize instance IDs."""
    running_ids = set(results['running']) & set(all_ids)
    completed_ids = set(results['completed']) & set(all_ids)
    pending_ids = set(all_ids) - running_ids - completed_ids
    return {
        'running': list(running_ids),
        'completed': list(completed_ids),
        'pending': list(pending_ids)
    }
    
# Progress Tracking Functions
def wait_for_running(*, all_ids: list[str], api_key: str, subset: str,
                    split: str, run_id: str, console: Console, timeout):
    """Spin a progress bar until no predictions are pending."""
    headers = {
        "x-api-key": api_key
    }
    poll_payload = {
        'run_id': run_id,
        'subset': subset,
        'split': split
    }
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Processing submission..."),
        BarColumn(),
        TaskProgressColumn(text_format="[progress.percentage]{task.percentage:>3.2f}%"),
        TimeElapsedColumn(),
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
                # if progress is 0, raise an error, otherwise just print a warning
                if progress.task_total == 0:
                    raise ValueError((
                        "Submission waiter timed out without making progress - this is probably a bug.\n"
                        "Please submit a bug report at https://github.com/swe-bench/sb-cli/issues"
                    ))
                else:
                    console.print(
                        "[bold red]Submission waiter timed out - re-run the command to continue waiting[/]"
                )
                break
            else:
                time.sleep(8)
        progress.stop()
    console.print("[bold green]✓ Submission complete![/]")

def wait_for_completion(
    *,
    all_ids: list[str],
    api_key: str,
    subset: str,
    split: str,
    run_id: str,
    console: Console,
    timeout: int
):
    """Spin a progress bar until all predictions are complete."""
    headers = {
        "x-api-key": api_key
    }
    poll_payload = {
        'run_id': run_id,
        'subset': subset,
        'split': split
    }
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Evaluating predictions..."),
        BarColumn(),
        TaskProgressColumn(text_format="[progress.percentage]{task.percentage:>3.2f}%"),
        TimeElapsedColumn(),
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
                console.print(
                    "[bold red]Evaluation waiter timed out - re-run the command to continue waiting[/]"
                )
                break
            else:
                time.sleep(15)
        progress.stop()
    console.print("[bold green]✓ Evaluation complete![/]")

# Main Submission Function
def submit(
    subset: Subset = typer.Argument(..., help="Subset to submit predictions for"),
    split: str = typer.Argument(..., help="Split to submit predictions for"),
    predictions_path: str = typer.Option(..., '--predictions_path', help="Path to the predictions file"),
    run_id: str = typer.Option(..., '--run_id', help="Run ID for the predictions"),
    instance_ids: Optional[str] = typer.Option(
        None, 
        '--instance_ids',
        help="Instance ID subset to submit predictions - (defaults to all submitted instances)",
        callback=lambda x: x.split(',') if x else None
    ),
    output_dir: Optional[str] = typer.Option('sb-cli-reports', '--output_dir', '-o', help="Directory to save report files"),
    overwrite: bool = typer.Option(False, '--overwrite', help="Overwrite existing report"),
    gen_report: bool = typer.Option(True, '--gen_report', help="Generate a report after evaluation is complete"),
    api_key: Optional[str] = typer.Option(
        None, 
        '--api_key', 
        help="API key to use - (defaults to SWEBENCH_API_KEY)", 
        envvar="SWEBENCH_API_KEY"
    ),
):
    """Submit predictions to the SWE-bench M API."""
    console = Console()
    predictions = process_predictions(predictions_path, instance_ids)
    headers = {
        "x-api-key": api_key
    }
    payload_base = {
        "split": split,
        "subset": subset,
        "instance_ids": instance_ids,
        "run_id": run_id
    }

    # Split predictions into chunks of 50
    prediction_chunks = list(chunk_dict(predictions, 50))
    
    all_new_ids = []
    all_completed_ids = []
    
    with console.status("[bold blue]Predictions sent. Waiting for confirmation...", spinner="dots"):
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all chunks in parallel
            future_to_chunk = {
                executor.submit(submit_chunk, chunk, headers, payload_base): chunk 
                for chunk in prediction_chunks
            }
            
            # Collect results
            for future in as_completed(future_to_chunk):
                try:
                    launch_data = future.result()
                    all_new_ids.extend(launch_data['new_ids'])
                    all_completed_ids.extend(launch_data['completed_ids'])
                except Exception as e:
                    console.print(f"[bold red]Error submitting chunk: {str(e)}[/]")
                    raise e

    all_ids = all_new_ids + all_completed_ids
    
    if len(all_completed_ids) > 0:
        console.print((
            f'[bold yellow]Warning: {len(all_completed_ids)} predictions already submitted. '
            'These will not be re-evaluated[/]'
        ))
    if len(all_new_ids) > 0:
        console.print(
            f'[bold green]✓ {len(all_new_ids)} new predictions uploaded[/][bold yellow] - these cannot be changed[/]'
        )

    run_metadata = {
        'run_id': run_id,
        'subset': subset.value,
        'split': split,
        'api_key': api_key
    }
    wait_for_running(
        all_ids=all_ids, 
        console=console, 
        timeout=60 * 5,
        **run_metadata
    )
    if gen_report:
        wait_for_completion(
            all_ids=all_ids, 
            console=console, 
            timeout=60 * 1,
            **run_metadata
        )
        get_report(
            output_dir=output_dir,
            overwrite=overwrite,
            **run_metadata,
        )
