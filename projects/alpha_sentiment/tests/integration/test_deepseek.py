"""Integration tests for DeepSeek sentiment analysis"""
import pytest
import os
from backend.services.sentiment import SentimentAnalyzer


class TestDeepSeekIntegration:
    """Integration tests for DeepSeek API calls"""

    @pytest.fixture
    def analyzer(self):
        """Create SentimentAnalyzer"""
        return SentimentAnalyzer()

    @pytest.fixture
    def sample_comments(self):
        """Sample comments for testing"""
        return [
            {"content": "这只股票前景不错，准备加仓", "source": "测试", "timestamp": "2024-01-01"},
            {"content": "业绩超预期，继续持有", "source": "测试", "timestamp": "2024-01-01"},
            {"content": "大盘不好，先观望一下", "source": "测试", "timestamp": "2024-01-01"},
        ]

    @pytest.mark.integration
    def test_analyze_comments_real(self, analyzer, sample_comments, skip_without_deepseek_key):
        """Test real sentiment analysis with DeepSeek API"""
        result = analyzer.analyze_comments("平安银行", sample_comments)

        assert isinstance(result, dict)
        assert "score" in result
        assert "sentiment" in result
        assert "keywords" in result
        assert "summary" in result

        # Validate score range
        assert 0 <= result["score"] <= 100

        # Validate sentiment value
        assert result["sentiment"] in ["bullish", "bearish", "neutral"]

        # Validate ratios
        if "bullish_ratio" in result:
            assert 0 <= result["bullish_ratio"] <= 1
        if "bearish_ratio" in result:
            assert 0 <= result["bearish_ratio"] <= 1

    @pytest.mark.integration
    def test_analyze_empty_comments(self, analyzer):
        """Test analysis with empty comments (should return default)"""
        result = analyzer.analyze_comments("测试股票", [])

        assert result["score"] == 50
        assert result["sentiment"] == "neutral"

    @pytest.mark.integration
    def test_batch_analyze_real(self, analyzer, sample_comments, skip_without_deepseek_key):
        """Test batch analysis with real API"""
        stocks_data = [
            {"code": "000001", "name": "平安银行", "comments": sample_comments},
        ]

        results = analyzer.batch_analyze(stocks_data)

        assert len(results) == 1
        assert results[0]["code"] == "000001"
        assert "analysis" in results[0]
        assert "score" in results[0]["analysis"]

    @pytest.mark.integration
    def test_no_api_key(self):
        """Test behavior when API key is not set"""
        # Temporarily clear the API key
        original_key = os.environ.get("DEEPSEEK_API_KEY")
        if "DEEPSEEK_API_KEY" in os.environ:
            del os.environ["DEEPSEEK_API_KEY"]

        try:
            # Need to reimport to get fresh instance
            from backend.services.sentiment import SentimentAnalyzer
            analyzer = SentimentAnalyzer()

            # Client should be None
            if not original_key:
                assert analyzer.client is None

            # Should return default analysis
            result = analyzer.analyze_comments("测试", [{"content": "test"}])
            assert result["score"] == 50
        finally:
            # Restore the key
            if original_key:
                os.environ["DEEPSEEK_API_KEY"] = original_key
