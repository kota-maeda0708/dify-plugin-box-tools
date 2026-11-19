from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from box_client import BoxApiError, BoxAuthError, BoxClient
from tools.outputs import listing_vars, with_outputs
from tools.params import SEARCH_LIMIT_MAX, parse_limit


class SearchFilesTool(Tool):
    @with_outputs
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        query = tool_parameters.get("query")
        if not query:
            yield self.create_text_message("A search query is required.")
            return

        folder_id = tool_parameters.get("folder_id") or None
        try:
            limit = parse_limit(tool_parameters.get("limit"), default=20, maximum=SEARCH_LIMIT_MAX)
        except ValueError as e:
            yield self.create_text_message(str(e))
            return

        try:
            client = BoxClient(self.runtime.credentials)
            result = client.search(query=query, limit=limit, folder_id=folder_id)
        except (BoxAuthError, BoxApiError) as e:
            yield self.create_text_message(f"Failed to search Box for '{query}': {e}")
            return
        except Exception as e:
            yield self.create_text_message(f"Unexpected error while searching Box for '{query}': {e}")
            return

        entries = result.get("entries") or []
        self._out.update(listing_vars(result), success=True)
        yield self.create_text_message(f"Found {len(entries)} item(s) matching '{query}'.")
        yield self.create_json_message({"query": query, "item_count": len(entries), "items": entries})
