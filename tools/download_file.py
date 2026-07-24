import mimetypes
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from box_client import BoxApiError, BoxAuthError, BoxClient

# Matches this plugin's manifest.yaml resource.memory ceiling (256MB), leaving headroom
# for the runtime itself so a large download doesn't risk an OOM kill.
_MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024


class DownloadFileTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        file_id = tool_parameters.get("file_id")
        if not file_id:
            yield self.create_text_message("A file_id is required.")
            return

        try:
            client = BoxClient(self.runtime.credentials)
            file_info = client.get_file_info(file_id)

            file_size = file_info.get("size")
            if isinstance(file_size, int) and file_size > _MAX_DOWNLOAD_BYTES:
                size_mb = file_size / (1024 * 1024)
                limit_mb = _MAX_DOWNLOAD_BYTES / (1024 * 1024)
                yield self.create_text_message(
                    f"Box file {file_id} is {size_mb:.1f}MB, which exceeds this tool's "
                    f"{limit_mb:.0f}MB download limit."
                )
                return

            content = client.download_file(file_id)
        except (BoxAuthError, BoxApiError) as e:
            yield self.create_text_message(f"Failed to download Box file {file_id}: {e}")
            return
        except Exception as e:
            yield self.create_text_message(f"Unexpected error while downloading Box file {file_id}: {e}")
            return

        file_name = file_info.get("name") or f"box_file_{file_id}"
        mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"

        yield self.create_text_message(f"File '{file_name}' downloaded successfully ({len(content)} bytes).")
        # Emitted as a Dify file (not just base64/JSON) so it can be used directly by
        # downstream nodes (e.g. document extractor, LLM vision, another upload tool).
        yield self.create_blob_message(content, meta={"filename": file_name, "mime_type": mime_type})
        yield self.create_json_message({"file_id": file_id, "name": file_name, "size": len(content), "mime_type": mime_type})
