import requests


class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        return self.session.get(f"{self.base_url}{endpoint}", **kwargs)

    def post(self, endpoint: str, payload: dict, **kwargs) -> requests.Response:
        return self.session.post(f"{self.base_url}{endpoint}", json=payload, **kwargs)

    def put(self, endpoint: str, payload: dict, **kwargs) -> requests.Response:
        return self.session.put(f"{self.base_url}{endpoint}", json=payload, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        return self.session.delete(f"{self.base_url}{endpoint}", **kwargs)
