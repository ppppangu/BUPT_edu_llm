"""数据获取服务 - 基于 AkShare 获取 A 股数据"""
import akshare as ak
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Callable, TypeVar
from functools import wraps

from ..models.schemas import (
    HotStock, StockPrice, StockInfo, KlineData, NewsData, StockRating, StockAllData
)
from ..config import MAX_RETRIES, RETRY_DELAY

logger = logging.getLogger(__name__)

# 样例股票代码（平安银行）
SAMPLE_STOCK_CODE = "000001"

T = TypeVar('T')


def with_retry(max_retries: int = MAX_RETRIES, delay: float = RETRY_DELAY):
    """重试装饰器，用于处理网络请求失败"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (attempt + 1)
                        logger.warning(f"{func.__name__} 第 {attempt + 1} 次失败: {e}, {wait_time}秒后重试...")
                        time.sleep(wait_time)
            logger.error(f"{func.__name__} 重试 {max_retries} 次后仍失败: {last_error}")
            raise last_error
        return wrapper
    return decorator


class DataFetcher:
    """股票数据获取器（AkShare + 代理）"""

    def _clean_symbol(self, symbol: str) -> str:
        """清理股票代码，去掉 SZ/SH 前缀"""
        symbol = str(symbol).upper()
        for prefix in ['SZ', 'SH', 'BJ']:
            if symbol.startswith(prefix):
                symbol = symbol[2:]
        return symbol.zfill(6)

    def check_network(self) -> bool:
        """检查连接（带重试）"""
        for attempt in range(MAX_RETRIES):
            try:
                df = ak.stock_hot_rank_em()
                if df is not None and not df.empty:
                    logger.info("AkShare 连接正常")
                    return True
                return False
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (attempt + 1)
                    logger.warning(f"连接测试第 {attempt + 1} 次失败: {e}, {wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"连接测试失败: {e}")
                    return False
        return False

    def get_hot_stocks(self, limit: int = 20) -> list[HotStock]:
        """获取热门股票（AkShare，带重试）"""
        for attempt in range(MAX_RETRIES):
            try:
                df = ak.stock_hot_rank_em()
                if df is None or df.empty:
                    if attempt < MAX_RETRIES - 1:
                        wait_time = RETRY_DELAY * (attempt + 1)
                        logger.warning(f"获取热门股票返回空，{wait_time}秒后重试...")
                        time.sleep(wait_time)
                        continue
                    return []

                stocks = []
                for idx, row in df.head(limit).iterrows():
                    code = str(row.get("股票代码", row.get("代码", "")))
                    name = str(row.get("股票简称", row.get("股票名称", row.get("名称", ""))))
                    price = float(row.get("最新价", row.get("现价", 0)) or 0)
                    change = float(row.get("涨跌幅", 0) or 0)

                    if code:
                        stocks.append(HotStock(
                            code=code,
                            name=name,
                            price=price,
                            change=change,
                            heat=len(stocks) + 1
                        ))

                logger.info(f"获取热门股票成功，共 {len(stocks)} 只")
                return stocks
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (attempt + 1)
                    logger.warning(f"获取热门股票第 {attempt + 1} 次失败: {e}, {wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"获取热门股票失败: {e}")
                    return []
        return []

    def get_stock_price(self, symbol: str) -> Optional[StockPrice]:
        """获取股票价格（优先从热门榜获取，备用新浪数据源）"""
        code = self._clean_symbol(symbol)

        # 方法1: 尝试从热门股票榜获取（stock_hot_rank_em 已包含价格）
        try:
            df = ak.stock_hot_rank_em()
            if df is not None and not df.empty:
                stock = df[df["代码"].str.endswith(code)]
                if not stock.empty:
                    row = stock.iloc[0]
                    return StockPrice(
                        code=code,
                        name=str(row.get("股票名称", "")),
                        price=float(row.get("最新价", 0) or 0),
                        change=float(row.get("涨跌幅", 0) or 0),
                        volume=0,
                        amount=0
                    )
        except Exception as e:
            logger.debug(f"从热门榜获取价格失败: {e}")

        # 方法2: 备用新浪数据源
        for attempt in range(MAX_RETRIES):
            try:
                df = ak.stock_zh_a_spot()
                if df is None or df.empty:
                    return None

                stock = df[df["代码"].str.endswith(code)]
                if stock.empty:
                    return None

                row = stock.iloc[0]
                return StockPrice(
                    code=code,
                    name=str(row.get("名称", "")),
                    price=float(row.get("最新价", 0) or 0),
                    change=float(row.get("涨跌幅", 0) or 0),
                    volume=int(row.get("成交量", 0) or 0),
                    amount=float(row.get("成交额", 0) or 0)
                )
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (attempt + 1)
                    logger.warning(f"获取价格第 {attempt + 1} 次失败: {e}, {wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"获取价格失败: {e}")
                    return None
        return None

    def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """获取股票信息（AkShare）"""
        try:
            code = self._clean_symbol(symbol)
            df = ak.stock_individual_info_em(symbol=code)
            if df is None or df.empty:
                return None

            info = {}
            for _, row in df.iterrows():
                info[row["item"]] = row["value"]

            return StockInfo(
                code=code,
                name=info.get("股票简称", ""),
                industry=info.get("行业", ""),
                market=info.get("上市时间", "")[:4] if info.get("上市时间") else "",
                list_date=info.get("上市时间", ""),
                area=""
            )
        except Exception as e:
            logger.error(f"获取信息失败: {e}")
            return None

    def get_stock_kline(self, symbol: str, days: int = 30) -> list[KlineData]:
        """获取K线数据（AkShare 163数据源，带重试）"""
        code = self._clean_symbol(symbol)
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days + 10)).strftime('%Y%m%d')

        # 构造 163 数据源需要的 symbol 格式: sz000001 或 sh600000
        if code.startswith('6'):
            full_symbol = f"sh{code}"
        else:
            full_symbol = f"sz{code}"

        for attempt in range(MAX_RETRIES):
            try:
                df = ak.stock_zh_a_daily(
                    symbol=full_symbol,
                    start_date=start_date,
                    end_date=end_date,
                    adjust="hfq"
                )

                if df is None or df.empty:
                    logger.warning(f"未获取到 {code} 的K线数据")
                    return []

                df = df.tail(days)
                klines = []
                for _, row in df.iterrows():
                    date = row.get('date', '')
                    if hasattr(date, 'strftime'):
                        date_str = date.strftime('%Y-%m-%d')
                    else:
                        date_str = str(date)[:10]

                    klines.append(KlineData(
                        date=date_str,
                        open=float(row.get('open', 0) or 0),
                        high=float(row.get('high', 0) or 0),
                        low=float(row.get('low', 0) or 0),
                        close=float(row.get('close', 0) or 0),
                        volume=int(row.get('volume', 0) or 0),
                        amount=float(row.get('amount', 0) or 0)
                    ))

                logger.info(f"获取股票 {symbol} K线成功，共 {len(klines)} 条")
                return klines

            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (attempt + 1)
                    logger.warning(f"获取K线第 {attempt + 1} 次失败: {e}, {wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"获取K线失败: {e}")
                    return []
        return []

    def get_stock_news(self, stock_name: str, limit: int = 10) -> list[NewsData]:
        """获取股票相关新闻（从财联社全市场新闻中过滤）"""
        try:
            df = ak.stock_news_main_cx()
            if df is None or df.empty:
                logger.info("无法获取财联社新闻")
                return []

            # 按股票名称过滤相关新闻
            news_list = []
            for _, row in df.iterrows():
                tag = str(row.get("tag", ""))
                summary = str(row.get("summary", ""))

                # 检查标题或摘要是否包含股票名
                if stock_name in tag or stock_name in summary:
                    news_list.append(NewsData(
                        title=tag,
                        content=summary,
                        source="财联社",
                        publish_time=str(row.get("pub_time", "")),
                        url=str(row.get("url", ""))
                    ))
                    if len(news_list) >= limit:
                        break

            logger.info(f"获取股票 {stock_name} 相关新闻 {len(news_list)} 条")
            return news_list

        except Exception as e:
            logger.warning(f"获取新闻失败: {e}")
            return []

    def get_stock_rating(self, symbol: str) -> Optional[StockRating]:
        """获取千股千评数据（综合得分、机构参与度等）"""
        code = self._clean_symbol(symbol)

        try:
            df = ak.stock_comment_em()
            if df is None or df.empty:
                return None

            stock = df[df["代码"] == code]
            if stock.empty:
                return None

            row = stock.iloc[0]
            rating = StockRating(
                score=float(row.get("综合得分", 0) or 0),
                institution_ratio=float(row.get("机构参与度", 0) or 0),
                attention_index=float(row.get("关注指数", 0) or 0),
                rank=int(row.get("目前排名", 0) or 0),
                rank_change=int(row.get("上升", 0) or 0),
                main_cost=float(row.get("主力成本", 0) or 0),
                pe_ratio=float(row.get("市盈率", 0) or 0),
                turnover_rate=float(row.get("换手率", 0) or 0)
            )
            logger.info(f"获取股票 {symbol} 千股千评成功，综合得分: {rating.score}")
            return rating

        except Exception as e:
            logger.warning(f"获取股票 {symbol} 千股千评失败: {e}")
            return None

    def fetch_all_news(self) -> dict[str, list[NewsData]]:
        """一次性获取全市场新闻，按股票名称分组

        Returns:
            dict: {股票名称: [新闻列表]}
        """
        try:
            df = ak.stock_news_main_cx()
            if df is None or df.empty:
                logger.info("无法获取财联社新闻")
                return {}

            # 存储原始数据供后续过滤
            all_news = []
            for _, row in df.iterrows():
                all_news.append({
                    "tag": str(row.get("tag", "")),
                    "summary": str(row.get("summary", "")),
                    "pub_time": str(row.get("pub_time", "")),
                    "url": str(row.get("url", ""))
                })

            logger.info(f"批量获取财联社新闻成功，共 {len(all_news)} 条")
            return {"_raw": all_news}  # 返回原始数据，由调用方过滤

        except Exception as e:
            logger.warning(f"批量获取新闻失败: {e}")
            return {}

    def filter_news_for_stock(self, stock_name: str, raw_news: list[dict], limit: int = 10) -> list[NewsData]:
        """从预获取的新闻中过滤特定股票的新闻"""
        news_list = []
        for item in raw_news:
            tag = item.get("tag", "")
            summary = item.get("summary", "")

            if stock_name in tag or stock_name in summary:
                news_list.append(NewsData(
                    title=tag,
                    content=summary,
                    source="财联社",
                    publish_time=item.get("pub_time", ""),
                    url=item.get("url", "")
                ))
                if len(news_list) >= limit:
                    break

        return news_list

    def fetch_all_ratings(self) -> dict[str, StockRating]:
        """一次性获取全市场千股千评数据

        Returns:
            dict: {股票代码: StockRating}
        """
        try:
            df = ak.stock_comment_em()
            if df is None or df.empty:
                logger.info("无法获取千股千评数据")
                return {}

            ratings = {}
            for _, row in df.iterrows():
                code = str(row.get("代码", ""))
                if code:
                    ratings[code] = StockRating(
                        score=float(row.get("综合得分", 0) or 0),
                        institution_ratio=float(row.get("机构参与度", 0) or 0),
                        attention_index=float(row.get("关注指数", 0) or 0),
                        rank=int(row.get("目前排名", 0) or 0),
                        rank_change=int(row.get("上升", 0) or 0),
                        main_cost=float(row.get("主力成本", 0) or 0),
                        pe_ratio=float(row.get("市盈率", 0) or 0),
                        turnover_rate=float(row.get("换手率", 0) or 0)
                    )

            logger.info(f"批量获取千股千评成功，共 {len(ratings)} 只股票")
            return ratings

        except Exception as e:
            logger.warning(f"批量获取千股千评失败: {e}")
            return {}

    def get_all_stock_data(self, symbol: str, name: str = "") -> StockAllData:
        """获取完整数据

        Args:
            symbol: 股票代码
            name: 股票名称（用于新闻过滤，可选）
        """
        return StockAllData(
            price_info=self.get_stock_price(symbol),
            kline=self.get_stock_kline(symbol),
            news=self.get_stock_news(name) if name else [],
            rating=self.get_stock_rating(symbol)
        )

    async def get_stock_data_async(
        self,
        symbol: str,
        name: str = "",
        price_info: Optional[StockPrice] = None,
        raw_news: Optional[list[dict]] = None,
        all_ratings: Optional[dict[str, StockRating]] = None
    ) -> StockAllData:
        """异步并发获取股票数据（优化版）

        Args:
            symbol: 股票代码
            name: 股票名称（用于新闻过滤）
            price_info: 已有的价格信息（可选，避免重复获取）
            raw_news: 预获取的全市场新闻原始数据（可选，避免重复API调用）
            all_ratings: 预获取的全市场千股千评数据（可选，避免重复API调用）

        Returns:
            StockAllData: 包含所有数据的对象
        """
        code = self._clean_symbol(symbol)

        # 如果有预获取数据，直接从内存过滤，不需要API调用
        news = []
        if raw_news is not None:
            news = self.filter_news_for_stock(name, raw_news) if name else []

        rating = None
        if all_ratings is not None:
            rating = all_ratings.get(code)

        # 只需要获取 K线数据（每只股票独立）
        kline_task = asyncio.to_thread(self.get_stock_kline, symbol)

        # 如果没有预获取数据，则并发调用原有方法
        tasks = [kline_task]
        need_news = raw_news is None and name
        need_rating = all_ratings is None

        if need_news:
            tasks.append(asyncio.to_thread(self.get_stock_news, name))
        if need_rating:
            tasks.append(asyncio.to_thread(self.get_stock_rating, symbol))

        # 并发执行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 解析结果
        kline = results[0] if not isinstance(results[0], Exception) else []

        idx = 1
        if need_news:
            news = results[idx] if not isinstance(results[idx], Exception) else []
            idx += 1
        if need_rating:
            rating = results[idx] if not isinstance(results[idx], Exception) else None

        # 记录异常
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"获取股票 {symbol} 数据时任务 {i} 失败: {result}")

        return StockAllData(
            price_info=price_info,
            kline=kline,
            news=news,
            rating=rating
        )

    def verify_data_source(self) -> bool:
        """启动时验证数据源（简化版：只验证网络连通性）

        注意：具体的数据获取会在实际爬取时自然验证，无需提前单独验证
        """
        logger.info("正在验证数据源连接...")

        if not self.check_network():
            logger.error("网络连接失败，无法连接 AkShare 数据源")
            return False

        logger.info("数据源验证通过，AkShare 连接正常")
        return True
