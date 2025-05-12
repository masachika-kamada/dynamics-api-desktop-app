import json
import requests

class APIClient:
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Accept": "application/json"
        }

    def get(self, url, token):
        self.headers["Authorization"] = f"Bearer {token}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"GET request failed: {response.status_code}")
            print(response.text)
            return None

    def post(self, url, token, data):
        self.headers["Authorization"] = f"Bearer {token}"
        response = requests.post(url, headers=self.headers, data=json.dumps(data))
        if response.status_code in [200, 204]:
            return response.json()
        else:
            print(f"POST request failed: {response.status_code}")
            print(response.text)
            return None