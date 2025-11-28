"""Tests for Pydantic models/schemas"""
import pytest
from pydantic import ValidationError

from backend.models.schemas import (
    KlineData,
    HotStock,
    StockDetail,
    SentimentAnalysis,
    CommentData
)


class TestKlineData:
    """Tests for KlineData model"""

    def test_valid_kline_data(self):
        """Test valid KlineData creation"""
        kline = KlineData(
            date="2024-01-01",
            open=10.0,
            close=10.5,
            high=10.8,
            low=9.8,
            volume=100000,
            amount=1050000.0
        )

        assert kline.date == "2024-01-01"
        assert kline.open == 10.0
        assert kline.close == 10.5
        assert kline.high == 10.8
        assert kline.low == 9.8
        assert kline.volume == 100000
        assert kline.amount == 1050000.0

    def test_kline_data_missing_field(self):
        """Test KlineData with missing required field"""
        with pytest.raises(ValidationError):
            KlineData(
                date="2024-01-01",
                open=10.0,
                close=10.5,
                high=10.8,
                low=9.8,
                volume=100000
                # missing amount
            )

    def test_kline_data_type_coercion(self):
        """Test KlineData type coercion"""
        kline = KlineData(
            date="2024-01-01",
            open="10.0",  # string to float
            close="10.5",
            high="10.8",
            low="9.8",
            volume="100000",  # string to int
            amount="1050000.0"
        )

        assert isinstance(kline.open, float)
        assert isinstance(kline.volume, int)


class TestHotStock:
    """Tests for HotStock model"""

    def test_valid_hot_stock(self):
        """Test valid HotStock creation"""
        stock = HotStock(
            code="000001",
            name="平安银行",
            price=10.5,
            change=2.5,
            heat=1,
            tags=["主力增持", "业绩预增"],
            sentiment_score=65
        )

        assert stock.code == "000001"
        assert stock.name == "平安银行"
        assert stock.price == 10.5
        assert stock.change == 2.5
        assert stock.heat == 1
        assert len(stock.tags) == 2
        assert stock.sentiment_score == 65

    def test_hot_stock_empty_tags(self):
        """Test HotStock with empty tags"""
        stock = HotStock(
            code="000001",
            name="平安银行",
            price=10.5,
            change=2.5,
            heat=1,
            tags=[],
            sentiment_score=50
        )

        assert stock.tags == []

    def test_hot_stock_missing_field(self):
        """Test HotStock with missing required field"""
        with pytest.raises(ValidationError):
            HotStock(
                code="000001",
                name="平安银行",
                price=10.5,
                change=2.5,
                heat=1,
                tags=[]
                # missing sentiment_score
            )


class TestStockDetail:
    """Tests for StockDetail model"""

    def test_valid_stock_detail(self):
        """Test valid StockDetail creation"""
        kline = KlineData(
            date="2024-01-01",
            open=10.0,
            close=10.5,
            high=10.8,
            low=9.8,
            volume=100000,
            amount=1050000.0
        )

        detail = StockDetail(
            code="000001",
            name="平安银行",
            price=10.5,
            change=2.5,
            sentiment_score=65,
            analysis="市场看涨",
            keywords=[{"word": "看好", "sentiment": "bullish"}],
            news=[{"title": "新闻", "content": "内容"}],
            kline=[kline]
        )

        assert detail.code == "000001"
        assert detail.sentiment_score == 65
        assert len(detail.kline) == 1

    def test_stock_detail_empty_lists(self):
        """Test StockDetail with empty lists"""
        detail = StockDetail(
            code="000001",
            name="平安银行",
            price=10.5,
            change=2.5,
            sentiment_score=50,
            analysis="暂无分析",
            keywords=[],
            news=[],
            kline=[]
        )

        assert detail.keywords == []
        assert detail.news == []
        assert detail.kline == []


class TestSentimentAnalysis:
    """Tests for SentimentAnalysis model"""

    def test_valid_sentiment_analysis(self):
        """Test valid SentimentAnalysis creation"""
        analysis = SentimentAnalysis(
            score=65,
            sentiment="bullish",
            keywords=["看好", "持有", "上涨"],
            summary="市场情绪偏向看涨",
            bullish_ratio=0.6,
            bearish_ratio=0.3
        )

        assert analysis.score == 65
        assert analysis.sentiment == "bullish"
        assert len(analysis.keywords) == 3
        assert analysis.bullish_ratio == 0.6
        assert analysis.bearish_ratio == 0.3

    def test_sentiment_analysis_neutral(self):
        """Test neutral SentimentAnalysis"""
        analysis = SentimentAnalysis(
            score=50,
            sentiment="neutral",
            keywords=[],
            summary="暂无分析数据",
            bullish_ratio=0.5,
            bearish_ratio=0.5
        )

        assert analysis.score == 50
        assert analysis.sentiment == "neutral"

    def test_sentiment_analysis_ratios_sum(self):
        """Test sentiment analysis ratios"""
        analysis = SentimentAnalysis(
            score=70,
            sentiment="bullish",
            keywords=["看好"],
            summary="强烈看涨",
            bullish_ratio=0.7,
            bearish_ratio=0.2
        )

        # Note: ratios don't need to sum to 1 (neutral is the remainder)
        assert analysis.bullish_ratio + analysis.bearish_ratio <= 1.0


class TestCommentData:
    """Tests for CommentData model"""

    def test_valid_comment_data(self):
        """Test valid CommentData creation"""
        comment = CommentData(
            content="看好后市",
            source="东方财经",
            timestamp="2024-01-01 10:00"
        )

        assert comment.content == "看好后市"
        assert comment.source == "东方财经"
        assert comment.timestamp == "2024-01-01 10:00"

    def test_comment_data_optional_timestamp(self):
        """Test CommentData with optional timestamp"""
        comment = CommentData(
            content="看好后市",
            source="东方财经"
        )

        assert comment.content == "看好后市"
        assert comment.timestamp is None

    def test_comment_data_missing_required(self):
        """Test CommentData with missing required field"""
        with pytest.raises(ValidationError):
            CommentData(
                content="看好后市"
                # missing source
            )


class TestModelSerialization:
    """Tests for model serialization"""

    def test_kline_to_dict(self):
        """Test KlineData serialization to dict"""
        kline = KlineData(
            date="2024-01-01",
            open=10.0,
            close=10.5,
            high=10.8,
            low=9.8,
            volume=100000,
            amount=1050000.0
        )

        data = kline.model_dump()

        assert data["date"] == "2024-01-01"
        assert data["open"] == 10.0

    def test_hot_stock_to_json(self):
        """Test HotStock serialization to JSON"""
        stock = HotStock(
            code="000001",
            name="平安银行",
            price=10.5,
            change=2.5,
            heat=1,
            tags=["主力增持"],
            sentiment_score=65
        )

        json_str = stock.model_dump_json()

        assert "000001" in json_str
        assert "平安银行" in json_str

    def test_from_dict(self):
        """Test model creation from dict"""
        data = {
            "content": "看好后市",
            "source": "东方财经",
            "timestamp": "2024-01-01"
        }

        comment = CommentData(**data)

        assert comment.content == "看好后市"
