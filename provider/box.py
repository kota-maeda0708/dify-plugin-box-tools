import secrets
import time
import urllib.parse
from collections.abc import Mapping
from typing import Any

import requests
from werkzeug import Request

from dify_plugin import ToolProvider
from dify_plugin.entities.oauth import ToolOAuthCredentials
from dify_plugin.errors.tool import ToolProviderCredentialValidationError, ToolProviderOAuthError

from box_client import BoxAuthError, BoxClient, BOX_TOKEN_URL


class BoxProvider(ToolProvider):
    _AUTHORIZE_URL = "https://account.box.com/api/oauth2/authorize"
    _TOKEN_URL = BOX_TOKEN_URL

    def _oauth_get_authorization_url(self, redirect_uri: str, system_credentials: Mapping[str, Any]) -> str:
        state = secrets.token_urlsafe(16)
        params = {
            "response_type": "code",
            "client_id": system_credentials["client_id"],
            "redirect_uri": redirect_uri,
            "state": state,
        }
        return f"{self._AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

    def _oauth_get_credentials(
        self, redirect_uri: str, system_credentials: Mapping[str, Any], request: Request
    ) -> ToolOAuthCredentials:
        code = request.args.get("code")
        if not code:
            raise ToolProviderOAuthError("No code provided")

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": system_credentials["client_id"],
            "client_secret": system_credentials["client_secret"],
            "redirect_uri": redirect_uri,
        }
        response = requests.post(self._TOKEN_URL, data=data, timeout=10)
        response_json = response.json()
        access_token = response_json.get("access_token")
        if not access_token:
            raise ToolProviderOAuthError(f"Error in Box OAuth: {response_json}")

        expires_in = int(response_json.get("expires_in", 3600))
        return ToolOAuthCredentials(
            credentials={
                "access_token": access_token,
                "refresh_token": response_json.get("refresh_token", ""),
            },
            expires_at=int(time.time()) + expires_in,
        )

    def _oauth_refresh_credentials(
        self, redirect_uri: str, system_credentials: Mapping[str, Any], credentials: Mapping[str, Any]
    ) -> ToolOAuthCredentials:
        refresh_token = credentials.get("refresh_token")
        if not refresh_token:
            raise ToolProviderOAuthError("No refresh token available to refresh Box credentials.")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": system_credentials["client_id"],
            "client_secret": system_credentials["client_secret"],
        }
        response = requests.post(self._TOKEN_URL, data=data, timeout=10)
        response_json = response.json()
        access_token = response_json.get("access_token")
        if not access_token:
            raise ToolProviderOAuthError(f"Error refreshing Box OAuth token: {response_json}")

        expires_in = int(response_json.get("expires_in", 3600))
        return ToolOAuthCredentials(
            credentials={
                "access_token": access_token,
                "refresh_token": response_json.get("refresh_token", refresh_token),
            },
            expires_at=int(time.time()) + expires_in,
        )

    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            client = BoxClient(credentials)
            client.get_current_user()
        except BoxAuthError as e:
            raise ToolProviderCredentialValidationError(str(e)) from e
        except Exception as e:
            raise ToolProviderCredentialValidationError(f"Failed to validate Box credentials: {e}") from e
