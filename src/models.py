class ApiRequest:
    def __init__(self, name, method, url, headers, payload):
        self.name = name
        self.method = method
        self.url = url
        self.headers = headers
        self.payload = payload

    def to_dict(self):
        return {
            "name": self.name,
            "method": self.method,
            "url": self.url,
            "headers": self.headers,
            "payload": self.payload
        }

    @staticmethod
    def from_dict(d):
        return ApiRequest(
            d["name"], d["method"], d["url"], d["headers"], d["payload"]
        )
