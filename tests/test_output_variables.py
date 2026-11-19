"""The list and search tools emit exactly the variables their output_schema declares, with the declared types, on success and on error."""
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

import box_client
from tools.list_files import ListFilesTool
from tools.outputs import _EMPTY
from tools.params import LIST_LIMIT_MAX, SEARCH_LIMIT_MAX, parse_limit
from tools.search_files import SearchFilesTool

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
PY_TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "object": dict, "array": list}
FILE = {"type": "file", "id": "111", "name": "a.pdf", "size": 3, "created_at": "2026-10-01T00:00:00-07:00", "modified_at": "2026-10-02T00:00:00-07:00"}
FOLDER = {"type": "folder", "id": "222", "name": "Reports", "size": 0, "created_at": None, "modified_at": None}
WEB_LINK = {"type": "web_link", "id": "333", "name": "Portal", "created_at": "2026-10-03T00:00:00-07:00", "modified_at": "2026-10-03T00:00:00-07:00"}

TOOL_FILES = {ListFilesTool: "list_files", SearchFilesTool: "search_files"}
CASES = [(ListFilesTool, {"folder_id": "0"}), (SearchFilesTool, {"query": "a"})]
IDS = ["list", "search"]
# The text and json each tool produced before the output variables were added.
EXPECTED_OUTPUT = {
    ListFilesTool: lambda entries: [
        ("text", f"Found {len(entries)} item(s) in folder 0."),
        ("json", {"folder_id": "0", "item_count": len(entries), "items": entries}),
    ],
    SearchFilesTool: lambda entries: [
        ("text", f"Found {len(entries)} item(s) matching 'a'."),
        ("json", {"query": "a", "item_count": len(entries), "items": entries}),
    ],
}


class FakeClient:
    """Stands in for BoxClient: records each call's arguments, then returns ``result`` or raises ``error``."""

    calls: list[dict] = []

    def __init__(self, credentials, result=None, error=None):
        self._result, self._error = result, error

    def _respond(self, **kwargs):
        FakeClient.calls.append(kwargs)
        if self._error:
            raise self._error
        return self._result

    list_folder_items = search = _respond


def make_tool(cls):
    tool = cls.__new__(cls)
    tool.runtime = SimpleNamespace(credentials={})
    tool.create_text_message = lambda text: ("text", text)
    tool.create_json_message = lambda data: ("json", data)
    tool.create_variable_message = lambda name, value: ("var", name, value)
    return tool


def invoke(cls, params, monkeypatch, result=None, error=None):
    FakeClient.calls = []
    monkeypatch.setattr(f"tools.{TOOL_FILES[cls]}.BoxClient", lambda creds: FakeClient(creds, result, error))
    messages = list(make_tool(cls)._invoke(params))
    return messages, {m[1]: m[2] for m in messages if m[0] == "var"}


def schema(cls):
    return yaml.safe_load((TOOLS_DIR / f"{TOOL_FILES[cls]}.yaml").read_text(encoding="utf-8"))["output_schema"]["properties"]


def assert_types(variables, declared):
    assert set(variables) == set(declared)
    for name, spec in declared.items():
        assert isinstance(variables[name], PY_TYPES[spec["type"]]), name
        if spec["type"] == "array" and spec["items"]["type"] == "object":
            for item in variables[name]:
                assert set(item) == set(spec["items"]["properties"])
                for key, sub in spec["items"]["properties"].items():
                    assert isinstance(item[key], PY_TYPES[sub["type"]]), f"{name}.{key}"


def assert_empty_failure(variables, declared):
    """On failure every declared variable is still there, empty, with success false."""
    assert_types(variables, declared)
    assert variables["success"] is False and variables["error"]
    assert variables["items"] == [] and variables["file_ids"] == [] and variables["folder_ids"] == []
    assert (variables["count"], variables["file_count"], variables["folder_count"]) == (0, 0, 0)
    assert variables["has_more"] is False


@pytest.mark.parametrize("cls", list(TOOL_FILES), ids=IDS)
def test_every_declared_type_has_an_empty_value(cls):
    # An undeclared type would make the tool emit null for that variable on error.
    for name, spec in schema(cls).items():
        assert spec.get("type") in _EMPTY, name


@pytest.mark.parametrize("cls, params", CASES, ids=IDS)
def test_success_emits_every_declared_variable_with_its_type(cls, params, monkeypatch):
    entries = [FILE, FOLDER, WEB_LINK]
    messages, variables = invoke(cls, params, monkeypatch, result={"total_count": 5, "entries": entries})
    assert_types(variables, schema(cls))
    assert variables["file_ids"] == ["111"]
    assert variables["folder_ids"] == ["222"]
    assert [i["id"] for i in variables["items"]] == ["111", "222", "333"]
    # count covers every item; a web link is neither a file nor a folder.
    assert (variables["count"], variables["file_count"], variables["folder_count"]) == (3, 1, 1)
    assert variables["has_more"] is True
    assert variables["success"] is True and variables["error"] == ""
    # The existing text and json outputs are unchanged and come before the variables.
    assert messages[:2] == EXPECTED_OUTPUT[cls](entries)


