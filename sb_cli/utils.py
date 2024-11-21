import requests

def verify_response(response):
    if response.status_code != 200:
        message = response.json().get("message", "No message provided")
        raise requests.RequestException(f"API request failed with status code {response.status_code}: {message}")