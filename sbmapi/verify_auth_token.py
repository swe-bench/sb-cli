function_url = 'https://hyjpnlzllvjonvrogyfi7uroku0bxnlc.lambda-url.us-east-2.on.aws/'
import json
import requests
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
    parser.add_argument("--auth_token", required=True, help="Auth token to verify")
    parser.add_argument("--verification_code", required=True, help="Verification code to verify")
    args = parser.parse_args()
    main(args.auth_token, args.verification_code)
