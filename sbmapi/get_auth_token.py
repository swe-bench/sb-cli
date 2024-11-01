# function_url = 'https://dt7fohwzhwmoqijg6z3pbip7sq0nvdby.lambda-url.us-east-2.on.aws/'
function_url = 'https://api.swebench.com/prod/sbm-get-auth'
import json
import requests
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter


def main(email: str):
    payload = {
        'email': email,
    }
    response = requests.post(function_url, json=payload)
    print(response.json())


if __name__ == "__main__":
    parser = ArgumentParser(description="Get auth token", formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("--email", required=True, help="Email to get auth token for")
    args = parser.parse_args()
    main(args.email)
