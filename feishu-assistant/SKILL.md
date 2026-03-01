---
name: feishu-assistant
description: 飞书助手：向团队成员/群组发消息、创建和更新文档、读取知识库文章、查看群消息、获取通讯录。当用户提到飞书相关操作（发消息、写文档、查知识库、看群聊）时使用此技能。
---

# 飞书助手

> 作者：凯寓 (KAIYU)

通过飞书 Open API 实现消息发送、文档管理、知识库阅读等功能。

## 首次使用前

用户需要先完成安装配置（运行一次即可）：

```bash
python scripts/setup.py
```

## 执行命令须知

所有命令通过 `python scripts/feishu_client.py <command>` 调用。
执行前必须先 cd 到本 skill 的 Base directory。

## 查找联系人和知识库

发消息前需要知道接收者的 open_id，查知识库前需要知道 space_id。
这些信息保存在缓存文件中，**请先读取缓存文件**获取：

- **通讯录**：读取 `scripts/cache/contacts.json`，格式为 `[{"name": "张三", "open_id": "ou_xxx", "mobile": "+86xxx", "status": "已激活"}, ...]`
- **知识库列表**：读取 `scripts/cache/wiki_spaces.json`，格式为 `[{"name": "空间名", "space_id": "xxx", "description": "..."}, ...]`
- **默认群聊 ID**：读取 `scripts/config.json` 中的 `default_chat_id` 字段
- **team_members**：读取 `scripts/config.json` 中的 `team_members` 字段（姓名 → open_id 映射）

如果缓存文件不存在，运行以下命令生成：

```bash
python scripts/feishu_client.py refresh-contacts
python scripts/feishu_client.py refresh-spaces
```

## 核心命令

### 消息

```bash
# 发送文本消息（支持 text/post/interactive/image）
python scripts/feishu_client.py send-message --type text --content "内容" --receive_id "ou_xxx" --receive_id_type open_id

# 向群组发消息
python scripts/feishu_client.py send-message --type text --content "内容" --receive_id "oc_xxx" --receive_id_type chat_id

# 读取群消息
python scripts/feishu_client.py get-chat-messages --chat_id "oc_xxx" --page_size 20
```

### 文档（需要 OAuth 授权）

```bash
# 创建文档
python scripts/feishu_client.py create-doc --title "标题" --content "内容"

# 更新文档
python scripts/feishu_client.py update-doc --doc_token "doxcxxx" --content "新内容"
```

### 知识库（需要 OAuth 授权）

```bash
# 列出所有知识库空间
python scripts/feishu_client.py list-wiki-spaces

# 列出空间下的文章（支持 --parent_node_token 查看子节点）
python scripts/feishu_client.py list-wiki-nodes --space_id "xxx" --page_size 50

# 读取文章纯文本内容
python scripts/feishu_client.py read-wiki-node --node_token "xxx"
```

### 通讯录与组织

```bash
# 显示团队通讯录（从缓存读取）
python scripts/feishu_client.py show-contacts

# 刷新通讯录缓存（从飞书 API 重新拉取）
python scripts/feishu_client.py refresh-contacts

# 显示知识库列表
python scripts/feishu_client.py show-spaces

# 刷新知识库缓存
python scripts/feishu_client.py refresh-spaces

# 显示组织信息
python scripts/feishu_client.py show-org

# 通过邮箱查用户
python scripts/feishu_client.py get-user --email "user@example.com"
```

### 文件上传

```bash
python scripts/feishu_client.py upload-file --file_path "path/to/file.pdf" --parent_node "fldxxx"
```

### 管理命令

```bash
# 检查配置是否完整
python scripts/feishu_client.py check-config
```

## 配置

`scripts/config.json` 关键字段：

| 字段 | 说明 |
|------|------|
| `app_id` / `app_secret` | 飞书应用凭证 |
| `oauth_scopes` | OAuth 授权范围（空格分隔），新增权限改这里再重新授权 |
| `default_chat_id` | 默认群聊 ID |
| `team_members` | 成员姓名 → open_id 映射（由 refresh-contacts 自动填充） |

用户 Token 自动存储在 `scripts/cache/user_token.json`，有效期内自动刷新。

## OAuth 授权

文档操作和知识库阅读需要用户身份，首次使用或 scope 变更后运行：

```bash
python scripts/oauth_server.py
```

浏览器会打开授权页面，完成后 token 自动保存。scope 从 `config.json` 的 `oauth_scopes` 读取。

## 错误处理

权限错误会自动识别并给出修复步骤：
- 能提取到缺失的 scope 名时，直接告诉你要在 `oauth_scopes` 加什么
- 提取不到时，提示检查 `oauth_scopes` 配置
- 非权限错误显示原始错误码和消息

## 故障排除

| 错误 | 原因 | 修复 |
|------|------|------|
| config.json 不存在 | 未运行安装引导 | 运行 `python scripts/setup.py` |
| Unauthorized / scope 相关 | OAuth 授权时缺少所需 scope | 在 `oauth_scopes` 加上缺失 scope，重新运行 `oauth_server.py` |
| Token 刷新失败 | refresh_token 过期（>30天） | 重新运行 `oauth_server.py` |
| Invalid app_access_token | 凭证错误 | 检查 `config.json` 的 app_id / app_secret |
| 通讯录/知识库缓存为空 | 未刷新缓存 | 运行 `refresh-contacts` 或 `refresh-spaces` |
| Bot has NO availability | 机器人对目标用户无可用性 | 在飞书开放平台将应用可用范围设为「所有员工」并重新发布 |

飞书开放平台后台：https://open.feishu.cn/app
