"""
Hungry Panda 商家后台评论爬虫。

该文件只保留平台差异：路由、文案、选择器、API 字段映射。
登录、分店进入、评论页导航、API 拦截、DOM 表格解析与翻页均复用
RecipeMerchantCrawler，便于后续 Keeta / Grab / Foodpanda 等后台继续接入。
"""
from __future__ import annotations

from typing import Optional

from core.models import OcrStrategy, Platform
from .merchant_backend import MerchantReviewRecipe, RecipeMerchantCrawler

APPRAISE_PATH = "/order/appraise"
LOGIN_TIMEOUT = 180_000

_LOGGED_IN_TEXTS = (
    "分店管理", "进入分店", "数据中心", "看板", "商品中心", "订单管理", "营业信息",
    "Branch management", "Enter branch", "Data Center", "Dashboard", "Product Center",
    "Order Management", "Orders", "Settings", "Menu", "Account Settings", "Log out",
    "매장", "주문", "메뉴", "설정", "로그아웃",
    "Succursale", "Commandes", "Paramètres", "Menu", "Se déconnecter",
)

_ORDER_REVIEW_TEXTS = (
    "Ratings and reviews", "订单评价", "评价", "评价内容", "Review contents",
    "Review", "Reviews", "Order review", "Order reviews",
    "주문 평가", "리뷰", "리뷰내용",
    "Examen de la commande", "Avis", "Contenu",
)

_ALL_REVIEW_TEXTS = (
    "All reviews", "全部评价", "全部評價", "所有评价", "所有評價",
    "전체 리뷰", "Tous les avis",
)

_NOT_REPLIED_TEXTS = (
    "Not replied", "未回复", "未回覆", "미답장", "Pas répondu",
)

_ENTER_BRANCH_TEXTS = (
    "进入分店", "進入分店", "进入门店", "进入店铺",
    "Enter the Branch Page",
    "Enter branch", "Enter Branch", "Enter store", "Enter Store", "Enter shop", "Enter Shop",
    "매장 입장", "지점 입장",
    "Entrer", "Entrer dans la succursale",
)

_REVIEW_TEXTS = _ORDER_REVIEW_TEXTS + _ALL_REVIEW_TEXTS + _NOT_REPLIED_TEXTS

_SUB_RATING_LABELS = {
    "Dish package": "包装",
    "Dish taste": "口味",
    "Overall review": "综合评价",
    "菜品包装": "包装",
    "菜品口味": "口味",
    "综合评价": "综合评价",
    "요리 포장": "包装",
    "요리 입맛": "口味",
    "종합평점": "综合评价",
    "L'emballage": "包装",
    "Goût de plat": "口味",
    "Evoluation": "综合评价",
    "Evaluation": "综合评价",
}

