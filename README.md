# Box Plugin for Dify

**Author:** kota-maeda0708
**Version:** 0.0.1
**Type:** Tool

## Description

The Box plugin enables Dify applications to interact with files and folders in
[Box](https://www.box.com/). With this plugin, you can build AI applications that list, search,
upload, download, create folders, delete, and move/rename items in Box.

## Features

- **List Files and Folders**: View the contents of any folder in your Box account
- **Search Files**: Find files and folders matching a keyword
- **Upload Files**: Create new files in Box from text or base64-encoded content
- **Download Files**: Retrieve file content from Box
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
