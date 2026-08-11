---
name: starpushskills-sy
description: Generate, save, and publish StarPush promotion content for Zhihu, Xiaohongshu, Douyin, Baidu Tieba, Weibo, and Xiaoyuzhou. Use when the user asks to promote StarPush, create platform-specific copy, generate a dream-focused or virtual-character Douyin video with strict real-UI constraints, or publish content.
---

# StarPush 推广助手

## 你只需要这样说

直接告诉我平台和方向即可。例如：

- “帮我推广 StarPush，发小红书和贴吧，方向是睡前记录梦境。”
- “帮我做一个抖音视频，主题是醒来就记下梦。”
- “把刚才的小红书内容发布出去。”

没有指定方向时，自动选择一个适合梦境记录的主题。没有指定平台时，先生成六个平台的版本。

## 工作方式

1. 读取 [references/product-profile.md](references/product-profile.md)，默认产品是 StarPush / STAR DREAM，不重复询问产品资料。
2. 按平台分别创作真实可发布的内容，并调用 `scripts/ensure_drafts_dir.py` 创建 `drafts/`，再把内容保存进去。
3. 用户只要求“写内容”时，只生成并保存草稿，不打开发布页面。
4. 用户要求“生成视频”时，先读取 [references/video-content.md](references/video-content.md)，再优先调用 `scripts/generate_video_via_api.py` 使用小云雀 API，自动提交、等待并下载视频；如果本机还没有 API Key，才使用小云雀网页浏览器流程。视频默认按主题创作梦境内容，不要默认做平台功能介绍。
5. 用户要求“发布”时，打开目标平台，填写刚生成的内容并发布。只有用户明确说发布，才执行最终发布操作。
6. 用户给出发布时间时，保存简单定时计划；到点只有浏览器仍可用并已登录时才发布，否则保留草稿并提示用户。

## 登录

每位同事直接在自己使用的浏览器里登录自己的平台账号，skill 以页面上显示的账号为准，不需要提供账号密码。

已经配置小云雀 API Key 时，生成视频不需要打开小云雀网页或再次登录。没有 API Key 时，才提示用户在小云雀页面完成手机号短信登录或抖音登录；用户说“登录好了”后，重新检查页面是否已经进入工作台和对应账号，再继续操作。不要让用户提供任何登录凭证。

如果当前无法操作浏览器，就先把文字、视频脚本和发布内容保存到 `drafts/`，明确告诉用户内容已保存但还没有发布，不要声称已经登录或发布成功。

## 平台格式

- 抖音：视频主题、口播稿、分镜、封面文案、话题。
- 小红书：标题、正文、标签。
- 知乎：标题、回答正文、话题。
- 百度贴吧：标题、帖子正文、互动引导。
- 微博：短文案、话题。
- 小宇宙：标题、口播稿、节目简介。

具体写法见 [references/platform-templates.md](references/platform-templates.md)。同一主题要改成各平台自然的表达，不要六个平台复制同一份广告文案。

## 草稿

第一次使用自动创建 `drafts/`。每次任务建立一个新的草稿目录，里面至少保存 `content.md`；视频任务还保存生成的视频文件和提示词。用户可以手动把自己的图片或视频放进这个目录，再要求继续发布。

小云雀 API 的设置和本地 Key 存放方式见 [references/xiaoyunque-api.md](references/xiaoyunque-api.md)。

视频内容和画面真实性规则见 [references/video-content.md](references/video-content.md)。没有真实官网界面参考素材时，禁止让视频出现软件界面；优先使用虚拟人物、动画或梦境场景。

已确认的线上界面截图清单见 [references/ui-reference.md](references/ui-reference.md)。使用 API 生成平台演示视频时，脚本会自动上传匹配截图并把返回的素材 ID 附加到生成任务；只有上传成功后，才允许在视频中展示界面。

## 内容边界

- 梦境默认只属于用户，不宣传为自动公开。
- AI 解梦只能宣传为自我观察和娱乐参考，不得宣传诊断、治疗、科学预测或确定性预言。
- 真人解梦师只能称为“平台认证真人解梦师”，不得暗示未确认的医疗或心理资质。
- 不虚构价格、活动、用户数量、效果数据或未确认的功能入口。
