# 浏览器发布配置

## 目标

通过平台后台页面直接登录、填写、发布，不依赖开放 API。

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

短信、二维码和抖音授权不能由脚本代填。先执行：

```bash
.venv/bin/python scripts/bootstrap_browser_session.py --platform xiaoyunque --name zhangsan
```

在可见浏览器中完成登录后回到终端按回车。会话文件保存在账号配置的 `storage_state` 路径，之后生成和发布都会复用它。
