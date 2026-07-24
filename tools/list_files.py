from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from box_client import BoxApiError, BoxAuthError, BoxClient


class ListFilesTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        folder_id = str(tool_parameters.get("folder_id") or "0")
        limit_param = tool_parameters.get("limit")
        limit = int(limit_param) if limit_param is not None else 100

        try:
            client = BoxClient(self.runtime.credentials)
            result = client.list_folder_items(folder_id=folder_id, limit=limit)
        except (BoxAuthError, BoxApiError) as e:
            yield self.create_text_message(f"Failed to list Box folder {folder_id}: {e}")
            return
        except Exception as e:
            yield self.create_text_message(f"Unexpected error while listing Box folder {folder_id}: {e}")
            return

        entries = result.get("entries", [])
        yield self.create_text_message(f"Found {len(entries)} item(s) in folder {folder_id}.")
        yield self.create_json_message({"folder_id": folder_id, "item_count": len(entries), "items": entries})
