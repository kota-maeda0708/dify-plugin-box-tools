from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from box_client import BoxApiError, BoxAuthError, BoxClient
from tools.outputs import listing_vars, with_outputs
from tools.params import LIST_LIMIT_MAX, parse_limit


class ListFilesTool(Tool):
    @with_outputs
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        folder_id = str(tool_parameters.get("folder_id") or "0")
        try:
            limit = parse_limit(tool_parameters.get("limit"), default=100, maximum=LIST_LIMIT_MAX)
        except ValueError as e:
            yield self.create_text_message(str(e))
            return

        try:
            client = BoxClient(self.runtime.credentials)
            result = client.list_folder_items(folder_id=folder_id, limit=limit)
        except (BoxAuthError, BoxApiError) as e:
            yield self.create_text_message(f"Failed to list Box folder {folder_id}: {e}")
            return
        except Exception as e:
            yield self.create_text_message(f"Unexpected error while listing Box folder {folder_id}: {e}")
            return

        entries = result.get("entries") or []
        self._out.update(listing_vars(result), success=True)
        yield self.create_text_message(f"Found {len(entries)} item(s) in folder {folder_id}.")
        yield self.create_json_message({"folder_id": folder_id, "item_count": len(entries), "items": entries})
