# Stitch 导出模板接入方案

## 当前导出形态

当前采用的导出目录：

`C:\Users\Administrator\Downloads\stitch_global_review_insight_console (7)`

历史导出目录：

`C:\Users\Administrator\Downloads\stitch_global_review_insight_console`

已归档到项目：

`ui/stitch_static`

旧的简易索引版本已备份到：

`ui/stitch_static_backup_before_export7`

文件类型：

- 每个页面是独立 `code.html`。
- 每个页面附带 `screen.png`。
- 样式依赖 Tailwind CDN、Google Fonts、Material Symbols。
- 没有 `package.json`，不是 React/Vite/Next 项目。
- 无需安装依赖即可打开 HTML 预览。

## 已归档页面

| 页面 | 路径 |
|---|---|
| 入口索引 | `ui/stitch_static/index.html`，自动跳转 Dashboard |
| 首页 Dashboard | `ui/stitch_static/dashboard_global/code.html` |
| 采集任务 | `ui/stitch_static/collection_tasks_global/code.html` |
| 门店覆盖 | `ui/stitch_static/store_coverage_global/code.html` |
| 评论工作台 | `ui/stitch_static/review_workbench_global/code.html` |
| 平台能力 | `ui/stitch_static/platform_matrix_global/code.html` |
| 质量报告 | `ui/stitch_static/quality_report_global/code.html` |
| 安全审计 | `ui/stitch_static/safety_audit_global/code.html` |

## 推荐接入路线

### 阶段 1：静态原型归档

目标：保留 Stitch 视觉成果，作为产品 Demo 和前端参照。

已完成：

- 复制到 `ui/stitch_static`。
- 生成 `index.html` 入口。

预览方式：

```powershell
cd C:\Users\Administrator\Desktop\foodreview_crawler
python -m http.server 8088 --directory ui\stitch_static
```

然后打开：

`http://localhost:8088`

### 阶段 2：NiceGUI 嵌入

目标：在现有 Python/NiceGUI 项目里展示 Stitch 页面。

建议：

- 新增一个 NiceGUI 路由，例如 `/prototype`。
- 用 iframe 指向静态页面。
- 后端仍使用现有 `unified_collector`。

优点：

- 改动小。
- 不需要引入 Node 构建链。
- 适合内部演示。

### 阶段 3：组件化重构

目标：把 Stitch HTML 转成真实可交互页面。

建议：

- 抽取共用 sidebar/header/table/card。
- 用后端 API 提供任务、门店、评论、质量报告数据。
- 页面数据从静态示例替换为 `exports/` 和 `data/store_registry.json`。

### 阶段 4：生产前端

如需独立前端，可再迁移到：

- Vite + React + Tailwind
- 或继续 NiceGUI，保持 Python 全栈

当前不建议马上引入 React，原因是项目主体仍是 Python 采集与 NiceGUI。

## 风险与注意

- Tailwind CDN 适合原型，不适合生产构建。
- Google Fonts/Material Symbols 依赖外网，离线环境可能显示异常。
- `review_workbench_global` 和 `store_coverage_global` 引用了外部图片 URL，后续生产要替换为真实采集图片 URL 或本地占位。
- Stitch HTML 当前是静态页面，按钮不会直接触发采集任务。

## 下一步

建议优先做：

1. 新增 NiceGUI `/prototype` 路由嵌入 `ui/stitch_static/index.html`。
2. 新增 `/api/summary` 输出当前采集汇总。
3. 新增 `/api/store-registry` 输出 `data/store_registry.json`。
4. 将 Dashboard 的示例数字替换成真实导出统计。
