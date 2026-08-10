# 已登录浏览器工作流

## 先判定状态

发布或生成视频前，先检查运行环境的浏览器能力和可控制标签。只能把下面三种状态作为判断依据：

- **未连接**：浏览器工具不可用，或 Chrome relay/扩展返回空的 tabs。此时不能使用用户电脑里的 Chrome，也不能声称“已登录”。
- **已连接但未登录**：能看到 `https://xyq.jianying.com/home` 或平台页面，但页面显示手机号登录、通过抖音登录、二维码或其他登录入口。此时只能请用户本人在这个已连接标签中登录。
- **已连接且已登录**：能看到创作 Agent、平台发布工作台，并能从页面看到当前账号身份。只有这个状态才允许填充内容、生成视频或发布。

新建的浏览器窗口、刚生成的 `userDataDir`、存在但为空的 Cookies 文件，都只能说明浏览器启动了，不能说明用户已经登录。

如果用户说“我本地 Chrome 已经登录”，但当前工具列出的 relay tabs 为空，必须如实说明“当前运行环境还接不到那个 Chrome 标签”。不要要求用户发送密码、Cookie 或验证码；应提示用户把目标标签附加到运行环境支持的 relay，或者选择在当前可见浏览器重新登录。不要自行发明扩展名、按钮名称或“Attached”状态文案，除非当前运行环境确实显示了这些信息。

浏览器里已经登录，并不要求工作区里存在 `accounts.json` 或 `sessions/*.json`。

当前浏览器会话的账号以页面上显示的账号头像、昵称或工作台身份为准。多人共用 skill 时，每个人应在自己的浏览器用户配置中登录自己的账号；skill 不读取 Cookie、localStorage、密码、验证码或浏览器 profile，也不把登录态导出到仓库。

## 飞书 OpenClaw 的连接边界

飞书只是消息入口，真正能操作浏览器的是 OpenClaw Gateway/浏览器节点。必须先确认 Gateway 和 Chrome 的部署关系：

- **同一台电脑**：扩展设置里的默认端口 `18792` 才可能有效；在这台电脑运行 `openclaw browser extension pair`，把命令输出的配对字符串粘贴到扩展工具栏弹窗中，再选择 `All tabs` 或 `Selected tabs`。
- **Gateway 在远程服务器**：不要把远程 Gateway 的地址或飞书机器人 token 填进 `127.0.0.1` 配置。由 Gateway 所在机器生成配对字符串：`openclaw browser extension pair --gateway-url wss://你的-gateway-域名`，再在本机 Chrome 扩展中完成配对；远程 Gateway 必须实际开放 `/browser/extension` 路径。
- **浏览器节点模式**：本机运行 OpenClaw browser node，由 Gateway 通过已认证的节点连接代理浏览器操作；这不是把 Chrome Cookie 上传到飞书。

截图里的 `Gateway token` 是 OpenClaw Gateway 的认证配置（`gateway.auth.token` 或 `OPENCLAW_GATEWAY_TOKEN`），不是飞书 token、StarPush 账号密码、小云雀手机号或短信验证码。若没有明确拿到本机 Gateway 的配置，不要猜 token，也不要把 token 发到聊天中。

配对成功的判断不是看设置页能否打开，而是扩展不再显示红色连接错误，并且 OpenClaw 的 Chrome profile 能列出带真实 URL 的普通网页标签，例如 `https://xyq.jianying.com/home`。如果 OpenClaw 运行在飞书云端且没有本机浏览器节点或远程扩展 relay，skill 无法直接操作用户本机 Chrome。

## 无浏览器时的后备模式

只有用户明确要求使用独立命令行流程时，才使用：

- 本机 `accounts.json` 读取账号配置。
- Playwright 独立浏览器和 `sessions/*.json` 登录态。
- 首次登录由用户本人完成短信、二维码或抖音授权，再保存 `storage_state`。

`scripts/generate_video_via_browser.py` 和 `scripts/publish_via_browser.py` 属于这个后备模式，不能自动接管用户已经打开的 Chrome 或模型内浏览器。找不到本地会话文件时，不能直接断言用户没有登录；先说明“本地后备模式没有登录态，但当前浏览器是否登录需要另行确认”。只有用户选择后备模式才提示执行 `bootstrap_browser_session.py`。

## 小云雀

小云雀入口是 `https://xyq.jianying.com/home`。页面登录方式是手机号短信验证码或“通过抖音登录”。已连接的标签打开后如果出现登录页，停止自动化，提示用户本人在这个标签完成登录；用户说登录完成后重新读取页面确认，不要只凭口头确认继续。

登录成功后，在“创作 Agent”页面使用可见的文本输入区（提示语类似“描述你的想法，用 @ 引用图片/视频/音频/文件作为参考，用 / 使用技能”）提交视频创作要求，再使用“开始生成”。生成完成后下载视频到本次 skill 的 `drafts/<本次草稿>/` 目录，并把视频文件名写入抖音草稿清单。

生成视频可能消耗小云雀额度或产生外部内容。用户只要求写稿时不要点击“开始生成”；用户明确要求生成视频时才执行，并在提交前确认产品、方向和平台没有理解错误。

## 发布

用户明确要求发布时，只在“已连接且已登录”状态打开目标平台的可见发布页面，核对当前登录身份，填入本平台草稿，上传本地媒体（如有），再提交。用户只要求生成内容或保存草稿时，不点击最终发布按钮。

验证码、二维码、短信和抖音授权由用户本人完成；不要尝试绕过。提交发布是外部副作用，提交前必须能确认目标平台、当前账号和本次文案/媒体。

## 定时发布

定时任务保存草稿、发布时间、平台和账号标识。真正到点发布时仍需要一个能唤醒模型并连接到已登录浏览器的执行环境；本地 `publish_scheduled.py` 只适用于已经保存 `storage_state` 的 Playwright 后备模式，不会凭空获得当前 Chrome 登录态。
