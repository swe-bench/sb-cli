import json
import time
import requests
import typer
import sys
from typing import Optional
from typing_extensions import Annotated
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.console import Console
from sb_cli.config import API_BASE_URL, Subset
from sb_cli.get_report import get_report
from sb_cli.utils import verify_response
from pathlib import Path

app = typer.Typer(help="Submit predictions to the SBM API")

def submit_prediction(prediction: dict, headers: dict, payload_base: dict):
    """Submit a single prediction."""
    payload = payload_base.copy()
    payload["prediction"] = prediction
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
    return preds

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
def run_progress_task(
    console: Console, 
    task_name: str, 
    total: int, 
    task_func, 
    timeout: Optional[int] = None, 
    *args, 
    **kwargs
):
    """Run a task with a progress bar and a default timeout."""
    progress = Progress(
        SpinnerColumn(),
        TextColumn(f"[blue]{task_name}..."),
        BarColumn(),
        TaskProgressColumn(text_format="[progress.percentage]{task.percentage:>3.1f}%"),
        TimeElapsedColumn(),
        console=console,
    )
    start_time = time.time()
    completed = 0
    exception = None
    with progress:
        task = progress.add_task("", total=total)
        try:
            # Run the task function with a timeout
            result = task_func(progress, task, *args, **kwargs)
        except Exception as e:
            exception = e
        finally:
            elapsed_time = time.time() - start_time
            progress.stop()
            if exception:
                console.print(f"[red]Error during task: {str(exception)}[/]")
                raise exception
            final_percentage = progress.tasks[task].completed / progress.tasks[task].total * 100
            completed = progress.tasks[task].completed
            total = progress.tasks[task].total
            progress.remove_task(task)
            if completed == total:
                console.print(f"[green]✓ {task_name} complete![/]")
            elif timeout and elapsed_time > timeout:
                # don't print the timeout message if the task completed
                console.print(f"[red]✗ {task_name} timed out after {timeout} seconds. Try re-running submit to continue.[/]")
                sys.exit(1)
            else:
                console.print(f"[yellow]✓ {task_name} completed with {completed}/{total} instances[/]")
    return {
        "result": result,
        "elapsed_time": elapsed_time,
        "final_percentage": final_percentage,
        "completed": completed,
        "total": total,
        "timeout": timeout and elapsed_time > timeout,
    }

def submit_predictions_with_progress(
    predictions: list[dict], 
    headers: dict, 
    payload_base: dict, 
) -> tuple[list[str], list[str]]:
    """Submit predictions with a progress bar and return new and completed IDs."""
    def task_func(progress, task):
        all_new_ids = []
        all_completed_ids = []
        failed_ids = []
        with ThreadPoolExecutor(max_workers=min(24, len(predictions))) as executor:
            future_to_prediction = {
                executor.submit(submit_prediction, pred, headers, payload_base): pred 
                for pred in predictions
            }
            for future in as_completed(future_to_prediction):
                try:
                    launch_data = future.result()
                    if launch_data["launched"]:
                        all_new_ids.append(launch_data['instance_id'])
                    else:
                        all_completed_ids.append(launch_data['instance_id'])
                except Exception as e:
                    # Retrieve the prediction associated with the failed future
                    pred = future_to_prediction[future]
                    failed_ids.append(pred['instance_id'])
                    raise RuntimeError(f"Error submitting prediction for instance {pred['instance_id']}: {str(e)}")
                finally:
                    progress.update(task, advance=1)
        return {
            "new_ids": all_new_ids,
            "all_completed_ids": all_completed_ids,
            "failed_ids": failed_ids
        }
    console = Console()
    result = run_progress_task(
        console,
        "Submitting predictions", 
        len(predictions), 
        task_func,
    )["result"]
    new_ids = result["new_ids"]
    all_completed_ids = result["all_completed_ids"]
    failed_ids = result["failed_ids"]
    if len(all_completed_ids) > 0:
        console.print((
            f'[yellow]  Warning: {len(all_completed_ids)} predictions already submitted. '
            'These will not be re-evaluated[/]'
        ))
    if len(new_ids) > 0:
        console.print(
            f'[green]  {len(new_ids)} new predictions uploaded[/][yellow] - these cannot be changed[/]'
        )
    if len(failed_ids) > 0:
        console.print(
            f'[red]✗ {len(failed_ids)} predictions failed to submit[/]'
        )
    return new_ids, all_completed_ids

