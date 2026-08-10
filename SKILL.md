---
name: starpushskills-sy
description: Generate and publish StarPush promotion content for Zhihu, Xiaohongshu, Douyin, Baidu Tieba, Weibo, and Xiaoyuzhou, with local draft saving and account-aware publishing. Use when the user asks to promote a product, create platform-matched content, reuse a direction for multiple platforms, or save drafts for later/manual/automatic posting.
---

# StarPush Skills SY

## 目标

把同一条推广需求，自动改写成适合不同平台的内容，并支持先落本地草稿、再手动发布或定时发布。

## 使用流程

1. 读取 [references/product-profile.md](references/product-profile.md) 作为默认产品资料。用户说“推广我们平台”或“推广 StarPush”时直接使用它，不要再次追问产品是什么；用户明确推广其他产品时才要求一句话产品描述。
2. 识别用户给的是“自主推广”还是“定向创作”。用户只给方向时，使用默认产品资料加这个方向创作。
3. 识别目标平台和是否需要视频。按平台生成内容，文字平台优先输出 `标题`、`正文`、`标签/话题`；抖音优先输出视频脚本、口播/分镜、封面文案和话题。
4. 需要视频时，先写抖音内容，再在用户明确要求生成视频后使用小云雀。视频生成完成后保存到本次草稿目录。
5. 第一次运行时调用 `scripts/ensure_drafts_dir.py`，把文字、脚本、视频和清单都保存到 skill 目录下的 `drafts/`。
6. 需要实际落盘时调用 `scripts/create_draft_bundle.py`；需要生成本地发布计划时调用 `scripts/build_publish_plan.py`。
7. 需要发布或生成视频时，先按 [references/browser-session.md](references/browser-session.md) 检查浏览器连接和登录状态。必须先确认运行环境能看到目标网页，再根据页面状态决定下一步；不能根据用户过去说过“已经登录”就直接假定当前会话可用。
8. 浏览器处于“已连接且已登录”状态时，直接操作可见网页，以页面显示的账号为准，不要求 `accounts.json`。浏览器处于“未连接”或“已连接但未登录”状态时，先停止生成/发布，提示用户连接自己的浏览器标签或在当前可见浏览器完成短信/抖音登录；不得把新建的空白沙箱浏览器当成用户自己的 Chrome。
9. 只有用户明确选择独立命令行后备模式时，才使用 [references/account-config.md](references/account-config.md) 的本地账号后备模式，调用 `scripts/load_account.py`、`scripts/publish_via_browser.py` 或 `scripts/generate_video_via_browser.py`。首次短信、二维码或抖音登录调用 `scripts/bootstrap_browser_session.py`，由用户本人完成。
10. 用户明确要定时发布时保存 `schedule.json`。如果使用当前浏览器会话，定时点需要由能重新连接该浏览器的模型任务执行；`scripts/publish_scheduled.py` 只适用于本地 `storage_state` 后备模式。

## 常用命令

只生成文字草稿时不需要账号；默认产品是 StarPush 梦境平台：

```bash
.venv/bin/python scripts/run_campaign.py \
  --topic "梦境记录工具推广" \
  --direction "睡前记录" \
  --platforms "小红书,百度贴吧"
```

用户明确选择本地后备模式时，抖音视频或自动发布才需要先在 `accounts.json` 中选定 `--name`。短信、二维码或抖音授权平台首次使用时，先执行：

```bash
.venv/bin/python scripts/bootstrap_browser_session.py \
  --platform xiaoyunque \
  --name zhangsan \
  --account-file accounts.json
```

之后再用 `run_campaign.py --name zhangsan ... --platforms 抖音` 生成视频；发布时增加 `--auto-publish`。平台页面首次接入或页面改版前，先用 `publish_via_browser.py --dry-run` 检查填充结果。

有可用已登录浏览器时，不要为了“证明登录”去读取浏览器 Cookie 或强制创建 `storage_state`。直接在已经连接的标签中打开平台网页，确认页面账号后操作；具体步骤见 [references/browser-session.md](references/browser-session.md)。

## 平台规则

- `抖音`：视频脚本、分镜/口播、封面文案、话题。
- `小红书`：标题、种草正文、标签。
- `知乎`：标题、回答正文、话题。
- `百度贴吧`：标题、帖子正文、互动引导。
- `微博`：短文案、话题。
- `小宇宙`：标题、口播稿、节目简介。

## 账号规则

- 同一 skill 允许多人共用。
- 每个同事使用自己的浏览器账号；只有本地后备模式才维护自己的 `accounts.json` 和会话文件。
- 发布时必须识别当前账号：可见浏览器模式以页面上的账号身份为准；本地后备模式才读取 `accounts.json`，不允许写死单账号。
- 账号文件使用 `accounts.json`，支持旧的单账号格式和 `accounts` 多账号格式；该文件只保存在本机。
- 密码、Cookie 和 token 不得写进草稿清单、截图说明或终端输出。

## 可执行组件

- `scripts/create_draft_bundle.py`：创建草稿目录、写入清单和平台内容。
- `scripts/load_account.py`：按同事名和平台读取账号配置。
- `scripts/build_publish_plan.py`：把草稿和账号拼成发布计划。
- `scripts/ensure_drafts_dir.py`：首次使用时创建 `drafts/`。
- `scripts/publish_via_browser.py`：在本地 Playwright 后备模式打开平台后台、填充内容并提交发布。
- `scripts/bootstrap_browser_session.py`：人工完成短信/抖音登录后保存会话。
- `scripts/generate_video_via_browser.py`：在本地 Playwright 后备模式调用小云雀生成视频并保存到草稿目录；不能接管当前 Chrome。
- `scripts/run_campaign.py`：按平台批量生成、排队和发布。
- `scripts/publish_scheduled.py`：执行已经到时间的本地发布队列。

## 交付边界

- 可以完成：内容生成、平台改写、草稿落盘、账号选择、发布包整理。
- 暂不直接承诺：平台后台 API 直发，因为不同平台的授权和接口形式不一致。
- 如果用户要求自动发布，只有在浏览器状态确认是“已连接且已登录”时才操作后台并提交；没有可用浏览器时先停下说明原因，用户明确选后备模式后才用 Playwright。
- 如果登录页需要验证码、短信或抖音授权，必须人工完成一次登录，不尝试绕过。
- 后备模式人工登录成功后只保存 Playwright `storage_state`，后续任务复用本地登录态，不重复填写短信或授权信息；可见浏览器模式不导出登录态。
- 登录态失效时停止当前任务：可见浏览器模式让用户在当前页面重新登录，本地后备模式才提示重新执行人工登录命令；不得在未确认登录成功时发布。
- 如果用户要求视频，先让小云雀生成，再把视频文件放进草稿包。
- 如果用户指定发布时间，使用 `schedule.json` 保存计划；可见浏览器模式由能在到点时连接浏览器的模型任务执行，本地后备模式可运行 `scripts/publish_scheduled.py --once`。两种模式都不能绕过人工登录。

## 输出要求

- 先保证内容像对应平台的真实用户发帖。
- 不要把所有平台都写成同一种广告口吻。
- 如果用户只给方向，就先按方向创作，再按平台拆分。
- 如果用户明确要求仅生成草稿，就不要自动发布。

## 参考

- 平台输出模板：见 [references/platform-templates.md](references/platform-templates.md)
- 账号配置格式：见 [references/account-config.md](references/account-config.md)
