# Box Plugin for Dify

**Author:** kota-maeda0708
**Version:** 0.1.0
**Type:** Tool
**Source repository:** https://github.com/kota-maeda0708/dify-plugin-box-tools

## Description

The Box plugin enables Dify applications to interact with files and folders in
[Box](https://www.box.com/). With this plugin, you can build AI applications that list, search,
upload, download, create folders, delete, and move/rename items in Box.

## Features

- **List Files and Folders**: View the contents of any folder in your Box account
- **Search Files**: Find files and folders matching a keyword
- **Upload Files**: Create new files in Box from a file input, plain text, or base64-encoded content
- **Download Files**: Retrieve a file from Box as a Dify file usable by downstream nodes
- **Create Folders**: Organize your Box account by creating new folders
- **Delete Files/Folders**: Remove files or folders from Box
- **Move / Rename**: Move an item to another folder and/or rename it

## Working with Box IDs

Box addresses items by **numeric ID**, not by path:

- The **root folder** always has the ID `0`.
- Every file and folder has its own ID.

Use **List Files** (starting from the root folder `0`) or **Search Files** to discover the IDs of
the items you want to operate on, then pass those IDs to the other tools.

## Authentication

This plugin supports **two** authentication methods, selectable when you configure the plugin:

### 1. OAuth 2.0 (User Authentication)

1. Create a Box application in the [Box Developer Console](https://app.box.com/developers/console)
   using the **OAuth 2.0 (User Authentication)** app type.
2. Add the redirect URI provided by Dify to the app's OAuth 2.0 Redirect URI setting.
3. Copy the app's **Client ID** and **Client Secret**.
4. In Dify, choose the OAuth authentication method and enter the Client ID / Client Secret, then
   complete the authorization flow in the browser. Dify stores the resulting access and refresh
   tokens and automatically refreshes the access token when it expires.

### 2. Secret Key (Client Credentials Grant / Server Authentication)

1. Create a Box application in the [Box Developer Console](https://app.box.com/developers/console)
   using the **Server Authentication (Client Credentials Grant)** app type, and authorize the app
   in your Box Admin Console.
2. Copy the app's **Client ID** and **Client Secret**.
3. Note your Box **Enterprise ID** (or the **User ID** to impersonate a specific user).
4. In Dify, choose the Secret Key authentication method and enter the Client ID, Client Secret,
   Subject Type (`enterprise` or `user`), and the matching Enterprise/User ID. This method does
   not require an interactive browser redirect and is well suited for server-to-server use.

## Files

- **Download File** returns the file as an actual Dify file (not just base64 text), so it can
  be wired directly into downstream nodes/tools such as document extraction, LLM vision, or
  another upload step.
- **Upload File** accepts a `File` input (e.g. a chat file upload, or the output of Download
  File / another tool). If no file is provided, you can instead type plain text or paste
  base64-encoded content directly.
- Box's simple upload endpoint (used by Upload File) supports files up to **50MB**; larger files
  are not supported by this version of the plugin. Download File refuses files larger than
  **100MB** to avoid excessive memory use.

## Output Variables

In a workflow, **List Files** and **Search Files** expose their results as output variables
in addition to the usual `text` and `json`, so no Code node is needed to pick them apart:

| Variable | Type | Description |
| --- | --- | --- |
| `items` | `array[object]` | Each item's `id`, `name`, `type`, `size`, `created_at`, `modified_at` |
| `file_ids` | `array[string]` | IDs of the files only (folders excluded); pass to an Iteration with Download File |
| `folder_ids` | `array[string]` | IDs of the folders only (files excluded); pass to an Iteration with List Files |
| `count` | `integer` | Number of items returned (files, folders and web links) |
| `file_count` | `integer` | Number of files returned |
| `folder_count` | `integer` | Number of folders returned |
| `has_more` | `boolean` | True when Box reports more items than were returned (the result is partial) |
| `success` | `boolean` | False when the tool stopped with an error |
| `error` | `string` | Why the tool stopped, empty on success |

The `json` output is unchanged, so existing workflows that read it keep working.

Notes:

- **When `has_more` is true, the result is partial.** Only the first `limit` items are returned,
  and `file_ids`, `folder_ids` and the counts cover only those items. List Files returns folders
  first, then files, then web links, so with a small `limit` its `file_ids` can be empty even
  though the folder contains files. To process everything, set `limit` above the number of items
  or check `has_more` and stop or warn when it is true.
- **`limit` ranges.** List Files accepts 1 to 1000 (default 100) and Search Files 1 to 200
  (default 20), the maximums of the Box API. Larger values are capped to the maximum. A value that
  is not a whole number stops the tool with `success` false.
- **Errors do not fail the node.** When Box returns an error, the tool node still finishes as
  successful, so the node's "fail branch" error handling is not triggered. Branch on `success`
  with an IF/ELSE node instead; `error` holds the reason. Every variable is still emitted with an
  empty value (`[]`, `0`, `false`, `""`), so later nodes never see a missing variable.
- Search results are ordered by Box's relevance, not by name.

### Example: download every file in a folder

1. **List Files** with the folder's ID.
2. **Iteration** with `file_ids` from List Files as its input.
3. Inside the Iteration, **Download File** with the Iteration's current item as `file_id`.
4. Set the Iteration's output to Download File's `files` to collect all downloaded files.

To walk into subfolders, pass `folder_ids` to another Iteration that runs List Files.

## Usage Examples

### List files in your Box root folder
```
List all files in my Box (folder 0)
```

### Search for specific files
```
Find all PDF files in my Box
```

### Upload a new file
```
Upload a file named "meeting-notes.txt" to my Box with the content "Meeting scheduled for next Tuesday"
```

### Download file content
```
Download the Box file with ID 123456789
```

### Create a folder
```
Create a folder named "Reports" in my Box root folder
```

### Delete an item
```
Delete the Box file with ID 123456789
```

### Move or rename a file
```
Rename the Box file with ID 123456789 to "final-report.pdf"
```
```
Move the Box file with ID 123456789 into folder 987654321
```

## Requirements

- A Box account
- A Box application (OAuth 2.0 app, or a Client Credentials Grant app)
- Dify platform

## Running Tests

```bash
uv sync
uv run --with pytest python -m pytest -q tests
```
