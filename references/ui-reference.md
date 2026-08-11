# StarPush 界面参考素材

`assets/ui-reference/` 中的截图来自 StarPush 线上移动端页面，是视频出现产品界面时的唯一视觉参考。线上截图统一使用手机视口 `390x844` 采集；`record-dream.png` 和 `create-character.png` 是用户提供的登录后页面参考，保留用于补充线上匿名访问无法直接进入的功能状态。

| 文件 | 页面 | 可表达的内容 |
| --- | --- | --- |
| `online-home-dream.png` | 梦境首页 | 醒来记录梦境、梦境手记、真人解梦入口 |
| `record-dream.png` | 记录梦境 | 文字或语音记录、AI 协助回忆、整理这场梦 |
| `online-human-dream-guide.png` | 真人解梦 | 浏览平台认证真人解梦师和服务方向 |
| `online-human-dream-guide-detail.png` | 解梦师详情 | 查看解梦师资料和预约入口 |
| `online-activities.png` | 活动页 | 浏览平台活动和角色相关内容，只有用户明确要求时使用 |
| `create-character.png` | 创建角色 | 创建虚拟角色资料和角色设定 |
| `online-login-register.png` | 登录注册弹窗 | 需要登录时的真实产品状态 |
| `online-create-menu.png` | 创建菜单 | 记录梦境和发布动态的入口选择 |
| `online-character-home.png` | 角色首页 | 浏览虚拟角色相关内容 |
| `online-character-profile.png` | 角色资料页 | 查看虚拟角色档案和设定 |
| `online-feed.png` | 动态推荐页 | 浏览社区动态和内容推荐 |
| `online-dream-brain-test.png` | 梦脑测试首页 | 梦脑测试的入口和介绍状态 |
| `online-dream-brain-question.png` | 梦脑测试题目 | 梦脑测试的答题状态 |
| `online-stardust.png` | 星屑漂流 | 星屑漂流功能和内容状态 |
| `online-bonsai-login.png` | 星光盆栽登录状态 | 登录保护下的星光盆栽页面 |
| `online-my-login.png` | 我的页面登录状态 | 登录保护下的个人中心页面 |

## 使用规则

- 生成视频出现产品界面时，只能使用上述真实截图或基于它们的真实录屏。
- 不得根据文件名、产品名称或官网地址重新绘制页面。
- API 的 `product-demo` 模式会根据 [ui-reference.json](ui-reference.json) 的关键词自动选择最多 3 张截图；`auto` 模式识别到“平台介绍、界面、使用流程”等演示意图时也会自动选择。随后逐张调用官方文件上传接口，再把返回的 `pippit_asset_id` 放进营销视频任务的 `asset_ids`。
- 默认平台演示优先使用梦境首页、记录梦境和真人解梦这组核心素材；其他页面会按主题关键词自动匹配。
- 可以通过重复使用 `--ui-reference <素材ID>` 精确指定截图，例如 `--ui-reference home-dream --ui-reference dream-brain-test`。
- 任何截图上传失败都必须停止视频任务，不能静默退回无参考素材的假界面生成。
- 梦境故事和虚拟人物模式默认不上传界面截图；没有实际附加素材时继续禁止生成软件界面。
- `source: "online"` 表示已从线上页面采集，`source: "user-provided"` 表示由用户提供；新增截图应先确认页面确实来自 `https://starpush.show/`，再加入这个清单。
