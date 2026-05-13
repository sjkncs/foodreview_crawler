# 视觉接管 PoC

这个目录提供一个“截图输入、坐标输出”的浏览器视觉 Agent 原型，用于验证是否能少写平台专用爬虫代码。

## 运行方式

```powershell
python visual_agent/browser_visual_agent.py visual_agent/tasks/grabfood_reviews_poc.json
```

## 设计边界

- 只允许导航、点击筛选、滚动、打开详情、读取数据。
- 默认禁止提交、保存、发送、回复、删除、确认等动作。
- 模型输出必须是 JSON action；所有步骤会记录到 `exports/visual_agent/`。
- 这是 PoC，不替代现有结构化爬虫；生产采集建议继续保留 DOM/API 抽取做校验。

## 推荐用法

1. 用视觉 Agent 负责“进入正确页面、打开详情弹窗”。
2. 用现有平台爬虫负责“字段解析、去重、时间过滤、CSV/JSON 导出”。
3. 对低频页面变化，用视觉 Agent 作为 fallback，而不是完全替代爬虫。
