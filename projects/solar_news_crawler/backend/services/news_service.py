# -*- coding: utf-8 -*-
"""新闻数据服务"""
import glob
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from backend.config import DATA_DIR


class NewsService:
    """新闻数据服务类"""

    def __init__(self):
        self.news_data: List[Dict] = []
        self.irena_news_data: List[Dict] = []
        self.translated_news_data: List[Dict] = []
        self.domestic_ai_summary: Dict = {}
        self.international_ai_summary: Dict = {}

        self.last_update_time: Optional[datetime] = None
        self.last_irena_update_time: Optional[datetime] = None
        self.last_translated_update_time: Optional[datetime] = None

        self.file_hashes = {"combined": None, "irena": None, "translator": None}

        # 初始化加载数据
        self.initialize_data()

    def _find_latest_file(self, pattern: str, directory: Path = None) -> Optional[str]:
        """查找指定模式的最新文件"""
        if directory is None:
            directory = DATA_DIR

        if not directory.exists():
            return None

        files = glob.glob(str(directory / pattern))
        if not files:
            return None

        files.sort(key=os.path.getmtime, reverse=True)
        return files[0]

    def _calculate_file_hash(self, filepath: str) -> Optional[str]:
        """计算文件的MD5哈希值"""
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return None

    def initialize_data(self):
        """初始化数据（从文件加载）"""

        if self._load_news_from_file():
            self.last_update_time = datetime.now()
            latest = self._find_latest_file("combined_*.json")
            if latest:
                self.file_hashes["combined"] = self._calculate_file_hash(latest)
            print(f"Loaded {len(self.news_data)} domestic news")

        if self._load_irena_news_from_file():
            self.last_irena_update_time = datetime.now()
            latest = self._find_latest_file("irena_*_translated.json")
            if latest:
                self.file_hashes["irena"] = self._calculate_file_hash(latest)
            print(f"Loaded {len(self.irena_news_data)} IRENA news")

        if self._load_translated_news_from_file():
            self.last_translated_update_time = datetime.now()
            latest = self._find_latest_file("translator_*.json")
            if latest:
                self.file_hashes["translator"] = self._calculate_file_hash(latest)
            print(f"Loaded {len(self.translated_news_data)} translated news")

        self._load_ai_summaries()

    def check_and_reload_data(self) -> bool:
        """检查数据文件是否有更新，如果有则重新加载"""
        reload_flags = {"combined": False, "irena": False, "translator": False}

        # 检查 combined 文件
        latest_combined = self._find_latest_file("combined_*.json")
        if latest_combined:
            current_hash = self._calculate_file_hash(latest_combined)
            if current_hash and current_hash != self.file_hashes["combined"]:
                self.file_hashes["combined"] = current_hash
                reload_flags["combined"] = True

        # 检查 irena 翻译文件
        latest_irena = self._find_latest_file("irena_*_translated.json")
        if latest_irena:
            current_hash = self._calculate_file_hash(latest_irena)
            if current_hash and current_hash != self.file_hashes["irena"]:
                self.file_hashes["irena"] = current_hash
                reload_flags["irena"] = True

        # 检查 translator 文件
        latest_translator = self._find_latest_file("translator_*.json")
        if latest_translator:
            current_hash = self._calculate_file_hash(latest_translator)
            if current_hash and current_hash != self.file_hashes["translator"]:
                self.file_hashes["translator"] = current_hash
                reload_flags["translator"] = True

        # 重新加载数据
        if reload_flags["combined"] and self._load_news_from_file():
            self.last_update_time = datetime.now()

        if reload_flags["irena"] and self._load_irena_news_from_file():
            self.last_irena_update_time = datetime.now()

        if reload_flags["translator"] and self._load_translated_news_from_file():
            self.last_translated_update_time = datetime.now()

        return any(reload_flags.values())

    def _load_news_from_file(self) -> bool:
        """加载国内新闻数据"""
        try:
            latest_file = self._find_latest_file("combined_*.json")
            if not latest_file:
                return False

            with open(latest_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                self.news_data = data
                return True
            return False
        except Exception as e:
            print(f"Error loading news: {e}")
            return False

    def _load_irena_news_from_file(self) -> bool:
        """加载 IRENA 新闻数据"""
        try:
            latest_file = self._find_latest_file("irena_*_translated.json")
            if not latest_file:
                return False

            with open(latest_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                self.irena_news_data = data
                return True
            elif isinstance(data, dict) and "news_list" in data:
                self.irena_news_data = data["news_list"]
                return True
            return False
        except Exception as e:
            print(f"Error loading IRENA news: {e}")
            return False

    def _load_translated_news_from_file(self) -> bool:
        """加载翻译新闻数据"""
        try:
            latest_file = self._find_latest_file("translator_*.json")
            if not latest_file:
                return False

            with open(latest_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict) and "news_list" in data:
                self.translated_news_data = data["news_list"]
                return True
            elif isinstance(data, list):
                self.translated_news_data = data
                return True
            return False
        except Exception as e:
            print(f"Error loading translated news: {e}")
            return False

    def _load_ai_summaries(self):
        """加载 AI 总结数据"""
        domestic_file = DATA_DIR / "summary_domestic.json"
        international_file = DATA_DIR / "summary_international.json"

        try:
            if domestic_file.exists():
                with open(domestic_file, "r", encoding="utf-8") as f:
                    self.domestic_ai_summary = json.load(f)
        except Exception:
            pass

        try:
            if international_file.exists():
                with open(international_file, "r", encoding="utf-8") as f:
                    self.international_ai_summary = json.load(f)
        except Exception:
            pass

    def get_news(
        self,
        start_date: str = None,
        end_date: str = None,
        keyword: str = None,
        source: str = None
    ) -> Dict[str, Any]:
        """获取筛选后的国内新闻"""
        self.check_and_reload_data()

        filtered = []
        for news in self.news_data:
            include = True

            # 日期筛选
            if start_date and end_date:
                try:
                    news_date = datetime.strptime(news["date"], "%Y-%m-%d").date()
                    start = datetime.strptime(start_date, "%Y-%m-%d").date()
                    end = datetime.strptime(end_date, "%Y-%m-%d").date()
                    if not (start <= news_date <= end):
                        include = False
                except ValueError:
                    include = False

            # 关键词筛选
            if include and keyword:
                if keyword.lower() not in news.get("title", "").lower():
                    include = False

            # 来源筛选
            if include and source:
                if news.get("source") != source:
                    include = False

            if include:
                filtered.append(news)

        # 按日期排序
        filtered.sort(key=lambda x: x.get("date", ""), reverse=True)

        # 统计来源
        source_stats = {}
        for news in filtered:
            src = news.get("source", "Unknown")
            source_stats[src] = source_stats.get(src, 0) + 1

        return {
            "success": True,
            "data": filtered,
            "count": len(filtered),
            "total_count": len(self.news_data),
            "source_stats": source_stats,
            "last_update": self.last_update_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_update_time else None
        }

    def get_news_stats(self) -> Dict[str, Any]:
        """获取国内新闻统计"""
        source_stats = {}
        for news in self.news_data:
            src = news.get("source", "Unknown")
            source_stats[src] = source_stats.get(src, 0) + 1

        return {
            "success": True,
            "total_count": len(self.news_data),
            "source_stats": source_stats,
            "last_update": self.last_update_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_update_time else None
        }

    def get_international_news(
        self,
        start_date: str = None,
        end_date: str = None,
        keyword: str = None,
        source: str = None
    ) -> Dict[str, Any]:
        """获取筛选后的国际新闻（翻译合并数据）"""
        self.check_and_reload_data()

        filtered = []
        for news in self.translated_news_data:
            include = True

            # 日期筛选
            if start_date and end_date:
                try:
                    date_str = news.get("publish_date") or news.get("date", "")
                    if date_str:
                        if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
                            news_date = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
                        else:
                            include = False
                            continue

                        start = datetime.strptime(start_date, "%Y-%m-%d").date()
                        end = datetime.strptime(end_date, "%Y-%m-%d").date()
                        if not (start <= news_date <= end):
                            include = False
                except ValueError:
                    include = False

            # 关键词筛选
            if include and keyword:
                kw_lower = keyword.lower()
                title = news.get("title_translated", "") or news.get("title", "")
                summary = news.get("summary", "")
                if kw_lower not in title.lower() and kw_lower not in summary.lower():
                    include = False

            # 来源筛选
            if include and source:
                if news.get("source") != source:
                    include = False

            if include:
                filtered.append(news)

        # 按日期排序
        filtered.sort(key=lambda x: x.get("publish_date") or x.get("date", ""), reverse=True)

        # 统计来源
        source_stats = {}
        for news in filtered:
            src = news.get("source", "Unknown")
            source_stats[src] = source_stats.get(src, 0) + 1

        return {
            "success": True,
            "data": filtered,
            "count": len(filtered),
            "total_count": len(self.translated_news_data),
            "source_stats": source_stats,
            "last_update": self.last_translated_update_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_translated_update_time else None
        }

    def get_international_stats(self) -> Dict[str, Any]:
        """获取国际新闻统计"""
        source_stats = {}
        for news in self.translated_news_data:
            src = news.get("source", "Unknown")
            source_stats[src] = source_stats.get(src, 0) + 1

        return {
            "success": True,
            "total_count": len(self.translated_news_data),
            "source_stats": source_stats,
            "last_update": self.last_translated_update_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_translated_update_time else None
        }

    def get_ai_summary(self, news_type: str) -> Dict[str, Any]:
        """获取 AI 总结"""
        self._load_ai_summaries()

        if news_type == "domestic":
            return {
                "success": True,
                "data": self.domestic_ai_summary
            }
        elif news_type == "international":
            return {
                "success": True,
                "data": self.international_ai_summary
            }
        else:
            return {
                "success": False,
                "error": "Invalid news type. Use 'domestic' or 'international'."
            }


# 全局单例
news_service = NewsService()
