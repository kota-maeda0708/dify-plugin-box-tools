from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from box_client import BoxApiError, BoxAuthError, BoxClient


class CreateFolderTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        name = tool_parameters.get("name")
        if not name:
            yield self.create_text_message("A folder name is required.")
            return

        parent_folder_id = str(tool_parameters.get("parent_folder_id") or "0")

        try:
            client = BoxClient(self.runtime.credentials)
            result = client.create_folder(name=name, parent_folder_id=parent_folder_id)
        except (BoxAuthError, BoxApiError) as e:
            yield self.create_text_message(f"Failed to create folder '{name}' in Box: {e}")
            return

        yield self.create_text_message(f"Folder '{name}' created in folder {parent_folder_id}.")
        yield self.create_json_message(result)
