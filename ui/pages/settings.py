"""
设置页面 — 深色主题
"""
from nicegui import ui
import config as cfg_module
from config import API_PRESETS

CARD   = "background:#141414; border:1px solid #222; border-radius:10px; padding:20px"
CARD2  = "background:#0e0e0e; border:1px solid #1a1a1a; border-radius:8px; padding:12px 16px"
BTN_P  = "background:#fff; color:#000; border:none; border-radius:7px; padding:8px 22px; font-size:13px; font-weight:600; cursor:pointer"
BTN_G  = "background:transparent; color:#888; border:1px solid #333; border-radius:7px; padding:8px 18px; font-size:13px; cursor:pointer"
LABEL  = "font-size:11px; color:#555; font-weight:500; letter-spacing:0.5px"
VAL    = "font-size:13px; color:#bbb"


def render() -> None:
    cfg = cfg_module.load()

    with ui.column().classes("w-full gap-4"):
        with ui.row().classes("items-center justify-between w-full").style("margin-bottom:8px"):
            with ui.column().classes("gap-0"):
                ui.label("系统设置").style("font-size:26px; font-weight:700; color:#fff; letter-spacing:-0.5px")
                ui.label("Settings").style("font-size:12px; color:#444")

        # ── 当前 API 状态 ─────────────────────────────────────────
        info = cfg_module.get_active_api_info()
        with ui.element("div").style(CARD2 + "; margin-bottom:4px; border-left:3px solid #fff"):
            with ui.row().classes("items-center gap-4 flex-wrap"):
                ui.label("当前 API").style(LABEL)
                ui.label(info["label"]).style("font-size:13px; color:#fff; font-weight:600")
                ui.label(info["base_url"]).style("font-size:11px; color:#444")
                ui.label(f"模型: {info['model']}").style("font-size:11px; color:#444")

        # ── API 端点切换 ──────────────────────────────────────────
        with ui.element("div").style(CARD):
            ui.label("API 端点切换").style("font-size:14px; font-weight:600; color:#fff; margin-bottom:4px")
            ui.label("一键切换不同 API 服务商").style("font-size:11px; color:#444; margin-bottom:16px")

            active_preset = cfg.get("api_preset", "iflow_new")
            preset_radio = ui.radio(
                options={k: v["label"] for k, v in API_PRESETS.items()},
                value=active_preset,
            ).props("inline dark color=white")
            preset_info = ui.label("").style("font-size:11px; color:#444; margin-top:4px")

            def update_preset_info():
                k = preset_radio.value
                p = API_PRESETS.get(k, {})
                preset_info.set_text(f"📡 {p.get('base_url', '')}  {p.get('note', '')}")

            preset_radio.on("update:model-value", lambda _: update_preset_info())
            update_preset_info()

            with ui.column().classes("w-full").style("margin-top:12px") as custom_section:
                custom_key_input = ui.input(
                    label="自定义 API Key",
                    value=cfg.get("anthropic_api_key", "") if active_preset == "custom" else "",
                    password=True, password_toggle_button=True,
                ).classes("w-full").props("dark dense outlined color=white label-color=grey-6")
                custom_url_input = ui.input(
                    label="自定义 Base URL",
                    value=cfg.get("anthropic_base_url", "") if active_preset == "custom" else "",
                ).classes("w-full").props("dark dense outlined color=white label-color=grey-6")

            def toggle_custom():
                custom_section.set_visibility(preset_radio.value == "custom")

            preset_radio.on("update:model-value", lambda _: toggle_custom())
            toggle_custom()

            async def apply_preset():
                k = preset_radio.value
                if k == "custom":
                    cfg_module.switch_api_preset("custom",
                        custom_key=custom_key_input.value,
                        custom_url=custom_url_input.value)
                else:
                    cfg_module.switch_api_preset(k)
                ui.notify(f"✅ 已切换：{API_PRESETS.get(k, {}).get('label', k)}", type="positive")

            async def test_connection():
                current_cfg = cfg_module.load()
                if not current_cfg.get("anthropic_api_key"):
                    ui.notify("请先填写 API Key", type="warning")
                    return
                try:
                    from processors.ai_client import chat
                    reply = await chat("只回复：连接成功", max_tokens=20)
                    ui.notify(f"✅ 连接成功 → {reply}", type="positive")
                except Exception as exc:
                    ui.notify(f"❌ 连接失败: {exc}", type="negative")

            with ui.row().classes("gap-3").style("margin-top:16px"):
                ui.button("应用切换", on_click=apply_preset).style(BTN_P)
                ui.button("测试连接", on_click=test_connection).style(BTN_G)

        # ── 模型设置 ──────────────────────────────────────────────
        with ui.element("div").style(CARD):
            ui.label("模型设置").style("font-size:14px; font-weight:600; color:#fff; margin-bottom:16px")

            ui.label("文字任务模型（情感分析 / 翻译 / 关键词 / 回复生成）").style(LABEL + "; margin-bottom:6px")
            model_select = ui.select(
                options={
                    "qwen3-235b-a22b-thinking-2507": "Qwen3-235B Thinking（深度推理 ✅）",
                    "qwen3-max":    "Qwen3-Max（通义千问旗舰）",
                    "deepseek-v3":  "DeepSeek-V3（均衡）",
                    "deepseek-r1":  "DeepSeek-R1（深度推理）",
                    "kimi-k2":      "Kimi-K2（月之暗面）",
                    "claude-haiku-4-5":  "Claude Haiku 4.5（需 Anthropic Key）",
                    "claude-sonnet-4-6": "Claude Sonnet 4.6（需 Anthropic Key）",
                },
                label="文字模型",
                value=cfg.get("model", "qwen3-235b-a22b-thinking-2507"),
            ).classes("w-full").props("dark dense outlined color=white label-color=grey-6")

            ui.label("OCR 视觉模型（固定用于截图识别）").style(LABEL + "; margin-top:14px; margin-bottom:6px")
            ocr_model_select = ui.select(
                options={
                    "qwen3-vl-plus": "qwen3-vl-plus（当前 ✅）",
                    "qwen3-vl-max":  "qwen3-vl-max（更强，消耗更多）",
                },
                label="OCR 模型",
                value=cfg.get("ocr_model", "qwen3-vl-plus"),
            ).classes("w-full").props("dark dense outlined color=white label-color=grey-6")

        # ── 爬虫策略 ──────────────────────────────────────────────
        with ui.element("div").style(CARD):
            ui.label("爬虫策略").style("font-size:14px; font-weight:600; color:#fff; margin-bottom:4px")
            ui.label("hybrid = 自动降级（推荐）：先尝试 API 拦截，失败后自动切换 OCR").style("font-size:11px; color:#444; margin-bottom:14px")

            ocr_strategy = ui.select(
                options={
                    "hybrid":         "🔀 Hybrid 自动降级（推荐）",
                    "api_intercept":  "⚡ API 拦截（速度最快）",
                    "dom_parse":      "🌐 DOM 解析（稳定）",
                    "ocr_screenshot": "📷 OCR 截图（反爬最强）",
                },
                label="爬取策略",
                value=cfg.get("ocr_strategy", "hybrid"),
            ).classes("w-full").props("dark dense outlined color=white label-color=grey-6")

            with ui.row().classes("items-center gap-6 flex-wrap").style("margin-top:14px"):
                headless_check = ui.checkbox(
                    "无头模式（后台运行，不显示浏览器窗口）",
                    value=cfg.get("headless", True),
                ).props("dark color=white")

            proxy_input = ui.input(
                label="代理地址（可选）",
                value=cfg.get("proxy", ""),
                placeholder="http://127.0.0.1:7890",
            ).classes("w-full").style("margin-top:10px").props("dark dense outlined color=white label-color=grey-6")

            max_pages_input = ui.number(
                label="默认最大爬取页数",
                value=cfg.get("max_pages", 10),
                min=1, max=200,
            ).style("width:180px; margin-top:10px").props("dark dense outlined color=white label-color=grey-6")

        # ── 自动化处理 ────────────────────────────────────────────
        with ui.element("div").style(CARD):
            ui.label("自动化处理").style("font-size:14px; font-weight:600; color:#fff; margin-bottom:14px")
            with ui.column().classes("gap-3"):
                auto_analyze_check = ui.checkbox(
                    "爬取后自动情感分析 + 关键词提取",
                    value=cfg.get("auto_analyze", True),
                ).props("dark color=white")
                auto_translate_check = ui.checkbox(
                    "自动翻译非中文评论",
                    value=cfg.get("auto_translate", True),
                ).props("dark color=white")
                auto_reply_check = ui.checkbox(
                    "自动生成回复建议（消耗较多 Token）",
                    value=cfg.get("auto_reply", False),
                ).props("dark color=white")

        # ── 保存 ─────────────────────────────────────────────────
        def save_all():
            current_cfg = cfg_module.load()
            current_cfg.update({
                "model":          model_select.value,
                "ocr_model":      ocr_model_select.value,
                "ocr_strategy":   ocr_strategy.value,
                "headless":       headless_check.value,
                "proxy":          proxy_input.value,
                "max_pages":      int(max_pages_input.value or 10),
                "auto_analyze":   auto_analyze_check.value,
                "auto_translate": auto_translate_check.value,
                "auto_reply":     auto_reply_check.value,
            })
            cfg_module.save(current_cfg)
            ui.notify("✅ 设置已保存", type="positive")

        ui.button("保存所有设置", on_click=save_all).style(BTN_P + "; margin-top:8px")
