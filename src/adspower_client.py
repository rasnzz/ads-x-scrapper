import requests
from typing import Dict, List, Optional


class AdsPowerClient:
    def __init__(self, base_url: str = "http://local.adspower.net:50325", api_key: str = None):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    def start_profile(self, user_id: str, headless: bool = False) -> dict:
        url = f"{self.base_url}/api/v2/browser-profile/start"
        payload = {
            "profile_id": user_id,
            "params": {
                "open_tabs": 1,
                "ip_tab": 0,
                "headless": 1 if headless else 0,
                "clear_cache_after_closing": 0
            }
        }
        resp = requests.post(url, json=payload, headers=self.headers)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"AdsPower API error: {data.get('msg')}")
        return data["data"]

    def stop_profile(self, user_id: str) -> bool:
        url = f"{self.base_url}/api/v2/browser-profile/stop"
        # Согласно документации, параметры должны передаваться в теле запроса
        payload = {
            "profile_id": user_id
        }
        resp = requests.post(url, json=payload, headers=self.headers)
        resp.raise_for_status()
        data = resp.json()
        return data.get("code") == 0

    def get_profile_list(self, page: int = 1, page_size: int = 100) -> list:
        url = f"{self.base_url}/api/v1/user/list"
        params = {"page": page, "page_size": page_size}
        resp = requests.get(url, params=params, headers=self.headers)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"AdsPower API error: {data.get('msg')}")
        return data["data"]["list"]

    def get_profile_status(self, user_id: str) -> bool:
        url = f"{self.base_url}/api/v1/browser/active"
        params = {"user_id": user_id}
        resp = requests.get(url, params=params, headers=self.headers)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"AdsPower API error: {data.get('msg')}")
        return data["data"]["active"]