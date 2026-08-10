---
name: starpushskills-sy
description: Generate and publish StarPush promotion content for Zhihu, Xiaohongshu, Douyin, Baidu Tieba, Weibo, and Xiaoyuzhou, with local draft saving and account-aware publishing. Use when the user asks to promote a product, create platform-matched content, reuse a direction for multiple platforms, or save drafts for later/manual/automatic posting.
---

# StarPush Skills SY

## 目标

把同一条推广需求，自动改写成适合不同平台的内容，并支持先落本地草稿、再手动发布或定时发布。

## 使用流程

1. 先识别用户给的是“自主推广”还是“定向创作”。
2. 再识别目标平台和是否需要视频。
3. 按平台生成内容，优先用最简输出：`标题`、`正文`、`标签/话题`。
4. 如果是 `抖音`，先产出视频脚本，再调用小云雀生成视频素材。
5. 生成结果先保存到本 skill 目录下的 `drafts/`。
6. 第一次运行时，如果 `drafts/` 不存在，先自动创建。
7. 发布前读取当前账号配置，避免混号。
8. 需要实际落盘时，优先调用 `scripts/create_draft_bundle.py`。
9. 需要读取账号时，优先调用 `scripts/load_account.py`。
10. 需要直接登录平台后台发布时，优先调用 `scripts/publish_via_browser.py`。
11. 如果平台要求短信验证码、二维码或抖音登录，先用 `scripts/bootstrap_browser_session.py` 完成一次人工登录，再复用本地会话。
12. 如果需要让小云雀生成视频，优先调用 `scripts/generate_video_via_browser.py`。
13. 如果用户只想要一条命令跑完整流程，优先调用 `scripts/run_campaign.py`。

## 常用命令

只生成文字草稿时不需要账号：

```bash
.venv/bin/python scripts/run_campaign.py \
  --topic "梦境记录工具推广" \
  --direction "睡前记录" \
  --platforms "小红书,百度贴吧"
```

抖音视频或自动发布需要先在 `accounts.json` 中选定 `--name`。短信、二维码或抖音授权平台首次使用时，先执行：

```bash
.venv/bin/python scripts/bootstrap_browser_session.py \
  --platform xiaoyunque \
  --name zhangsan \
  --account-file accounts.json
```

之后再用 `run_campaign.py --name zhangsan ... --platforms 抖音` 生成视频；发布时增加 `--auto-publish`。平台页面首次接入或页面改版前，先用 `publish_via_browser.py --dry-run` 检查填充结果。

## 平台规则

- `抖音`：视频脚本、分镜/口播、封面文案、话题。
- `小红书`：标题、种草正文、标签。
- `知乎`：标题、回答正文、话题。
- `百度贴吧`：标题、帖子正文、互动引导。
- `微博`：短文案、话题。
- `小宇宙`：标题、口播稿、节目简介。

## 账号规则

- 同一 skill 允许多人共用。
- 每个同事使用自己的平台账号配置。
- 发布时必须读取当前账号，不允许写死单账号。
- 账号文件使用 `accounts.json`，支持旧的单账号格式和 `accounts` 多账号格式；该文件只保存在本机。
- 密码、Cookie 和 token 不得写进草稿清单、截图说明或终端输出。

## 可执行组件

- `scripts/create_draft_bundle.py`：创建草稿目录、写入清单和平台内容。
- `scripts/load_account.py`：按同事名和平台读取账号配置。
- `scripts/build_publish_plan.py`：把草稿和账号拼成发布计划。
- `scripts/ensure_drafts_dir.py`：首次使用时创建 `drafts/`。
- `scripts/publish_via_browser.py`：用账号密码打开平台后台并提交发布。
- `scripts/bootstrap_browser_session.py`：人工完成短信/抖音登录后保存会话。
- `scripts/generate_video_via_browser.py`：调用小云雀生成视频并保存到草稿目录。
- `scripts/run_campaign.py`：按平台批量生成、排队和发布。
- `scripts/publish_scheduled.py`：执行已经到时间的本地发布队列。

## 交付边界

- 可以完成：内容生成、平台改写、草稿落盘、账号选择、发布包整理。
- 暂不直接承诺：平台后台 API 直发，因为不同平台的授权和接口形式不一致。
- 如果用户要求自动发布，优先用浏览器自动化登录后台并提交。
- 如果登录页需要验证码、短信或抖音授权，必须人工完成一次登录，不尝试绕过。
- 人工登录成功后只保存 Playwright `storage_state`，后续任务复用本地登录态，不重复填写短信或授权信息。
- 登录态失效时停止当前任务，并提示重新执行人工登录命令；不得在未确认登录成功时发布。
- 如果用户要求视频，先让小云雀生成，再把视频文件放进草稿包。
- 如果用户指定发布时间，使用 `--publish-at` 写入 `schedule.json`，到时间后运行 `scripts/publish_scheduled.py --once` 对到期草稿发布；队列不会绕过人工登录。

## 输出要求

- 先保证内容像对应平台的真实用户发帖。
- 不要把所有平台都写成同一种广告口吻。
- 如果用户只给方向，就先按方向创作，再按平台拆分。
- 如果用户明确要求仅生成草稿，就不要自动发布。

## 参考

- 平台输出模板：见 [references/platform-templates.md](references/platform-templates.md)
- 账号配置格式：见 [references/account-config.md](references/account-config.md)
