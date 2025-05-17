import json
import requests

class APIClient:
    def get(self, url, token, headers):
        headers = dict(headers)  # copy
        headers["Authorization"] = f"Bearer {token}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"GET request failed: {response.status_code}")
            print(response.text)
            return None

    def post(self, url, token, data, headers):
        headers = dict(headers)  # copy
        headers["Authorization"] = f"Bearer {token}"
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code in [200, 204]:
            return response.json()
        else:
            print(f"POST request failed: {response.status_code}")
            print(response.text)
            return None
