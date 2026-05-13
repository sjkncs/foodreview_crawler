# Merchant Backend Review Automation

## 目标

海外外卖平台后台的评论采集流程拆成两层：

- 通用层：登录态复用、分店列表、进入分店、导航到评论页、表格解析、分页、最近 N 天过滤、CSV/JSON 导出。
- 平台层：国家域名、登录字段、导航文案、评论表头、评分字段、API 字段映射。

这样 Hungry Panda、KeeTa、Grab、Foodpanda 等平台只需要提供平台层配置，不重复写浏览器流程。

## Hungry Panda 当前流程

1. 打开国家后台分店列表。
2. 如果已登录，直接进入分店列表。
3. 如果未登录，填写账号密码；遇验证码时启用人工门。
4. 遍历 `Enter the Branch Page` 分店入口。
5. 进入分店后点击左侧 `Orders`。
6. 点击顶部 `Ratings and reviews`。
7. 提取字段：
   - `Review`
   - `Review contents`
   - `Image URLs`
   - `Order ID`
   - `Review time`
   - `Operation`
   - `Child ratings`
8. 只保留最近 7 天，按订单号去重，导出 UTF-8 BOM CSV。

评论图片优先保留 Hungry Panda 静态图片地址，例如：

```text
https://static.hungrypanda.co/panda/17678399473065a3ef90724a54e7e9e15d55f16d43882.jpg
```

## 国家配置

`scripts/hungry_panda_weekly_reviews.py` 支持：

- `--region usa`
- `--region ca`
- `--region au`
- `--region uk`
- `--region kr`

各国家使用独立 Edge profile：

- `data/browser_profiles/hungry_panda_usa`
- `data/browser_profiles/hungry_panda_ca`
- `data/browser_profiles/hungry_panda_au`
- `data/browser_profiles/hungry_panda_uk`
- `data/browser_profiles/hungry_panda_kr`

这些目录保存登录态，已被 `.gitignore` 排除。

## 凭据

不要把账号密码写进 Git。脚本按以下顺序读取：

1. 命令行 `--username` / `--password`
2. 环境变量：
   - `HUNGRY_PANDA_USERNAME`
   - `HUNGRY_PANDA_PASSWORD`
   - `HUNGRY_PANDA_KR_USERNAME`
   - `HUNGRY_PANDA_KR_PASSWORD`
3. 本地文件 `data/hungry_panda_credentials.local.json`

`data/` 已被 `.gitignore` 排除。

## 执行示例

首次登录某个国家时，如果出现验证码：

```bash
python scripts/hungry_panda_weekly_reviews.py --region ca --limit 1 --manual-login
```

在弹出的 Edge 窗口完成验证码后，脚本会继续采集并保存登录态。

登录态保存后可分段批量执行：

```bash
python scripts/hungry_panda_weekly_reviews.py --region ca --start-index 0 --limit 5 --max-reviews 100 --output-prefix ca_seg_0_4
python scripts/hungry_panda_weekly_reviews.py --region ca --start-index 5 --limit 5 --max-reviews 100 --output-prefix ca_seg_5_9
```

合并分段结果：

```bash
python scripts/merge_hungry_panda_exports.py --region ca --output-prefix ca_all
```

## 后续平台接入

新增平台时优先复用 `crawlers/merchant_backend.py` 的 recipe 模式，只补以下差异：

- 登录 URL 和登录检测 URL
- 国家/地区后台域名
- 分店管理入口文案
- 订单/评论导航文案
- 评论表格列映射
- 评论 API 字段映射
- 是否需要人工门处理验证码/Google 登录

不能点击回复、编辑、保存、删除等会修改商家后台状态的按钮。
