function_url = 'https://api.swebench.com/list-runs'
import requests
import json
import os
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter


def main(auth_token: str):
    payload = {
        "auth_token": auth_token
    }
    response = requests.post(f"{function_url}/api/list_runs", json=payload)
    result = response.json()
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print("Run IDs:")
        for run_id in result['run_ids']:
            print(run_id)


if __name__ == "__main__":
    parser = ArgumentParser(
        description="List runs from the SBMapi",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--auth_token", type=str, required=False)
    args = parser.parse_args()
    if not args.auth_token:
        args.auth_token = os.getenv('SWEBENCH_API_KEY')
    main(args.auth_token)
