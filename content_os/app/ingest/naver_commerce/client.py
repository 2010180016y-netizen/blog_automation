from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx


@dataclass
class OAuthToken:
    access_token: str
    expires_at: float

    def is_expired(self, skew_s: int = 120) -> bool:
        return time.time() >= (self.expires_at - skew_s)


class NaverCommerceClient:
    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str,
        requester=None,
        max_retries: int = 3,
        timeout_s: float = 15.0,
        token_body_format: str = "form",
    ):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self._requester = requester
        self.max_retries = max_retries
        self.timeout_s = timeout_s
        self._token: Optional[OAuthToken] = None
        self.token_body_format = token_body_format

    def _request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        data_body: Optional[Dict[str, Any]] = None,
    ):
        url = f"{self.base_url}{path}"
        if self._requester:
            return self._requester(method=method, url=url, headers=headers, json=json_body, data=data_body)

        with httpx.Client(timeout=self.timeout_s) as client:
            return client.request(method=method, url=url, headers=headers, json=json_body, data=data_body)

    def issue_token(self) -> OAuthToken:
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        preferred = os.getenv("NAVER_OAUTH_TOKEN_BODY_FORMAT", self.token_body_format).lower()

        if preferred == "json":
            response = self._request("POST", "/v1/oauth2/token", headers={"Content-Type": "application/json"}, json_body=payload)
        else:
            response = self._request(
                "POST",
                "/v1/oauth2/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data_body=payload,
            )
            if response.status_code in (400, 401, 403, 404, 415):
                response = self._request(
                    "POST",
                    "/v1/oauth2/token",
                    headers={"Content-Type": "application/json"},
                    json_body=payload,
                )

        response.raise_for_status()
        data = response.json()
        token = data.get("access_token")
        if not token:
            raise RuntimeError("missing access_token in OAuth response")
        expires_in = int(data.get("expires_in", 10800))
        self._token = OAuthToken(access_token=token, expires_at=time.time() + expires_in)
        return self._token

    def get_access_token(self) -> str:
        if self._token is None or self._token.is_expired():
            self.issue_token()
        return self._token.access_token

    def _request_with_retry(self, method: str, path: str, json_body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            token = self.get_access_token()
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            response = self._request(method, path, headers=headers, json_body=json_body)

            if response.status_code == 401:
                self._token = None
                last_error = RuntimeError("unauthorized token")
                continue

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                sleep_s = float(retry_after) if retry_after else min(2 ** attempt, 8)
                time.sleep(sleep_s)
                last_error = RuntimeError("rate limited")
                continue

            if response.status_code >= 500:
                time.sleep(min(2 ** attempt, 8))
                last_error = RuntimeError(f"server error: {response.status_code}")
                continue

            response.raise_for_status()
            return response.json()

        if last_error:
            raise last_error
        raise RuntimeError("request failed")

    def search_products(self, page: int = 1, size: int = 100) -> Dict[str, Any]:
        return self._request_with_retry("POST", "/v1/products/search", json_body={"page": page, "size": size})

    def get_channel_product(self, channel_product_no: str) -> Dict[str, Any]:
        return self._request_with_retry("GET", f"/v2/products/channel-products/{channel_product_no}")

    def get_origin_product(self, origin_product_no: str) -> Dict[str, Any]:
        return self._request_with_retry("GET", f"/v2/products/origin-products/{origin_product_no}")
