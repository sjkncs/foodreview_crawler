# KeeTa HK Review Collector

只读采集 KeeTa 香港商家后台「顾客评价」数据，适用于已授权账号的近一周评价导出。

## 采集范围

- 页面：`https://merchant.mykeeta.com/m/web/app/shop#/evaluate`
- 接口：浏览器页面自动请求 `/api/order/getMerchantComments`
- 时间：默认 `2026-05-01` 至 `2026-05-07`，香港时区
- 门店：账号下 11 家 HEYTEA 香港门店
- 字段：评价人、评分、评价内容、标签、图片 URL、订单号、订单商品明细、原始 JSON

## 安全边界

脚本只执行登录、进入评价页、滚动分页和读取接口响应，不点击 `回复`、`申诉`、`提交`、`保存`、`确认` 等写入动作。

## 执行

```powershell
$env:PYTHONIOENCODING='utf-8'
python platforms\keeta\keeta_weekly_reviews.py --max-pages 22 --max-reviews 120 --browser-channel msedge
```

如需复用已登录态且不自动登录：

```powershell
python platforms\keeta\keeta_weekly_reviews.py --no-login --max-pages 22 --max-reviews 120 --browser-channel msedge
```

## 本地凭据

凭据保存在本地文件 `data/keeta_credentials.local.json`，不要提交到 GitHub。

```json
{
  "username": "...",
  "password": "..."
}
```

## 导出

导出目录：`exports/keeta/`

- JSON：UTF-8，包含 `reviews` 和采集元数据
- CSV：UTF-8 BOM，适合 Excel 直接打开

## 已验证结果

2026-05-08 执行全量检查：

- 捕获 22 页，共 433 条 30 日原始评价
- 本地筛选 2026-05-01 至 2026-05-07，共 99 条有效评价
- 99 条均包含订单商品明细
- 14 条包含图片 URL
