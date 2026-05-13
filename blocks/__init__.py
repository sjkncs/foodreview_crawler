"""
积木式自动化框架 - Block 基础层
"""
from .base_block import BaseBlock, BlockResult, BlockStatus, BlockChain
from .navigator import (
    OpenPageBlock, ShopSearchBlock, ClickTabBlock,
    FilterNewestBlock, ExpandMoreBlock,
)
from .extractor import ExtractReviewsBlock, AIProcessBlock, ExportBlock
from .decider import DeciderBlock, HumanGateBlock

__all__ = [
    "BaseBlock", "BlockResult", "BlockStatus", "BlockChain",
    "OpenPageBlock", "ShopSearchBlock", "ClickTabBlock",
    "FilterNewestBlock", "ExpandMoreBlock",
    "ExtractReviewsBlock", "AIProcessBlock", "ExportBlock",
    "DeciderBlock", "HumanGateBlock",
]
