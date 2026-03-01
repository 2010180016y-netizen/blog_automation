"""Centralized HTTP mocking helper for sync flow tests.

We use httpx.MockTransport to avoid external network/dependency coupling in CI.
"""

from typing import Dict, Tuple, Union

import httpx

Payload = Union[dict, str]
RouteMap = Dict[Tuple[str, str], Tuple[int, Payload]]


def build_mock_client(routes: RouteMap) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method, str(request.url))
        if key not in routes:
            return httpx.Response(404, json={"detail": f"unmocked route: {key}"}, request=request)
        status_code, payload = routes[key]
        if isinstance(payload, dict):
            return httpx.Response(status_code, json=payload, request=request)
        return httpx.Response(status_code, text=str(payload), request=request)

    return httpx.Client(transport=httpx.MockTransport(handler), timeout=3.0)
