# 大一统外卖评论采集框架方案

## 目标

把 Hungry Panda、Fantuan、GrabFood、Mfood、KeeTa、Google Maps、OpenRice 等平台统一到一套可配置、可审计、可扩展的采集系统中。

原则是：保留现有平台专用代码作为高可靠执行器，不重写已经跑通的平台脚本；统一框架只负责任务描述、调度、只读安全控制、字段标准化、质量评估、翻译处理和后续平台扩展。

## 总体判断

纯视觉模型不能单独作为生产级采集方案。最优路线是 **Model-Guided Hybrid Automation**：

1. **接口优先**：优先读取后台 API 或网络响应，字段完整、可复现、准确率最高。
2. **DOM 第二优先**：适合后台表格、评价列表、订单详情弹窗、图片预览弹窗。
3. **视觉 Agent 负责导航**：用于跨语言菜单定位、按钮识别、异常状态识别、页面结构变化恢复。
4. **OCR/VLM 作为兜底**：当页面强动态、DOM 混淆、图片化表格时，用 VLM/OCR 结构化识别。
5. **人工门只处理高风险状态**：验证码、二次验证、登录异常、可能写入后台的动作必须暂停。

这条路线能让用户体验接近“只描述目标”，同时保留生产采集所需的准确性、可审计性和可回放性。

## 分层架构

| 层级 | 名称 | 职责 | 当前落地 |
|---|---|---|---|
| L0 | 任务 DSL | 描述平台、账号、门店、时间范围、字段、安全策略 | `unified_collector/schema.py` |
| L1 | 任务加载器 | 从 JSON 加载并校验任务 | `unified_collector/task_loader.py` |
| L2 | 执行器注册表 | 将统一任务分发到平台脚本 | `unified_collector/executors.py` |
| L3 | 平台执行器 | 登录、选店、筛选日期、读取列表、打开详情 | `platforms/` / `scripts/` |
| L4 | 抽取器 | 抽取评论、订单详情、图片 URL、原始 JSON/DOM | 平台脚本内部 |
| L5 | 视觉导航 | 菜单定位、按钮定位、登录/验证码/空数据判断 | `visual_agent/` 后续接入 |
| L6 | 数据治理 | 去重、近 N 天过滤、字段映射、翻译、导出 | `processors/` + 平台导出 |
| L7 | 质量评估 | 完整率、详情覆盖率、图片覆盖率、错误统计 | 统一结果指标 |

## 标准能力接口

每个平台最终应暴露同一组能力，哪怕内部实现完全不同：

```text
ensure_login()
select_scope(country/account/store)
open_review_page()
apply_time_range(start_date, end_date)
iter_review_rows()
open_order_detail(review)
extract_order_detail()
extract_image_urls(review)
normalize_review(raw)
export()
```

统一框架只调用这些能力，不直接维护平台页面选择器。页面选择器和接口字段属于平台执行器内部细节。

## 标准任务 DSL

```json
{
  "platform": "google_maps",
  "country": "美国",
  "stores": "all",
  "time_range": {
    "type": "last_days",
    "days": 7
  },
  "fields": [
    "rating",
    "review",
    "customer",
    "review_time",
    "image_urls",
    "translated_review"
  ],
  "mode": "auto",
  "max_reviews": 100,
  "safe_mode": true,
  "options": {
    "headless": false,
    "browser_channel": "msedge"
  }
}
```

## 标准字段模型

| 字段 | 含义 |
|---|---|
| `platform` | 平台名称 |
| `country` | 国家/地区 |
| `account` | 使用的账号标签，不保存明文密码 |
| `store` | 门店名称 |
| `store_id` | 平台门店 ID 或 JDE |
| `rating` | 综合评分 |
| `sub_ratings` | 口味、包装、配送、服务等子评分 |
| `review` | 原始评论或平台译文 |
| `review_language` | 识别语言 |
| `translated_review` | 中文翻译 |
| `customer` | 用户名或匿名名 |
| `review_time` | 评论时间 |
| `order_id` | 平台订单 ID |
| `ordered_items` | 商品明细结构化 JSON |
| `order_detail` | 完整订单详情文本 |
| `image_urls` | 评论图片 URL，排除头像 |
| `source` | API / DOM / OCR / visual |
| `raw_json` | 原始响应或原始 DOM 片段 |
| `quality_flags` | 缺字段、详情失败、疑似重复等标记 |

## 执行生命周期

```text
加载任务 DSL
  -> 校验安全策略
  -> 选择平台 executor
  -> 检查登录态
  -> 进入门店或国家范围
  -> 打开评价页
  -> 应用近 N 天筛选
  -> 读取评价列表
  -> 打开只读订单详情
  -> 提取评论图片 URL
  -> 标准化字段
  -> 翻译外文评论
  -> 导出 JSON/CSV/Excel
  -> 输出质量报告
```

