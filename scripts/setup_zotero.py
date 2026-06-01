#!/usr/bin/env python3
"""
Zotero MCP 配置工具。

检测 Zotero MCP 服务是否可用，引导用户补全环境变量。

Usage:
  python3 scripts/setup_zotero.py             检测并提示配置
  python3 scripts/setup_zotero.py --check     仅检测状态
  python3 scripts/setup_zotero.py --export    输出 export 命令
"""
import sys, os, json, subprocess, shutil

def check_mcp():
    """检测 Zotero MCP 是否已注册到 Hermes/OpenClaw"""
    for cmd in ["hermes", "openclaw"]:
        if shutil.which(cmd):
            try:
                r = subprocess.run([cmd, "mcp", "list"], capture_output=True, text=True, timeout=5)
                if "zotero" in r.stdout.lower():
                    return True, cmd
            except:
                pass
    return False, None

def check_env():
    """检测环境变量"""
    api_key = os.environ.get("ZOTERO_API_KEY", "")
    user_id = os.environ.get("ZOTERO_USER_ID", "")
    return api_key, user_id

def check_zotero_local():
    """检测 Zotero 桌面端是否运行（本地 API 端口）"""
    try:
        import urllib.request, json
        r = urllib.request.urlopen("http://127.0.0.1:23119/api/users/1/items?limit=1", timeout=3)
        return True
    except:
        return False

def print_status():
    mcp_ok, agent = check_mcp()
    api_key, user_id = check_env()
    local_ok = check_zotero_local()

    print("=" * 50)
    print("Zotero 环境检测")
    print("=" * 50)

    print(f"\n🔌 Zotero MCP 服务: {'✅ 已启用' if mcp_ok else '❌ 未注册'}")
    if mcp_ok:
        print(f"   平台: {agent}")

    print(f"\n🔑 ZOTERO_API_KEY:   {'✅ 已设置' if api_key else '❌ 未设置'}")
    print(f"👤 ZOTERO_USER_ID:   {'✅ 已设置 (' + user_id + ')' if user_id else '❌ 未设置'}")

    print(f"\n💻 Zotero 桌面端:    {'✅ 运行中（本地 API 可用）' if local_ok else '❌ 未检测到'}")

    if not api_key and not user_id and not local_ok:
        print("\n⚠  Zotero 集成未配置。手动拖拽 PDF 到 Zotero 桌面端即可，无需配置。")
        print("   如需自动导入，请按以下步骤：")
        print("   1. 打开 https://www.zotero.org/settings/keys")
        print("   2. 创建 API Key")
        print("   3. 在终端执行：")
        print(f'      export ZOTERO_API_KEY=***')
        print(f'      export ZOTERO_USER_ID=***')
        print("   4. 将上述 export 命令加入 ~/.zshrc 或 ~/.bashrc")

    print()

if __name__ == "__main__":
    if "--check" in sys.argv:
        mcp_ok, _ = check_mcp()
        api_key, user_id = check_env()
        result = {
            "mcp_enabled": mcp_ok,
            "api_key_set": bool(api_key),
            "user_id_set": bool(user_id),
            "local_running": check_zotero_local()
        }
        print(json.dumps(result, indent=2))
    elif "--export" in sys.argv:
        print("# 添加到 ~/.zshrc 或 ~/.bashrc")
        print('export ZOTERO_API_KEY=***')
        print('export ZOTERO_USER_ID=***')
    else:
        print_status()
