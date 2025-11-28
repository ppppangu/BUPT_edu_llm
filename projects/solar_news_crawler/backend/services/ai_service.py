# -*- coding: utf-8 -*-
"""AI 总结服务"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

import requests

from backend.config import AI_API_KEY, AI_BASE_URL, AI_ENABLED, AI_MODEL, DATA_DIR


class AISummarizerService:
    """AI新闻总结服务"""

    def __init__(self):
        self.base_url = AI_BASE_URL.rstrip("/") if AI_BASE_URL else ""
        self.api_key = AI_API_KEY
        self.model = AI_MODEL
        self.enabled = AI_ENABLED

    def _call_llm(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """调用大语言模型API"""
        if not self.enabled:
            raise ValueError("AI 服务未配置")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def generate_summary(self, news_data: List[Dict], news_type: str = "domestic") -> Dict:
        """
        根据新闻数据生成AI简报

        Args:
            news_data: 新闻数据列表
            news_type: 新闻类型 'domestic'(国内) 或 'international'(国际)

        Returns:
            Dict: 包含总结内容的字典
        """
        if not news_data:
            return {
                "success": False,
                "error": "没有新闻数据",
                "summary": "",
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        if not self.enabled:
            return {
                "success": False,
                "error": "AI 服务未配置",
                "summary": "",
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        news_titles = []
        source_stats = {}

        for news in news_data[:100]:
            if news_type == "international":
                title = news.get("title_translated") or news.get("title_original", "")
            else:
                title = news.get("title", "")

            if title:
                news_titles.append(title)

            source = news.get("source", "Unknown")
            source_stats[source] = source_stats.get(source, 0) + 1

        news_type_cn = "国内" if news_type == "domestic" else "国际"
        today = datetime.now().strftime("%Y年%m月%d日")

        context = f"""
今天是{today}，以下是今日收集的{news_type_cn}光伏行业新闻标题({len(news_titles)}条):

{chr(10).join(f"{i+1}. {title}" for i, title in enumerate(news_titles[:50]))}

数据来源统计:
{chr(10).join(f"- {source}: {count}条" for source, count in source_stats.items())}
"""

        prompt = f"""请根据以上{news_type_cn}光伏行业新闻标题，生成"今日光伏产业焦点"简报。

要求：
1. 首先用一句话总结今日整体趋势
2. 提取3-5个主要热点话题
3. 每个话题用1句话精炼概括
4. 使用markdown格式，用 "### " 标记每个话题标题
5. 总字数控制在250字以内
6. 语言精炼专业

请直接输出简报内容，不要添加标题和额外说明。"""

        messages = [
            {"role": "system", "content": "你是一位资深的光伏行业分析师，擅长从大量新闻中提取核心信息并生成简报。"},
            {"role": "user", "content": context + "\n\n" + prompt},
        ]

        try:
            summary_text = self._call_llm(messages, temperature=0.7)

            return {
                "success": True,
                "summary": summary_text.strip(),
                "news_count": len(news_data),
                "processed_count": len(news_titles),
                "source_stats": source_stats,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "news_type": news_type,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "summary": "",
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "news_type": news_type,
            }

    def save_summary_to_file(self, summary_data: Dict, output_path: str) -> bool:
        """将总结保存到JSON文件"""
        try:
            existing_data = []
            if os.path.exists(output_path):
                try:
                    with open(output_path, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                        if not isinstance(existing_data, list):
                            existing_data = []
                except Exception:
                    existing_data = []

            today = datetime.now().strftime("%Y-%m-%d")
            existing_data = [item for item in existing_data if item.get("date") != today]

            new_record = {
                "date": today,
                "generated_at": summary_data.get("generated_at"),
                "summary": summary_data.get("summary"),
                "news_count": summary_data.get("news_count"),
                "processed_count": summary_data.get("processed_count"),
                "source_stats": summary_data.get("source_stats"),
                "news_type": summary_data.get("news_type"),
                "success": summary_data.get("success")
            }

            existing_data.insert(0, new_record)
            existing_data = existing_data[:30]

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)

            return True

        except Exception:
            return False

    def run_summary(self, news_data: List[Dict], news_type: str, output_filename: str) -> Dict:
        """生成并保存总结"""
        summary_data = self.generate_summary(news_data, news_type)

        if summary_data.get("success"):
            output_path = DATA_DIR / output_filename
            self.save_summary_to_file(summary_data, str(output_path))

        return summary_data


# 全局单例
ai_service = AISummarizerService()
