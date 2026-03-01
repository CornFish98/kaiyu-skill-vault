# 飞书助手 (feishu-assistant)

> 作者：**凯寓 (KAIYU)**

让 Claude Code 帮你操作飞书：发消息、读知识库、写文档，一句话搞定。

## 快速开始

### 第 1 步：安装

把这个文件夹放到 Claude Code 的 skills 目录下：

- **Windows**: `C:\Users\你的用户名\.claude\skills\feishu-assistant\`
- **macOS**: `~/.claude/skills/feishu-assistant/`

### 第 2 步：运行安装引导

打开终端（Windows 叫「命令提示符」或「PowerShell」），运行：

```bash
# Windows
python scripts\setup.py

# macOS
python3 scripts/setup.py
```

安装引导会一步步教你完成配置，全程中文提示。

### 第 3 步：开始使用

在 Claude Code 里直接用自然语言操作飞书：

- "给张三发一条飞书消息，内容是明天下午开会"
- "看看知识库里有什么文章"
- "帮我创建一个飞书文档，标题是会议纪要"
- "读一下知识库里的《xxx》这篇文章"

## 前置条件

1. **Python 3.8+**（一般电脑都自带）
2. **飞书企业账号**（需要有管理员权限来创建应用）
3. **Claude Code**

## 功能列表

- 发送消息（私聊/群聊）
- 读取群组消息
- 创建和更新飞书文档
- 浏览和阅读知识库文章
- 查看团队通讯录
- 上传文件到飞书云文档
- 创建日历事件

## 文件结构

```
feishu-assistant/
├── SKILL.md                    # Claude 读取的技能定义
├── README.md                   # 你正在看的这个文件
├── .gitignore
└── scripts/
    ├── setup.py                # 安装引导（运行一次即可）
    ├── feishu_client.py        # 核心 API 客户端
    ├── oauth_server.py         # OAuth 授权工具
    ├── config.example.json     # 配置文件模板
    ├── config.json             # 你的配置（自动生成，不要分享）
    └── cache/                  # 运行时缓存
        ├── contacts.json       # 通讯录缓存
        ├── wiki_spaces.json    # 知识库列表缓存
        └── user_token.json     # OAuth Token（自动管理）
```

## 常用命令

```bash
# 检查配置是否正确
python scripts/feishu_client.py check-config

# 刷新通讯录
python scripts/feishu_client.py refresh-contacts

# 刷新知识库列表
python scripts/feishu_client.py refresh-spaces

# 重新 OAuth 授权
python scripts/oauth_server.py

# 重新运行安装引导
python scripts/setup.py
```

## 安全提醒

- `config.json` 包含你的应用密钥，**不要分享给别人**
- `cache/user_token.json` 包含你的登录凭证，**不要分享给别人**
- 以上文件已在 `.gitignore` 中排除，不会被 git 提交

## 常见问题

**Q: 报错 "config.json 不存在"**
A: 运行 `python scripts/setup.py` 完成初始配置。

**Q: 报错 "用户 token 不可用"**
A: 运行 `python scripts/oauth_server.py` 完成 OAuth 授权。

**Q: 发消息报错 "Bot has NO availability"**
A: 在飞书开放平台 → 你的应用 → 版本管理与发布 → 将可用范围设为「所有员工」→ 重新发布。

**Q: 通讯录是空的**
A: 运行 `python scripts/feishu_client.py refresh-contacts`。如果仍为空，检查应用是否有通讯录权限。

**Q: macOS 上 `python` 命令不存在**
A: macOS 请使用 `python3` 代替 `python`。
