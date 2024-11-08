function_url = 'https://api.swebench.com/gen-auth-token'
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
