# 大一统方案：硬编码边界与可借鉴工程模式

## 结论

大一统方案不是“完全不写死”。生产系统必须把不可避免的平台差异封装在平台执行器内部，同时把业务范围、门店、账号、时间、字段、安全策略配置化。

正确边界是：

- **写死平台协议，不写死业务数据**。
- **写死安全禁区，不写死门店范围**。
- **写死稳定能力接口，不写死页面文本唯一表达**。
- **配置化任务、门店、账号标签、时间范围、导出字段**。

## 必须写死的内容

| 类别 | 内容 | 原因 | 放置位置 |
|---|---|---|---|
| 平台入口协议 | 登录 URL、评价页路径、订单详情入口 | 每个平台结构不同，必须由 executor 负责 | `platforms/*` |
| API/DOM 选择器 | 表格行、详情弹窗、图片节点、接口字段名 | 属于平台适配层，不应暴露给用户 | `platforms/*` |
| 安全禁区 | 回复、保存、提交、删除、支付、确认 | 防止误写后台，必须全局固定 | `SafetyPolicy` |
| 标准能力接口 | `ensure_login/open_review_page/extract_order_detail` | 保证上层统一调度 | `docs` + executor 约定 |
| 质量指标定义 | 完整率、详情覆盖率、图片覆盖率、错误数 | 保证跨平台可比较 | `QualityReport` |
| 平台能力矩阵 | 是否支持订单详情、图片、登录、时间筛选 | 调度器需要知道能力边界 | `platform_capabilities.py` |

## 不应该写死的内容

| 类别 | 应配置化方式 | 当前/下一步 |
|---|---|---|
| 门店清单 | `data/store_registry.json` | 已生成 |
| JDE、门店名、国家 | 门店注册表 | 已生成 |
| 平台链接 | 门店注册表 `platforms.*.url` | 已生成 |
| 国家/账号/门店范围 | 任务 DSL `country/stores/account` | 已支持 |
| 时间范围 | 任务 DSL `time_range` | 已支持 |
| 导出字段 | 任务 DSL `fields` | 已支持 |
| Headless/浏览器通道 | 任务 DSL `options` | 已支持 |
| 分段运行参数 | `start_index/limit/limit_stores` | 已支持 |
| 输出前缀 | `output.output_prefix` | 已支持 |

## 可借鉴的硅谷工程模式

这里借鉴的是工程思想，不是照搬某家公司产品。

### 1. Palantir AIP / Foundry：Ontology + Action + Guardrails

可借鉴点：

- 用对象模型统一业务实体：`Store`、`Review`、`OrderDetail`、`CollectionTask`、`QualityReport`。
- 用 Action 封装可执行动作：采集、打开详情、翻译、导出。
- 用 Guardrails 限制动作：只读、禁止回复/保存/删除/提交。
- 用审计日志证明每一步做了什么。

本项目落地：

- `data/store_registry.json` 是门店对象目录。
- `unified_collector/schema.py` 是任务和结果对象。
- `unified_collector/platform_capabilities.py` 是平台能力和安全边界。

### 2. Temporal：长任务分段与可恢复执行

可借鉴点：

- 长任务拆成国家、账号、门店、页码多个 Activity。
- 每个 Activity 可重试、可恢复、可记录状态。
- 浏览器崩溃时从上一个门店继续，不整批失败。

本项目落地建议：

- 后续增加 `runs/<run_id>/state.json`。
- 每采完一个门店写入 checkpoint。
- 失败门店进入 retry queue。

### 3. Stripe：幂等键与安全动作

可借鉴点：

- 每次任务有唯一 idempotency key。
- 重复执行不会重复写入或重复导出污染数据。
- 风险动作显式禁止。

本项目落地建议：

- 去重键：`platform + store_id/JDE + order_id + review_time + reviewer`。
- 输出文件带 `run_id`。
- 所有写动作默认不可调用。

### 4. dbt / Semantic Layer：统一指标口径

可借鉴点：

- 所有平台统一字段模型。
- 质量指标定义一次，多平台复用。
- Dashboard 不直接依赖平台原始字段。

本项目落地：

- 标准字段模型已定义。
- 后续把平台导出结果统一转成 `normalized_reviews.jsonl`。

### 5. Airflow / Dagster：可观测数据管道

可借鉴点：

- 每个平台采集是一个节点。
- 每个节点有日志、输入、输出、错误。
- 失败不影响其他国家/平台继续执行。

本项目落地建议：

- `CollectionTask -> ExecutorResult -> QualityReport` 形成可观测链路。
- Dashboard 展示每个平台的最后成功时间和失败原因。

## 推荐架构边界

```text
配置层
  store_registry.json
  task.json
  platform_capabilities.py

执行层
  unified_collector/run_task.py
  unified_collector/executors.py
  platforms/* collector

治理层
  normalize
  dedupe
  translate
  quality report

展示层
  dashboard
  review workbench
  quality report
```

## 下一步实现优先级

1. 将 Excel 门店信息稳定生成 `data/store_registry.json`。
2. 让 Google Maps、OpenRice、KeeTa 优先从注册表定位门店链接。
3. 为每次任务生成 `run_id` 和 checkpoint。
4. 统一平台导出字段到 `normalized_reviews.jsonl`。
5. 建立质量报告和失败门店重试机制。
