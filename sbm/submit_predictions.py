import json
import os
import requests
import typer
from typing import Optional, List
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.console import Console

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
    instance_ids: Optional[List[str]] = typer.Option(
        None, 
        '--instance_ids', 
        help="Instance ID subset to submit predictions - (defaults to all submitted instances)"
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
    
    console = Console()
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Submitting predictions..."),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    )
    
    with progress:
        task = progress.add_task("", total=None)  # Unknown total initially
        with requests.post("https://api.swebench.com/submit", json=payload, stream=True) as response:
            for line in response.iter_lines():
                if line:
                    status = json.loads(line.decode('utf-8'))
                    if 'status' not in status:
                        raise ValueError(f"Error submitting predictions: {str(status)}")
                    
                    # Update progress
                    progress.update(task, 
                        total=status['total'],
                        completed=status['succeeded'],
                        description=f"[green]✓ {status['succeeded']}[/] - [red]✗ {status['failed']}[/] - Total: {status['total']}"
                    )
                    
                    if status['status'] == 'complete':
                        console.print("\n[bold green]✓ Submission complete![/]")
                        break
