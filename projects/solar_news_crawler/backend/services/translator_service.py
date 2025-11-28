# -*- coding: utf-8 -*-
"""翻译服务"""
import glob
import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests

from backend.config import DATA_DIR


def find_latest_file(pattern: str, directory: Path = None) -> Optional[str]:
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


class TranslatorService:
    """多源新闻翻译服务"""

    def __init__(self):
        self.cache_file = DATA_DIR / 'translation_cache.json'
        self.translation_cache = self._load_cache()

    def _load_cache(self) -> Dict:
        """加载翻译缓存"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_cache(self):
        """保存翻译缓存"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.translation_cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def translate_text(self, text: str) -> str:
        """使用免费的翻译服务"""
        if not text or not text.strip():
            return text

        cache_key = self._get_cache_key(text)
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]

        translation_methods = [
            self._libretranslate_translate,
            self._mymemory_translate,
            self._simply_translate
        ]

        for method in translation_methods:
            try:
                result = method(text)
                if result and result.strip() and result != text:
                    self.translation_cache[cache_key] = result
                    self._save_cache()
                    return result
            except Exception:
                continue

        return text

    def _libretranslate_translate(self, text: str) -> Optional[str]:
        """使用LibreTranslate"""
        endpoints = [
            "https://translate.argosopentech.com/translate",
            "https://libretranslate.de/translate",
            "https://translate.fortran.is/translate"
        ]

        for endpoint in endpoints:
            try:
                data = {
                    'q': text,
                    'source': 'en',
                    'target': 'zh',
                    'format': 'text'
                }
                response = requests.post(endpoint, json=data, timeout=15)
                if response.status_code == 200:
                    return response.json()['translatedText']
            except Exception:
                continue
        return None

    def _mymemory_translate(self, text: str) -> Optional[str]:
        """使用MyMemory翻译API"""
        try:
            url = "https://api.mymemory.translated.net/get"
            params = {'q': text, 'langpair': 'en|zh'}
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('responseStatus') == 200:
                    return data['responseData']['translatedText']
        except Exception:
            pass
        return None

    def _simply_translate(self, text: str) -> Optional[str]:
        """使用SimplyTranslate"""
        try:
            url = "https://simplytranslate.org/api/translate"
            data = {'text': text, 'from': 'en', 'to': 'zh'}
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                return response.text.strip()
        except Exception:
            pass
        return None

    def process_pv_magazine_file(self, filename: str) -> List[Dict]:
        """处理PV Magazine格式的文件"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            processed_news = []
            for item in data:
                original_title = item.get('title', '')
                translated_title = self.translate_text(original_title)

                news_item = {
                    'title_original': original_title,
                    'title_translated': translated_title,
                    'link': item.get('link', ''),
                    'publish_date': item.get('publish_date', ''),
                    'source': 'PV Magazine',
                    'content_type': item.get('content_type', 'news'),
                    'file_source': os.path.basename(filename)
                }
                processed_news.append(news_item)
                time.sleep(2)

            return processed_news
        except Exception as e:
            print(f"处理PV Magazine文件失败: {e}")
            return []

    def process_irena_file(self, filename: str) -> List[Dict]:
        """处理IRENA格式的文件"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, dict) and 'news_list' in data:
                news_list = data['news_list']
            elif isinstance(data, list):
                news_list = data
            else:
                return []

            processed_news = []
            for item in news_list:
                original_title = item.get('title', '')
                translated_title = self.translate_text(original_title)

                news_item = {
                    'title_original': original_title,
                    'title_translated': translated_title,
                    'link': item.get('link', ''),
                    'publish_date': item.get('date', ''),
                    'source': 'IRENA',
                    'summary': item.get('summary', ''),
                    'category': item.get('category', ''),
                    'language': item.get('language', ''),
                    'file_source': os.path.basename(filename)
                }
                processed_news.append(news_item)
                time.sleep(2)

            return processed_news
        except Exception as e:
            print(f"处理IRENA文件失败: {e}")
            return []

    def process_iea_file(self, filename: str) -> List[Dict]:
        """处理IEA格式的文件"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            processed_news = []
            for item in data:
                original_title = item.get('title', '')
                translated_title = self.translate_text(original_title)

                news_item = {
                    'title_original': original_title,
                    'title_translated': translated_title,
                    'link': item.get('link', ''),
                    'publish_date': item.get('publish_date', ''),
                    'source': 'IEA',
                    'content_type': item.get('content_type', 'news'),
                    'file_source': os.path.basename(filename)
                }
                processed_news.append(news_item)
                time.sleep(2)

            return processed_news
        except Exception as e:
            print(f"处理IEA文件失败: {e}")
            return []

    def merge_and_save_translations(self) -> Optional[str]:
        """合并所有翻译结果并保存"""
        all_news = []

        files_to_process = [
            {
                'filename': find_latest_file('pvmagazine_*.json'),
                'processor': self.process_pv_magazine_file,
                'source': 'PV Magazine'
            },
            {
                'filename': find_latest_file('irena_*.json'),
                'processor': self.process_irena_file,
                'source': 'IRENA'
            },
            {
                'filename': find_latest_file('iea_*.json'),
                'processor': self.process_iea_file,
                'source': 'IEA'
            }
        ]

        for file_info in files_to_process:
            filename = file_info['filename']
            processor = file_info['processor']

            if filename and os.path.exists(filename):
                news_items = processor(filename)
                all_news.extend(news_items)

        output_data = {
            'merge_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_news': len(all_news),
            'sources': {
                'PV Magazine': len([n for n in all_news if n['source'] == 'PV Magazine']),
                'IRENA': len([n for n in all_news if n['source'] == 'IRENA']),
                'IEA': len([n for n in all_news if n['source'] == 'IEA'])
            },
            'news_list': all_news
        }

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"translator_{timestamp}.json"
        output_filepath = DATA_DIR / output_filename

        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        return str(output_filepath)


# 全局单例
translator_service = TranslatorService()
