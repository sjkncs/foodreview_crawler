# Fantuan Review Collector

饭团平台单独放在 `platforms/fantuan/`，与 Hungry Panda 脚本隔离。

国家执行子目录：

- `platforms/fantuan/ca/`
- `platforms/fantuan/us/`
- `platforms/fantuan/au/`

## 覆盖范围

- 平台：Fantuan / 饭团
- 国家：`ca` / `us` / `au`
- 门户：统一使用 `https://merchant.fantuan.ca/#/login`
- 登录差异：先切换国家，再走账号密码登录
- 门店枚举：登录后从 `SESSIONKEY.groupStores` 自动读取账号下全部门店
- 评论页：`https://merchant.fantuan.ca/#/{restaurantId}-{COUNTRY}/evaluate/custom`
- 导出目录：
  - `exports/fantuan/ca/`
  - `exports/fantuan/us/`
  - `exports/fantuan/au/`

## 已验证

- `ca`：加拿大账号可抓评论和订单详情
- `us`：美国账号 `${FANTUAN_US_USERNAME}` 可登录，评论接口走 `us-gateway.fantuan.ca`
- `au`：澳洲账号 `${FANTUAN_AU_USERNAME}` 可登录，评论接口走 `au-gateway.fantuan.ca`

澳洲账号下已探测到多个门店，例如：

- `247551-AU` `HEYTEA喜茶（Hurstville）`
- `247306-AU` `HEYTEA喜茶（Burwood）`
- `247261-AU` `HEYTEA喜茶（George Street）`

## 采集字段

- 国家 / 国家代码 / 门店 ID / 门店路由 / 门店名称 / 区域名称
- 用户名称 / 头像 URL
- 评论内容 / 推荐商品 / 评论图片 URL
- 评分 / 包装评分 / 口味评分
- 评论时间 / 订单号 / POS 订单 ID
- 订单详情商品、规格、单价
- 完整订单详情文本
- 商品小计、净销售额、GST、佣金、佣金税、推广费、结算金额
- 完整订单详情 JSON

## 登录凭据

不要写入 Git。脚本按顺序读取：

1. 命令行 `--username` / `--password`
2. 环境变量：
   - `FANTUAN_CA_USERNAME` / `FANTUAN_CA_PASSWORD`
   - `FANTUAN_US_USERNAME` / `FANTUAN_US_PASSWORD`
   - `FANTUAN_AU_USERNAME` / `FANTUAN_AU_PASSWORD`
3. 本地文件 `data/fantuan_credentials.local.json`

`data/` 已被 `.gitignore` 排除。

## 执行

加拿大：

```bash
python platforms/fantuan/fantuan_weekly_reviews.py --country ca --max-reviews 100
```

美国：

```bash
python platforms/fantuan/fantuan_weekly_reviews.py --country us --max-reviews 100
```

澳洲：

```bash
python platforms/fantuan/fantuan_weekly_reviews.py --country au --max-reviews 100
```

只抓单个门店：

```bash
python platforms/fantuan/fantuan_weekly_reviews.py --country au --restaurant-id 247551 --max-reviews 20
```

限制门店数量做烟雾测试：

```bash
python platforms/fantuan/fantuan_weekly_reviews.py --country us --limit-stores 1 --max-reviews 3 --output-prefix smoke
```

脚本只做登录、导航、分页和“订单详情”读取，不点击回复、置顶、保存、发券等会修改后台状态的按钮。
