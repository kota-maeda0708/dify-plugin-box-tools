import json
from typing import Any

import requests

BOX_API_BASE = "https://api.box.com/2.0"
BOX_UPLOAD_BASE = "https://upload.box.com/api/2.0"
BOX_TOKEN_URL = "https://api.box.com/oauth2/token"

_REQUEST_TIMEOUT = 30


class BoxAuthError(Exception):
    pass


class BoxApiError(Exception):
    pass


class BoxClient:
    """Thin wrapper around the Box API v2 that accepts either an OAuth
    access token or Client Credentials Grant (client_id/client_secret,
    a.k.a. "Secret Key") credentials.
    """

    def __init__(self, credentials: dict[str, Any]):
        self._access_token = self._resolve_access_token(credentials)

    @staticmethod
    def _resolve_access_token(credentials: dict[str, Any]) -> str:
        access_token = credentials.get("access_token")
        if access_token:
            return access_token

        client_id = (credentials.get("client_id") or "").strip()
        client_secret = (credentials.get("client_secret") or "").strip()
        box_subject_id = (credentials.get("box_subject_id") or "").strip()
        box_subject_type = (credentials.get("box_subject_type") or "enterprise").strip()
        if not client_id or not client_secret or not box_subject_id:
            raise BoxAuthError(
                "Box credentials are incomplete: provide either an OAuth access token, "
                "or client_id / client_secret / box_subject_id for Client Credentials Grant."
            )

        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "box_subject_type": box_subject_type,
            "box_subject_id": box_subject_id,
        }
        try:
            response = requests.post(BOX_TOKEN_URL, data=data, timeout=_REQUEST_TIMEOUT)
        except requests.exceptions.RequestException as e:
            raise BoxAuthError(f"Failed to reach Box while requesting an access token: {e}") from e
        if response.status_code != 200:
            raise BoxAuthError(f"Failed to obtain a Box access token: {response.text}")
        try:
            token = response.json().get("access_token")
        except ValueError as e:
            raise BoxAuthError(f"Box token response was not valid JSON: {e}") from e
        if not token:
            raise BoxAuthError(f"Box token response did not contain an access token: {response.text}")
        return token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._access_token}"}

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        headers = kwargs.pop("headers", {})
        headers.update(self._headers())
        try:
            response = requests.request(method, url, headers=headers, timeout=_REQUEST_TIMEOUT, **kwargs)
        except requests.exceptions.RequestException as e:
            raise BoxApiError(f"Failed to reach the Box API: {e}") from e
        if response.status_code >= 400:
            raise BoxApiError(f"Box API error ({response.status_code}): {response.text}")
        return response

    @staticmethod
    def _json(response: requests.Response) -> Any:
        try:
            return response.json()
        except ValueError as e:
            raise BoxApiError(f"Box API returned a response that was not valid JSON: {e}") from e

    def get_current_user(self) -> dict[str, Any]:
        return self._json(self._request("GET", f"{BOX_API_BASE}/users/me"))

    def list_folder_items(self, folder_id: str = "0", limit: int = 100, offset: int = 0) -> dict[str, Any]:
        params = {
            "limit": limit,
            "offset": offset,
            "fields": "id,name,type,size,modified_at,created_at",
        }
        return self._json(self._request("GET", f"{BOX_API_BASE}/folders/{folder_id}/items", params=params))

    def search(self, query: str, limit: int = 20, folder_id: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {
            "query": query,
            "limit": limit,
            "fields": "id,name,type,size,modified_at,created_at",
        }
        if folder_id:
            params["ancestor_folder_ids"] = folder_id
        return self._json(self._request("GET", f"{BOX_API_BASE}/search", params=params))

    def upload_file(self, parent_folder_id: str, file_name: str, file_content: bytes) -> dict[str, Any]:
        attributes = {"name": file_name, "parent": {"id": parent_folder_id}}
        files = {
            "attributes": (None, json.dumps(attributes), "application/json"),
            "file": (file_name, file_content),
        }
        return self._json(self._request("POST", f"{BOX_UPLOAD_BASE}/files/content", files=files))

    def get_file_info(self, file_id: str) -> dict[str, Any]:
        params = {"fields": "id,name,size,extension"}
        return self._json(self._request("GET", f"{BOX_API_BASE}/files/{file_id}", params=params))

    def download_file(self, file_id: str) -> bytes:
        return self._request("GET", f"{BOX_API_BASE}/files/{file_id}/content").content

    def create_folder(self, name: str, parent_folder_id: str = "0") -> dict[str, Any]:
        payload = {"name": name, "parent": {"id": parent_folder_id}}
        return self._json(self._request("POST", f"{BOX_API_BASE}/folders", json=payload))

    def delete_item(self, item_id: str, item_type: str = "file") -> None:
        endpoint = "files" if item_type == "file" else "folders"
        params = {"recursive": "true"} if item_type == "folder" else None
        self._request("DELETE", f"{BOX_API_BASE}/{endpoint}/{item_id}", params=params)

    def move_or_rename_item(
        self,
        item_id: str,
        item_type: str = "file",
        new_name: str | None = None,
        new_parent_id: str | None = None,
    ) -> dict[str, Any]:
        endpoint = "files" if item_type == "file" else "folders"
        payload: dict[str, Any] = {}
        if new_name:
            payload["name"] = new_name
        if new_parent_id:
            payload["parent"] = {"id": new_parent_id}
        if not payload:
            raise BoxApiError("Either new_name or new_parent_id must be provided.")
        return self._json(self._request("PUT", f"{BOX_API_BASE}/{endpoint}/{item_id}", json=payload))
