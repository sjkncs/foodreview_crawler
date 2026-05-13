"""生成完整 Jupyter Notebook"""
import json
from pathlib import Path


def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source}


def code(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source,
    }


cells = [

# ══════════════════════════════════════════════════════════════
# 封面
# ══════════════════════════════════════════════════════════════
md("""# 🍜 外卖评论智能采集系统 · 完整使用指南

**版本**: v2.0 | **AI模型**: DeepSeek-V3 (文字) + qwen3-vl-plus (OCR)
**平台**: 美团外卖 / 饿了么 / 抖音外卖 / 大众点评 / Google Maps / KeeTa

---

## 📋 目录

| 章节 | 内容 |
|------|------|
| 第1章 | 环境配置 & API 切换 |
| 第2章 | 快速开始（3步完成爬取）|
| 第3章 | 各平台爬虫详解 |
| 第4章 | OCR 策略（qwen3-vl-plus 两步法）|
| 第5章 | AI 处理管线（翻译→情感→关键词→回复）|
| 第6章 | 积木式框架（BlockChain）|
| 第7章 | 数据导出（Excel/CSV/JSON）|
| 第8章 | 数据分析可视化 |
| 第9章 | 故障排查 & 诊断脚本 |
"""),

# ══════════════════════════════════════════════════════════════
# 第1章
# ══════════════════════════════════════════════════════════════
md("## 第 1 章：环境配置"),

code("""\
# 安装依赖（首次运行执行一次）
# !pip install nicegui playwright anthropic openai jieba openpyxl httpx python-dotenv
# !python -m playwright install chromium

import sys
sys.path.insert(0, r"C:\\Users\\Administrator\\Desktop\\foodreview_crawler")

import importlib
for pkg in ["nicegui", "playwright", "anthropic", "openai", "jieba", "openpyxl"]:
    try:
        importlib.import_module(pkg)
        print(f"  OK  {pkg}")
    except ImportError:
        print(f"  MISS {pkg} -- 请运行 pip install {pkg}")
"""),

md("### 1.1 API 端点切换（Claude Code Switch）"),

code("""\
import config

# 查看当前配置
info = config.get_active_api_info()
print("当前 API 配置:")
for k, v in info.items():
    print(f"  {k:12}: {v}")
"""),

code("""\
from config import switch_api_preset, API_PRESETS

print("可用预设:")
for key, preset in API_PRESETS.items():
    print(f"  [{key:10}] {preset['label']:20} {preset['base_url']}")

# 切换到 iflow（已内置 Key，开箱即用）
switch_api_preset("iflow")
print("\\n已切换到:", config.get_active_api_info()["label"])
"""),

md("### 1.2 验证 API 连通性"),

code("""\
import asyncio
from processors.ai_client import chat, OCR_MODEL

async def test():
    resp = await chat("你好，只回复：OK", max_tokens=10)
    print(f"文字模型 ({config.get('model')}): {resp}")
    print(f"OCR 专用模型: {OCR_MODEL}  (固定，不受全局配置影响)")

asyncio.run(test())
"""),

# ══════════════════════════════════════════════════════════════
# 第2章
# ══════════════════════════════════════════════════════════════
md("## 第 2 章：快速开始"),

md("""\
> **3 步完成一次完整爬取**：初始化 → 爬取 → AI处理 → 导出

```python
# Step 1: 初始化
from core.database import init_db
from crawlers import get_crawler
from processors import process_and_save, export_excel
from core.models import Platform

init_db()

# Step 2: 爬取
crawler = get_crawler(Platform.MEITUAN, headless=True, strategy="hybrid")
reviews = await crawler.crawl("商家ID", "商家名称", max_pages=5)

# Step 3: AI处理 + 导出
results = await process_and_save(reviews)
path = export_excel(results)
print(f"完成！导出到: {path}")
```
"""),

code("""\
# 验证项目结构
from core.database import init_db, count_reviews
from crawlers import _REGISTRY
from core.models import Platform

init_db()
print(f"数据库已初始化，当前共 {count_reviews()} 条评论")
print(f"\\n已注册平台 ({len(_REGISTRY)} 个):")
for p, cls in _REGISTRY.items():
    print(f"  {p.value:15} -> {cls.__name__}")
"""),

# ══════════════════════════════════════════════════════════════
# 第3章
# ══════════════════════════════════════════════════════════════
md("## 第 3 章：各平台爬虫详解"),

md("""\
### 爬取策略对比

| 策略 | 速度 | 稳定性 | 反爬能力 | 适用场景 |
|------|------|--------|----------|----------|
| `api_intercept` | ⚡ 最快 | ★★★ | ★ | API 未加密的平台 |
| `dom_parse` | 中等 | ★★★★ | ★★ | 稳定 DOM 结构 |
| `ocr_screenshot` | 最慢 | ★★★★★ | ★★★★★ | 强反爬/动态渲染 |
| **`hybrid` ✅** | 自适应 | ★★★★★ | ★★★★ | **推荐，自动降级** |

降级链：`api_intercept → dom_parse → ocr_screenshot → local_ocr`
"""),

code("""\
from crawlers.base import BaseCrawler

# 演示降级链
chain, s = [], "api_intercept"
while s:
    chain.append(s)
    s = BaseCrawler._next_fallback(s)
print("降级链:", " -> ".join(chain))

# 各平台策略说明
strategies = {
    "美团外卖":    "API拦截(XHR) + DOM解析备用",
    "饿了么":      "API拦截(XHR) + DOM解析备用",
    "抖音外卖":    "API拦截(XHR)",
    "大众点评":    "DOM解析（无稳定API，反爬较强）",
    "Google Maps": "DOM解析（滚动加载）+ 相对时间解析",
    "KeeTa":       "API拦截 + Cookie登录（手动首次登录）",
}
print("\\n各平台默认策略:")
for p, s in strategies.items():
    print(f"  {p:12}: {s}")
"""),

md("### 3.1 KeeTa 商户后台（特殊登录流程）"),

code("""\
from pathlib import Path
import json

cookie_file = Path("data/keeta_cookies.json")
if cookie_file.exists():
    cookies = json.loads(cookie_file.read_text(encoding="utf-8"))
    domains = set(c.get("domain", "") for c in cookies)
    print(f"已有 Cookie 文件: {len(cookies)} 条，域名: {domains}")
else:
    print("未找到 Cookie 文件")
    print("首次运行 KeetaCrawler 时会自动弹出浏览器，完成登录后自动保存")
    print()
    print("使用方法:")
    print("  from crawlers.keeta import KeetaCrawler")
    print("  crawler = KeetaCrawler(headless=False, days=30)")
    print("  reviews = await crawler.crawl('', '我的餐厅', max_pages=10)")
"""),

# ══════════════════════════════════════════════════════════════
# 第4章
# ══════════════════════════════════════════════════════════════
md("## 第 4 章：OCR 策略（qwen3-vl-plus 两步法）"),

md("""\
### OCR 两步法流程

```
Step 1 ─ 评论区定位
  全页截图 → qwen3-vl-plus
  识别「评论/评价/食评/Reviews」Tab 位置
  → 自动点击进入评论区（支持中/繁/英/日/韩）

Step 2 ─ 逐屏结构化识别
  滚动截图 → qwen3-vl-plus
  提取每条评论的完整字段：
    用户名 | 评分(数星星) | 评论内容 | 图片URL
    商家回复 | 子评分(口味/配送/包装) | 发布日期
  → 映射到 Review 数据模型

降级链：
  qwen3-vl-plus → PaddleOCR → Tesseract
```
"""),

code("""\
import asyncio, httpx
from processors.ai_client import OCR_MODEL, _is_openai_compat
import config

cfg = config.load()
base_url = cfg.get("anthropic_base_url", "")

print(f"OCR 专用模型 : {OCR_MODEL}")
print(f"API 端点     : {base_url}")
print(f"兼容模式     : {'OpenAI 兼容' if _is_openai_compat(base_url) else 'Anthropic 原生'}")

async def check_vlm():
    headers = {"Authorization": f"Bearer {cfg.get('anthropic_api_key', '')}"}
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{base_url}/models", headers=headers)
        if r.status_code == 200:
            models = [m["id"] for m in r.json().get("data", [])]
            ok = OCR_MODEL in models
            print(f"\\n{OCR_MODEL} 在 iflow 可用: {'YES' if ok else 'NO'}")
            vl = [m for m in models if "vl" in m.lower()]
            print(f"所有 VL 模型: {vl}")

asyncio.run(check_vlm())
"""),

# ══════════════════════════════════════════════════════════════
# 第5章
# ══════════════════════════════════════════════════════════════
md("## 第 5 章：AI 处理管线"),

md("""\
### 管线流程

```
Review (原始)
  │
  ├─ 1. translator   非中文 → 中文翻译（DeepSeek-V3）
  ├─ 2. sentiment    正面/负面/中性 + 置信度分值
  ├─ 3. keywords     Top-8 关键标签提取
  └─ 4. reply_gen    商家回复建议（可选，auto_reply=True 时启用）
         │
         ▼
      SQLite 数据库（asyncio.to_thread 非阻塞写入）
```

**并发控制**：Semaphore(3)，每条 3 次 AI 调用，实际并发 ≤9，不触发限速
"""),

code("""\
import asyncio
from datetime import datetime
from core.models import Review, Platform, ReviewType
from processors.pipeline import process_review

# 构造英文测试评论（会被自动翻译）
test_review = Review(
    id=None,
    platform=Platform.GOOGLE_MAPS,
    shop_name="HEYTEA MOKO",
    shop_id="test_001",
    reviewer_name="Yummy Bunny Bites",
    content="Great matcha coconut milk tea! The taro layer is amazing. Delivery was fast.",
    rating=5.0,
    published_at=datetime.now(),
    crawled_at=datetime.now(),
    review_type=ReviewType.REVIEW,
)

async def demo():
    print("原始评论:", test_review.content)
    print("语言:     英文（将被自动翻译）\\n")

    result = await process_review(test_review)

    print("=== AI 处理结果 ===")
    print(f"  翻译内容: {result.translated_content}")
    print(f"  情感标签: {result.sentiment.value if result.sentiment else 'N/A'}")
    if result.sentiment_score is not None:
        print(f"  情感分值: {result.sentiment_score:.2f}  (-1=最负面, +1=最正面)")
    print(f"  关键词:   {result.keywords}")

asyncio.run(demo())
"""),

# ══════════════════════════════════════════════════════════════
# 第6章
# ══════════════════════════════════════════════════════════════
md("## 第 6 章：积木式框架（BlockChain）"),

md("""\
### 设计理念

参考 MIT Scratch 积木组合思想：每个 Block 是独立的原子操作，通过 `BlockChain` 串联拼接。

```
积木块类型：
  🔵 导航块  OpenPageBlock / ShopSearchBlock / ClickTabBlock
  🟡 筛选块  FilterNewestBlock
  🟠 展开块  ExpandMoreBlock（四级策略：点击→JS解锁→调函数→VLM定位）
  🔴 决策块  DeciderBlock（VLM截图判断：正常/验证码/登录/限流/错误）
  ⏸  人工门  HumanGateBlock（遇验证码→暂停→等待人工→继续）
  🟢 提取块  ExtractReviewsBlock（对接现有爬虫）
  🤖 AI块    AIProcessBlock（翻译+情感+关键词）
  📤 导出块  ExportBlock（Excel/CSV/JSON）
```

**人机协同流程**：
```
自动运行 → 遇验证码/登录墙
  → DeciderBlock 返回 PAUSED
  → BlockChain 自动暂停
  → CLI: 打印提示，等待 Enter
  → GUI: 弹出提示框，等待点击"已完成"
  → 继续后续积木块
```
"""),

code("""\
from blocks.base_block import BlockChain, BlockStatus, BlockResult
from blocks.navigator import ShopSearchBlock, ClickTabBlock, FilterNewestBlock, ExpandMoreBlock
from blocks.decider import DeciderBlock, HumanGateBlock
from blocks.extractor import ExtractReviewsBlock, AIProcessBlock, ExportBlock
from core.models import Platform, ReviewType

print("积木块加载成功")
print()

# 构建一个完整的爬取流程
chain = BlockChain([
    DeciderBlock(),                      # 检测页面状态（验证码/登录/限流）
    ClickTabBlock(),                     # 点击评论Tab
    FilterNewestBlock(),                 # 按最新排序
    ExpandMoreBlock(),                   # 展开所有"更多"
    ExtractReviewsBlock(
        platform=Platform.MEITUAN,
        shop_id="123456",
        shop_name="示例餐厅",
        max_pages=5,
    ),
    AIProcessBlock(),                    # AI翻译+情感+关键词
    ExportBlock(fmt="excel"),            # 导出Excel
])

print(f"流程链构建完成，共 {len(chain._blocks)} 个积木块:")
for i, block in enumerate(chain._blocks, 1):
    print(f"  {i}. {block.name}")
"""),

md("### 6.1 ExpandMoreBlock 四级展开策略"),

code("""\
# 演示 ExpandMoreBlock 的四级策略逻辑
print("ExpandMoreBlock 展开策略（按优先级）:")
print()
print("策略1: 直接点击展开按钮")
print("  - 匹配文字: 展开更多/更多评论/查看更多/Load More/Show More")
print("  - 使用 Playwright locator 点击")
print()
print("策略2: JS 解除 disabled 属性")
print("  - 找到 button[disabled] 或 button.disabled")
print("  - 过滤含 '更多/more/load/expand' 文字的按钮")
print("  - removeAttribute('disabled') 后触发 click()")
print()
print("策略3: 调用页面内部函数")
print("  - 尝试 window.loadMore / fetchMore / loadNextPage / showMore")
print()
print("策略4: VLM 定位点击（终极兜底）")
print("  - 截图 → qwen3-vl-plus 识别按钮坐标")
print("  - page.mouse.click(x, y)")
"""),

# ══════════════════════════════════════════════════════════════
# 第7章
# ══════════════════════════════════════════════════════════════
md("## 第 7 章：数据导出"),

code("""\
from processors.reporter import HEADERS

print(f"导出表头（共 {len(HEADERS)} 列）:")
for i, h in enumerate(HEADERS, 1):
    print(f"  {i:2}. {h}")
"""),

code("""\
from core.database import get_reviews, init_db
from processors.reporter import export_csv, export_excel, export_json

init_db()
reviews = get_reviews(limit=1000)
print(f"数据库中共 {len(reviews)} 条评论")

if reviews:
    path_excel = export_excel(reviews)
    print(f"  Excel (彩色情感标注): {path_excel}")

    path_csv = export_csv(reviews)
    print(f"  CSV  (UTF-8 BOM):     {path_csv}")

    path_json = export_json(reviews)
    print(f"  JSON:                 {path_json}")
else:
    print("  数据库为空，请先运行爬取任务")
    print("  可以先运行第2章的快速开始示例")
"""),

# ══════════════════════════════════════════════════════════════
# 第8章
# ══════════════════════════════════════════════════════════════
md("## 第 8 章：数据分析"),

code("""\
import json
from collections import Counter
from core.database import get_reviews, get_sentiment_stats, get_top_keywords, init_db

init_db()
reviews = get_reviews(limit=5000)
stats   = get_sentiment_stats()
kws     = get_top_keywords(20)

print(f"总评论数: {len(reviews)}")

if stats:
    print("\\n各平台情感分布:")
    for s in stats:
        total = max(s["total"], 1)
        pos_bar = "█" * int(20 * s["positive"] / total)
        neg_bar = "█" * int(20 * s["negative"] / total)
        print(f"  {s['platform']:12} 正:{pos_bar:<20} 负:{neg_bar:<20} 均分:{s.get('avg_rating',0):.1f}")

if kws:
    print("\\n高频关键词 Top 10:")
    for word, cnt in kws[:10]:
        bar = "█" * min(cnt, 30)
        print(f"  {word:8} {bar} ({cnt})")
"""),

code("""\
# 评分分布
if reviews:
    rating_dist = Counter(int(r.rating) for r in reviews if r.rating > 0)
    print("评分分布:")
    for star in range(1, 6):
        cnt = rating_dist.get(star, 0)
        pct = cnt / len(reviews) * 100 if reviews else 0
        bar = "★" * int(pct / 2)
        print(f"  {star}星: {bar:<25} {cnt:4}条 ({pct:.1f}%)")

    # 子评分分析
    sub_scores = {"口味": [], "配送": [], "包装": [], "服务": []}
    for r in reviews:
        if r.child_rating:
            try:
                sub = json.loads(r.child_rating)
                for key in sub_scores:
                    for k, v in sub.items():
                        if key in k:
                            try:
                                sub_scores[key].append(float(v))
                            except Exception:
                                pass
            except Exception:
                pass

    print("\\n子评分平均值:")
    for dim, scores in sub_scores.items():
        if scores:
            avg = sum(scores) / len(scores)
            bar = "★" * int(avg)
            print(f"  {dim}: {bar} {avg:.2f} ({len(scores)}条)")
        else:
            print(f"  {dim}: 无数据")
"""),

# ══════════════════════════════════════════════════════════════
# 第9章
# ══════════════════════════════════════════════════════════════
md("## 第 9 章：故障排查"),

md("""\
### 常见问题速查

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `playwright not found` | 未安装浏览器 | `python -m playwright install chromium` |
| `API Key 未配置` | config.json 无 Key | 调用 `switch_api_preset("iflow")` |
| `404 /v1/v1/messages` | base_url 重复 /v1 | iflow 端点已修复，使用 `/v1` 结尾 |
| 评论为空 | 商家ID错误/反爬 | 检查 shop_id；切换 `strategy="ocr_screenshot"` |
| Cookie 失效 | KeeTa 登录过期 | 删除 `data/keeta_cookies.json`，重新登录 |
| Excel 乱码 | 编码问题 | 已用 UTF-8 BOM，直接双击打开即可 |
| 进度条回跳 | 并发乱序 | 已修复（原子计数器 + asyncio.to_thread）|
"""),

code("""\
import asyncio

async def full_diagnosis():
    print("=" * 50)
    print("项目全面诊断")
    print("=" * 50)

    checks = []

    # 1. 数据库
    try:
        from core.database import init_db, count_reviews
        init_db()
        total = count_reviews()
        checks.append(("数据库", True, f"{total} 条评论"))
    except Exception as e:
        checks.append(("数据库", False, str(e)))

    # 2. 爬虫工厂
    try:
        from crawlers import _REGISTRY
        checks.append(("爬虫工厂", True, f"{len(_REGISTRY)} 个平台"))
    except Exception as e:
        checks.append(("爬虫工厂", False, str(e)))

    # 3. AI API
    try:
        from processors.ai_client import chat
        resp = await chat("ping", max_tokens=5)
        checks.append(("AI API", True, f"响应: {repr(resp[:15])}"))
    except Exception as e:
        checks.append(("AI API", False, str(e)[:60]))

    # 4. 积木框架
    try:
        from blocks.base_block import BlockChain
        from blocks.navigator import ShopSearchBlock
        checks.append(("积木框架", True, "BlockChain + 5个Block"))
    except Exception as e:
        checks.append(("积木框架", False, str(e)))

    # 5. 导出模块
    try:
        from processors.reporter import HEADERS
        checks.append(("导出模块", True, f"{len(HEADERS)} 列"))
    except Exception as e:
        checks.append(("导出模块", False, str(e)))

    print()
    for name, ok, msg in checks:
        status = "OK " if ok else "ERR"
        print(f"  [{status}] {name:12}: {msg}")

    print()
    all_ok = all(ok for _, ok, _ in checks)
    print("=" * 50)
    print("诊断结果:", "全部正常" if all_ok else "存在问题，请查看上方错误信息")

asyncio.run(full_diagnosis())
"""),

code("""\
# 语法检查所有 Python 文件
import sys, pathlib, py_compile

project_root = pathlib.Path(r"C:\\Users\\Administrator\\Desktop\\foodreview_crawler")
errors = []
for f in sorted(project_root.rglob("*.py")):
    if "__pycache__" in str(f):
        continue
    try:
        py_compile.compile(str(f), doraise=True)
    except py_compile.PyCompileError as e:
        errors.append(f"{f.name}: {e}")

if errors:
    print("语法错误:")
    for e in errors:
        print(" ", e)
else:
    n = len(list(project_root.rglob("*.py")))
    print(f"全部 {n} 个 Python 文件语法正确")
"""),

]  # end cells

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.11.0"},
    },
    "cells": cells,
}

out = Path(r"C:\Users\Administrator\Desktop\foodreview_crawler\外卖评论采集系统_完整指南.ipynb")
out.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Notebook 已生成: {out}")
print(f"共 {len(cells)} 个 cell")
