# 小云雀 API

## 新手设置

1. 打开小云雀，进入【CLI/API】-【API】。
2. 点击【新建 Access Key】，复制完整 Key。
3. 在 skill 目录创建 `local/xiaoyunque-access-key.txt`，只写入这一行 Key。

也可以使用环境变量 `XIAOYUNQUE_ACCESS_KEY`。两种方式任选其一，不要把 Key 发到聊天或提交到 GitHub。

官方说明：[小云雀 API 体验指南](https://bytedance.larkoffice.com/docx/CQOYdJNLioLz6fxRzKXcCsKLnJh)。

## 自动生成

用户要求抖音视频时，skill 会自动：

1. 调用营销视频接口提交中文创作要求。
2. 使用 `run_id` 和 `thread_id` 轮询生成状态。
3. 下载完成的视频到本次 `drafts/` 草稿目录。
4. 更新抖音草稿清单中的视频文件名。

默认使用竖屏 `9:16`、720p、15-20 秒和字幕。用户明确指定时再调整这些参数。

API 只负责生成和下载视频；发布到抖音仍然需要当前已登录的发布页面，并且只有用户明确要求发布时才提交。
