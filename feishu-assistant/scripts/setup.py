#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书助手 · 安装引导
全程中文交互，帮助用户完成飞书应用配置和授权。

作者：凯寓 (KAIYU)
"""

import json
import os
import sys
import time
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ─── 路径定义 ───────────────────────────────────────────────
SCRIPTS_DIR = Path(__file__).parent
SKILL_DIR = SCRIPTS_DIR.parent
CONFIG_PATH = SCRIPTS_DIR / "config.json"
CONFIG_EXAMPLE_PATH = SCRIPTS_DIR / "config.example.json"
CACHE_DIR = SCRIPTS_DIR / "cache"
USER_TOKEN_PATH = CACHE_DIR / "user_token.json"
CONTACTS_CACHE_PATH = CACHE_DIR / "contacts.json"
SPACES_CACHE_PATH = CACHE_DIR / "wiki_spaces.json"


def check_python_version():
    """检查 Python 版本是否满足要求"""
    if sys.version_info < (3, 8):
        print()
        print("  ❌ 你的 Python 版本太低了！")
        print(f"     当前版本：Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        print("     需要版本：Python 3.8 或更高")
        print()
        print("  请到 https://www.python.org/downloads/ 下载最新版本安装。")
        print("  安装时记得勾选「Add Python to PATH」选项。")
        print()
        sys.exit(1)


def ensure_utf8():
    """确保控制台能正常显示中文"""
    if sys.platform == "win32":
        os.system("")  # 启用 Windows ANSI 转义
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")


def clear_screen():
    """清屏"""
    os.system("cls" if sys.platform == "win32" else "clear")


def print_header(title, step=None, total=None):
    """打印美观的步骤标题"""
    print()
    print("=" * 56)
    if step and total:
        print(f"  第 {step} 步（共 {total} 步）：{title}")
    else:
        print(f"  {title}")
    print("=" * 56)
    print()


def ask(prompt, default="", required=True, secret=False):
    """
    交互式输入，支持默认值和必填校验。
    secret=True 时提示用户注意保密（不做隐藏，因为他们需要粘贴）。
    """
    while True:
        hint = f"  {prompt}"
        if default:
            hint += f"（直接回车使用: {default}）"
        hint += ": "

        try:
            value = input(hint).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  已取消安装。\n")
            sys.exit(0)

        if not value and default:
            return default
        if not value and required:
            print("  ⚠ 这一项不能为空，请重新输入。\n")
            continue
        return value


def ask_yes_no(prompt, default_yes=True):
    """是/否选择"""
    hint = "Y/n" if default_yes else "y/N"
    try:
        value = input(f"  {prompt} [{hint}]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n\n  已取消安装。\n")
        sys.exit(0)

    if not value:
        return default_yes
    return value in ("y", "yes", "是")


# ─── OAuth 回调处理 ──────────────────────────────────────────
class _OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        if "code" in params:
            self.server.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                "<html><body style='text-align:center;padding-top:80px;font-family:sans-serif'>"
                "<h1>✅ 授权成功！</h1>"
                "<p>你可以关闭这个页面，回到终端继续操作。</p>"
                "</body></html>".encode("utf-8")
            )
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                "<html><body style='text-align:center;padding-top:80px;font-family:sans-serif'>"
                "<h1>❌ 授权失败</h1>"
                "<p>没有收到授权码，请重试。</p>"
                "</body></html>".encode("utf-8")
            )

    def log_message(self, format, *args):
        pass  # 不打印 HTTP 日志


def do_oauth(app_id, app_secret, scopes):
    """执行 OAuth 授权流程，返回 token 数据"""
    import requests

    redirect_uri = "http://127.0.0.1:8080/callback"
    auth_url = (
        f"https://open.feishu.cn/open-apis/authen/v1/authorize?"
        f"app_id={app_id}&redirect_uri={redirect_uri}&scope={scopes}&state=setup"
    )

    print("  正在打开浏览器，请在弹出的页面中点击「授权」...")
    print()
    print(f"  如果浏览器没有自动打开，请手动复制以下网址到浏览器：")
    print(f"  {auth_url}")
    print()

    webbrowser.open(auth_url)

    server = HTTPServer(("127.0.0.1", 8080), _OAuthHandler)
    server.auth_code = None

    print("  等待你在浏览器中完成授权...")
    while server.auth_code is None:
        server.handle_request()

    # 用 code 换 token
    # Step 1: 获取 app_access_token
    r = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal",
        json={"app_id": app_id, "app_secret": app_secret},
    )
    app_token_data = r.json()
    if app_token_data.get("code") != 0:
        raise Exception(f"获取应用凭证失败: {app_token_data.get('msg')}")

    # Step 2: 用 code 换 user_access_token
    r = requests.post(
        "https://open.feishu.cn/open-apis/authen/v1/oidc/access_token",
        json={"grant_type": "authorization_code", "code": server.auth_code},
        headers={
            "Authorization": f"Bearer {app_token_data['app_access_token']}",
            "Content-Type": "application/json",
        },
    )
    data = r.json()
    if data.get("code") != 0:
        raise Exception(f"授权失败: {data.get('msg')}")

    token_data = data.get("data", {})
    token_data["_token_time"] = time.time()
    return token_data


def fetch_contacts(app_id, app_secret):
    """拉取通讯录并返回精简列表"""
    import requests

    # 获取 tenant token
    r = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": app_id, "app_secret": app_secret},
    )
    data = r.json()
    if data.get("code") != 0:
        return None, f"获取凭证失败: {data.get('msg')}"

    token = data["tenant_access_token"]

    # 拉取根部门成员
    r = requests.get(
        "https://open.feishu.cn/open-apis/contact/v3/users",
        headers={"Authorization": f"Bearer {token}"},
        params={"department_id": "0", "page_size": 50},
    )
    data = r.json()
    if data.get("code") != 0:
        return None, f"获取通讯录失败（错误码 {data.get('code')}）: {data.get('msg')}"

    items = data.get("data", {}).get("items", [])
    contacts = []
    for u in items:
        contacts.append({
            "name": u.get("name", ""),
            "open_id": u.get("open_id", ""),
            "mobile": u.get("mobile", ""),
            "status": "已激活" if u.get("status", {}).get("is_activated") else "未激活",
        })
    return contacts, None


def fetch_wiki_spaces(app_id, app_secret, user_token):
    """拉取知识库空间列表"""
    import requests

    all_spaces = []
    page_token = None

    while True:
        params = {"page_size": 50}
        if page_token:
            params["page_token"] = page_token

        r = requests.get(
            "https://open.feishu.cn/open-apis/wiki/v2/spaces",
            headers={"Authorization": f"Bearer {user_token}"},
            params=params,
        )
        data = r.json()
        if data.get("code") != 0:
            return None, f"获取知识库失败（错误码 {data.get('code')}）: {data.get('msg')}"

        items = data.get("data", {}).get("items", [])
        for s in items:
            all_spaces.append({
                "name": s.get("name", ""),
                "space_id": s.get("space_id", ""),
                "description": s.get("description", ""),
            })

        if not data.get("data", {}).get("has_more"):
            break
        page_token = data.get("data", {}).get("page_token")

    return all_spaces, None


# ─── 主流程 ──────────────────────────────────────────────────
def main():
    check_python_version()
    ensure_utf8()
    clear_screen()

    total_steps = 4

    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║                                              ║")
    print("  ║        飞书助手 · 安装引导                   ║")
    print("  ║        让 Claude 帮你操作飞书                ║")
    print("  ║                                              ║")
    print("  ╚══════════════════════════════════════════════╝")
    print()
    print("  接下来会分 4 步完成配置，大约需要 3~5 分钟。")
    print("  如果中途想退出，按 Ctrl+C 即可。")
    print()
    input("  准备好了吗？按回车开始 → ")

    # ─── 检查 requests 库 ─────────────────────────────────
    try:
        import requests  # noqa: F401
    except ImportError:
        print()
        print("  需要安装一个网络请求库（requests），正在自动安装...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
        print("  ✅ 安装完成！")
        import requests  # noqa: F401, F811

    # ═══════════════════════════════════════════════════════
    # 第 1 步：获取飞书应用凭证
    # ═══════════════════════════════════════════════════════
    print_header("获取飞书应用凭证", 1, total_steps)
    print("  你需要在飞书开放平台创建一个「应用」，")
    print("  就像给 Claude 办一张进入你飞书的「通行证」。")
    print()

    if ask_yes_no("要自动打开飞书开放平台吗？"):
        webbrowser.open("https://open.feishu.cn/app")
        print()
        print("  浏览器已打开。请按以下步骤操作：")
    else:
        print()
        print("  请手动打开这个网址：https://open.feishu.cn/app")
        print("  然后按以下步骤操作：")

    print()
    print("  ┌─────────────────────────────────────────┐")
    print("  │ 1. 点击「创建应用」→「企业自建应用」    │")
    print("  │ 2. 填写应用名称（比如「我的飞书助手」） │")
    print("  │ 3. 创建后，进入应用 →「凭证与基础信息」 │")
    print("  │ 4. 复制 App ID 和 App Secret            │")
    print("  └─────────────────────────────────────────┘")
    print()
    print("  如果你已经有应用了，直接粘贴凭证即可。")
    print()

    app_id = ask("App ID（应用ID，以 cli_ 开头）")
    app_secret = ask("App Secret（应用密钥）")

    # 验证凭证
    print()
    print("  正在验证凭证...")
    r = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal",
        json={"app_id": app_id, "app_secret": app_secret},
    )
    verify_data = r.json()
    if verify_data.get("code") != 0:
        print(f"  ❌ 凭证验证失败: {verify_data.get('msg')}")
        print("  请检查 App ID 和 App Secret 是否正确，然后重新运行此脚本。")
        sys.exit(1)
    print("  ✅ 凭证验证通过！")

    # ═══════════════════════════════════════════════════════
    # 第 2 步：基本配置
    # ═══════════════════════════════════════════════════════
    print_header("基本配置", 2, total_steps)
    print("  现在设置一些基本选项。不确定的可以直接按回车跳过，")
    print("  以后随时可以在 config.json 里修改。")
    print()

    default_chat_id = ask("默认群聊 ID（可选，按回车跳过）", default="", required=False)

    scopes = "docx:document docx:document:readonly wiki:wiki:readonly"
    print()
    print(f"  默认授权范围: {scopes}")
    print("  （包含：创建文档、读取文档、读取知识库）")
    if ask_yes_no("使用默认授权范围？"):
        pass
    else:
        scopes = ask("请输入自定义授权范围（空格分隔）")

    # 保存 config.json
    config = {
        "_说明": "飞书助手配置文件，由 setup.py 生成。请勿泄露 app_secret。",
        "app_id": app_id,
        "app_secret": app_secret,
        "default_chat_id": default_chat_id,
        "oauth_scopes": scopes,
        "team_members": {},
    }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print()
    print("  ✅ 配置已保存！")

    # ═══════════════════════════════════════════════════════
    # 第 3 步：OAuth 授权
    # ═══════════════════════════════════════════════════════
    print_header("授权登录", 3, total_steps)
    print("  接下来需要你在浏览器中登录飞书并点击「授权」，")
    print("  这样 Claude 才能以你的身份读写文档和知识库。")
    print()
    print("  ⚠ 重要：授权之前，请先在飞书开放平台完成以下设置：")
    print()
    print("  ┌──────────────────────────────────────────────────┐")
    print("  │ 进入你的应用 → 左侧菜单「安全设置」              │")
    print("  │ → 找到「重定向 URL」                             │")
    print("  │ → 添加：http://127.0.0.1:8080/callback           │")
    print("  └──────────────────────────────────────────────────┘")
    print()

    if ask_yes_no("已完成上述设置，开始授权？"):
        try:
            token_data = do_oauth(app_id, app_secret, scopes)
            with open(USER_TOKEN_PATH, "w", encoding="utf-8") as f:
                json.dump(token_data, f, indent=2, ensure_ascii=False)
            print()
            print("  ✅ 授权成功！Token 已保存。")
        except Exception as e:
            print(f"\n  ❌ 授权过程出错: {e}")
            print("  你可以稍后手动运行 oauth_server.py 重试。")
            token_data = None
    else:
        print("  已跳过。你可以稍后运行以下命令完成授权：")
        python_cmd = "python" if sys.platform == "win32" else "python3"
        print(f"  {python_cmd} scripts/oauth_server.py")
        token_data = None

    # ═══════════════════════════════════════════════════════
    # 第 4 步：获取团队信息
    # ═══════════════════════════════════════════════════════
    print_header("获取团队信息", 4, total_steps)
    print("  最后一步，自动获取你的团队通讯录和知识库列表，")
    print("  这样 Claude 就知道你的团队有谁、有哪些知识库。")
    print()

    # 获取通讯录
    print("  正在获取通讯录...")
    contacts, err = fetch_contacts(app_id, app_secret)
    if err:
        print(f"  ⚠ 获取通讯录失败: {err}")
        print("  可能是应用还没有通讯录权限。你可以稍后运行以下命令重试：")
        python_cmd = "python" if sys.platform == "win32" else "python3"
        print(f"  {python_cmd} scripts/feishu_client.py refresh-contacts")
    else:
        with open(CONTACTS_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(contacts, f, indent=2, ensure_ascii=False)
        # 同时写入 config.json 的 team_members
        config["team_members"] = {c["name"]: c["open_id"] for c in contacts if c["name"]}
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"  ✅ 找到 {len(contacts)} 位成员")

    # 获取知识库
    if token_data:
        print("  正在获取知识库列表...")
        spaces, err = fetch_wiki_spaces(app_id, app_secret, token_data["access_token"])
        if err:
            print(f"  ⚠ 获取知识库失败: {err}")
            print("  你可以稍后运行以下命令重试：")
            python_cmd = "python" if sys.platform == "win32" else "python3"
            print(f"  {python_cmd} scripts/feishu_client.py refresh-spaces")
        else:
            with open(SPACES_CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(spaces, f, indent=2, ensure_ascii=False)
            print(f"  ✅ 找到 {len(spaces)} 个知识库空间")
    else:
        print("  ⚠ 跳过知识库获取（需要先完成 OAuth 授权）")

    # ═══════════════════════════════════════════════════════
    # 完成
    # ═══════════════════════════════════════════════════════
    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║                                              ║")
    print("  ║           🎉 安装完成！                      ║")
    print("  ║                                              ║")
    print("  ╚══════════════════════════════════════════════╝")
    print()
    print("  你现在可以在 Claude Code 中直接用自然语言操作飞书了，比如：")
    print()
    print('    "给张三发一条飞书消息"')
    print('    "看看知识库里有什么文章"')
    print('    "帮我创建一个飞书文档"')
    print()
    print("  配置文件位置：")
    print(f"    {CONFIG_PATH}")
    print()
    print("  如需重新授权或刷新缓存：")
    python_cmd = "python" if sys.platform == "win32" else "python3"
    print(f"    {python_cmd} scripts/setup.py          # 重新运行安装引导")
    print(f"    {python_cmd} scripts/oauth_server.py   # 仅重新授权")
    print()


if __name__ == "__main__":
    main()