## 策略选择顺序

```text
1. 已有平台 executor 可用       -> 直接运行
2. API/网络响应可读             -> API 抽取
3. DOM 表格/弹窗稳定            -> DOM 抽取
4. 页面入口或语言变化大          -> 视觉 Agent 导航 + DOM/API 抽取
5. DOM/API 均失败               -> OCR/VLM 兜底
6. 登录/验证码/风险写动作        -> 人工门暂停
```

## 安全边界

默认禁止：

- 回复客户、发送、提交、保存、删除、确认、支付、修改门店配置。
- 点击不确定是否会写入平台后台的按钮。
- 绕过验证码、暴力刷新、大批量异常登录。

默认允许：

- 登录、导航、点击菜单、筛选时间、选择门店、搜索、翻页、滚动。
- 打开只读详情弹窗、读取订单详情、关闭弹窗。
- 本地导出 JSON、CSV、Excel。

## 质量指标

| 指标 | 目标 | 说明 |
|---|---:|---|
| `field_completeness` | 95%+ | 核心字段非空比例 |
| `detail_coverage` | 90%+ | 有订单 ID 的评论成功读取订单详情比例 |
| `image_url_coverage` | 可解释 | 有图评论成功提取图片 URL 的比例 |
| `duplicate_rate` | <1% | 同平台同门店同订单去重后重复比例 |
| `out_of_range_rate` | 0% | 近 N 天过滤后越界数据比例 |
| `manual_gate_count` | 可追踪 | 登录/验证码/风险暂停次数 |
| `error_count` | 可追踪 | 每个平台、门店、订单详情失败数量 |

## 可靠性预期

| 方案 | 字段准确率 | 召回率 | 成本 | 适合场景 |
|---|---:|---:|---:|---|
| API/网络响应 | 98%+ | 95%+ | 低 | 后台接口可读 |
| DOM 抽取 | 90–97% | 85–95% | 中 | 表格结构稳定 |
| 视觉导航 + DOM/API | 90–98% | 80–95% | 中高 | 菜单和语言变化大 |
| OCR/VLM 表格识别 | 80–95% | 60–90% | 高 | 强反爬、截图页面 |
| 纯视觉 Agent | 70–90% | 50–85% | 高 | 探索、低频兜底、人工辅助 |

生产级采集应以混合方案为准，不以纯视觉作为唯一字段来源。

## 现有代码保留策略

现有平台脚本继续作为平台执行器：

- Hungry Panda：`scripts/hungry_panda_weekly_reviews.py`
- Fantuan：`platforms/fantuan/fantuan_weekly_reviews.py`
- GrabFood：`platforms/grabfood/grabfood_weekly_reviews.py`
- Google Maps：`platforms/google_maps/google_maps_weekly_reviews.py`
- KeeTa：`platforms/keeta/keeta_weekly_reviews.py`
- OpenRice：`platforms/openrice/openrice_public_reviews.py`
- Mfood：后续沉淀为 `platforms/mfood/mfood_weekly_reviews.py`

统一框架不替换这些脚本，而是把它们包装成 capability plugin。新平台先完成安全探索记录和任务 DSL，再沉淀平台 executor。

## 新平台接入流程

1. **账号与范围确认**：账号、国家、门店列表、后台链接、是否需要总账号进入分店。
2. **只读探索**：登录、菜单、评价页、筛选器、订单详情、图片入口。
3. **接口捕获**：记录评论列表 API、订单详情 API、图片字段来源。
4. **字段映射**：映射到标准字段模型。
5. **安全白名单**：明确允许点击和禁止点击的动作。
6. **采集器实现**：平台目录独立保存，例如 `platforms/mfood/`。
7. **统一入口接入**：在 `unified_collector/executors.py` 注册。
8. **质量报告**：每次导出附带字段完整率和错误列表。

## 用户最优交互

最终用户只需要做三件事：

1. 提供平台账号、门店或后台链接。
2. 选择时间范围和字段范围。
3. 运行统一任务，或让系统按国家/账号分批执行。

系统输出：

- 原始 JSON。
- UTF-8 BOM CSV。
- 翻译后的中文评论。
- 完整订单详情文本。
- 评论图片 URL。
- 质量报告和失败订单列表。

## 当前实施路线

1. 完善 `unified_collector` 的任务 DSL、执行器注册和结果标准化。
2. 将 Hungry Panda、Fantuan、GrabFood、Google Maps、KeeTa、OpenRice 注册为可调用 executor。
3. 完成 Mfood executor，保留登录态、评价列表 API、订单详情 API、图片 URL。
4. 将视觉 Agent 限定为导航和异常恢复 fallback。
5. 为每个平台建立能力矩阵、失败样本和只读安全边界。
6. 后续新平台按“探索 -> 标准字段 -> executor -> 质量报告”流程沉淀。
