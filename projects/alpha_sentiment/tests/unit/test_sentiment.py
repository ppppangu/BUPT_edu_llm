"""Tests for SentimentAnalyzer service"""
import pytest
import json
from unittest.mock import patch, MagicMock

from backend.services.sentiment import SentimentAnalyzer


class TestSentimentAnalyzer:
    """Test suite for SentimentAnalyzer class"""

    @patch('backend.services.sentiment.DEEPSEEK_API_KEY', '')
    def test_init_without_api_key(self):
        """Test initialization without API key"""
        analyzer = SentimentAnalyzer()
        assert analyzer.client is None

    @patch('backend.services.sentiment.DEEPSEEK_API_KEY', 'test-key')
    @patch('backend.services.sentiment.OpenAI')
    def test_init_with_api_key(self, mock_openai):
        """Test initialization with API key"""
        analyzer = SentimentAnalyzer()
        assert analyzer.client is not None
        mock_openai.assert_called_once()

    def test_default_analysis(self):
        """Test default analysis result"""
        with patch('backend.services.sentiment.DEEPSEEK_API_KEY', ''):
            analyzer = SentimentAnalyzer()
            result = analyzer._default_analysis()

            assert result["score"] == 50
            assert result["sentiment"] == "neutral"
            assert result["keywords"] == []
            assert result["summary"] == "暂无分析数据"
            assert result["bullish_ratio"] == 0.5
            assert result["bearish_ratio"] == 0.5
            assert result["tags"] == []

    @patch('backend.services.sentiment.DEEPSEEK_API_KEY', '')
    def test_analyze_comments_no_client(self, sample_comments):
        """Test analyze comments without client"""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze_comments("平安银行", sample_comments)

        assert result["score"] == 50
        assert result["sentiment"] == "neutral"

    @patch('backend.services.sentiment.DEEPSEEK_API_KEY', 'test-key')
    @patch('backend.services.sentiment.OpenAI')
    def test_analyze_comments_empty_comments(self, mock_openai):
        """Test analyze comments with empty list"""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze_comments("平安银行", [])

        assert result["score"] == 50
        assert result["sentiment"] == "neutral"

    @patch('backend.services.sentiment.DEEPSEEK_API_KEY', 'test-key')
    @patch('backend.services.sentiment.OpenAI')
    def test_analyze_comments_success(self, mock_openai, sample_comments, sample_sentiment_result):
        """Test successful sentiment analysis"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(sample_sentiment_result)
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        analyzer = SentimentAnalyzer()
        result = analyzer.analyze_comments("平安银行", sample_comments)

        assert result["score"] == 65
        assert result["sentiment"] == "bullish"
        assert "看好" in result["keywords"]

    @patch('backend.services.sentiment.DEEPSEEK_API_KEY', 'test-key')
    @patch('backend.services.sentiment.OpenAI')
    def test_analyze_comments_with_markdown_code_block(self, mock_openai, sample_comments, sample_sentiment_result):
        """Test sentiment analysis with markdown code block in response"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        # Response wrapped in markdown code block
        mock_response.choices[0].message.content = f"```json\n{json.dumps(sample_sentiment_result)}\n```"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        analyzer = SentimentAnalyzer()
        result = analyzer.analyze_comments("平安银行", sample_comments)

        assert result["score"] == 65

    @patch('backend.services.sentiment.DEEPSEEK_API_KEY', 'test-key')
    @patch('backend.services.sentiment.OpenAI')
    def test_analyze_comments_json_error(self, mock_openai, sample_comments):
        """Test sentiment analysis with JSON parse error"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "invalid json"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        analyzer = SentimentAnalyzer()
        result = analyzer.analyze_comments("平安银行", sample_comments)

        assert result["score"] == 50  # default analysis

    @patch('backend.services.sentiment.DEEPSEEK_API_KEY', 'test-key')
    @patch('backend.services.sentiment.OpenAI')
    def test_analyze_comments_api_error(self, mock_openai, sample_comments):
        """Test sentiment analysis with API error"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client

        analyzer = SentimentAnalyzer()
        result = analyzer.analyze_comments("平安银行", sample_comments)

        assert result["score"] == 50  # default analysis

    @patch('backend.services.sentiment.DEEPSEEK_API_KEY', 'test-key')
    @patch('backend.services.sentiment.OpenAI')
    def test_batch_analyze(self, mock_openai, sample_sentiment_result):
        """Test batch analysis of multiple stocks"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(sample_sentiment_result)
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        analyzer = SentimentAnalyzer()
        stocks_data = [
            {"code": "000001", "name": "平安银行", "comments": [{"content": "看好"}]},
            {"code": "000002", "name": "万科A", "comments": [{"content": "观望"}]},
        ]

        results = analyzer.batch_analyze(stocks_data)

        assert len(results) == 2
        assert results[0]["code"] == "000001"
        assert results[0]["name"] == "平安银行"
        assert results[0]["analysis"]["score"] == 65

    @patch('backend.services.sentiment.DEEPSEEK_API_KEY', 'test-key')
    @patch('backend.services.sentiment.OpenAI')
    def test_analyze_comments_limits_to_50(self, mock_openai, sample_sentiment_result):
        """Test that analysis limits to 50 comments"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(sample_sentiment_result)
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        analyzer = SentimentAnalyzer()
        # Create 100 comments with unique marker
        comments = [{"content": f"TESTCOMMENT{i}"} for i in range(100)]

        analyzer.analyze_comments("平安银行", comments)

        # Verify the API was called
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        prompt = call_args.kwargs['messages'][1]['content']

        # Should only contain 50 comments
        assert prompt.count("TESTCOMMENT") == 50
