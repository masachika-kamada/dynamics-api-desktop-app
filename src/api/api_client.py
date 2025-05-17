import json
import requests


class APIClient:
    def get(self, url, token, headers):
        headers = dict(headers)  # copy
        headers["Authorization"] = f"Bearer {token}"
        response = requests.get(url, headers=headers)
        return response

    def post(self, url, token, data, headers):
        headers = dict(headers)  # copy
        headers["Authorization"] = f"Bearer {token}"
        response = requests.post(url, headers=headers, data=json.dumps(data))
        return response
