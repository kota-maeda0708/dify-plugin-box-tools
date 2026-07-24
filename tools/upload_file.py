import base64
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from box_client import BoxApiError, BoxAuthError, BoxClient


class UploadFileTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        folder_id = str(tool_parameters.get("folder_id") or "0")
        file_name = tool_parameters.get("file_name")
        input_file = tool_parameters.get("file")

        if input_file is not None:
            try:
                content = input_file.blob
            except Exception as e:
                yield self.create_text_message(f"Failed to read the provided file: {e}")
                return
            file_name = file_name or getattr(input_file, "filename", None)
            if not file_name:
                yield self.create_text_message("Could not determine a file name; please provide File Name.")
                return
        else:
            if not file_name:
                yield self.create_text_message("A file_name is required when no File is provided.")
                return

            file_content = tool_parameters.get("file_content")
            file_content_base64 = tool_parameters.get("file_content_base64")
            if not file_content and not file_content_base64:
                yield self.create_text_message("Provide a File, or File Content / File Content (Base64).")
                return

            if file_content_base64:
                try:
                    content = base64.b64decode(file_content_base64)
                except Exception:
                    yield self.create_text_message("Invalid base64 content provided.")
                    return
            else:
                content = file_content.encode("utf-8")

        try:
            client = BoxClient(self.runtime.credentials)
            result = client.upload_file(parent_folder_id=folder_id, file_name=file_name, file_content=content)
        except (BoxAuthError, BoxApiError) as e:
            yield self.create_text_message(f"Failed to upload '{file_name}' to Box: {e}")
            return
        except Exception as e:
            yield self.create_text_message(f"Unexpected error while uploading '{file_name}' to Box: {e}")
            return

        entry = (result.get("entries") or [result])[0]
        yield self.create_text_message(f"File '{file_name}' uploaded successfully to folder {folder_id}.")
        yield self.create_json_message(entry)
