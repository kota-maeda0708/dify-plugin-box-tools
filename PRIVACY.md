# Privacy Policy

This plugin (Box) connects your Dify workspace to your Box account via the official Box API.

## Data Collected

- **Credentials**: Depending on the authentication method you choose, this plugin stores either
  (a) an OAuth 2.0 access token and refresh token obtained through Box's standard OAuth flow, or
  (b) a Box application Client ID, Client Secret, and Subject ID (Enterprise ID or User ID) that
  you provide directly, used for Box's Client Credentials Grant (Server Authentication).
  These credentials are stored encrypted by the Dify platform and are only used to authenticate
  requests to the Box API on your behalf.
- **File data**: When you invoke a tool (e.g. list, search, upload, download, create folder,
  delete, move/rename), the plugin sends the relevant request to Box's API (`api.box.com`,
  `upload.box.com`, `account.box.com`) and returns Box's response to your Dify workflow/agent.
  File content passed to the upload/download tools is transmitted directly between Dify and Box
  and is not persisted by this plugin beyond the duration of the request.

## Data Sharing

This plugin does not send your credentials or file data to any third party other than Box, Inc.
(https://www.box.com), which processes the data under its own privacy policy
(https://www.box.com/legal/privacypolicy).

## Data Retention

This plugin does not independently store, log, or cache your Box file contents. Credentials are
retained only for as long as you keep this plugin's authorization configured in your Dify
workspace; removing the authorization removes the stored credentials.

## Contact

For questions about this plugin's data handling, please open an issue on the plugin's source
repository.
