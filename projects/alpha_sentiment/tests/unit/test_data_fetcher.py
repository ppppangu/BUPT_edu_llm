# -*- coding: utf-8 -*-
"""Tests for DataFetcher service (AkShare)"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from backend.services.data_fetcher import DataFetcher
from backend.models.schemas import HotStock, StockPrice, KlineData, NewsData, StockRating


class TestDataFetcher:
    """Test suite for DataFetcher class"""

    def test_clean_symbol(self):
        """Test symbol cleaning"""
        fetcher = DataFetcher()
        assert fetcher._clean_symbol('SZ000001') == '000001'
        assert fetcher._clean_symbol('SH600000') == '600000'
        assert fetcher._clean_symbol('000001') == '000001'
        assert fetcher._clean_symbol('1') == '000001'

    @patch('backend.services.data_fetcher.ak')
    def test_check_network_success(self, mock_ak):
        """Test network check success"""
        mock_ak.stock_hot_rank_em.return_value = pd.DataFrame({
            '代码': ['000001'],
            '股票名称': ['平安银行']
        })

        fetcher = DataFetcher()
        assert fetcher.check_network() is True

    @patch('backend.services.data_fetcher.ak')
    def test_check_network_failure(self, mock_ak):
        """Test network check failure"""
        mock_ak.stock_hot_rank_em.side_effect = Exception("Network error")

        fetcher = DataFetcher()
        assert fetcher.check_network() is False

    @patch('backend.services.data_fetcher.ak')
    def test_get_hot_stocks_success(self, mock_ak):
        """Test hot stocks from AkShare"""
        mock_ak.stock_hot_rank_em.return_value = pd.DataFrame({
            '股票代码': ['000001', '600000'],
            '股票简称': ['平安银行', '浦发银行'],
            '最新价': [10.5, 8.2],
            '涨跌幅': [2.5, -1.2]
        })

        fetcher = DataFetcher()
        result = fetcher.get_hot_stocks(limit=2)

        assert len(result) == 2
        assert isinstance(result[0], HotStock)
        assert result[0].code == '000001'
        assert result[0].name == '平安银行'
        assert result[0].price == 10.5
        assert result[0].change == 2.5

    @patch('backend.services.data_fetcher.ak')
    def test_get_hot_stocks_empty(self, mock_ak):
        """Test hot stocks when empty"""
        mock_ak.stock_hot_rank_em.return_value = pd.DataFrame()

        fetcher = DataFetcher()
        result = fetcher.get_hot_stocks(limit=10)

        assert result == []

    @patch('backend.services.data_fetcher.ak')
    def test_get_stock_price_from_hot_rank(self, mock_ak):
        """Test stock price from hot rank data"""
        mock_ak.stock_hot_rank_em.return_value = pd.DataFrame({
            '代码': ['000001'],
            '股票名称': ['平安银行'],
            '最新价': [10.5],
            '涨跌幅': [2.5]
        })

        fetcher = DataFetcher()
        result = fetcher.get_stock_price('000001')

        assert result is not None
        assert isinstance(result, StockPrice)
        assert result.price == 10.5
        assert result.change == 2.5

    @patch('backend.services.data_fetcher.ak')
    def test_get_stock_kline_success(self, mock_ak):
        """Test K-line data from AkShare"""
        mock_ak.stock_zh_a_daily.return_value = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'open': [10.0, 10.5],
            'high': [11.0, 11.5],
            'low': [9.5, 10.0],
            'close': [10.5, 11.0],
            'volume': [1000000, 1200000],
            'amount': [10000000, 12000000]
        })

        fetcher = DataFetcher()
        result = fetcher.get_stock_kline('000001', days=2)

        assert len(result) == 2
        assert isinstance(result[0], KlineData)
        assert result[0].open == 10.0
        assert result[0].close == 10.5

    @patch('backend.services.data_fetcher.ak')
    def test_get_stock_kline_empty(self, mock_ak):
        """Test K-line data when empty"""
        mock_ak.stock_zh_a_daily.return_value = pd.DataFrame()

        fetcher = DataFetcher()
        result = fetcher.get_stock_kline('000001', days=30)

        assert result == []

    @patch('backend.services.data_fetcher.ak')
    def test_get_stock_news_success(self, mock_ak):
        """Test news from AkShare"""
        mock_ak.stock_news_main_cx.return_value = pd.DataFrame({
            'tag': ['平安银行发布年报', '其他新闻'],
            'summary': ['平安银行公布业绩', '无关内容'],
            'pub_time': ['2024-01-01 10:00', '2024-01-01 11:00'],
            'url': ['http://example.com/1', 'http://example.com/2']
        })

        fetcher = DataFetcher()
        result = fetcher.get_stock_news('平安银行', limit=10)

        # Should only return news containing stock name
        assert len(result) == 1
        assert isinstance(result[0], NewsData)
        assert '平安银行' in result[0].title

    @patch('backend.services.data_fetcher.ak')
    def test_get_stock_rating_success(self, mock_ak):
        """Test stock rating from AkShare"""
        mock_ak.stock_comment_em.return_value = pd.DataFrame({
            '代码': ['000001', '600000'],
            '综合得分': [80.5, 75.0],
            '机构参与度': [0.65, 0.55],
            '关注指数': [90.0, 85.0],
            '目前排名': [10, 20],
            '上升': [5, -3],
            '主力成本': [10.0, 8.0],
            '市盈率': [8.5, 7.0],
            '换手率': [2.5, 1.8]
        })

        fetcher = DataFetcher()
        result = fetcher.get_stock_rating('000001')

        assert result is not None
        assert isinstance(result, StockRating)
        assert result.score == 80.5
        assert result.institution_ratio == 0.65

    @patch('backend.services.data_fetcher.ak')
    def test_get_stock_rating_not_found(self, mock_ak):
        """Test stock rating when not found"""
        mock_ak.stock_comment_em.return_value = pd.DataFrame({
            '代码': ['600000'],
            '综合得分': [75.0]
        })

        fetcher = DataFetcher()
        result = fetcher.get_stock_rating('000001')

        assert result is None

    @patch('backend.services.data_fetcher.ak')
    def test_get_all_stock_data(self, mock_ak):
        """Test complete stock data retrieval"""
        # Mock hot rank for price
        mock_ak.stock_hot_rank_em.return_value = pd.DataFrame({
            '代码': ['000001'],
            '股票名称': ['平安银行'],
            '最新价': [10.5],
            '涨跌幅': [2.5]
        })

        # Mock K-line
        mock_ak.stock_zh_a_daily.return_value = pd.DataFrame({
            'date': ['2024-01-01'],
            'open': [10.0],
            'high': [11.0],
            'low': [9.5],
            'close': [10.5],
            'volume': [1000000],
            'amount': [10000000]
        })

        # Mock news (empty)
        mock_ak.stock_news_main_cx.return_value = pd.DataFrame()

        # Mock rating
        mock_ak.stock_comment_em.return_value = pd.DataFrame({
            '代码': ['000001'],
            '综合得分': [80.5],
            '机构参与度': [0.65],
            '关注指数': [90.0],
            '目前排名': [10],
            '上升': [5],
            '主力成本': [10.0],
            '市盈率': [8.5],
            '换手率': [2.5]
        })

        fetcher = DataFetcher()
        result = fetcher.get_all_stock_data('000001', '平安银行')

        assert result.price_info is not None
        assert result.price_info.price == 10.5
        assert len(result.kline) == 1
        assert result.news == []
        assert result.rating is not None
        assert result.rating.score == 80.5


class TestDataFetcherRetry:
    """Test retry mechanism"""

    @patch('backend.services.data_fetcher.ak')
    @patch('backend.services.data_fetcher.time.sleep')
    def test_retry_on_failure(self, mock_sleep, mock_ak):
        """Test retry mechanism on network failure"""
        # Fail twice, then succeed
        mock_ak.stock_hot_rank_em.side_effect = [
            Exception("Network error"),
            Exception("Network error"),
            pd.DataFrame({
                '股票代码': ['000001'],
                '股票简称': ['平安银行'],
                '最新价': [10.5],
                '涨跌幅': [2.5]
            })
        ]

        fetcher = DataFetcher()
        result = fetcher.get_hot_stocks(limit=1)

        assert len(result) == 1
        assert mock_sleep.call_count == 2  # Slept twice before success
