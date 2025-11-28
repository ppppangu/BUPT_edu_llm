"""Pytest fixtures for alpha_sentiment tests"""
import pytest
from pathlib import Path
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory for tests"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def mock_tushare_daily_df():
    """Mock DataFrame for Tushare daily data"""
    return pd.DataFrame({
        "ts_code": ["000001.SZ", "000002.SZ", "600000.SH"],
        "trade_date": ["20240101", "20240101", "20240101"],
        "open": [10.0, 15.0, 8.0],
        "close": [10.5, 15.2, 8.3],
        "high": [10.8, 15.5, 8.5],
        "low": [9.8, 14.8, 7.9],
        "pct_chg": [2.5, -1.3, 0.8],
        "vol": [10000, 20000, 15000],
        "amount": [105000, 304000, 125000],
    })


@pytest.fixture
def mock_tushare_stock_basic_df():
    """Mock DataFrame for Tushare stock basic"""
    return pd.DataFrame({
        "ts_code": ["000001.SZ", "000002.SZ", "600000.SH"],
        "name": ["平安银行", "万科A", "浦发银行"],
        "industry": ["银行", "房地产", "银行"],
        "market": ["主板", "主板", "主板"],
        "list_date": ["19910403", "19910129", "19991110"],
        "area": ["深圳", "深圳", "上海"],
    })


@pytest.fixture
def mock_tushare_trade_cal_df():
    """Mock DataFrame for Tushare trade calendar"""
    return pd.DataFrame({
        "cal_date": ["20240101", "20240102"],
        "is_open": ["1", "1"],
    })


@pytest.fixture
def sample_hot_stocks():
    """Sample hot stocks data"""
    return [
        {
            "code": "000001",
            "name": "平安银行",
            "price": 10.5,
            "change": 2.5,
            "heat": 1,
            "tags": [],
            "sentiment_score": 50,
        },
        {
            "code": "000002",
            "name": "万科A",
            "price": 15.2,
            "change": -1.3,
            "heat": 2,
            "tags": [],
            "sentiment_score": 50,
        },
    ]


@pytest.fixture
def sample_comments():
    """Sample comments data"""
    return [
        {"content": "看好后市", "source": "东方财经", "timestamp": "2024-01-01 10:00"},
        {"content": "继续持有", "source": "东方财经", "timestamp": "2024-01-01 11:00"},
    ]


@pytest.fixture
def sample_sentiment_result():
    """Sample sentiment analysis result"""
    return {
        "score": 65,
        "sentiment": "bullish",
        "keywords": ["看好", "持有", "上涨"],
        "summary": "市场情绪偏向看涨",
        "bullish_ratio": 0.6,
        "bearish_ratio": 0.3,
        "tags": ["主力增持", "业绩预增"]
    }


@pytest.fixture
def sample_stock_detail():
    """Sample stock detail data"""
    return {
        "code": "000001",
        "name": "平安银行",
        "price": 10.5,
        "change": 2.5,
        "sentiment_score": 65,
        "analysis": "市场情绪偏向看涨",
        "keywords": [{"word": "看好", "sentiment": "neutral"}],
        "news": [
            {
                "title": "看好后市",
                "content": "看好后市，继续持有",
                "source": "东方财经",
                "timestamp": "2024-01-01",
                "sentiment": "neutral"
            }
        ],
        "kline": [
            {
                "date": "20240101",
                "open": 10.0,
                "close": 10.5,
                "high": 10.8,
                "low": 9.8,
                "volume": 1000000,
                "amount": 105000000.0,
            }
        ],
        "tags": ["主力增持"]
    }
