# StarPush 界面参考素材

`assets/ui-reference/` 中的截图来自 StarPush 线上移动端页面，是视频出现产品界面时的唯一视觉参考：

| 文件 | 页面 | 可表达的内容 |
| --- | --- | --- |
| `home-dream.png` | 梦境首页 | 醒来记录梦境、梦境手记、真人解梦入口 |
| `record-dream.png` | 记录梦境 | 文字或语音记录、AI 协助回忆、整理这场梦 |
| `human-dream-guide.png` | 真人解梦 | 浏览平台认证真人解梦师和服务方向 |
| `activities.png` | 活动页 | 平台活动和角色相关内容，只有用户明确要求时使用 |
| `create-character.png` | 创建角色 | 创建虚拟角色资料和角色设定 |

## 使用规则

- 生成视频出现产品界面时，只能使用上述真实截图或基于它们的真实录屏。
- 不得根据文件名、产品名称或官网地址重新绘制页面。
- API 的 `product-demo` 模式会根据 [ui-reference.json](ui-reference.json) 的关键词自动选择最多 3 张截图；`auto` 模式识别到“平台介绍、界面、使用流程”等演示意图时也会自动选择。随后逐张调用官方文件上传接口，再把返回的 `pippit_asset_id` 放进营销视频任务的 `asset_ids`。
- 可以通过重复使用 `--ui-reference <素材ID>` 精确指定截图，例如 `--ui-reference home-dream --ui-reference record-dream`。
- 任何截图上传失败都必须停止视频任务，不能静默退回无参考素材的假界面生成。
- 梦境故事和虚拟人物模式默认不上传界面截图；没有实际附加素材时继续禁止生成软件界面。
- 用户提供新的线上截图后，应先确认页面确实来自 `https://starpush.show/`，再加入这个清单。
