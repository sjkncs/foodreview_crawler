"""
积木块基类 - 定义所有 Block 的公共接口
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


class BlockStatus(str, Enum):
    SUCCESS    = "success"
    SKIPPED    = "skipped"      # 平台搜索不到，跳过
    PAUSED     = "paused"       # 等待人工介入
    FAILED     = "failed"
    RETRYING   = "retrying"


@dataclass
class BlockResult:
    """积木块执行结果，可链式传递给下一个 Block"""
    status:   BlockStatus
    data:     Any = None          # 输出数据
    message:  str = ""
    metadata: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status in (BlockStatus.SUCCESS, BlockStatus.SKIPPED)

    @classmethod
    def success(cls, data=None, message="", **meta) -> "BlockResult":
        return cls(BlockStatus.SUCCESS, data, message, meta)

    @classmethod
    def skip(cls, reason="") -> "BlockResult":
        return cls(BlockStatus.SKIPPED, None, reason)

    @classmethod
    def pause(cls, reason="", **meta) -> "BlockResult":
        return cls(BlockStatus.PAUSED, None, reason, meta)

    @classmethod
    def fail(cls, reason="", **meta) -> "BlockResult":
        return cls(BlockStatus.FAILED, None, reason, meta)


class BaseBlock(ABC):
    """
    所有积木块的抽象基类。

    子类只需实现 execute()，框架自动处理：
      - 重试（max_retries 次）
      - 超时保护
      - 异常降级
      - 执行日志
    """
    name:        str = "BaseBlock"
    max_retries: int = 3
    timeout_s:   float = 30.0

    def __init__(self, **kwargs):
        self._kwargs = kwargs

    async def run(self, ctx: dict) -> BlockResult:
        """
        外部调用入口，带重试和超时。
        ctx: 上下文字典，Block 间传递共享状态（page、shop_name 等）
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    self.execute(ctx),
                    timeout=self.timeout_s,
                )
                if result.ok:
                    logger.info("[%s] ✅ %s", self.name, result.message or "成功")
                    return result
                if result.status == BlockStatus.PAUSED:
                    logger.info("[%s] ⏸ 等待人工介入: %s", self.name, result.message)
                    return result
                # FAILED：决定是否重试
                if attempt < self.max_retries:
                    wait = 2 ** attempt
                    logger.warning("[%s] ⚠ 第%d次失败，%ds后重试: %s",
                                   self.name, attempt, wait, result.message)
                    await asyncio.sleep(wait)
                else:
                    logger.error("[%s] ❌ 全部重试失败: %s", self.name, result.message)
                    return result
            except asyncio.TimeoutError:
                logger.warning("[%s] ⏰ 超时(%ds)，第%d次", self.name, int(self.timeout_s), attempt)
                if attempt == self.max_retries:
                    return BlockResult.fail(f"超时({self.timeout_s}s)")
            except Exception as exc:
                logger.error("[%s] 异常: %s", self.name, exc, exc_info=True)
                if attempt == self.max_retries:
                    return BlockResult.fail(str(exc))
                await asyncio.sleep(2 ** attempt)

        return BlockResult.fail("超过最大重试次数")

    @abstractmethod
    async def execute(self, ctx: dict) -> BlockResult:
        """子类实现具体逻辑"""
        ...


class BlockChain:
    """
    积木链：将多个 Block 串联，前一个的输出作为后一个的输入。

    使用示例：
        chain = BlockChain([
            ShopSearchBlock(shop_name="喜茶"),
            ClickReviewTabBlock(),
            FilterNewestBlock(),
            ExtractReviewsBlock(max_pages=5),
            AIProcessBlock(),
            ExportBlock(format="excel"),
        ])
        result = await chain.run()
    """
    def __init__(self, blocks: list[BaseBlock]):
        self._blocks = blocks

    async def run(self, initial_ctx: Optional[dict] = None) -> list[BlockResult]:
        ctx = initial_ctx or {}
        results: list[BlockResult] = []

        for block in self._blocks:
            result = await block.run(ctx)
            results.append(result)

            # SKIPPED：跳过后续 Block（平台搜索不到）
            if result.status == BlockStatus.SKIPPED:
                logger.info("[Chain] 跳过后续 Block（%s）", result.message)
                break

            # PAUSED：等待人工介入后继续
            if result.status == BlockStatus.PAUSED:
                logger.info("[Chain] ⏸ 链暂停，等待人工操作...")
                await self._wait_for_human(ctx, result)
                # 人工操作完成后重试当前 Block
                retry = await block.run(ctx)
                results.append(retry)
                if not retry.ok:
                    break

            # FAILED：中止整条链
            if result.status == BlockStatus.FAILED:
                logger.error("[Chain] ❌ 链中止于 %s", block.name)
                break

            # 将输出数据写入 ctx，供后续 Block 使用
            if result.data is not None:
                ctx[f"{block.name}_output"] = result.data
            ctx.update(result.metadata)

        return results

    async def _wait_for_human(self, ctx: dict, pause_result: BlockResult) -> None:
        """等待人工介入信号（轮询 ctx['human_done'] 标志）"""
        ctx["human_done"] = False
        # 发送桌面通知（可选）
        try:
            import subprocess
            subprocess.Popen([
                "msg", "Administrator",
                f"[爬虫系统] 需要人工操作: {pause_result.message}"
            ], shell=True)
        except Exception:
            pass

        logger.info("[Chain] 等待人工操作，完成后请设置 ctx['human_done'] = True")
        # 最多等待 5 分钟
        for _ in range(300):
            if ctx.get("human_done"):
                logger.info("[Chain] ✅ 人工操作完成，继续执行")
                return
            await asyncio.sleep(1)
        logger.warning("[Chain] ⏰ 人工等待超时（5分钟），强制继续")
