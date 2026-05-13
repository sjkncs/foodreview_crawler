# Unified Collector

统一任务层用于包装已有平台爬虫，统一任务 DSL、调度、安全策略与导出格式。

## 快速运行

```powershell
python -m unified_collector.run_task unified_collector/tasks/hungry_panda_uk_last7.json --pretty
python -m unified_collector.run_task unified_collector/tasks/grabfood_my_auro_last7.json --pretty
python -m unified_collector.run_task unified_collector/tasks/mfood_default_last7.json --pretty
```

## 已注册平台

| 平台 | 统一名称 | 执行器 |
|---|---|---|
| Hungry Panda | `hungry_panda` | `scripts/hungry_panda_weekly_reviews.py` |
| Fantuan | `fantuan` | `platforms/fantuan/fantuan_weekly_reviews.py` |
| GrabFood | `grabfood` | `platforms/grabfood/grabfood_weekly_reviews.py` |
| Google Maps | `google_maps` | `platforms/google_maps/google_maps_weekly_reviews.py` |
| KeeTa | `keeta` | `platforms/keeta/keeta_weekly_reviews.py` |
| OpenRice | `openrice` | `platforms/openrice/openrice_public_reviews.py` |
| Mfood | `mfood` | `platforms/mfood/mfood_weekly_reviews.py` |
| Aomi | `aomi` | `platforms/aomi/aomi_weekly_reviews.py` |

## 任务模板

- `unified_collector/tasks/hungry_panda_uk_last7.json`
- `unified_collector/tasks/grabfood_my_auro_last7.json`
- `unified_collector/tasks/grabfood_my_puresips_last7.json`
- `unified_collector/tasks/grabfood_sg_last7.json`
- `unified_collector/tasks/mfood_default_last7.json`
- `unified_collector/tasks/mfood_tianshenxiang_last7.json`
- `unified_collector/tasks/aomi_macao_last7.json`（需补 `options.portal_url`）

## 安全边界（默认）

- 禁止写操作：`reply/save/submit/delete/confirm/payment`
- 只允许只读动作：登录、导航、筛选、打开详情、读取数据、导出文件
- 支持人工门：验证码/二次验证/异常登录时人工接管后继续
