from typing import Any, Dict, Optional

import requests


def _build_response(resp: requests.Response) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "status": resp.status_code,
        "ok": resp.ok,
        "url": resp.url,
        "text": resp.text,
    }
    try:
        data["json"] = resp.json()
    except ValueError:
        data["json"] = None
    return data


def http_get(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 20,
) -> Dict[str, Any]:
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        return _build_response(resp)
    except requests.RequestException as e:
        return {"status": None, "ok": False, "url": url, "text": "", "json": None, "error": str(e)}


def http_post(
    url: str,
    json_body: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 20,
) -> Dict[str, Any]:
    try:
        resp = requests.post(url, json=json_body, headers=headers, timeout=timeout)
        return _build_response(resp)
    except requests.RequestException as e:
        return {"status": None, "ok": False, "url": url, "text": "", "json": None, "error": str(e)}
