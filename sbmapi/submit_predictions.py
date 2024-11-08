function_url = 'https://api.swebench.com/submit'
import requests
import json
import os
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter


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
            preds.append({'instance_id': instance_id, 'model_patch': p['model_patch'], 'model_name_or_path': p['model_name_or_path']})
    else:
        for instance_id, p in predictions.items():
            if instance_ids and instance_id not in instance_ids:
                continue
            preds.append({'instance_id': instance_id, 'model_patch': p['model_patch'], 'model_name_or_path': p['model_name_or_path']})
    if len(set([p['model_name_or_path'] for p in preds])) > 1:
        raise ValueError("All predictions must be for the same model")
    if len(set([p['instance_id'] for p in preds])) != len(preds):
        raise ValueError("Duplicate instance IDs found in predictions - please remove duplicates before submitting")
    return {p['instance_id']: p for p in preds}


def main(
    auth_token: str,
    predictions_path: str,
    instance_ids: list[str],
    run_id: str
):
    predictions = process_predictions(predictions_path, instance_ids)
    payload = {
        "auth_token": auth_token,
        "predictions": predictions,
        "split": "dev",
        "instance_ids": instance_ids,
        "run_id": run_id
    }
    with requests.post(f"{function_url}/api/evaluate", json=payload, stream=True) as response:
        for line in response.iter_lines():
            if line:
                status = json.loads(line.decode('utf-8'))
                if 'status' not in status:
                    raise ValueError(f"Error submitting predictions: {str(status)}")
                print(f"Progress: {status['succeeded']} submitted - {status['failed']} failed - {status['total']} total")
                if status['status'] == 'complete':
                    print("Launch complete")
                    break


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Submit predictions to the SBMapi",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--auth_token", type=str, required=False, help="Auth token to use - optional, will use SWEBENCH_API_KEY if not provided")
    parser.add_argument("--predictions_path", type=str, required=True, help="Path to the predictions file")
    parser.add_argument("--instance_ids", type=str, required=False, nargs='+', help="Instance IDs to submit predictions for - optional, will submit all instances if not provided")
    parser.add_argument("--run_id", type=str, required=True, help="Run ID for the predictions")
    args = parser.parse_args()
    if not args.auth_token:
        args.auth_token = os.getenv('SWEBENCH_API_KEY')
    main(args.auth_token, args.predictions_path, args.instance_ids, args.run_id)
