# OpenRice HK Public Review Collector

公开页面采集 OpenRice 香港喜茶门店食评，无需商户登录。

## 数据源

- 品牌页：`https://www.openrice.com/zh/hongkong/restaurants?chainId=10006678&tabIndex=0`
- 门店：品牌页自动枚举当前 10 家喜茶门店
- 食评页：每个门店 URL 后追加 `/reviews`
- 分页：优先页面按钮，失败时使用 `?page=2`、`?page=3` 等 URL 参数

## 字段

导出字段包括：

- 门店：名称、OpenRice URL、餐厅 ID、地址、区域
- 食评：评论 ID、评论 URL、作者、等级、日期、浏览量、标题、正文
- 评分：总评分、味道、环境、服务、卫生、抵食
- 用餐信息：推介美食、用餐日期、用餐途径、等候时间、人均消费
- 图片：评论图片 URL，使用 `|` 分隔

## 执行

```powershell
$env:PYTHONIOENCODING='utf-8'
python platforms\openrice\openrice_public_reviews.py --max-reviews-per-shop 45 --max-pages-per-shop 3 --browser-channel msedge
```

只跑单店：

```powershell
python platforms\openrice\openrice_public_reviews.py --shop-name "荃" --max-shops 1 --max-reviews-per-shop 15 --max-pages-per-shop 1 --browser-channel msedge
```

## 导出

导出目录：`exports/openrice/`

- JSON：UTF-8，保留结构化字段和门店列表
- CSV：UTF-8 BOM，适合 Excel 直接打开

## 已验证结果

2026-05-08 执行 10 店、每店最多 3 页：

- 当前门店：10 家
- 有效食评：185 条
- 正文完整：185 条
- 评分完整：185 条
- 图片 URL：163 条含图片

说明：OpenRice 的食评属于公开点评数据，页面顶部可能有平台推荐/置顶性质内容；脚本按页面展示顺序抓取，并按日期字段排序导出。
