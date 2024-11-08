import requests
import json
import os
from pathlib import Path
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter


def safe_save_json(data: dict, file_path: str, overwrite: bool = False):
    if Path(file_path).exists() and not overwrite:
        ext = 1
        while Path(f"{file_path}.json-{ext}").exists():
            ext += 1
        file_path = f"{file_path}.json-{ext}"
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Saved to {file_path}")


def main(auth_token: str, run_id: str, overwrite: bool = False, **kwargs):
    payload = {
        'auth_token': auth_token,
        'run_id': run_id,
        **kwargs
    }
    response = requests.post('https://api.swebench.com/get-report', json=payload)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return
    response = response.json()
    report = response.pop('report')
    safe_save_json(report, f"{run_id}.json", overwrite)
    if response:
        safe_save_json(response, f"{run_id}.response.json", False)


if __name__ == "__main__":
    parser = ArgumentParser(description="Get report for a run", formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("--auth_token", required=False, help="Auth token to verify")
    parser.add_argument("--run_id", required=True, help="Run ID")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing report")
    args, unknown = parser.parse_known_args()
    # if auth_token is not provided, try to get it from the environment
    if not args.auth_token:
        args.auth_token = os.getenv('SWEBENCH_API_KEY')
    kwargs = {k.lstrip('-'): v for k, v in zip(unknown[::2], unknown[1::2])}
    main(**vars(args), **kwargs)
