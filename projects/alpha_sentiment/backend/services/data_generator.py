"""数据生成服务 - 聚合 DataFetcher 和 SentimentAnalyzer

可直接运行:
    python -m backend.services.data_generator --run     # 生成数据
    python -m backend.services.data_generator --delete  # 删除数据
"""
import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
import shutil
import tempfile

logger = logging.getLogger(__name__)


def _get_config():
    """延迟导入配置（支持直接运行）"""
    from ..config import MAX_HOT_STOCKS, DATA_DIR, MAX_RETRIES, RETRY_DELAY
    return MAX_HOT_STOCKS, DATA_DIR, MAX_RETRIES, RETRY_DELAY


def _get_base_config():
    """延迟导入配置（支持直接运行）"""
    from ..config import MAX_HOT_STOCKS, DATA_DIR
    return MAX_HOT_STOCKS, DATA_DIR


def _atomic_write_json(file_path: Path, data: dict) -> None:
    """原子性写入 JSON 文件（先写临时文件，再替换）

    使用 os.replace() 实现真正的原子替换：
    - Linux/macOS: rename() 是原子操作
    - Windows: os.replace() 也是原子操作（单次系统调用）
    """
    import os
    temp_file = file_path.with_suffix('.json.tmp')
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # os.replace() 是跨平台的原子替换操作
        os.replace(temp_file, file_path)
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink()
        raise e


