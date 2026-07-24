from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from box_client import BoxApiError, BoxAuthError, BoxClient


class DeleteItemTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        item_id = tool_parameters.get("item_id")
        if not item_id:
            yield self.create_text_message("An item_id is required.")
            return

        item_type = tool_parameters.get("item_type") or "file"
        if item_type not in ("file", "folder"):
            yield self.create_text_message("item_type must be either 'file' or 'folder'.")
            return

        try:
            client = BoxClient(self.runtime.credentials)
            client.delete_item(item_id=item_id, item_type=item_type)
        except (BoxAuthError, BoxApiError) as e:
            yield self.create_text_message(f"Failed to delete Box {item_type} {item_id}: {e}")
            return
        except Exception as e:
            yield self.create_text_message(f"Unexpected error while deleting Box {item_type} {item_id}: {e}")
            return

        yield self.create_text_message(f"Box {item_type} {item_id} deleted successfully.")
        yield self.create_json_message({"item_id": item_id, "item_type": item_type, "deleted": True})
