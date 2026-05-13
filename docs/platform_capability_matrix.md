# 平台能力矩阵

## 总览

| 平台 | 当前代码位置 | 登录方式 | 默认采集策略 | 订单详情 | 图片 URL | 视觉 Agent 用途 | 状态 |
|---|---|---|---|---|---|---|---|
| Hungry Panda | `scripts/hungry_panda_weekly_reviews.py` | 手机号 + 区号 | DOM + 订单详情页 | 已支持 | 评论图、商品图支持 | 进入分店、导航、弹窗恢复 | 可生产运行 |
| Fantuan | `platforms/fantuan/fantuan_weekly_reviews.py` | 账号密码 | DOM/API 混合 | 已支持 | 已支持 | 评价管理导航、详情展开 | 可生产运行 |
| GrabFood | `platforms/grabfood/grabfood_weekly_reviews.py` | Grab Portal | DOM + 汇总页/门店页 | 部分支持 | 字段已预留 | Go to Portal、Feedback、Ratings and reviews 定位 | 可生产运行 |
| Google Maps | `platforms/google_maps/google_maps_weekly_reviews.py` | 公开页面 | DOM 滚动 + 最新排序 | 不适用 | 公开评论图片，排除头像 | 评价 Tab、展开全文、查看译文 | 可生产运行 |
| KeeTa | `platforms/keeta/keeta_weekly_reviews.py` | 账号密码/Cookie | DOM + 筛选门店/日期 | 已探索 | 待统一 | 登录态检查、顾客评价页定位 | 待统一跑批 |
| OpenRice | `platforms/openrice/openrice_public_reviews.py` | 公开页面 | DOM | 不适用 | 待增强 | 食评区定位、展开分页 | 可接入 |
| Mfood | 计划 `platforms/mfood/mfood_weekly_reviews.py` | 账号密码 | API + DOM 导航 | 已探索接口 | 已探索接口 | 登录态检查、进入门店、评价页定位 | 待沉淀 executor |

## 平台细节

### Hungry Panda

- 范围：美国、加拿大、澳大利亚、英国、韩国。
- 关键步骤：总账号登录 -> Branch management -> Enter branch page -> Orders -> Ratings and reviews。
- 只读详情：点击 Order ID 打开订单详情。
- 图片：评论图片 URL 形如 `static.hungrypanda.co/panda/...jpg`。
- 风险边界：禁止回复、保存、修改门店信息。

### Fantuan

- 范围：加拿大、美国、澳大利亚。
- 关键步骤：登录 -> 评价管理 -> 顾客评价 -> 打开订单详情 -> 展开商品规格。
- 只读详情：操作列订单详情弹窗。
- 图片：评论图片 URL 形如 `storage.fantuan.ca/fantuan/...jpg`。
- 风险边界：禁止回复、状态变更、导出后台配置。

### GrabFood

- 范围：马来西亚账号、新加坡账号。
- 关键步骤：登录 -> Go to portal -> Feedback -> Ratings and reviews -> All stores 或单门店。
- 当前建议：先跑汇总页近 7 天有效评论，再扩展门店逐个采集。
- 详情：评论卡片 More/Reply to Customer 可展示更完整上下文，只读读取，不提交。
- 风险边界：禁止 Reply 提交。

### Google Maps

- 范围：海外店铺 Excel 中 Google Maps 链接。
- 关键步骤：打开门店链接 -> 评价 Tab -> 最新排序 -> 滚动 -> 展开全文 -> 保留 Google 译文。
- 图片：提取 `googleusercontent` / `ggpht` 评论图片，过滤头像小图。
- 已增强：`展开/更多` 真实按钮、译文状态、非头像图片 URL。
- 风险边界：公开页面，只读；禁止点击“撰写评价”。

### KeeTa

- 范围：香港 KeeTa 商户后台。
- 关键步骤：登录 -> 顾客评价 -> 筛选门店 -> 自定义时间 -> 查看订单。
- 详情：订单详情下方商品信息需要完整读取。
- 风险边界：禁止回复、保存、修改订单状态。

### OpenRice

- 范围：香港 OpenRice 喜茶分店。
- 关键步骤：链路页 -> 分店 -> 食评 -> 排除商家指定置顶，按最近日期采集。
- 详情：公开评论平台，无订单详情。
- 待增强：评论图片 URL、分页和置顶评论标记。

### Mfood

- 已确认入口：`https://merchant.o2o.mfoodapp.com/#/appraise/tackout`。
- 已确认页面：订单管理、订单详情、评价页。
- 已探索接口：
  - 评论列表：`POST /merchants/takeouts/comment/_comment_list`
  - 评论图片：`POST /merchants/takeouts/comment/_check_img`
  - 订单详情：`POST /merchants/takeouts/order/_get`
- 风险边界：只登录、进入门店、打开评价页、捕获只读接口；禁止回复/保存/置顶/屏蔽/拉黑。

## 状态定义

- **可生产运行**：已有脚本可导出近 7 天评论，字段覆盖可量化。
- **可接入**：已有爬虫或探索代码，但还未完成统一任务 DSL 包装。
- **待统一跑批**：已明确页面路径和字段，下一步做统一入口跑批。
- **待沉淀 executor**：已完成安全探索，下一步写平台采集器。

## 通用质量门槛

| 项目 | 必须项 |
|---|---|
| 评论列表 | 门店、评分、评论内容、评论时间、用户标识 |
| 时间过滤 | 近 7 天，支持固定日期区间 |
| 图片 | 提取评论图片 URL，排除头像和商品缩略图 |
| 订单详情 | 有订单 ID 的平台必须尝试读取详情 |
| 翻译 | 外文评论需保留原文并输出中文翻译 |
| 安全 | 不触发回复、保存、删除、状态变更 |
| 导出 | JSON + UTF-8 BOM CSV，后续可转 Excel |
