import os
from typing import Any, Dict, Optional

import httpx

GITHUB_API = "https://api.github.com"


def _headers(token: Optional[str] = None) -> Dict[str, str]:
    token = token or os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


class GitHubClient:
    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN")
        self._client = httpx.AsyncClient(headers=_headers(self.token), timeout=20)

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        resp = await self._client.get(f"{GITHUB_API}{path}", params=params)
        resp.raise_for_status()
        return resp.json()

    async def close(self) -> None:
        await self._client.aclose()


