# Mfood 安全探索记录

## 范围

- 平台：Mfood 商户后台
- 入口：`https://merchant.o2o.mfoodapp.com/#/appraise/tackout`
- 探索账号：天神巷门店账号，本地凭据保存在 `data/mfood_credentials.local.json`
- 安全策略：只执行登录、进入门店、打开外卖评价、查看图片、订单详情读取；不点击回复、保存、提交、导出、屏蔽、置顶、拉黑等写动作。

## 登录与门店进入

登录页字段：

- 用户名：`input[name="username"]`
- 密码：`input[name="password"]`
- 登录按钮：`button.el-button--primary`

浏览器启动需要：

```python
ignore_https_errors=True
```

原因：Mfood 后台证书链在 Playwright 环境中会触发 HTTPS 校验问题。

进入门店流程：

1. 打开 `https://merchant.o2o.mfoodapp.com/#/store`
2. 等待门店表格加载。
3. 点击表格操作列 `進入門店`。
4. 稳定 selector：`td.el-table_1_column_6 span`
5. 进入后左侧菜单变为：商品管理、訂單管理、營銷管理、經營數據分析、財務管理、評價管理。
6. 再打开 `https://merchant.o2o.mfoodapp.com/#/appraise/tackout`。

## 已确认只读接口

### 登录

```text
POST https://management-api.mfoodapp.com/token/_get
```

请求体字段：

```json
{
  "account": "...",
  "password": "...",
  "scope": "merchant"
}
```

密码字段由前端加密后提交；采集器使用浏览器登录，不在代码里复刻加密算法。

### 当前用户与门店

```text
POST https://management-api.mfoodapp.com/merchants/orgs/users/_getInfo
```

关键字段：

```json
{
  "userCode": "${MFOOD_USERNAME}",
  "merchantName": "萬利千億商業服務有限公司",
  "storeList": [
    {
      "storeId": "202403111604027034611",
      "storeName": "heytea喜茶 (天神巷店)"
    }
  ]
}
```

### 门店列表

```text
POST https://management-api.mfoodapp.com/merchants/orgs/store/_list_store_for_takeout_merchant
```

请求体：

```json
{
  "pageNo": 1,
  "pageSize": 20
}
```

已确认门店：

```json
{
  "id": "202403111604027034611",
  "storeName": "heytea喜茶 (天神巷店)",
  "classifyName": "甜品飲品",
  "type": 1
}
```

### 外卖评价列表

```text
POST https://management-api.mfoodapp.com/merchants/takeouts/comment/_comment_list
```

请求体：

```json
{
  "storeMark": "",
  "packMark": "",
  "tasteMark": "",
  "merchantReply": null,
  "startTime": "",
  "endTime": "",
  "userId": "",
  "isShield": null,
  "top": "",
  "pageNo": 1,
  "pageSize": 20
}
```

响应关键字段：

```json
{
  "id": "202604301703144818721",
  "storeId": "202403111604027034611",
  "storeName": "heytea喜茶 (天神巷店)",
  "alias": "***",
  "orderId": "202604301322072892181",
  "orderNum": "CRD202604301322072892181",
  "storeMark": 5,
  "createTime": 1777539794000,
  "storeContent": null,
  "packMark": 5,
  "tasteMark": 5,
  "merchantReply": false,
  "merchantContent": null,
  "avgMark": 5.0,
  "badCommentRateStr": "0%"
}
```

页面显示同一条为 `2026-04-30 17:03:14`。采集器应优先按页面时间或平台本地时区转换后的时间过滤。

### 评论图片

```text
POST https://management-api.mfoodapp.com/merchants/takeouts/comment/_check_img
```

请求体：

```json
{
  "id": "202604301703144818721"
}
```

第一条样例返回空数组，页面显示 `圖片详情 / 暫無圖片`。采集器应保留该接口，遇到非空数组时提取 HTTP 图片 URL。

### 订单详情

```text
POST https://management-api.mfoodapp.com/merchants/takeouts/order/_get
```

请求体：

```json
{
  "id": "202604301322072892181"
}
```

响应关键字段：

- `buyerNick`
- `receiverName`
- `receiverMobile`
- `address`
- `remark`
- `prdtList`
- `orderNum`
- `createTime`
- `payTime`
- `receiveTime`

`prdtList` 商品字段：

- `productName`
- `skuName`
- `skuPrice`
- `buyCount`
- `productAmtn`
- `imgUrl`
- `propertiesNames`
- `ingredientNames`
- `extendNames`

页面订单详情弹窗已确认展示：

- 收货人信息
- 商品信息
- 商品数量与价格
- 餐盒费、膠袋費、服務費、配送費、优惠、總計
- 訂單信息：订单编号、下单时间、支付时间、接单时间

## 采集字段建议

Mfood collector 应导出：

- `Platform`
- `Account`
- `Store ID`
- `Store`
- `Reviewer Name`
- `Overall Rating`
- `Taste Rating`
- `Package Rating`
- `Review Content`
- `Review Time`
- `Order ID`
- `Order Num`
- `Merchant Replied`
- `Merchant Reply`
- `Image URLs`
- `Order Buyer Nick`
- `Order Receiver Name`
- `Order Receiver Mobile`
- `Order Address`
- `Order Remark`
- `Product Image URLs`
- `Order Items JSON`
- `Order Items Text`
- `Expanded Order Detail`
- `Order Detail JSON`
- `Raw Review JSON`

## 近 7 天数据状态

当前系统日期为 2026-05-08。评价列表第一页最新记录为：

- `2026-04-30 17:03:14`
- `2026-04-29 19:18:30`

严格按最近 7 天，即从 2026-05-01 起，当前天神巷门店可能没有有效评论。采集器仍应支持 `--days 7`，并允许用 `--days 14` 或 `--days 60 --max-reviews 3` 做结构验证。

## 下一步实现

1. 新增 `platforms/mfood/mfood_weekly_reviews.py`。
2. 使用 Playwright 登录和进入门店，API 响应作为主数据源。
3. 评论列表使用 `_comment_list`。
4. 图片使用 `_check_img`。
5. 订单详情使用 `_get`。
6. 导出 UTF-8 BOM CSV 与 JSON 到 `exports/mfood/`。
7. 注册到 `unified_collector/executors.py`。
