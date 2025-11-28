"""Pydantic 数据模型"""
from pydantic import BaseModel, Field
from typing import Optional


class KlineData(BaseModel):
    """K线数据"""
    date: str
    open: float
    close: float
    high: float
    low: float
    volume: int
    amount: float


class StockPrice(BaseModel):
    """股票价格"""
    code: str
    name: str
    price: float
    change: float
    volume: int = 0
    amount: float = 0


class StockInfo(BaseModel):
    """股票基本信息"""
    code: str
    name: str
    industry: str = ""
    market: str = ""
    list_date: str = ""
    area: str = ""


class HotStock(BaseModel):
    """热门股票"""
    code: str
    name: str
    price: float = 0
    change: float = 0
    heat: int = 0
    tags: list[str] = Field(default_factory=list)
    sentiment_score: int = 50


class CommentData(BaseModel):
    """评论数据（已废弃，保留兼容）"""
    content: str
    source: str
    timestamp: Optional[str] = None


class NewsData(BaseModel):
    """新闻数据"""
    title: str
    content: str
    source: str
    publish_time: str
    url: str = ""


class StockRating(BaseModel):
    """千股千评数据"""
    score: float = 0  # 综合得分
    institution_ratio: float = 0  # 机构参与度
    attention_index: float = 0  # 关注指数
    rank: int = 0  # 目前排名
    rank_change: int = 0  # 排名变化（上升为正）
    main_cost: float = 0  # 主力成本
    pe_ratio: float = 0  # 市盈率
    turnover_rate: float = 0  # 换手率


class SentimentAnalysis(BaseModel):
    """情绪分析结果"""
    score: int = 50
    sentiment: str = "neutral"
    keywords: list[str] = Field(default_factory=list)
    summary: str = "暂无分析数据"
    bullish_ratio: float = 0.5
    bearish_ratio: float = 0.5
    tags: list[str] = Field(default_factory=list)


class StockAllData(BaseModel):
    """股票完整数据"""
    price_info: Optional[StockPrice] = None
    kline: list[KlineData] = Field(default_factory=list)
    news: list[NewsData] = Field(default_factory=list)
    rating: Optional[StockRating] = None


class StockDetail(BaseModel):
    """股票详情"""
    code: str
    name: str
    price: float
    change: float
    sentiment_score: int
    analysis: str
    keywords: list[dict]
    news: list[dict]
    kline: list[KlineData]
