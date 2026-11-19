# Dify 的 Box 插件

**作者：** kota-maeda0708
**版本：** 0.0.3
**类型：** 工具
**源代码仓库：** https://github.com/kota-maeda0708/dify-plugin-box-tools

## 简介

Box 插件让 Dify 应用可以操作 [Box](https://www.box.com/) 中的文件和文件夹。
借助此插件，你可以构建能够在 Box 中列出、搜索、上传、下载、创建文件夹、删除以及移动/重命名项目的 AI 应用。

## 功能

- **列出文件和文件夹（List Files）**：查看 Box 账户中任意文件夹的内容
- **搜索文件（Search Files）**：查找与关键词匹配的文件和文件夹
- **上传文件（Upload File）**：通过文件输入、纯文本或 base64 编码内容在 Box 中创建新文件
- **下载文件（Download File）**：将 Box 文件作为 Dify 文件获取，供下游节点使用
- **创建文件夹（Create Folder）**：创建新文件夹来整理 Box 账户
- **删除文件/文件夹（Delete Item）**：从 Box 中删除文件或文件夹
- **移动/重命名（Move / Rename Item）**：将项目移动到其他文件夹和/或重命名

## 关于 Box ID

Box 通过 **数字 ID** 而不是路径来定位项目：

- **根文件夹** 的 ID 始终为 `0`。
- 每个文件和文件夹都有自己的 ID。

请使用 **List Files**（从根文件夹 `0` 开始）或 **Search Files** 查找要操作的项目 ID，再将这些 ID 传给其他工具。

## 认证

此插件支持 **两种** 认证方式，可在配置插件时选择：

### 1. OAuth 2.0（用户认证）

1. 在 [Box Developer Console](https://app.box.com/developers/console) 中，选择 **OAuth 2.0（用户认证）** 应用类型创建 Box 应用。
2. 将 Dify 提供的重定向 URI 添加到应用的 OAuth 2.0 重定向 URI 设置中。
3. 复制应用的 **Client ID** 和 **Client Secret**。
4. 在 Dify 中选择 OAuth 认证方式，输入 Client ID 和 Client Secret，然后在浏览器中完成授权。Dify 会保存获得的访问令牌和刷新令牌，并在访问令牌过期时自动刷新。

### 2. 密钥（Client Credentials Grant / 服务器认证）

1. 在 [Box Developer Console](https://app.box.com/developers/console) 中，选择 **服务器认证（Client Credentials Grant）** 应用类型创建 Box 应用，并在 Box 管理控制台中授权该应用。
2. 复制应用的 **Client ID** 和 **Client Secret**。
3. 记下 Box 的 **Enterprise ID**（如需以特定用户身份操作，则记下该用户的 **User ID**）。
4. 在 Dify 中选择密钥认证方式，输入 Client ID、Client Secret、主体类型（`enterprise` 或 `user`）以及对应的 Enterprise ID / User ID。此方式无需在浏览器中跳转，适合服务器之间的集成。

## 文件

- **Download File** 返回真正的 Dify 文件（而不仅仅是 base64 文本），因此可以直接连接到文档提取、LLM 视觉或再次上传等下游节点/工具。
- **Upload File** 接受 `File` 输入（例如聊天中上传的文件，或 Download File 等其他工具的输出）。如果没有提供文件，也可以直接输入纯文本或粘贴 base64 编码的内容。
- Upload File 使用的 Box 简单上传接口支持最大 **50MB** 的文件；本版本插件不支持更大的文件。为避免占用过多内存，Download File 会拒绝下载超过 **100MB** 的文件。

## 输出变量

在工作流中，**List Files** 和 **Search Files** 除了常规的 `text` 和 `json` 之外，还会将结果作为输出变量返回，因此无需使用代码节点来拆分结果：

| 变量 | 类型 | 说明 |
| --- | --- | --- |
| `items` | `array[object]` | 每个项目的 `id`、`name`、`type`、`size`、`created_at`、`modified_at` |
| `file_ids` | `array[string]` | 仅文件的 ID（不含文件夹）；可通过迭代传给 Download File |
| `folder_ids` | `array[string]` | 仅文件夹的 ID（不含文件）；可通过迭代传给 List Files |
| `count` | `integer` | 返回的项目数（包括文件、文件夹和网页链接） |
| `file_count` | `integer` | 返回的文件数 |
| `folder_count` | `integer` | 返回的文件夹数 |
| `has_more` | `boolean` | Box 表示还有比返回结果更多的项目时为 true（结果不完整） |
| `success` | `boolean` | 工具因错误停止时为 false |
| `error` | `string` | 停止的原因，成功时为空字符串 |

`json` 输出保持不变，因此读取它的现有工作流可以继续正常运行。

注意事项：

- **`has_more` 为 true 时，结果不完整。** 只会返回前 `limit` 个项目，`file_ids`、`folder_ids` 和各项计数也只覆盖这些项目。List Files 按文件夹、文件、网页链接的顺序返回，因此当 `limit` 较小时，即使文件夹中有文件，`file_ids` 也可能为空。如需处理全部项目，请将 `limit` 设为大于项目数，或检查 `has_more`，在其为 true 时停止或发出警告。
- **`limit` 的范围。** List Files 为 1 到 1000（默认 100），Search Files 为 1 到 200（默认 20），与 Box API 的上限一致。超过上限的值按上限处理。如果指定的值不是整数，工具会将 `success` 设为 false 并停止。
- **错误不会使节点失败。** 当 Box 返回错误时，工具节点仍会以成功状态结束，因此不会触发节点的"失败分支"错误处理。请改用 IF/ELSE 节点判断 `success`；原因保存在 `error` 中。即使出错，所有变量也都会以空值（`[]`、`0`、`false`、`""`）输出，因此后续节点不会遇到缺失的变量。
- 搜索结果按 Box 判断的相关度排序，而不是按名称排序。

### 示例：下载文件夹中的所有文件

1. 使用文件夹 ID 运行 **List Files**。
2. 添加 **迭代** 节点，以 List Files 的 `file_ids` 作为输入。
3. 在迭代内运行 **Download File**，将迭代的当前项作为 `file_id`。
4. 将迭代的输出设为 Download File 的 `files`，即可汇总所有下载的文件。

如需进入子文件夹，请将 `folder_ids` 传给另一个运行 List Files 的迭代。

## 使用示例

### 列出 Box 根文件夹中的文件
```
List all files in my Box (folder 0)
```

### 搜索特定文件
```
Find all PDF files in my Box
```

### 上传新文件
```
Upload a file named "meeting-notes.txt" to my Box with the content "Meeting scheduled for next Tuesday"
```

### 下载文件内容
```
Download the Box file with ID 123456789
```

### 创建文件夹
```
Create a folder named "Reports" in my Box root folder
```

### 删除项目
```
Delete the Box file with ID 123456789
```

### 移动或重命名文件
```
Rename the Box file with ID 123456789 to "final-report.pdf"
```
```
Move the Box file with ID 123456789 into folder 987654321
```

## 要求

- Box 账户
- Box 应用（OAuth 2.0 应用或 Client Credentials Grant 应用）
- Dify 平台

## 运行测试

```bash
uv sync
uv run --with pytest python -m pytest -q tests
```
