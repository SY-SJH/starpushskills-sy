# 小云雀视频生成

## 目标

通过浏览器进入小云雀后台，完成视频素材生成，并把结果保存到本地草稿目录。

## 最小配置

```json
{
  "name": "zhangsan",
  "platforms": {
    "xiaoyunque": {
      "auth_mode": "sms-or-douyin",
      "login_url": "https://example.com/login",
      "generate_url": "https://example.com/video-generator",
      "storage_state": "./sessions/xiaoyunque.json",
      "selectors": {
        "prompt": "textarea[name='prompt']",
        "style": "input[name='style']",
        "generate_button": "button:has-text('生成')",
        "download_button": "button:has-text('下载')"
      }
    }
  }
}
```

## 规则

- 首次登录先人工确认短信或抖音授权。
- 后续复用 `storage_state`。
- 生成完成后把成品和提示词一起保存进 `drafts/`。
- 如果页面需要选风格、比例或时长，先按配置填入，再执行生成。
- 生成页被重定向到登录页时停止，并提示重新执行人工登录命令。
- `selectors` 至少需要 `prompt`、`generate_button`、`download_button`；若生成按钮不会立即显示下载按钮，再配置 `generation_ready`。
- 下载后会将 `media_path` 和 `media_type` 写入抖音草稿项，发布脚本据此上传视频。

## 首次使用命令

```bash
.venv/bin/python scripts/bootstrap_browser_session.py \
  --platform xiaoyunque \
  --name zhangsan \
  --account-file accounts.json
```

完成短信或抖音登录后回到终端按回车，登录态会保存到配置中的 `storage_state`。这一步必须由账号本人完成。