HUNGRY_PANDA_RECIPE = MerchantReviewRecipe(
    name="Hungry Panda",
    platform=Platform.HUNGRY_PANDA,
    cookie_dir_name="hungry_panda_cookies",
    review_path=APPRAISE_PATH,
    login_path="/master/login",
    login_check_path="/master/dashBoard/dataCenter",
    management_path="/master/branchStore/storeList",
    persistent_profile_dir_name="hungry_panda_usa",
    browser_channel="msedge",
    login_timeout_ms=LOGIN_TIMEOUT,
    login_username_selectors=(
        'input[placeholder="Enter account number"]',
        "input[placeholder*='account number']",
        "input[type='tel']",
    ),
    login_password_selectors=(
        'input[placeholder="Enter password"]',
        "input[type='password']",
    ),
    login_submit_selectors=(
        "button:has-text('Login')",
        "button[type='submit']",
    ),
    credential_env_prefix="HUNGRY_PANDA",
    credential_host_env_prefixes={
        "merchant-kr.hungrypanda.co": "HUNGRY_PANDA_KR",
    },
    api_host_keyword="hungrypanda",
    api_required_paths=("/api/merchant",),
    api_patterns=("appraise", "review", "comment", "rating", "reply", "feedback"),
    logged_in_url_fragments=(
        "/order/appraise",
        "/dashboard",
        "/datacenter",
        "/order/",
        "/master/",
    ),
    logged_in_texts=_LOGGED_IN_TEXTS,
    review_texts=_ORDER_REVIEW_TEXTS,
    all_review_texts=_ALL_REVIEW_TEXTS,
    not_replied_texts=_NOT_REPLIED_TEXTS,
    enter_store_texts=_ENTER_BRANCH_TEXTS,
    row_selectors=(
        "tr.ant-table-row",
        ".ant-table-row",
        "[class*='table-row']",
        "tr",
    ),
    review_card_selectors=(
        "tr.ant-table-row",
        ".ant-table-row",
        "table tbody tr",
        "tbody tr",
        "[class*='appraise-item']",
        "[class*='review-item']",
        "[class*='comment-item']",
    ),
    content_selectors=(
        "[class*='appraise-content']",
        "[class*='review-content']",
        "[class*='comment-content']",
        "[class*='content']",
        "td:nth-child(1)",
        "p",
    ),
    date_selectors=(
        "[class*='appraise-time']",
        "[class*='review-time']",
        "[class*='date']",
        "td:nth-child(3)",
        "time",
    ),
    next_selectors=(
        ".ant-pagination-next:not(.ant-pagination-disabled)",
        "li.ant-pagination-next:not(.ant-pagination-disabled) button",
        "button:has-text('Next')",
        "button:has-text('下一页')",
        "a:has-text('Next')",
        "[class*='next']:not([disabled])",
    ),
    table_content_col=0,
    table_order_col=1,
    table_date_col=2,
    sub_rating_labels=_SUB_RATING_LABELS,
    list_keys=(
        "list", "records", "items", "rows", "dataList", "pageData",
        "reviews", "appraises", "comments",
    ),
    api_content_fields=(
        "content", "reviewContent", "commentContent", "comment", "review",
        "appraiseContent", "evaluateContent", "feedback", "text",
    ),
    api_reviewer_fields=(
        "nickname", "reviewerName", "userName", "username", "customerName",
    ),
    api_rating_fields=(
        "rating", "score", "overallScore", "star", "stars", "reviewScore",
        "evaluateScore", "appraiseScore",
    ),
    api_date_fields=(
        "reviewTime", "appraiseTime", "evaluateTime", "commentTime",
        "createdAt", "created_at", "createTime", "time",
    ),
    api_reply_fields=(
        "reply", "merchantReply", "replyInfo", "replyContent",
        "merchantReplyContent", "reply_content",
    ),
    api_image_fields=("images", "pics", "photos", "imageList", "pictureList"),
    api_sub_rating_fields=(
        ("dishPackageScore", "包装"),
        ("packageScore", "包装"),
        ("packingScore", "包装"),
        ("dishTasteScore", "口味"),
        ("tasteScore", "口味"),
        ("overallScore", "综合评价"),
    ),
)


class HungryPandaCrawler(RecipeMerchantCrawler):
    platform = Platform.HUNGRY_PANDA
    recipe = HUNGRY_PANDA_RECIPE

    def __init__(
        self,
        headless: bool = True,
        proxy: Optional[str] = None,
        strategy: str = OcrStrategy.HYBRID.value,
        shop_name: str = "Hungry Panda 商户",
        shop_hint: Optional[str] = None,
        login_url: Optional[str] = None,
        login_username: Optional[str] = None,
        login_password: Optional[str] = None,
    ):
        super().__init__(
            headless=headless,
            proxy=proxy,
            strategy=strategy,
            shop_name=shop_name,
            shop_hint=shop_hint,
            login_url=login_url,
            login_username=login_username,
            login_password=login_password,
        )


__all__ = [
    "APPRAISE_PATH",
    "HUNGRY_PANDA_RECIPE",
    "HungryPandaCrawler",
]
