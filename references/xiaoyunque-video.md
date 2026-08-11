# 小云雀视频生成

## 目标

通过浏览器进入小云雀后台，完成视频素材生成，并把结果保存到本地草稿目录。

## 当前网页

小云雀当前入口是 `https://xyq.jianying.com/home`，登录页是手机号验证码或“通过抖音登录”。登录成功后进入“创作 Agent”，可见输入区的提示语类似“描述你的想法，用 @ 引用图片/视频/音频/文件作为参考，用 / 使用技能”，生成按钮显示为“开始生成”。网页改版时优先按可见文本和 placeholder 重新定位，不要继续使用示例站点选择器。

优先使用 [browser-session.md](browser-session.md) 的已登录浏览器流程。下面的配置和命令只适用于没有可用已登录浏览器时的本地 Playwright 后备模式。

## 最小配置

```json
{
  "name": "zhangsan",
  "platforms": {
    "xiaoyunque": {
      "auth_mode": "sms-or-douyin",
      "login_url": "https://xyq.jianying.com/login",
      "generate_url": "https://xyq.jianying.com/home",
      "storage_state": "./sessions/xiaoyunque.json",
      "selectors": {
        "login_indicator": "input[placeholder='请输入手机号']",
        "auth_success": "textarea[placeholder*='描述你的想法']",
        "prompt": "textarea[placeholder*='描述你的想法'], [contenteditable='true']",
        "generate_button": "button:has-text('开始生成')",
        "download_button": "button:has-text('下载'), a:has-text('下载')"
      }
    }
  }
}
```

## 规则

- 生成视频前先读取 [video-content.md](video-content.md)，统一使用梦境主题、虚拟人物和真实界面约束；API 和网页模式不得各自发明另一套提示词规则。
- 首次登录先人工完成短信或抖音授权；不能绕过验证。
- 后续复用 `storage_state`。
- 生成完成后把成品和提示词一起保存进 `drafts/`。生成会消耗额度或产生外部内容，只有用户明确要求生成视频时才点击“开始生成”。
- 如果页面需要选风格、比例或时长，先按用户需求选择，再执行生成。
- 生成页被重定向到登录页时停止，并提示重新执行人工登录命令。
- 本地后备脚本的 `selectors` 至少需要 `prompt`、`generate_button`、`download_button`；若生成按钮不会立即显示下载按钮，再配置 `generation_ready`。
- 下载后会将 `media_path` 和 `media_type` 写入抖音草稿项，发布脚本据此上传视频。

## 首次使用命令

```bash
.venv/bin/python scripts/bootstrap_browser_session.py \
  --platform xiaoyunque \
  --name zhangsan \
  --account-file accounts.json
```

完成短信或抖音登录后回到终端按回车，登录态会保存到配置中的 `storage_state`。这一步必须由账号本人完成。
