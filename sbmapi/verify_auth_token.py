function_url = 'https://api.swebench.com/verify-token'
import json
import requests
import os
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter


def main(auth_token: str, verification_code: str):
    payload = {
        'auth_token': auth_token,
        'verification_code': verification_code
    }
    response = requests.post(function_url, json=payload)
    print(response.json())


if __name__ == "__main__":
    parser = ArgumentParser(description="Verify auth token", formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("--auth_token", required=False, help="Auth token to verify")
    parser.add_argument("--verification_code", required=True, help="Verification code to verify")
    args = parser.parse_args()
    if not args.auth_token:
        args.auth_token = os.getenv('SWEBENCH_API_KEY')
    main(args.auth_token, args.verification_code)
