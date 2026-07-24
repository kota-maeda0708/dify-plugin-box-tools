from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from box_client import BoxApiError, BoxAuthError, BoxClient


class MoveRenameItemTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        item_id = tool_parameters.get("item_id")
        if not item_id:
            yield self.create_text_message("An item_id is required.")
            return

        item_type = tool_parameters.get("item_type") or "file"
        if item_type not in ("file", "folder"):
            yield self.create_text_message("item_type must be either 'file' or 'folder'.")
            return

        new_name = tool_parameters.get("new_name") or None
        new_parent_folder_id = tool_parameters.get("new_parent_folder_id") or None

        if not new_name and not new_parent_folder_id:
            yield self.create_text_message("Provide new_name and/or new_parent_folder_id.")
            return

        try:
            client = BoxClient(self.runtime.credentials)
            result = client.move_or_rename_item(
                item_id=item_id,
                item_type=item_type,
                new_name=new_name,
                new_parent_id=new_parent_folder_id,
            )
        except (BoxAuthError, BoxApiError) as e:
            yield self.create_text_message(f"Failed to move/rename Box {item_type} {item_id}: {e}")
            return
        except Exception as e:
            yield self.create_text_message(f"Unexpected error while moving/renaming Box {item_type} {item_id}: {e}")
            return

        yield self.create_text_message(f"Box {item_type} {item_id} updated successfully.")
        yield self.create_json_message(result)
