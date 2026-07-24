import base64
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from box_client import BoxApiError, BoxAuthError, BoxClient


class DownloadFileTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        file_id = tool_parameters.get("file_id")
        if not file_id:
            yield self.create_text_message("A file_id is required.")
            return

        try:
            client = BoxClient(self.runtime.credentials)
            content = client.download_file(file_id)
        except (BoxAuthError, BoxApiError) as e:
            yield self.create_text_message(f"Failed to download Box file {file_id}: {e}")
            return

        response: dict[str, Any] = {
            "file_id": file_id,
            "size": len(content),
            "content_base64": base64.b64encode(content).decode("utf-8"),
        }
        if len(content) < 1024 * 1024:
            try:
                response["content_text"] = content.decode("utf-8")
            except UnicodeDecodeError:
                pass

        yield self.create_text_message(f"File {file_id} downloaded successfully ({len(content)} bytes).")
        yield self.create_json_message(response)
