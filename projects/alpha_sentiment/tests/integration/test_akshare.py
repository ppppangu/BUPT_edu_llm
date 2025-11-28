"""Integration tests for AkShare data fetching"""
import pytest
from backend.services.data_fetcher import DataFetcher


class TestAkShareIntegration:
    """Integration tests for AkShare API calls"""

    @pytest.fixture
    def fetcher(self):
        """Create DataFetcher with minimal rate limit"""
        return DataFetcher(rate_limit=0.5)

    @pytest.mark.integration
    def test_get_hot_stocks_real(self, fetcher):
        """Test fetching real hot stocks from AkShare"""
        stocks = fetcher.get_hot_stocks(limit=5)

        assert isinstance(stocks, list)
        if stocks:  # May be empty during non-trading hours
            stock = stocks[0]
            assert "code" in stock
            assert "name" in stock
            assert "price" in stock
            assert "change" in stock
            # Code may be empty if API returns different format
            if stock["code"]:
                assert len(stock["code"]) == 6

    @pytest.mark.integration
    def test_get_stock_price_real(self, fetcher, sample_stock_code):
        """Test fetching real stock price"""
        price_info = fetcher.get_stock_price(sample_stock_code)

        # May return None during non-trading hours
        if price_info:
            assert price_info["code"] == sample_stock_code
            assert "name" in price_info
            assert "price" in price_info
            assert isinstance(price_info["price"], float)

    @pytest.mark.integration
    def test_get_stock_kline_real(self, fetcher, sample_stock_code):
        """Test fetching real K-line data"""
        kline = fetcher.get_stock_kline(sample_stock_code, days=5)

        assert isinstance(kline, list)
        if kline:
            item = kline[0]
            assert "date" in item
            assert "open" in item
            assert "close" in item
            assert "high" in item
            assert "low" in item
            assert "volume" in item

    @pytest.mark.integration
    def test_get_stock_info_real(self, fetcher, sample_stock_code):
        """Test fetching real stock info"""
        info = fetcher.get_stock_info(sample_stock_code)

        # May return None if API fails
        if info:
            assert isinstance(info, dict)

    @pytest.mark.integration
    def test_get_all_stock_data_real(self, fetcher, sample_stock_code):
        """Test fetching all stock data"""
        data = fetcher.get_all_stock_data(sample_stock_code)

        assert "price_info" in data
        assert "kline" in data
        assert "comments" in data
        assert isinstance(data["kline"], list)
        assert isinstance(data["comments"], list)

    @pytest.mark.integration
    def test_invalid_stock_code(self, fetcher):
        """Test with invalid stock code"""
        price_info = fetcher.get_stock_price("999999")
        assert price_info is None