def wait_for_running(
    *, 
    all_ids: list[str], 
    api_key: str, 
    subset: str,
    split: str, 
    run_id: str, 
    timeout: int
):
    """Spin a progress bar until no predictions are pending."""
    def task_func(progress, task):
        headers = {"x-api-key": api_key}
        poll_payload = {'run_id': run_id, 'subset': subset, 'split': split}
        start_time = time.time()
        while True:
            poll_response = requests.get(f'{API_BASE_URL}/poll-jobs', json=poll_payload, headers=headers)
            verify_response(poll_response)
            poll_results = process_poll_response(poll_response.json(), all_ids)
            progress.update(task, completed=len(poll_results['running']) + len(poll_results['completed']))
            if len(poll_results['pending']) == 0:
                break

            if (time.time() - start_time) > timeout:
                break
            else:
                time.sleep(8)
    result = run_progress_task(
        Console(),
        "Processing submission", 
        len(all_ids), 
        task_func,
        timeout=timeout,
    )
    if result["timeout"] and result["completed"] == 0:
        raise ValueError((
            "Submission waiter timed out without making progress - this is probably a bug.\n"
            "Please submit a bug report at https://github.com/swe-bench/sb-cli/issues"
        ))

def wait_for_evaluation(
    *,
    all_ids: list[str],
    api_key: str,
    subset: str,
    split: str,
    run_id: str,
    timeout: int
):
    """Spin a progress bar until all predictions are complete."""
    def task_func(progress, task):
        headers = {"x-api-key": api_key}
        poll_payload = {'run_id': run_id, 'subset': subset, 'split': split}
        start_time = time.time()
        while True:
            poll_response = requests.get(f'{API_BASE_URL}/poll-jobs', json=poll_payload, headers=headers)
            verify_response(poll_response)
            poll_results = process_poll_response(poll_response.json(), all_ids)
            progress.update(task, completed=len(poll_results['completed']))
            if len(poll_results['completed']) == len(all_ids):
                break

            if (time.time() - start_time) > timeout:
                break
            else:
                time.sleep(15)

    run_progress_task(
        Console(),
        "Evaluating predictions", 
        len(all_ids), 
        task_func,
        timeout=timeout,
    )

# Main Submission Function
def submit(
    subset: Subset = typer.Argument(..., help="Subset to submit predictions for"),
    split: str = typer.Argument(..., help="Split to submit predictions for"),
    predictions_path: str = typer.Option(..., '--predictions_path', help="Path to the predictions file"),
    run_id: str = typer.Option("PARENT", '--run_id', help="Run ID for the predictions"),
    instance_ids: Optional[str] = typer.Option(
        None,
        '--instance_ids',
        help="Instance ID subset to submit predictions - (defaults to all submitted instances)",
        callback=lambda x: x.split(',') if x else None
    ),
    output_dir: Optional[str] = typer.Option('sb-cli-reports', '--output_dir', '-o', help="Directory to save report files"),
    overwrite: int = typer.Option(0, '--overwrite', help="Overwrite existing report"),
    gen_report: int = typer.Option(1, '--gen_report', help="Generate a report after evaluation is complete"),
    verify_submission: int = typer.Option(1, '--verify_submission', help="Verify submission before waiting for completion"),
    should_wait_for_evaluation: int = typer.Option(1, '--wait_for_evaluation', help="Wait for evaluation to complete before generating a report"),
    api_key: Optional[str] = typer.Option(
        None, 
        '--api_key', 
        help="API key to use - (defaults to SWEBENCH_API_KEY)", 
        envvar="SWEBENCH_API_KEY"
    ),
):
    """Submit predictions to the SWE-bench M API."""
    console = Console()
    
    # Convert predictions_path to a Path object
    predictions_path = Path(predictions_path)
    
    # Determine run_id based on special options
    if run_id == "PARENT":
        run_id = predictions_path.parent.name
    elif run_id == "STEM":
        run_id = predictions_path.stem

    predictions = process_predictions(str(predictions_path), instance_ids)
    headers = {
        "x-api-key": api_key
    }
    payload_base = {
        "split": split,
        "subset": subset,
        "instance_ids": instance_ids,
        "run_id": run_id
    }

    console.print(f"[yellow]  Submitting predictions for {run_id} - ({subset.value} {split})[/]")
    
    new_ids, all_completed_ids = submit_predictions_with_progress(predictions, headers, payload_base)
    all_ids = new_ids + all_completed_ids

    run_metadata = {
        'run_id': run_id,
        'subset': subset.value,
        'split': split,
        'api_key': api_key
    }
    if verify_submission:
        wait_for_running(
            all_ids=all_ids, 
            timeout=60 * 5,
            **run_metadata
        )
    if should_wait_for_evaluation:
        wait_for_evaluation(
            all_ids=all_ids, 
            timeout=60 * 10,
            **run_metadata
        )
    if gen_report:
        get_report(
            output_dir=output_dir,
            overwrite=overwrite,
            **run_metadata,
        )
