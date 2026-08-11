#!/usr/bin/env python3
"""构造小云雀视频提示词，集中维护品牌素材和画面边界。"""

from __future__ import annotations

from collections.abc import Sequence


VIDEO_MODES = {
    "auto": "自动判断",
    "product-demo": "平台功能演示",
    "dream-story": "梦境主题故事",
    "virtual-character": "虚拟人物演绎",
}


def normalize_video_mode(value: str) -> str:
    """校验视频内容模式，避免模型收到含义不明确的自由枚举值。"""

    mode = value.strip().lower() or "auto"
    if mode not in VIDEO_MODES:
        choices = ", ".join(VIDEO_MODES)
        raise ValueError(f"视频内容模式必须是 {choices} 之一")
    return mode


def build_video_prompt(
    *,
    topic: str,
    direction: str,
    product: str,
    website: str,
    mode: str = "auto",
    virtual_character: str = "",
    ui_references: Sequence[str] = (),
) -> str:
    """生成 API 和网页流程共用的中文视频创作提示词。"""

    normalized_mode = normalize_video_mode(mode)
    if normalized_mode == "product-demo":
        content_instruction = (
            "以产品真实使用场景为主，介绍用户如何记录、整理和回看梦境；"
            "除非有真实界面参考，否则用旁白、字幕和虚拟人物表达流程。"
        )
    elif normalized_mode == "dream-story":
        content_instruction = (
            "以具体梦境或梦境现象为主线，先讲清楚梦里的情节和醒来后的感受，"
            "最后自然带出记录、整理或解读梦境的需求，不要拍成硬广。"
        )
    elif normalized_mode == "virtual-character":
        content_instruction = (
            "以虚拟人物作为主要叙事者或表演者，通过一个梦境片段讲故事；"
            "产品只在结尾作为自然的记录和整理工具出现。"
        )
    else:
        content_instruction = (
            "根据主题选择最自然的表达方式：具体梦境优先做梦境故事，"
            "明确的功能需求才做平台演示；不要默认每条视频都介绍产品功能。"
        )

    character_instruction = (
        f"指定虚拟人物设定：{virtual_character.strip()}。保持人物形象、服装和配色一致。"
        if virtual_character.strip()
        else "优先使用原创虚拟人物、动画或插画角色，不要使用仿真人、真人演员或现实人物肖像。"
    )
    reference_labels = [item.strip() for item in ui_references if item.strip()]
    if reference_labels:
        interface_instruction = (
            f"本次已实际附加 StarPush 真实界面截图：{'、'.join(reference_labels)}。"
            "如需出现产品界面，只能直接使用这些截图作为原始画面素材，通过平移、缩放、裁切或转场展示；"
            "必须保留截图中的文字、按钮、颜色和布局，不得重新绘制、改写、补全或虚构任何界面。"
        )
    else:
        interface_instruction = (
            "当前请求没有附带官网界面参考素材，因此本次不要出现软件界面、浏览器窗口、"
            "手机 App 假界面或虚构功能入口。"
        )

    return (
        "请制作一条适合抖音发布的竖屏营销短视频。\n"
        f"产品：StarPush / STAR DREAM；官网：{website}。\n"
        f"产品定位：{product}\n"
        f"主题：{topic}\n"
        f"创作方向：{direction or '自主创作'}\n"
        f"内容模式：{VIDEO_MODES[normalized_mode]}\n"
        f"内容要求：{content_instruction}\n"
        f"人物要求：{character_instruction}\n"
        "界面真实性是最高优先级：只有任务实际附加 starpush.show 的真实截图或录屏时才允许出现软件界面。"
        f"{interface_instruction}\n"
        "只使用已确认的产品能力，不虚构价格、活动、用户数量、效果数据或未确认功能。"
        "不要使用医疗诊断、心理治疗、科学预测或确定性预言表述；梦境解读只能作为中性自我观察和娱乐参考。"
    )
