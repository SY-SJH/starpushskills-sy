# 浏览器发布配置

## 目标

通过平台后台页面直接登录、填写、发布，不依赖开放 API。

有浏览器控制能力时，优先使用同事本人已经登录的可见浏览器页面。当前浏览器显示的账号就是本次发布账号，不需要把账号密码复制到聊天，也不要求创建 `storage_state`。账号密码和 Playwright 会话只是没有可用已登录浏览器时的本地后备方案，完整流程见 [browser-session.md](browser-session.md)。

发布前必须先确认浏览器状态：未连接不能发布；已连接但页面是登录页不能发布；只有已连接且页面显示当前账号身份时，才可以填充和提交。浏览器工具列出的 tabs 为空时，不要把用户本机 Chrome 的登录状态当成当前可用状态。

## 配置要点

浏览器脚本依赖 Python Playwright；运行环境没有该模块时先安装依赖并准备 Chromium：

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
```

```json
{
  "accounts": [
    {
      "name": "zhangsan",
      "platforms": {
        "xiaohongshu": {
          "auth_mode": "password",
          "login_url": "https://平台登录页",
          "publish_url": "https://平台发布页",
          "username": "账号",
          "password": "密码",
          "storage_state": "./sessions/zhangsan-xiaohongshu.json",
          "selectors": {
            "username": "登录账号输入框",
            "password": "登录密码输入框",
            "login_button": "登录按钮",
            "title": "标题输入框",
            "body": "正文输入框",
            "tags": "话题输入框",
            "publish_button": "发布按钮",
            "publish_success": "发布成功标记"
          }
        }
      }
    }
  ]
}
```

## 规则

- 密码只读本地配置，不写入仓库。
- 每个平台单独配置登录页和发布页。
- 如果页面有验证码、短信校验或抖音授权，先停在人工确认，不要尝试绕过。
- 首次登录后保存 `storage_state`，后续复用同一个本地会话文件。
- 如果后台页面结构变化，先更新 selectors，再继续发布。
- 视频平台还需要 `media_input`；上传完成后建议填写 `upload_complete`，发布后建议填写 `publish_success`，这样结果状态可以被验证。
- `--dry-run` 只打开页面、填充内容并截图，不会点击发布按钮。

## 首次登录

仅在没有可用已登录浏览器、并且要使用本地后备模式时，才执行：

```bash
.venv/bin/python scripts/bootstrap_browser_session.py --platform xiaoyunque --name zhangsan
```

在可见浏览器中完成登录后回到终端按回车。会话文件保存在账号配置的 `storage_state` 路径，之后生成和发布都会复用它。短信、二维码和抖音授权不能由脚本代填，必须由账号本人操作。

如果用户已经在 Chrome 或模型浏览器中登录，不能因为本地没有 `sessions/*.json` 就要求重新登录；应直接回到可见浏览器发布流程。Playwright 脚本无法自动读取另一个浏览器的登录态。