class DataGenerator:
    """静态数据生成器"""

    def __init__(self):
        from .data_fetcher import DataFetcher
        from .sentiment import SentimentAnalyzer
        self.data_fetcher = DataFetcher()
        self.sentiment_analyzer = SentimentAnalyzer()
        # 获取重试配置
        _, _, self.max_retries, self.retry_delay = _get_config()

    async def _fetch_stock_async(
        self,
        stock: Any,
        index: int,
        total: int,
        raw_news: list[dict] | None = None,
        all_ratings: dict | None = None
    ) -> dict:
        """
        异步获取单只股票数据（带重试）

        优化点：
        1. 复用 hot_stocks 中已有的 price/change，避免重复调用 API
        2. 复用预获取的新闻和千股千评数据，避免重复调用全市场 API
        3. 只需并发获取各股票独立的 K线数据

        Args:
            stock: 股票对象（包含 code, name, price, change）
            index: 当前索引
            total: 总数
            raw_news: 预获取的全市场新闻原始数据
            all_ratings: 预获取的全市场千股千评数据

        Returns:
            包含 stock, stock_data, analysis 的字典，失败时 stock_data 为 None
        """
        from ..models.schemas import StockPrice

        code = stock.code
        name = stock.name
        logger.info(f"[{index}/{total}] 开始获取: {code} {name}")

        # 复用 hot_stocks 中已有的价格信息，避免重复调用 API
        price_info = StockPrice(
            code=code,
            name=name,
            price=stock.price,
            change=stock.change,
            volume=0,
            amount=0
        )

        for attempt in range(self.max_retries):
            try:
                # 使用优化后的异步方法（传入预获取的数据，只获取 K线）
                stock_data = await self.data_fetcher.get_stock_data_async(
                    symbol=code,
                    name=name,
                    price_info=price_info,
                    raw_news=raw_news,
                    all_ratings=all_ratings
                )

                # 情绪分析也用 to_thread（涉及网络请求）
                news_list = [n.model_dump() for n in stock_data.news]
                analysis = None
                if news_list:
                    analysis = await asyncio.to_thread(
                        self.sentiment_analyzer.analyze_news, name, news_list
                    )

                logger.info(f"[{index}/{total}] 完成: {code} - K线 {len(stock_data.kline)} 条, 新闻 {len(news_list)} 条")
                return {"stock": stock, "stock_data": stock_data, "analysis": analysis}

            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (attempt + 1)
                    logger.warning(f"[{index}/{total}] {code} 第 {attempt + 1} 次失败: {e}, {wait_time}秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"[{index}/{total}] {code} 重试 {self.max_retries} 次后失败: {e}")
                    return {"stock": stock, "stock_data": None, "analysis": None}

        return {"stock": stock, "stock_data": None, "analysis": None}

    async def _fetch_all_stocks_async(
        self,
        hot_stocks: list,
        raw_news: list[dict] | None = None,
        all_ratings: dict | None = None
    ) -> list[dict]:
        """并发获取所有股票数据

        Args:
            hot_stocks: 热门股票列表
            raw_news: 预获取的全市场新闻原始数据
            all_ratings: 预获取的全市场千股千评数据
        """
        tasks = [
            self._fetch_stock_async(stock, i, len(hot_stocks), raw_news, all_ratings)
            for i, stock in enumerate(hot_stocks, 1)
        ]
        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"任务 {i+1} 异常: {result}")
                processed.append({"stock": hot_stocks[i], "stock_data": None, "analysis": None})
            else:
                processed.append(result)

        return processed

    def generate(self) -> bool:
        """
        生成静态数据文件

        流程:
        1. 获取热门股票列表
        2. 并发获取每只股票的价格、K线、新闻、千股千评
        3. 对新闻进行 AI 情绪分析
        4. 保存为静态 JSON 文件（原子性写入）

        Returns:
            是否成功
        """
        MAX_HOT_STOCKS, DATA_DIR = _get_base_config()

        logger.info("=" * 50)
        logger.info("开始生成静态数据...")
        logger.info(f"输出目录: {DATA_DIR}")
        logger.info("=" * 50)

        # 确保输出目录存在
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # 1. 验证数据源
        logger.info("验证数据源连接...")
        if not self.data_fetcher.verify_data_source():
            logger.error("数据源验证失败，退出")
            return False

        # 2. 获取热门股票
        logger.info(f"获取热门股票 (前 {MAX_HOT_STOCKS} 只)...")
        hot_stocks = self.data_fetcher.get_hot_stocks(limit=MAX_HOT_STOCKS)
        if not hot_stocks:
            logger.error("获取热门股票失败")
            return False

        logger.info(f"获取到 {len(hot_stocks)} 只热门股票")

        # 3. 批量预获取全市场新闻和千股千评（各调用一次 API）
        logger.info("批量获取全市场新闻...")
        news_data = self.data_fetcher.fetch_all_news()
        raw_news = news_data.get("_raw", [])
        logger.info(f"获取到 {len(raw_news)} 条全市场新闻")

        logger.info("批量获取全市场千股千评...")
        all_ratings = self.data_fetcher.fetch_all_ratings()
        logger.info(f"获取到 {len(all_ratings)} 只股票的千股千评数据")

        # 4. 并发获取所有股票数据（只需获取各股票独立的 K线）
        logger.info("开始并发获取各股票 K线数据...")
        results = asyncio.run(self._fetch_all_stocks_async(hot_stocks, raw_news, all_ratings))

        # 5. 处理结果
        enriched_stocks = []
        stock_details = {}

        for result in results:
            stock = result["stock"]
            stock_data = result["stock_data"]
            analysis = result["analysis"]

            code = stock.code
            name = stock.name

            # 构建热门股票数据
            enriched_stock = stock.model_dump()

            if stock_data:
                news_list = [n.model_dump() for n in stock_data.news]
                rating = stock_data.rating

                if analysis:
                    enriched_stock["sentiment_score"] = analysis.get("score")
                    enriched_stock["tags"] = analysis.get("tags", [])
                else:
                    enriched_stock["sentiment_score"] = None
                    enriched_stock["tags"] = []

                # 添加千股千评数据
                if rating:
                    enriched_stock["rating_score"] = rating.score
                    enriched_stock["institution_ratio"] = rating.institution_ratio
                    enriched_stock["attention_index"] = rating.attention_index

                # 构建股票详情
                price_info = stock_data.price_info
                detail = {
                    "code": code,
                    "name": name,
                    "price": price_info.price if price_info else stock.price,
                    "change": price_info.change if price_info else stock.change,
                    "sentiment_score": analysis.get("score") if analysis else None,
                    "analysis": analysis.get("summary", "") if analysis else None,
                    "keywords": [
                        {"word": kw, "sentiment": "neutral"}
                        for kw in (analysis.get("keywords", []) if analysis else [])
                    ],
                    "news": [
                        {
                            "title": n.get("title", ""),
                            "content": n.get("content", ""),
                            "source": n.get("source", ""),
                            "publish_time": n.get("publish_time", ""),
                            "url": n.get("url", ""),
                        }
                        for n in news_list[:20]
                    ],
                    "kline": [k.model_dump() for k in stock_data.kline],
                    "tags": analysis.get("tags", []) if analysis else [],
                    "rating": rating.model_dump() if rating else None,
                }
                stock_details[code] = detail
            else:
                # 获取失败，只保留基础数据
                enriched_stock["sentiment_score"] = None
                enriched_stock["tags"] = []

            enriched_stocks.append(enriched_stock)

        # 6. 保存静态文件（原子性写入，确保数据一致性）
        timestamp = datetime.now().isoformat()
        success_count = len([s for s in enriched_stocks if s.get("sentiment_score") is not None])
        failed_count = len(enriched_stocks) - success_count

        # 热门股票列表（包含元数据）
        hot_stocks_data = {
            "updated_at": timestamp,
            "total_stocks": len(enriched_stocks),
            "success_count": success_count,
            "failed_count": failed_count,
            "stocks": enriched_stocks
        }
        hot_stocks_file = DATA_DIR / "hot_stocks.json"
        _atomic_write_json(hot_stocks_file, hot_stocks_data)
        logger.info(f"保存热门股票: {hot_stocks_file} (成功: {success_count}, 失败: {failed_count})")

        # 股票详情文件
        for code, detail in stock_details.items():
            detail_file = DATA_DIR / f"stock_{code}.json"
            _atomic_write_json(detail_file, {"updated_at": timestamp, "detail": detail})

        logger.info(f"保存 {len(stock_details)} 只股票详情")
        logger.info("=" * 50)
        logger.info(f"静态数据生成完成！共 {len(enriched_stocks)} 只股票")
        logger.info("=" * 50)

        return True

    @staticmethod
    def delete() -> bool:
        """删除所有生成的数据文件"""
        _, DATA_DIR = _get_base_config()

        if not DATA_DIR.exists():
            logger.info(f"数据目录不存在: {DATA_DIR}")
            return True

        deleted = 0
        for f in DATA_DIR.glob("*.json"):
            try:
                f.unlink()
                deleted += 1
                logger.info(f"已删除: {f.name}")
            except Exception as e:
                logger.error(f"删除失败 {f.name}: {e}")

        logger.info(f"共删除 {deleted} 个文件")
        return True


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="AlphaSenti Data Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m backend.services.data_generator --run     # Generate data
    python -m backend.services.data_generator --delete  # Delete all data
        """
    )
    parser.add_argument("--run", action="store_true", help="Generate static data")
    parser.add_argument("--delete", action="store_true", help="Delete all data files")

    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    if args.delete:
        success = DataGenerator.delete()
        sys.exit(0 if success else 1)
    elif args.run:
        generator = DataGenerator()
        success = generator.generate()
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
