# -*- coding: utf-8 -*-
"""情绪分析服务 - 基于 DeepSeek API 进行新闻情感分析"""
import json
import logging
import re
from openai import OpenAI
from typing import Optional

from ..config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """情绪分析器"""

    def __init__(self):
        """初始化 LLM 客户端"""
        if not LLM_API_KEY:
            logger.warning("LLM_API_KEY 未设置，情绪分析功能不可用")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=LLM_API_KEY,
                base_url=LLM_BASE_URL
            )
        self.model = LLM_MODEL

    def _extract_json(self, text: str) -> str:
        """Strip markdown fences and whitespace to keep pure JSON."""
        text = (text or '').strip()
        if text.startswith('```'):
            lines = [ln for ln in text.splitlines() if not ln.strip().startswith('```')]
            text = '\n'.join(lines).strip()
        return text

    def _parse_fields(self, text: str) -> dict:
        """Extract key fields from LLM text using regex instead of json.loads."""
        raw: dict[str, object] = {}
        if not text:
            return raw

        blob = text
        match = re.search(r"\{[\s\S]*?\}", text)
        if match:
            blob = match.group(0)

        def extract_number(key: str):
            m = re.search(fr'"?{key}"?\s*[:=]\s*([-+]?\d*\.?\d+)', blob, re.IGNORECASE)
            return m.group(1) if m else None

        def extract_text(key: str):
            m = re.search(fr'"?{key}"?\s*[:=]\s*"(.*?)"', blob, re.IGNORECASE | re.DOTALL)
            if m:
                return m.group(1)
            m = re.search(fr"'?{key}'?\s*[:=]\s*'(.*?)'", blob, re.IGNORECASE | re.DOTALL)
            return m.group(1) if m else None

        def extract_list(key: str):
            m = re.search(fr'"?{key}"?\s*[:=]\s*\[([^\]]*)\]', blob, re.IGNORECASE | re.DOTALL)
            segment = m.group(1) if m else ''
            if not segment:
                return []
            picks = re.findall(r'"([^"]+)"|\'([^\']+)\'', segment)
            flattened = [p[0] or p[1] for p in picks if (p[0] or p[1])]
            if not flattened:
                flattened = [s.strip() for s in segment.split(',') if s.strip()]
            return flattened

        raw['score'] = extract_number('score')
        raw['bullish_ratio'] = extract_number('bullish_ratio')
        raw['bearish_ratio'] = extract_number('bearish_ratio')
        raw['sentiment'] = extract_text('sentiment')
        raw['summary'] = extract_text('summary')
        raw['keywords'] = extract_list('keywords')
        raw['tags'] = extract_list('tags')
        return raw

    def _normalize_result(self, raw: dict) -> dict:
        """Coerce LLM output into a stable schema with defaults."""
        def to_ratio(val):
            try:
                return max(0.0, min(1.0, float(val)))
            except Exception:
                return 0.0

        def to_list(val):
            if isinstance(val, list):
                return [str(v).strip() for v in val if str(v).strip()]
            if isinstance(val, str) and val.strip():
                return [v.strip() for v in val.split(',') if v.strip()]
            return []

        try:
            score = int(float(raw.get('score', 50)))
        except Exception:
            score = 50
        score = max(0, min(score, 100))

        sentiment = str(raw.get('sentiment', 'neutral')).lower()
        if sentiment not in {'bullish', 'bearish', 'neutral'}:
            sentiment = 'neutral'

        keywords = to_list(raw.get('keywords', []))[:5]
        tags = to_list(raw.get('tags', []))[:5]
        summary = str(raw.get('summary', '')).strip() or '暂无分析摘要'

        return {
            'score': score,
            'sentiment': sentiment,
            'keywords': keywords,
            'summary': summary,
            'bullish_ratio': to_ratio(raw.get('bullish_ratio', 0)),
            'bearish_ratio': to_ratio(raw.get('bearish_ratio', 0)),
            'tags': tags
        }

    def analyze_news(self, stock_name: str, news_list: list[dict]) -> Optional[dict]:
        """
        分析股票新闻情绪

        Args:
            stock_name: 股票名称
            news_list: 新闻列表，每条包含 title, content, source, publish_time

        Returns:
            分析结果字典，失败时返回 None
        """
        if not self.client:
            logger.error("LLM 客户端未初始化")
            return None

        if not news_list:
            logger.info(f"股票 {stock_name} 没有新闻数据，跳过分析")
            return None

        news_text = "\n".join([
            f"【{n.get('source', '未知')}】{n.get('title', '')}\n{n.get('content', '')[:200]}"
            for n in news_list[:10]
        ])

        prompt = f"""请分析以下关于{stock_name}的新闻，给出情绪评估。

新闻内容:
{news_text}

请以 JSON 格式返回分析结果，格式如下:
{{
  "score": 65,
  "sentiment": "bullish",
  "keywords": ["利好", "增长", "突破"],
  "summary": "公司业绩表现良好，市场预期乐观，整体情绪偏向积极",
  "bullish_ratio": 0.7,
  "bearish_ratio": 0.1,
  "tags": ["业绩预增", "行业龙头"]
}}

字段说明:
- score: 情绪得分(0-100，50为中性，越高越乐观)
- sentiment: 情绪倾向(bullish/bearish/neutral)
- keywords: 关键词列表(最多5个)
- summary: 一句话分析摘要(不超过80字)
- bullish_ratio: 利好新闻占比(0-1)
- bearish_ratio: 利空新闻占比(0-1)
- tags: 标签分类(最多3个)"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位专业的股票分析师，擅长从新闻中分析市场情绪。请以 JSON 格式返回分析结果。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=500
            )

            result_text = response.choices[0].message.content
            if not result_text:
                logger.warning(f"股票 {stock_name} LLM 返回为空")
                return None

            cleaned = self._extract_json(result_text)
            raw_fields = self._parse_fields(cleaned)
            normalized = self._normalize_result(raw_fields)
            if not normalized:
                logger.warning(f"股票 {stock_name} 分析结果无效，返回默认 None")
                return None

            logger.info(f"股票 {stock_name} 情绪分析完成，得分: {normalized.get('score')}")
            return normalized

        except Exception as e:
            logger.error(f"DeepSeek API 调用失败: {e}")
            return None
