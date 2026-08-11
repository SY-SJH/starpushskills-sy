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

视频内容模式可以是：

- `auto`：根据主题判断；具体梦境优先做梦境故事，明确要求功能演示时才介绍平台。
- `product-demo`：围绕真实产品使用场景创作。
- `dream-story`：围绕具体梦境或梦境现象创作。
- `virtual-character`：使用虚拟人物演绎梦境或产品场景。

所有模式都遵守 [video-content.md](video-content.md) 的界面真实性规则。平台演示模式会自动：

1. 从 [ui-reference.json](ui-reference.json) 选择与主题匹配的真实页面截图。
2. 逐张调用 `POST /api/biz/v1/skill/upload_file` 上传文件。
3. 读取响应中的 `data.pippit_asset_id`。
4. 将素材 ID 列表作为 `asset_ids` 传入营销视频任务。
5. 在提示词中要求直接使用截图做平移、缩放、裁切或转场，不得重新绘制界面。

梦境故事和虚拟人物模式默认不上传产品截图；用户明确指定 `--ui-reference` 时除外。素材上传失败时停止任务，不会退回假界面生成。

API 只负责生成和下载视频；发布到抖音仍然需要当前已登录的发布页面，并且只有用户明确要求发布时才提交。