@pytest.mark.parametrize("cls, params", CASES, ids=IDS)
@pytest.mark.parametrize(
    "result",
    [
        {"total_count": 3, "entries": [FILE, FOLDER, WEB_LINK]},  # exactly everything
        {"entries": [FILE]},  # Box sent no total_count
        {"total_count": 0, "entries": []},  # empty folder / no hits
        {"entries": None},  # entries is null
    ],
    ids=["complete", "no-total", "empty", "null-entries"],
)
def test_has_more_is_false_when_nothing_is_left(cls, params, result, monkeypatch):
    messages, variables = invoke(cls, params, monkeypatch, result=result)
    assert_types(variables, schema(cls))
    assert variables["has_more"] is False
    assert variables["success"] is True
    assert variables["count"] == len(result["entries"] or [])
    assert messages[:2] == EXPECTED_OUTPUT[cls](result["entries"] or [])


@pytest.mark.parametrize(
    "cls, params, default, maximum",
    [(ListFilesTool, {"folder_id": "42"}, 100, LIST_LIMIT_MAX), (SearchFilesTool, {"query": "a", "folder_id": "42"}, 20, SEARCH_LIMIT_MAX)],
    ids=IDS,
)
@pytest.mark.parametrize("given, expected", [(None, "default"), ("7", 7), (7.0, 7), (99999, "max"), (0, 1)])
def test_limit_and_folder_reach_box(cls, params, default, maximum, given, expected, monkeypatch):
    sent = {"default": default, "max": maximum}.get(expected, expected)
    invoke(cls, {**params, "limit": given}, monkeypatch, result={"total_count": 0, "entries": []})
    assert FakeClient.calls == [{**({"query": "a"} if cls is SearchFilesTool else {}), "folder_id": "42", "limit": sent}]


@pytest.mark.parametrize("cls, params", CASES, ids=IDS)
@pytest.mark.parametrize("bad", ["abc", "2.5", True])
def test_invalid_limit_reports_error_without_calling_box(cls, params, bad, monkeypatch):
    _, variables = invoke(cls, {**params, "limit": bad}, monkeypatch, result={"entries": []})
    assert FakeClient.calls == []
    assert_empty_failure(variables, schema(cls))
    assert "limit must be a whole number" in variables["error"]


@pytest.mark.parametrize("cls, params", CASES, ids=IDS)
def test_box_error_still_emits_every_declared_variable(cls, params, monkeypatch):
    _, variables = invoke(cls, params, monkeypatch, error=box_client.BoxApiError("404 not_found"))
    assert_empty_failure(variables, schema(cls))
    assert "404 not_found" in variables["error"]


@pytest.mark.parametrize("cls, params", CASES, ids=IDS)
def test_unexpected_error_still_emits_every_declared_variable(cls, params, monkeypatch):
    _, variables = invoke(cls, params, monkeypatch, error=RuntimeError("boom"))
    assert_empty_failure(variables, schema(cls))
    assert "Unexpected error" in variables["error"] and "boom" in variables["error"]


def test_search_without_query_reports_error():
    tool = make_tool(SearchFilesTool)
    variables = {m[1]: m[2] for m in tool._invoke({}) if m[0] == "var"}
    assert_empty_failure(variables, schema(SearchFilesTool))
    assert variables["error"] == "A search query is required."


@pytest.mark.parametrize("cls, params", CASES, ids=IDS)
def test_create_text_message_is_restored(cls, params, monkeypatch):
    monkeypatch.setattr(f"tools.{TOOL_FILES[cls]}.BoxClient", lambda creds: FakeClient(creds, {"entries": [FILE]}))
    tool = make_tool(cls)
    original = tool.create_text_message
    list(tool._invoke(params))
    assert tool.create_text_message is original

    def broken_json(data):
        raise RuntimeError("json failed")

    tool.create_json_message = broken_json
    with pytest.raises(RuntimeError):
        list(tool._invoke(params))
    assert tool.create_text_message is original


@pytest.mark.parametrize(
    "value, expected",
    [(None, 20), ("", 20), (" ", 20), (5, 5), ("5", 5), ("5.0", 5), (5.0, 5), (0, 1), (-3, 1), (500, 200)],
)
def test_parse_limit(value, expected):
    assert parse_limit(value, default=20, maximum=200) == expected


@pytest.mark.parametrize("value", ["abc", "2.5", 2.5, True, [5], {}])
def test_parse_limit_rejects_non_whole_numbers(value):
    with pytest.raises(ValueError):
        parse_limit(value, default=20, maximum=200)
