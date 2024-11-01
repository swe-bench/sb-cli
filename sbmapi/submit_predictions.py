import requests
import json
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter

function_url = 'https://zackrtimj6lcc427vggtkcnt3a0dlpkr.lambda-url.us-east-2.on.aws/'


def main(
    auth_token: str,
    predictions_path: str,
    instance_ids: list[str],
    run_id: str
):
    with open(predictions_path, 'r') as f:
        if predictions_path.endswith('.json'):
            predictions = json.load(f)
            if isinstance(predictions, list):
                predictions = {p['instance_id']: p for p in predictions}
        else:
            # Convert list of predictions to a dictionary with instance_id as key
            predictions_list = [json.loads(line) for line in f]
            predictions = {p['instance_id']: p for p in predictions_list}
    payload = {
        "auth_token": auth_token,
        "predictions": predictions,
        "split": "dev",
        "instance_ids": instance_ids,
        "run_id": run_id
    }
    # Method 1: Stream the response (recommended)
    with requests.post(f"{function_url}/api/evaluate", json=payload, stream=True) as response:
        for line in response.iter_lines():
            if line:
                status = json.loads(line.decode('utf-8'))
                print(f"Progress: {status['succeeded']} submitted - {status['failed']} failed - {status['total']} total")
                if status['status'] == 'complete':
                    print("Launch complete")
                    break


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Submit predictions to the SBMapi",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--auth_token", type=str, required=True)
    parser.add_argument("--predictions_path", type=str, required=True)
    parser.add_argument("--instance_ids", type=str, required=False, nargs='+')
    parser.add_argument("--run_id", type=str, required=True)
    args = parser.parse_args()
    main(args.auth_token, args.predictions_path, args.instance_ids, args.run_id)
